import sqlite3
import logging
from ..config import project_path

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def fetch_unused_posts(channel_name):
    """
    Получение не использованных постов (used_post = 0) из базы данных.
    """
    unused_posts = {}
    database_path = project_path / 'core' / 'data' / 'info.db'
    with sqlite3.connect(database_path) as database:
        cursor = database.cursor()

        # Проверка существования таблицы для данного канала
        cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{channel_name}'")
        if not cursor.fetchone():
            logger.warning(f"Таблица для канала '{channel_name}' не найдена в базе данных.")
            return []

        # Извлечение всех неиспользованных постов
        cursor.execute(f"SELECT post_id, text_exists, count_photo FROM '{channel_name}' WHERE used_post = 0")
        for post_id, text_exists, count_photo in cursor.fetchall():
            unused_posts[post_id] = {
                "text_exists": bool(text_exists),
                "count_photo": count_photo
            }

    logger.info(f"Найдено {len(unused_posts)} неиспользованных постов для канала '{channel_name}'.")
    return unused_posts


def get_post_file_paths(channel_name, post_id, text_exists, count_photo):
    """
    Получает пути ко всем файлам (текст и фото) для указанного поста.
    """
    base_path = project_path / 'core' / 'data' / channel_name

    # Путь к текстовому файлу
    text_file_path = base_path / 'text' / f"{post_id}.txt" if text_exists else None

    # Пути к фото
    photo_paths = [
        base_path / 'photo' / f"{post_id}-item-{i + 1}.jpg"
        for i in range(count_photo)
    ]

    return text_file_path, photo_paths


def mark_posts_as_used(channel_name, post_ids):
    """
    Пометить пост использованным (used_post на 1
    """
    database_path = project_path / 'core' / 'data' / 'info.db'
    with sqlite3.connect(database_path) as database:
        cursor = database.cursor()

        for post_id in post_ids:
            cursor.execute(f"UPDATE '{channel_name}' SET used_post = 1 WHERE post_id = ?", (post_id,))

        database.commit()
        logger.info(f"Обновлено {len(post_ids)} постов как использованные для канала '{channel_name}'.")
