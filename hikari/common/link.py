###############################################################
# Link类主要提供fetch方法，获取链接中的内容
###############################################################
import logging

from enum import Enum

from hikari.common import datebase
from hikari.common.linktype import LinkType
from hikari.common.character import Character
from hikari.common import content


class TaskStatus(Enum):
	NOT_EXIST = 1
	EXIST_BUT_NOT_COMPLETE = 2
	FAIL = 3
	DONE = 4


class Link:
	def __init__(self, url: str):
		self.url = url
		self.linktype = Character.match(url)  # if not match: raise LinktypeNotExistError
		self.task_id = 0
		self.task_done = False

	async def create_link_task(self):
		self.task_id = await datebase.create_link_task_to_database(self.url)
		logging.info(f"识别到链接{self.url}, 已创建下载任务,id={self.task_id}")

	async def mark_link_task_done(self):
		await datebase.mark_task_done(self.task_id)
		logging.info(f"链接任务id={self.task_id}已标记完成")

	async def check_duplicated_task(self):
		res = await datebase.check_duplicated_task(self.url)
		if not res:
			return TaskStatus.NOT_EXIST, {}
		elif res['complete'] and not res['fail']:
			return TaskStatus.DONE, {}
		elif not res['complete'] and not res['fail']:
			return TaskStatus.EXIST_BUT_NOT_COMPLETE, res
		elif res['fail']:
			return TaskStatus.FAIL, res

	async def rebuild_content_element(self):
		elements_meta = await datebase.query_download_history_by_task_id(self.task_id)
		for element_meta in elements_meta:
			pass  # 重建元素

	async def __fetch(self):
		parse_func = {
			LinkType.PIXIV: content.Pixiv,
			LinkType.TWITTER: content.Twitter,
			LinkType.TWIMG: content.Twimg,
			LinkType.DANBOORU: content.Danbooru,
			LinkType.FANBOX: content.Fanbox,
			LinkType.YANDE: content.Yande,
			LinkType.KEMONO: content.Kemono,
			LinkType.FANTIA: content.Fantia
		}
		return parse_func.get(self.linktype)(self.url)

	async def start(self):
		task_status, res = await self.check_duplicated_task()
		if task_status is TaskStatus.NOT_EXIST:  # 不存在，开启标准下载流程
			await self.create_link_task()
			content_obj = await self.__fetch()
			content_obj.link_database_id = self.task_id
			await content_obj.start()
			self.task_done = content_obj.link_task_done
			if self.task_done:
				await self.mark_link_task_done()
		elif task_status is TaskStatus.DONE:
			# 已完成，但还是有可能文件损坏，找对应的元素重建 逐个检查完整性
			logging.info(f"{self.url} 已完成，若要强制重试请使用-r指令")
		elif task_status is TaskStatus.EXIST_BUT_NOT_COMPLETE:
			# 没完成也没失败，找找download_history有没有对应元素，对应元素是否完成，
			logging.info(f"{self.url} 可能正在进行中，若要强制重试请使用-r指令")
		elif task_status is TaskStatus.FAIL:
			logging.info(f"{self.url} 任务失败，失败原因为：{res['reason']}，尝试重建任务")

# # 对应每个网站的解析方法
# async def __fetch_pixiv(self) -> Content:
# 	# 先获取pixiv的图片基础信息
# 	if "member_illust.php" in self.url:
# 		re_result = re.match(r"https?://www.pixiv.net/member_illust.php\?mode=\w+&illust_id=(\d{8,9})", self.url
# 		                     ).groups()
# 	else:
# 		re_result = re.match(r"https?://www.pixiv.net/artworks/(\d{8,9})", self.url).groups()
# 	pixiv_id = re_result[0]
# 	pixiv_userinfo_url = pixiv_info_url(pixiv_id)
#
# 	async with aiohttp.ClientSession() as session:
# 		async with session.get(pixiv_userinfo_url, proxy=self.proxy_path) as response:
# 			resp_json = await response.json()
#
# 	# 请求错误处理
# 	if resp_json["error"] is True:
# 		raise LinkServerRaiseError(f"{self.url} {resp_json['message']}")
# 	# 如果是动图则跳过下载
# 	if (illust_type := resp_json["body"]["illustType"]) != 0:
# 		raise FileCanNotDownloadError(f"{self.url}不是图片, illustType={illust_type}")
#
# 	# 请求正确，获取用户信息
# 	user_id = resp_json["body"]["userId"]
# 	user_name = resp_json["body"]["userName"]
# 	image_count = resp_json["body"]["pageCount"]
# 	illust_id = resp_json["body"]["illustId"]
# 	userinfo = AuthorInfo(self.linktype, user_name, user_id)
# 	content = Content(self.url, userinfo)
# 	if image_count == 1:
# 		filename = f"{illust_id}_p0"
# 		picture = Picture(pixiv_proxy_url(illust_id),
# 		                  userinfo.generate_save_folder(),
# 		                  filename
# 		                  )
# 		content.element = [picture]
# 	elif image_count > 1:
# 		for p in range(image_count):
# 			filename = f"{illust_id}_p{p}"
# 			picture = Picture(pixiv_proxy_url(illust_id, p + 1),
# 			                  userinfo.generate_save_folder(),
# 			                  filename
# 			                  )
# 			content.element.append(picture)
# 	return content

# async def __fetch_twitter(self) -> Content:
# 	"""
# 	推特会有一个链接下，有两个推文文内容（发推人不一定一致）的情况，此处只能返回两个Content
# 	:return:
# 	"""
# 	index_iter = index_generator()
#
# 	re_result = re.findall(r"\d{18,}", self.url)
# 	if not re_result:
# 		raise LinktypeNotExistError(self.url)
# 	tweet_id = str(re_result[0])
#
# 	content = Content(self.url)
#
# 	resp_json = await tweet_brief(tweet_id)
#
# 	# 如推文被删除等错误
# 	if "errors" in resp_json:
# 		raise LinkServerRaiseError(resp_json["errors"][0]["message"])
#
# 	entries_list = resp_json['data']['threaded_conversation_with_injections_v2']['instructions'][0]['entries']
# 	tweet_detail = tuple(filter(lambda entry: entry['entryId'].startswith('tweet-'), entries_list))[-1]
# 	tweet_info = tweet_detail['content']['itemContent']['tweet_results']['result']
# 	if "tweet" in tweet_info:  # 当推文内容为视频时，返回值格式会有变化，此处消除该变化，令其与图片的格式一致
# 		tweet_info = tweet_info["tweet"]
#
# 	user_rest_id = tweet_info['core']['user_results']['result']['rest_id']  # 这个id用于关注推特用户
#
# 	user_info = tweet_info['core']['user_results']['result']['legacy']
# 	name = user_info['name']  # 用户名
# 	screen_name = user_info['screen_name']  # @后面的字符
#
# 	twitter_user = AuthorInfo(self.linktype, name, screen_name)
# 	content.author_info = twitter_user
# 	save_folder = twitter_user.generate_save_folder()
#
# 	tweet_favorited = tweet_info['legacy']['favorited']
# 	if (not tweet_favorited) and config.get("setting").get("favoritedTweetAfterDownload"):
# 		like_success, like_error_msg = await like_tweet(tweet_id)
# 		if like_success:
# 			logging.info(f"已点赞推文{self.url}")
# 		else:
# 			logging.info(f"点赞失败，{like_error_msg}")
#
# 	media_contents = tweet_info['legacy']['extended_entities']['media']
# 	for media_content in media_contents:
# 		media_type = media_content['type']
# 		if media_type in ['video', 'animated_gif']:
# 			videos_info = filter(lambda video: video['content_type'] == 'video/mp4',
# 			                     media_content['video_info']['variants']
# 			                     )
# 			media_url_https = max(videos_info, key=itemgetter('bitrate'))['url']
# 			video_element = Video(media_url_https, save_folder, f"{tweet_id}_p{next(index_iter)}")
# 			content.element.append(video_element)
# 		elif media_type == 'photo':
# 			media_url_https = media_content['media_url_https'] + '?format=jpg&name=4096x4096'
# 			image_element = Picture(media_url_https, save_folder, f"{tweet_id}_p{next(index_iter)}")
# 			content.element.append(image_element)
# 		else:
# 			raise FileCanNotDownloadError(f'twitter内容解析:{media_type}是不支持的media类型')
#
# 	return content
#
# async def __fetch_fanbox(self) -> Content:
# 	pass
#
# async def __fetch_yande(self) -> Content:
# 	pass
#
# async def __fetch_kemono(self) -> Content:
# 	pass
#
# async def __fetch_fantia(self) -> Content:
# 	pass
