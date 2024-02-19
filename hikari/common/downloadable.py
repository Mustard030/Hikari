import asyncio.locks as locks
import cv2
import hashlib
import logging
import os
import zipfile
import zlib

from PIL import Image

from hikari.common.countdown import count_down_to_retry
from hikari.common.databases import database_async_functions
from hikari.common.decorator import retry
from hikari.common.downloader import Downloader
from hikari.common.exceptions import FileIOError
from hikari.common.filetype import DownloadableFileType

lock = locks.Lock()


class Downloadable:
    def __init__(self, url, folder, filename,
                 save_path=None,
                 suffix='',
                 database_download_id=0,
                 force=False,
                 custom_source='',
                 headers=None,
                 cookies=None,
                 filetype: [DownloadableFileType | None] = None):
        """

        :param url: 网络文件url
        :param folder: 保存文件夹
        :param filename: 文件名
        :param suffix: 后缀名
        :param force: 强制下载
        """
        self.url = url
        self.folder = folder
        self.filename = filename
        self.suffix = suffix
        self.save_path = save_path if save_path else self.generate_save_path()
        self.verified = False
        self.database_download_id = database_download_id
        self.force = force
        self.custom_source = custom_source
        self.headers = headers if headers else dict()
        self.cookies = cookies if cookies else dict()
        self.filetype = filetype

    def __str__(self):
        return f"<[id:{self.database_download_id}]{self.url} -> {self.save_path}>"

    def generate_save_path(self):
        assert self.folder is not None, "folder is None"
        assert self.filename is not None, "filename is None"
        path = os.path.join(self.folder, str(self.filename) + '.' + self.suffix)
        return path

    async def create_download_history(self, source, task_id, author_id):
        self.database_download_id = await database_async_functions.create_download_task(source, self.url,
                                                                                        self.save_path, task_id,
                                                                                        author_id, self.filetype.value
                                                                                        )

    async def mark_download_done(self):
        await database_async_functions.mark_download_task_done(self.database_download_id)

    @retry(5, wait=10)
    async def download(self, only_download=False):
        """
        下载这张图片，如果非强制下载，图片存在且没有损坏，则跳过这个下载
        :return:
        """
        if not self.force and self.file_check():  # 不强制下载且图片存在无损坏
            logging.info(f"{self.url} 已存在于{self.save_path}")
            await self.mark_download_done()  # 标记完成
        else:
            downloader = Downloader(headers=self.headers, cookies=self.cookies)
            logging.info(f"{self.url} 开始下载")

            async with lock:
                await downloader.download(self.url, self.save_path)

            if not only_download:
                self.file_check()
                self.file_check()
                # logging.info(f"{self.save_path} : {self.verified}")
                if not self.verified:  # 文件校验不通过，抛出错误等待重试下载
                    raise FileIOError(self.save_path)
                else:
                    await self.mark_download_done()
                    count_down_to_retry.reset()
                    logging.info(f"下载任务id={self.database_download_id}已标记完成")
                    logging.info(f"{self.url} 下载成功，已保存到 {self.save_path}")

    def file_check(self):
        pass

    @property
    def file_md5(self):
        """
        计算文件的md5
        """
        m = hashlib.md5()  # 创建md5对象
        with open(self.save_path, 'rb') as f:
            while True:
                data = f.read(4096)
                if not data:
                    break
                m.update(data)  # 更新md5对象

        return m.hexdigest()  # 返回md5对象


class Picture(Downloadable):
    def __init__(self, url, folder=None, filename=None, save_path=None, suffix='jpg', database_download_id=0,
                 force=False, custom_source='', headers=None,
                 cookies=None):
        super().__init__(url=url, folder=folder, filename=filename, save_path=save_path, suffix=suffix,
                         database_download_id=database_download_id, force=force,
                         custom_source=custom_source, headers=headers, cookies=cookies,
                         filetype=DownloadableFileType.Picture)

    def file_check(self):
        """
        检测图片是否完整，
        :return:
        """
        if not os.path.isfile(self.save_path):  # 路径不存在
            self.verified = False
            return self.verified
        try:
            Image.open(self.save_path).load()
            self.verified = True
        except (OSError, SyntaxError):
            self.verified = False
        finally:
            return self.verified


class Video(Downloadable):
    def __init__(self, url, folder=None, filename=None, save_path=None, suffix='mp4', database_download_id=0,
                 force=False, custom_source='',
                 headers=None,
                 cookies=None):
        super().__init__(url=url, folder=folder, save_path=save_path, filename=filename, suffix=suffix,
                         database_download_id=database_download_id, force=force,
                         custom_source=custom_source, headers=headers, cookies=cookies,
                         filetype=DownloadableFileType.Video)

    def file_check(self):
        if not os.path.isfile(self.save_path):
            self.verified = False
            return self.verified
        try:
            cap = cv2.VideoCapture(self.save_path)
            if cap.isOpened():
                self.verified = True
        except:
            self.verified = False
        finally:
            return self.verified


class ZipFile(Downloadable):
    def __init__(self, url, folder=None, filename=None, save_path=None, suffix='zip', database_download_id=0,
                 force=False, custom_source='',
                 headers=None,
                 cookies=None):
        super().__init__(url=url, folder=folder, save_path=save_path, filename=filename, suffix=suffix,
                         database_download_id=database_download_id, force=force,
                         custom_source=custom_source, headers=headers, cookies=cookies,
                         filetype=DownloadableFileType.ZipFile)

    def file_check(self):
        try:
            res = zipfile.ZipFile(self.save_path).testzip()
        except (FileNotFoundError, zipfile.BadZipFile, zlib.error):
            self.verified = False
            return self.verified
        else:
            self.verified = res is None
            return self.verified


class GifFile(Downloadable):
    def __init__(self, url, folder=None, filename=None, save_path=None, suffix='gif', database_download_id=0,
                 force=False, custom_source='',
                 headers=None,
                 cookies=None):
        super().__init__(url=url, folder=folder, save_path=save_path, filename=filename, suffix=suffix,
                         database_download_id=database_download_id, force=force,
                         custom_source=custom_source, headers=headers, cookies=cookies,
                         filetype=DownloadableFileType.GifFile)

    def file_check(self):
        if not os.path.isfile(self.save_path):  # 路径不存在
            self.verified = False
            return self.verified
        try:
            Image.open(self.save_path).load()
            self.verified = True
        except (OSError, SyntaxError):
            self.verified = False
        finally:
            return self.verified
