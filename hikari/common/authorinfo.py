import os.path
import re

from hikari.common.linktype import LinkType
from hikari.common import datebase
from hikari.config.hikari_config import config


class AuthorInfo:
	def __init__(self, platform: LinkType, name: str, userid: str):
		self.platform: str = str(platform)
		self.name: str = name
		self.userid: str = userid

	def generate_save_folder(self):
		root = config.get("default").get("savePath")
		save_name = re.sub(r'[:<>|"?*]', "_", self.name)
		folder = os.path.join(root, self.platform, save_name)
		return folder

	async def get_author_id(self) -> int:
		author_id = await datebase.query_author_id(self)
		if author_id == 0:  # 0代表不存在此作者
			author_id = await datebase.create_author_data(self)
		return int(author_id)


class NoUserAuthor(AuthorInfo):
	def generate_save_folder(self):  # 由于找不到固定的作者，故不设作者文件夹，只使用图片id作为文件名区分,图片直接存在平台文件夹下
		root = config.get("default").get("savePath")
		folder = os.path.join(root, self.platform)
		return folder


# yande找不到固定的作者，直接使用一个作者代替
class YandeUser(NoUserAuthor):
	def __init__(self):
		super().__init__(LinkType.YANDE, 'yande', 'yande')


# Twitter的折中方案，只存图片
class DanbooruUser(NoUserAuthor):
	def __init__(self):
		super().__init__(LinkType.DANBOORU, 'danbooru', 'danbooru')


# Twitter的折中方案，只存图片
class TwimgUser(NoUserAuthor):
	def __init__(self):
		super().__init__(LinkType.TWIMG, 'twimg', 'twimg')
