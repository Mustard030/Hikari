###############################################################
# 输入链接后 获取页面内容
# 主要用于承接Link和Downloadable的过渡类
###############################################################
import asyncio
import logging
import re
import urllib.parse
import aiohttp
from bs4 import BeautifulSoup

from hikari.common import downloadable, authorinfo
from hikari.common.exceptions import CannotFoundElementError, FileCanNotDownloadError, LinkServerRaiseError, \
    LinktypeNotExistError
from hikari.common.function import index_generator, like_pixiv_image, pixiv_info_url, pixiv_proxy_url, proxy_path, \
    sankaku_info_url, sankaku_post_url
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
        return f"""<Content {self.__class__.__name__}
		source:{self.source_url}
		>"""

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
        async with asyncio.TaskGroup() as tg:
            [tg.create_task(file.download()) for file in self.element_list]
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
        self.pixiv_id = self.content_origin_data["body"]["illustId"]

        save_folder = self.author.generate_save_folder()
        if image_count == 1:
            filename = f"{self.pixiv_id}_p0"
            picture = downloadable.Picture(url=pixiv_proxy_url(self.pixiv_id), folder=save_folder, filename=filename)
            self.element_list = [picture]
        elif image_count > 1:
            for p in range(image_count):
                filename = f"{self.pixiv_id}_p{p}"
                picture = downloadable.Picture(url=pixiv_proxy_url(self.pixiv_id, p + 1), folder=save_folder,
                                               filename=filename
                                               )
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


class Twimg(Content):
    def __init__(self, url):
        super().__init__(url)
        self.platform = LinkType.TWIMG

    async def parse_author(self):
        self.author = authorinfo.TwimgUser()

    async def parse_element(self):
        res = re.match(r"https://pbs.twimg.com/media/(?P<filename>[\w\d_-]+)", self.source_url)
        if not res:
            raise LinktypeNotExistError(self.source_url)

        file_url = res.group() + '?format=png&name=4096x4096'
        filename = res.groupdict().get('filename')
        save_folder = self.author.generate_save_folder()
        image = downloadable.Picture(url=file_url, folder=save_folder, filename=filename, suffix='png')
        self.element_list.append(image)


class Danbooru(Content):
    def __init__(self, url):
        super().__init__(url)
        self.platform = LinkType.DANBOORU

    async def init(self):
        res = re.match(r"https://danbooru.donmai.us/posts/(\d+)", self.source_url)
        url = res.group() + '.json'
        async with aiohttp.ClientSession() as session:
            async with session.get(url, proxy=proxy_path()) as response:
                self.content_origin_data = await response.json()

    async def parse_author(self):
        self.author = authorinfo.DanbooruUser()

    async def parse_element(self):
        save_folder = self.author.generate_save_folder()
        filename = self.content_origin_data['id']
        file_url = self.content_origin_data['file_url']
        picture = downloadable.Picture(file_url, save_folder, filename)
        self.element_list.append(picture)


class Gelbooru(Content):
    def __init__(self, url):
        super().__init__(url)
        self.platform = LinkType.GELBOORU

    async def init(self):
        res = re.search(r"id=(?P<id>\d+)", self.source_url)
        url = f"https://gelbooru.com/index.php?page=dapi&s=post&q=index&json=1&id={res.groupdict().get('id')}"
        async with aiohttp.ClientSession() as session:
            async with session.get(url, proxy=proxy_path()) as response:
                self.content_origin_data = await response.json()

    async def parse_author(self):
        self.author = authorinfo.GelbooruUser()

    async def parse_element(self):
        save_folder = self.author.generate_save_folder()
        filename = self.content_origin_data.get('post')[0]['id']
        file_url = self.content_origin_data.get('post')[0]['file_url']
        picture = downloadable.Picture(file_url, save_folder, filename)
        self.element_list.append(picture)


class Yande(Content):
    def __init__(self, url):
        if 'browse' in url:
            id_ = re.search(r'(\d+)', url).groups()[0]
            url = self.yande_post_url(id_)
        super().__init__(url)
        self.platform = LinkType.YANDE
        self.author = authorinfo.YandeUser()
        self.yande_parent_url = url
        self.child_posts = []

    @staticmethod
    def yande_post_url(post_id):
        return f"https://yande.re/post/show/{post_id}"

    @staticmethod
    def yande_post_id(url):
        return re.search(r'/post/(show|browse)(/|#)(?P<postid>\d+)', url).groupdict().get('postid')

    @staticmethod
    def get_image_url_in_this_page(html: str | BeautifulSoup) -> str:
        """
		从yande页面中获取下载原图的链接
		:param html:
		:return:
		"""
        if isinstance(html, str):
            html = BeautifulSoup(html, "lxml")
        elif isinstance(html, BeautifulSoup):
            pass
        else:
            raise ValueError

        file_list = html.findAll('a', class_="original-file-changed") + html.findAll('a',
                                                                                     class_="original-file-unchanged"
                                                                                     )
        big_file = file_list[-1]
        return big_file.get('href')

    @staticmethod
    async def fetch_this_post_html(url) -> BeautifulSoup:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, proxy=proxy_path()) as response:
                html = await response.text()
                return BeautifulSoup(html, "lxml")

    # 没有父图像(自己就是父图像)或者无关紧要的提示，直接作为源数据
    async def init(self):
        self.content_origin_data = await self.fetch_this_post_html(self.source_url)
        status_notices = self.content_origin_data.findAll('div', class_='status-notice')

        # 看看提示说了什么
        for notice in status_notices:
            if 'This post belongs to a parent post' in notice.text:  # 有父图像, 父图像作为源数据传入
                parent_post_href = notice.find('a').get('href')
                if post_id := self.yande_post_id(parent_post_href):
                    self.yande_parent_url = self.yande_post_url(post_id)  # 格式化父图像的url
                    self.content_origin_data = await self.fetch_this_post_html(self.yande_parent_url)
                    return
                else:
                    raise CannotFoundElementError(f"yande can't find parent post id in \"{parent_post_href}\"")

    # 此时self.content_origin_data中一定是父图像的页面数据，可以开始解析子图像存在
    async def preprocess(self):
        status_notices = self.content_origin_data.findAll('div', class_='status-notice')
        # 看看提示说了什么
        for notice in status_notices:
            if 'child post' in (notice_text := notice.text):  # 有子图像
                self.child_posts = re.findall(r'(\d+)', notice_text)  # 拿到子图像的id列表

    async def parse_element(self):
        # 现在已经拿到了父图像的网页内容和子图像的id列表
        image_url = self.get_image_url_in_this_page(self.content_origin_data)
        save_folder = self.author.generate_save_folder()
        image = downloadable.Picture(url=image_url, folder=save_folder,
                                     filename=self.yande_post_id(self.yande_parent_url),
                                     custom_source=self.yande_parent_url
                                     )
        self.element_list.append(image)

        for child_post_id in self.child_posts:  # 根据子图像的id列表拿到每一个子图像的下载链接
            child_post_url = self.yande_post_url(child_post_id)
            child_html = await self.fetch_this_post_html(child_post_url)
            child_image_url = self.get_image_url_in_this_page(child_html)
            image = downloadable.Picture(url=child_image_url, folder=save_folder,
                                         filename=child_post_id,
                                         custom_source=child_post_url
                                         )
            self.element_list.append(image)

    async def create_download_history(self):
        author_id = await self.author.get_author_id()
        for element in self.element_list:
            await element.create_download_history(element.custom_source, self.link_database_id, author_id)


class Kemono(Content):
    def __init__(self, url, skip=0):
        super().__init__(url)
        self.re_result = re.match(r"https://(www.)?kemono.(party|su)/\w+/user/(?P<userid>\d+)/post/(?P<postid>\d+)",
                                  self.source_url
                                  ).groupdict()
        self.platform = LinkType.KEMONO
        self.host = "https://kemono.su"
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
        file_list = self.content_origin_data.findAll('a', class_="post__attachment-link")
        image_list = self.content_origin_data.findAll('a', class_="fileThumb")[self.skip:]
        for file in file_list:
            href_url = file.get("href")
            file_name = urllib.parse.unquote(href_url.split('?f=')[1])
            if ".mp4" in file_name:
                self.element_list.append(downloadable.Video(url=href_url, folder=save_folder,
                                                            filename=f"{post_id}_p{next(index_gen)}"
                                                            )
                                         )
            elif ".mov" in file_name:
                self.element_list.append(downloadable.Video(url=href_url, folder=save_folder,
                                                            filename=f"{post_id}_p{next(index_gen)}"
                                                            )
                                         )
            elif ".zip" in file_name:
                self.element_list.append(downloadable.ZipFile(url=href_url, folder=save_folder,
                                                              filename=f"{post_id}_p{next(index_gen)}"
                                                              )
                                         )

        for image in image_list:
            href_url = image.get("href")
            file_name = f"{post_id}_p{next(index_gen)}"
            _image = downloadable.Picture(url=href_url,
                                          folder=save_folder,
                                          filename=file_name,
                                          )
            self.element_list.append(_image)


class Sankaku(Content):
    def __init__(self, url):
        super().__init__(url)
        self.platform = LinkType.SANKAKU
        self.author = authorinfo.SankakuUser()

    async def init(self):
        sankaku_id = re.search(r"show/(\d+)", self.source_url).groups()[0]
        sankaku_info = sankaku_info_url()
        query = {
            "page": 1,
            "limit": 40,
            "tags": f"id_range:{sankaku_id}"
        }
        async with aiohttp.ClientSession() as session:
            async with session.get(sankaku_info, params=query, proxy=proxy_path()) as response:
                temp_resp = await response.json()

                if temp_resp[0]["parent_id"] is not None:  # 有父找父
                    sankaku_id = temp_resp["parent_id"]
                    query['tags'] = f"parent:{sankaku_id}"
                    async with session.get(sankaku_info, params=query, proxy=proxy_path()) as resp:
                        self.content_origin_data = await resp.json()
                elif temp_resp[0]["has_children"]:  # 无父有子 链接id就是父id
                    query['tags'] = f"parent:{sankaku_id}"
                    async with session.get(sankaku_info, params=query, proxy=proxy_path()) as resp:
                        self.content_origin_data = await resp.json()
                else:  # 无父无子 只有自己一张图直接下载
                    self.content_origin_data = temp_resp

    async def parse_element(self):
        save_folder = self.author.generate_save_folder()
        for item in self.content_origin_data:
            file_name = item["id"]
            item_post_url = sankaku_post_url(file_name)
            if item["file_type"] == "image/jpeg":
                picture = downloadable.Picture(url=item["file_url"], folder=save_folder, filename=file_name,
                                               custom_source=item_post_url)
                self.element_list.append(picture)
            elif item["file_type"] == "video/mp4":
                video = downloadable.Video(url=item["file_url"], folder=save_folder, filename=file_name,
                                           custom_source=item_post_url)
                self.element_list.append(video)

    async def create_download_history(self):
        author_id = await self.author.get_author_id()
        for element in self.element_list:
            await element.create_download_history(element.custom_source, self.link_database_id, author_id)


class Fantia(Content):
    def __init__(self, url):
        super().__init__(url)
        self.platform = LinkType.FANTIA


class Fanbox(Content):
    def __init__(self, url):
        super().__init__(url)
        self.platform = LinkType.FANBOX
