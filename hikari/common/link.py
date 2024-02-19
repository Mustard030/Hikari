###############################################################
# Link类主要提供fetch方法，获取链接中的内容
###############################################################
import logging

from enum import Enum

from hikari.common.character import match_strategy
from hikari.common.countdown import count_down_to_retry
from hikari.common.databases import database_async_functions
from hikari.common.databases.database_models import DBTaskModel
from hikari.common.downloadable import Picture, ZipFile, Video, GifFile
from hikari.common.filetype import DownloadableFileType


class TaskStatus(Enum):
    NOT_EXIST = 1
    EXIST_BUT_NOT_COMPLETE = 2
    FAIL = 3
    DONE = 4


class Link:
    def __init__(self, url: str = None, task_id: int = 0):
        self.url = url
        self.strategy = match_strategy(url) if url else None
        self.task_id = task_id
        self.task_done = False

    async def create_database_link_task(self):
        self.task_id = await database_async_functions.create_link_task_to_database(self.url)
        logging.info(f"识别到链接{self.url}, 已创建下载任务,id={self.task_id}")

    async def mark_database_link_task_done(self):
        await database_async_functions.mark_task_done(self.task_id)
        logging.info(f"链接任务id={self.task_id}已标记完成")

    async def mark_database_link_task_fail(self, reason: str):
        await database_async_functions.mark_task_fail(str(reason), self.task_id)
        logging.info(f"链接任务id={self.task_id}已标记失败，原因为{reason}")

    async def check_duplicated_task(self) -> tuple[TaskStatus, DBTaskModel | None]:

        res = await database_async_functions.check_duplicated_task_by_content(self.url)
        if not res:
            return TaskStatus.NOT_EXIST, res
        elif res.complete and not res.fail:
            self.task_id = res.id
            return TaskStatus.DONE, res
        elif not res.complete and not res.fail:
            self.task_id = res.id
            return TaskStatus.EXIST_BUT_NOT_COMPLETE, res
        elif res.fail:
            self.task_id = res.id
            return TaskStatus.FAIL, res

    async def rebuild_content_element(self):
        elements_meta = await database_async_functions.query_download_history_by_task_id(self.task_id)
        elements_list = []
        filetype_to_class = {
            DownloadableFileType.Picture: Picture,
            DownloadableFileType.Video: Video,
            DownloadableFileType.ZipFile: ZipFile,
            DownloadableFileType.GifFile: GifFile,
        }
        for element_meta in elements_meta:
            obj = filetype_to_class[element_meta.filetype](database_download_id=element_meta.id, url=element_meta.url,
                                                           save_path=element_meta.local_path)
            elements_list.append(obj)
        return elements_list

    async def retry(self, taskid=0, force=False):
        """
        通过重试任务创建Link对象，需要传入url和已存在的task
        :params taskid:若需要重试特定任务id则传入该参数
        :params force:删除已解析的元素和对应文件并重新获取元素信息下载
        """
        count_down_to_retry.reset()
        if taskid != 0:  # 重试特定任务id
            task_obj = await database_async_functions.query_task_by_id(taskid)
        else:  # 自动挑选一个任务
            task_obj = await database_async_functions.uncompleted_task()

        if task_obj is None:  # 先行判断要重试的任务是否存在
            logging.warning("No uncompleted task or task id is not exist")
            return

        self.task_id = task_obj.id
        self.url = task_obj.content
        self.strategy = match_strategy(self.url)

        await database_async_functions.increase_retry_times(self.task_id)  # 更新重试次数，防止无限重试

        elements = await self.rebuild_content_element()
        if elements and not force:  # 如果有查到下载记录即链接解析成功但部分文件未完成下载
            # TODO: 查询下载记录，若已存在对应文件，则下载未完成的文件，检查已完成的文件完整性
            content_obj = self.strategy.get_content(self.url)
            content_obj.element_list = elements
            try:
                await content_obj.download_elements()
            except* Exception as e:
                await self.mark_database_link_task_fail(str(e.exceptions[0]))
            self.task_done = content_obj.link_task_done
            if self.task_done:
                await self.mark_database_link_task_done()
        else:  # TODO:链接解析失败，需要重新解析链接并下载
            content_obj = self.strategy.get_content(self.url)
            content_obj.link_database_id = self.task_id
            try:
                await content_obj.start()
            except* Exception as e:
                await self.mark_database_link_task_fail(str(e.exceptions[0]))
            self.task_done = content_obj.link_task_done
            if self.task_done:
                await self.mark_database_link_task_done()

    async def start(self, force=False):
        count_down_to_retry.reset()
        task_status, task_obj = await self.check_duplicated_task()
        if task_status is TaskStatus.NOT_EXIST:  # 不存在，开启标准下载流程
            content_obj = self.strategy.get_content(self.url)  # 先走url判断再创建数据库行，可以避免错误格式url被存入数据库
            await self.create_database_link_task()
            content_obj.link_database_id = self.task_id
            try:
                await content_obj.start()
            except* Exception as e:
                await self.mark_database_link_task_fail(str(e.exceptions[0]))
            self.task_done = content_obj.link_task_done
            if self.task_done:
                await self.mark_database_link_task_done()
        elif task_status is TaskStatus.DONE:
            if force:
                # 已完成，但还是有可能文件损坏，找对应的元素重建对象 逐个检查完整性
                content_obj = self.strategy.get_content(self.url)
                content_obj.link_database_id = self.task_id
                history_list = await database_async_functions.query_download_history_by_task_id(task_obj.id)
                for history in history_list:
                    pass
            else:
                logging.info(f"{self.url} 已完成，若要强制重试请使用-rf指令")
        elif task_status is TaskStatus.EXIST_BUT_NOT_COMPLETE:
            # 没完成也没失败，找找download_history有没有对应元素，对应元素是否完成，
            logging.info(f"{self.url} 可能正在进行中，若要强制重试请使用-rf指令")
        elif task_status is TaskStatus.FAIL:
            logging.info(f"{self.url} 任务失败，失败原因为：{task_obj.reason}，尝试重建任务")
            await self.retry(taskid=task_obj.id)


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
	# media_contents = tweet_info['legacy']['extended_entities']['media']
	# for media_content in media_contents:
	# 	media_type = media_content['type']
	# 	if media_type in ['video', 'animated_gif']:
	# 		videos_info = filter(lambda video: video['content_type'] == 'video/mp4',
	# 		                     media_content['video_info']['variants']
	# 		                     )
	# 		media_url_https = max(videos_info, key=itemgetter('bitrate'))['url']
	# 		video_element = Video(media_url_https, save_folder, f"{tweet_id}_p{next(index_iter)}")
	# 		content.element.append(video_element)

