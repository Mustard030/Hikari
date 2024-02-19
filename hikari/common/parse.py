###############################################################
# 将输入解析为对应的任务类型
###############################################################
import asyncio
from operator import itemgetter

import json5
import logging
import os
import re

from hikari.common.authorinfo import TwimgMediaUser
from hikari.common.command import Command
from hikari.common.downloadable import Video
from hikari.common.exceptions import LinktypeNotSupportError, LinkServerRaiseError, CannotFoundElementError
from hikari.common.link import Link
from hikari.event import create_task


# 解析输入内容
async def parse(value):
    if (value.startswith('"') and value.endswith('"')) or (value.startswith("'") and value.endswith("'")):
        value = value[1:-1]

    # 是网络链接则创建解析链接任务
    if is_link(value):
        create_task(parse_link(value))

    # 是文件（夹）路径，则解析路径做对应方法
    elif is_file_path(value):
        # 是文件则调用识图任务上传识图网站
        if os.path.isfile(value):
            create_task(parse_file(value))

        # 是文件夹就对每一个文件调用识图任务
        elif os.path.isdir(value):
            create_task(parse_folder(value))

    # 是命令
    elif execute_function := parse_command(value):
        await execute_function()


# 解析粘贴板内容
async def parse_paperclip(value):
    if (value.startswith('"') and value.endswith('"')) or (value.startswith("'") and value.endswith("'")):
        value = value[1:-1]

    # 是网络链接则创建解析链接任务
    if is_link(value):
        create_task(parse_link(value))

    # 推文的特殊解析方法
    elif is_tweet_detail(value):
        create_task(parse_tweet(value))

        # 是文件（夹）路径，则解析路径做对应方法
    elif is_file_path(value):
        # 是文件则调用识图任务上传识图网站
        if os.path.isfile(value):
            create_task(parse_file(value))


def is_file_path(value: str):
    return os.path.exists(value)


async def parse_file(value):
    # TODO: 替换掉下面的实现
    new_file_name = re.sub(r"【.*?】", '', value)
    new_file_name = re.sub(r"_高清 1080P ?", '', new_file_name)
    os.rename(value, new_file_name)


async def parse_folder(value):
    top_dir = list(os.walk(value))[0]
    root, dirs, files = top_dir
    for file in files:
        pass


def parse_command(value):
    cmd_dict = {
        "#": Command.change_paperclip_listening,
        "mov": Command.to_mp4,
        "t": Command.any_function,
    }
    return cmd_dict.get(value, Command.do_nothing)


def is_link(value: str):
    return value.startswith(r"http://") or value.startswith(r"https://")


async def parse_link(value):
    # 创建Link类对象，并且自动判别链接类型及平台
    try:  # 绕过统一错误处理，只显示简单信息
        link = Link(
                value)  # if not match any link character, it will raise LinktypeNotExistError and print traceback info
    except LinktypeNotSupportError as e:
        logging.info(e)
    else:
        await link.start()


def is_tweet_detail(value: str):
    return "threaded_conversation_with" in value


async def parse_tweet(value):  # 只下载不记录
    tweet_obj = json5.loads(value, encoding="utf-8")
    if "errors" in tweet_obj:
        raise LinkServerRaiseError(tweet_obj["errors"][0]["message"])

    author = TwimgMediaUser()
    elements = []
    entries_list = tweet_obj['data']['threaded_conversation_with_injections_v2']['instructions'][0]['entries']
    try:
        tweet_detail = tuple(filter(lambda entry: entry['entryId'].startswith('tweet-'), entries_list))[-1]
    except IndexError:
        raise CannotFoundElementError("No tweet content")
    else:
        tweet_info = tweet_detail['content']['itemContent']['tweet_results']['result']
        if "tweet" in tweet_info:  # 当推文内容为视频时，返回值格式会有变化，此处消除该变化，令其与图片的格式一致
            tweet_info = tweet_info["tweet"]
        media_contents = tweet_info['legacy']['extended_entities']['media']
        for media_content in media_contents:
            media_type = media_content['type']
            if media_type in ['video', 'animated_gif']:
                videos_info = filter(lambda video: video['content_type'] == 'video/mp4',
                                     media_content['video_info']['variants']
                                     )
                media_url_https = max(videos_info, key=itemgetter('bitrate'))['url']
                uuid_name = media_url_https.split('/')[-1].split('.')[0]
                video_element = Video(media_url_https, folder=author.generate_save_folder(), filename=f"{tweet_info['rest_id']}_{uuid_name}")
                elements.append(video_element)

        async with asyncio.TaskGroup() as tg:
            [tg.create_task(file.download(True)) for file in elements]
