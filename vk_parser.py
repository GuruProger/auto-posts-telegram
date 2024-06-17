import vk_api
import asyncio
import aiohttp
import time
import sqlite3
from pathlib import Path
from core.config import project_path


class ParserVK:
    def __init__(self):
        self.tasks_channel = []

    async def pars_tasks(self, token, channel_list: list | tuple):
        s = time.time()
        # Авторизация
        vk_session = vk_api.VkApi(token=token)

        for channel_ids in channel_list:
            # Добавляем асинхронные задачи
            self.tasks_channel.append(asyncio.create_task(self.pars_channel(channel_ids, vk_session)))
        await asyncio.gather(*self.tasks_channel)
        e = time.time()
        print(e - s)

    async def pars_channel(self, channel_ids, vk_session):
        # Получение идентификатора канала
        channel_info = vk_session.method('groups.getById', {'group_ids': channel_ids})
        channel_id = -channel_info[0]['id']
        channel_name = channel_info[0]['name']

        # Запрашиваем последние n постов со стены канала
        response = vk_session.method('wall.get', {
            'owner_id': channel_id,
            'count': 10
        })

        self.__info_post = {}  # Информация о постах. Для записи в json

        # Обработка ответа
        tasks = []
        for post in response['items']:
            task = asyncio.create_task(self.__save_post(post, channel_name))
            tasks.append(task)
        await asyncio.gather(*tasks)
        self.write_info(channel_name)

    async def __save_post(self, post, channel_name: str):
        # Чистка названия канала для сохранения
        combined_channel_name = channel_name + '_' + str(post['id'])
        # Создание пути для сохранения
        path_for_save = project_path / 'core' / 'data' / channel_name
        # Создание папок для сохранения, если они не существуют
        [Path(path).mkdir(parents=True, exist_ok=True) for path in [
            path_for_save,
            path_for_save / 'photo',
            path_for_save / 'text',
        ] if not Path(path).exists()]

        # Если текст не пустой
        if post['text'] != '':
            self.__info_post[int(post['id'])] = {'text_exists': True}
        # Текст
        else:
            self.__info_post[int(post['id'])] = {'text_exists': False}

        # Проверяем, есть ли в посте вложения
        count_photo = 0
        if len(post['attachments']) != 0:

            # Сохранение каждой фотографии
            for photo in post['attachments']:
                # Проверяем, есть ли во вложении фото
                if photo['type'] == 'photo':
                    count_photo += 1
        self.__info_post[int(post['id'])]['count_photo'] = count_photo

        if self.__info_post[int(post['id'])]['text_exists']:
            # Сохраняем текст

            with open(path_for_save / 'text' / (str(post['id']) + '.txt'), 'w', encoding='utf-8') as f_txt:
                f_txt.write(post['text'])

        if self.__info_post[int(post['id'])]['count_photo']:
            tasks_photo = []
            count_photo = 1
            for photo in post['attachments']:
                try:
                    photo_url = photo['photo']['sizes'][-1]['url']
                except:
                    print(photo)

                path_photo = path_for_save / 'photo' / (str(post['id']) + f'-item-{count_photo}.jpg')
                count_photo += 1
                tasks_photo.append(asyncio.create_task(self.__save_photo(photo_url, path_photo)))
            # Сохраняем фотографии
            await asyncio.gather(*tasks_photo)

    def write_info(self, name):
        with sqlite3.connect(project_path / 'core' / 'data' / 'info.db') as database:
            cursor = database.cursor()

            # Создание таблицы, если она не существует
            cursor.execute(f"""CREATE TABLE IF NOT EXISTS "{name}" (
            post_id INTEGER PRIMARY KEY,
            text_exists INTEGER,
            count_photo INTEGER,
            used_post INTEGER
            )""")

            for post_id in self.__info_post:
                text_exists = int(self.__info_post[post_id]['text_exists'])
                count_photo = self.__info_post[post_id]['count_photo']

                try:
                    cursor.execute(f'INSERT INTO "{name}" (post_id, text_exists, count_photo, used_post) VALUES (?, ?, ?, ?)',
                                   (post_id, text_exists, count_photo, 0))
                except sqlite3.IntegrityError:
                    # Запись уже существует
                    pass

            database.commit()

    @staticmethod
    async def __save_photo(photo_url, path_photo):
        async with aiohttp.ClientSession() as session:
            async with session.get(photo_url, ssl=False) as response:
                photo_data = await response.read()
                # Сохраняем фото
                with open(path_photo, 'wb') as f_jpg:
                    f_jpg.write(photo_data)


if __name__ == '__main__':
    from core.config import vk_bot_token, channel_list

    pars = ParserVK()

    asyncio.run(pars.pars_tasks(token=vk_bot_token, channel_list=channel_list))
