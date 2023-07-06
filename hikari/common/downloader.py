import asyncio
import os

import aiohttp

from hikari.common.exceptions import LinkServerRaiseError
from hikari.common.function import proxy_path


class Downloader:
    def __init__(self, headers=None, cookies=None):
        # 请求头
        self.__headers = headers if headers else dict()
        self.__cookies = cookies if cookies else dict()
        self.proxy_path = proxy_path()

    def set_headers(self, new_headers):
        # 设置请求头
        self.__headers = new_headers

    def set_cookies(self, new_cookies):
        # 设置cookies
        self.__cookies = new_cookies

    async def __down(self, queue):
        """
        :param queue: 分割队列
        """
        while not queue.empty():
            task = await queue.get()
            session, path, url, start, headers = task[0], task[1], task[2], task[3], task[4]
            async with session.get(url,
                                   headers=headers,
                                   cookies=self.__cookies,
                                   proxy=self.proxy_path,
                                   timeout=20) as resp:
                with open(path, 'rb+') as f:
                    # 写入位置，指针移到指定位置
                    f.seek(start)
                    async for b in resp.content.iter_chunked(1024 * 1024):
                        f.write(b)
        # 更新进度条，每次请求得到的长度

    async def __get_length(self, session, path, url):
        """创建占位文件，返回文件长度"""
        async with session.get(url,
                               headers=self.__headers,
                               cookies=self.__cookies,
                               proxy=self.proxy_path,
                               timeout=20) as resp:
            # 获取视频长度
            try:
                le = int(resp.headers['Content-Length'])
            except (KeyError, asyncio.TimeoutError):
                raise LinkServerRaiseError("url中文件内容请求失败")
            else:
                f = open(path, 'wb')
                f.truncate(le)
                f.close()
                return le

    async def __start_async(self, url, path, count=16):
        """
        :param url:视频地址
        :param path: 视频保存位置
        :param count:协程数量
        """
        path_, name = os.path.split(path)
        # 判断目录是否存在
        if not os.path.exists(path_):
            os.makedirs(path_, exist_ok=True)
        async with aiohttp.ClientSession() as session:
            # 文件长度
            content_length = await self.__get_length(session, path, url=url)

            # 将文件按大小分解为任务队列
            queue = asyncio.Queue()
            # 每个区块10M大小
            size = 10 * 1024 * 1024  # M
            amount = content_length // size or 1
            for i in range(amount):
                start = i * size
                if i == amount - 1:
                    end = content_length
                else:
                    end = start + size
                if start > 0:
                    start += 1
                # 设置请求内容位置
                headers = {
                    'Range': f'bytes={start}-{end}'
                }
                # 合并请求头
                headers.update(self.__headers)
                queue.put_nowait([session, path, url, start, headers])

            async with asyncio.TaskGroup() as tg:
                [tg.create_task(self.__down(queue)) for i in range(count)]

    async def download(self, url, path, count=32):
        """
        :param url: 网络地址
        :param path: 保存地址
        :param count: 协程数量
        :return: 传入的保存地址
        """
        try:
            await self.__start_async(url, path, count)
            return path
        except Exception:
            if os.path.exists(path):
                os.remove(path)
            raise
