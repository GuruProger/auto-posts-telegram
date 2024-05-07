import os
from pathlib import Path
from dotenv import load_dotenv


def _checking_folder():
	data_path = Path(__file__).resolve().parent / 'data'
	print(data_path)
	if not data_path.exists():
		data_path.mkdir()


project_path = Path(__file__).resolve().parent.parent
_checking_folder()
load_dotenv(os.path.join(project_path, ".env"))
vk_bot_token = os.getenv("TOKEN_VK")
tg_bot_token = os.getenv("TOKEN_TG")

channel_tg_id = os.getenv("CHANNEL_TG_ID")

channel_list = tuple(os.getenv("CHANNEL_LIST").split())
