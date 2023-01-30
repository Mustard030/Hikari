###############################################################
# 输入链接后 获取页面内容
# 主要用于承接Link和Downloadable的过渡类
###############################################################
import asyncio
import logging
import re
import aiohttp
import urllib.parse

from bs4 import BeautifulSoup

from hikari.common import downloadable, authorinfo
from hikari.common.exceptions import FileCanNotDownloadError, LinkServerRaiseError
from hikari.common.function import index_generator, like_pixiv_image, pixiv_info_url, pixiv_proxy_url, proxy_path
from hikari.common.linktype import LinkType


class Content:
	def __init__(self, url):
		self.source_url: str = url
		self.link_database_id: int = 0
		self.platform: "LinkType" = LinkType.NONE  # 为了创建作者，已知作者就没有意义了
		self.element_list: list["downloadable.Downloadable"] = []
		self.author: "authorinfo.AuthorInfo" = None
		self.content_origin_data: dict | BeautifulSoup = {}
		self.link_task_done = False

	def __str__(self):
		return self.source_url

	async def init(self):
		pass

	async def preprocess(self):
		pass

	async def parse_author(self):
		pass

	async def parse_element(self):
		pass

	async def create_download_history(self):
		author_id = await self.author.get_author_id()
		for element in self.element_list:
			await element.create_download_history(self.source_url, self.link_database_id, author_id)

	async def download_elements(self):
		await asyncio.wait([file.download() for file in self.element_list])
		self.link_task_done = all([element.verified for element in self.element_list])

	async def post_processing(self):
		pass

	# 统一开始入口
	async def start(self):
		# 获取初始信息，主要目的是获取信息后赋值self.content_origin_data
		await self.init()
		# 预处理，处理self.content_origin_data中的内容，如错误返回识别，等
		await self.preprocess()
		# 分析author
		await self.parse_author()
		# 分析所有的element
		await self.parse_element()
		# 创建element的数据库下载记录并把id给对应的Downloadable元素,标记完成由Downloadable元素自己负责
		await self.create_download_history()
		# 开启下载
		await self.download_elements()
		# 后处理（如点赞）
		await self.post_processing()


class Pixiv(Content):
	def __init__(self, url):
		super().__init__(url)
		self.platform = LinkType.PIXIV
		self.pixiv_id = ''

	async def init(self):
		# 先获取pixiv的图片基础信息
		if "member_illust.php" in self.source_url:
			re_result = re.match(r"https?://www.pixiv.net/member_illust.php\?mode=\w+&illust_id=(\d{8,9})",
			                     self.source_url
			                     ).groups()
		else:
			re_result = re.match(r"https?://www.pixiv.net/artworks/(\d{8,9})", self.source_url).groups()
		pixiv_id = re_result[0]
		pixiv_userinfo_url = pixiv_info_url(pixiv_id)

		async with aiohttp.ClientSession() as session:
			async with session.get(pixiv_userinfo_url, proxy=proxy_path()) as response:
				self.content_origin_data = await response.json()

	async def preprocess(self):
		# 请求错误处理
		if self.content_origin_data["error"] is True:
			raise LinkServerRaiseError(f"{self.source_url} {self.content_origin_data['message']}")
		# 如果是动图则跳过下载
		if (illust_type := self.content_origin_data["body"]["illustType"]) != 0:
			raise FileCanNotDownloadError(f"{self.source_url}不是图片, illustType={illust_type}")

	async def parse_author(self):
		user_id = self.content_origin_data["body"]["userId"]
		user_name = self.content_origin_data["body"]["userName"]
		self.author = authorinfo.AuthorInfo(self.platform, user_name, user_id)

	async def parse_element(self):
		image_count = self.content_origin_data["body"]["pageCount"]
		illust_id = self.content_origin_data["body"]["illustId"]
		self.pixiv_id = illust_id
		save_folder = self.author.generate_save_folder()
		if image_count == 1:
			filename = f"{illust_id}_p0"
			picture = downloadable.Picture(pixiv_proxy_url(illust_id), save_folder, filename)
			self.element_list = [picture]
		elif image_count > 1:
			for p in range(image_count):
				filename = f"{illust_id}_p{p}"
				picture = downloadable.Picture(pixiv_proxy_url(illust_id, p + 1), save_folder, filename)
				self.element_list.append(picture)

	async def post_processing(self):
		like_error, error_message = await like_pixiv_image(self.pixiv_id)
		if like_error:
			logging.info(error_message)


# 推特不敢搞了
class Twitter(Content):
	def __init__(self, url):
		super().__init__(url)
		self.platform = LinkType.TWITTER


class Yande(Content):
	def __init__(self, url):
		super().__init__(url)
		self.platform = LinkType.YANDE
		self.author = authorinfo.YandeUser()


class Kemono(Content):
	def __init__(self, url, skip=0):
		super().__init__(url)
		self.re_result = re.match(r"https://www.kemono.party/\w+/user/(?P<userid>\d+)/post/(?P<postid>\d+)",
		                          self.source_url
		                          ).groupdict()
		self.platform = LinkType.KEMONO
		self.host = "https://www.kemono.party"
		self.skip = skip

	async def init(self):
		async with aiohttp.ClientSession() as session:
			async with session.get(self.source_url, proxy=proxy_path()) as response:
				html = await response.text()
				self.content_origin_data = BeautifulSoup(html, "lxml")

	async def parse_author(self):
		author_name = self.content_origin_data.find('a', class_="post__user-name").text.strip()
		author_id = self.re_result['userid']
		self.author = authorinfo.AuthorInfo(platform=self.platform, name=author_name, userid=author_id)

	async def parse_element(self):
		index_gen = index_generator()
		post_id = self.re_result['postid']
		save_folder = self.author.generate_save_folder()
		file_list = self.content_origin_data.findAll('a', class_="post__attachment-link")  # .attrs['href']
		image_list = self.content_origin_data.findAll('a', class_="fileThumb")[self.skip:]
		for file in file_list:
			bare_url = file.get("href")
			file_name = urllib.parse.unquote(bare_url.split('?f=')[1])
			if ".mp4" in file_name:
				video = downloadable.Video(url=self.host + bare_url, folder=save_folder, filename=file_name.removesuffix(".mp4"))
				self.element_list.append(video)
			elif ".zip" in file_name:
				zf = downloadable.ZipFile(url=self.host + bare_url, folder=save_folder, filename=file_name.removesuffix(".zip"))
				self.element_list.append(zf)

		for image in image_list:
			bare_url = image.get("href")
			file_name = f"{post_id}_p{next(index_gen)}"
			_image = downloadable.Picture(url=self.host + bare_url, folder=save_folder, filename=file_name)
			self.element_list.append(_image)


class Fantia(Content):
	def __init__(self, url):
		super().__init__(url)
		self.platform = LinkType.FANTIA


class Fanbox(Content):
	def __init__(self, url):
		super().__init__(url)
		self.platform = LinkType.FANBOX

