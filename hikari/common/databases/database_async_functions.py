import asyncio
import aiomysql
import logging

from hikari.common.databases.sqltable import *
from hikari.common.databases.database_models import DBTaskModel, DBDHistoryModel
from hikari.config.hikari_config import config
from hikari.event import loop

g_pool: aiomysql.Pool = None


async def init_pool():
    global g_pool
    g_pool = await aiomysql.create_pool(
            minsize=2,  # 连接池最小值
            maxsize=10,  # 连接池最大值
            host=config["database"]["host"],
            port=config["database"]["port"],
            user=config["database"]["username"],
            password=config["database"]["password"],
            db=config["database"]["db_name"],
            autocommit=True,  # 自动提交模式
            # echo=True,  # 打印日志
    )
    if g_pool:
        logging.info("Database Connected")


loop.create_task(init_pool())


# task
async def create_link_task_to_database(value: str) -> int:
    global g_pool
    async with g_pool.acquire() as conn:
        cursor = await conn.cursor(aiomysql.DictCursor)
        await cursor.execute(CREATE_TASK_SQL, (str(value),))
        return cursor.lastrowid


async def mark_task_done(taskid) -> bool:
    global g_pool
    async with g_pool.acquire() as conn:
        cursor = await conn.cursor(aiomysql.DictCursor)
        await cursor.execute(UPDATE_TASK_DONE_SQL, (int(taskid),))
        return cursor.lastrowid


async def mark_task_fail(reason, taskid) -> bool:
    global g_pool
    async with g_pool.acquire() as conn:
        cursor = await conn.cursor(aiomysql.DictCursor)
        await cursor.execute(UPDATE_TASK_FAIL_SQL, (str(reason), int(taskid),))
        return cursor.lastrowid


async def check_duplicated_task_by_content(value) -> DBTaskModel:
    global g_pool
    async with g_pool.acquire() as conn:
        cursor = await conn.cursor(aiomysql.DictCursor)
        await cursor.execute(QUERY_DUPLICATED_TASK_ID_SQL, (str(value),))
        res = await cursor.fetchone()
        return DBTaskModel(**res) if res else None


async def query_task_by_id(taskid) -> DBTaskModel:
    global g_pool
    async with g_pool.acquire() as conn:
        cursor = await conn.cursor(aiomysql.DictCursor)
        await cursor.execute(QUERY_TASK_BY_ID_SQL, (int(taskid),))
        res = await cursor.fetchone()
        return DBTaskModel(**res) if res else None


async def uncompleted_task() -> DBTaskModel | None:
    """
    获取一个未完成的task记录
    """
    global g_pool
    async with g_pool.acquire() as conn:
        cursor = await conn.cursor(aiomysql.DictCursor)
        await cursor.execute(QUERY_UNCOMPLETE_AND_RETRY_LEAST_TIMES_TASK_SQL)
        res = await cursor.fetchone()
        return DBTaskModel(**res) if res else None


# download_history
async def create_download_task(source, picurl, local_path, task_id: int, author_id: int, filetype: int) -> int:
    global g_pool
    async with g_pool.acquire() as conn:
        cursor = await conn.cursor(aiomysql.DictCursor)
        await cursor.execute(CREATE_DOWNLOAD_HISTORY_SQL, (source, picurl, local_path, task_id, author_id, filetype))
        return cursor.lastrowid


async def mark_download_task_done(task_id: int):
    global g_pool
    async with g_pool.acquire() as conn:
        cursor = await conn.cursor(aiomysql.DictCursor)
        await cursor.execute(UPDATE_DOWNLOAD_DONE_SQL, (task_id,))
        return cursor.lastrowid


async def query_download_history_by_task_id(taskid):
    global g_pool
    async with g_pool.acquire() as conn:
        cursor = await conn.cursor(aiomysql.DictCursor)
        await cursor.execute(QUERY_HISTORY_BY_TASK_ID_SQL, (int(taskid),))
        rs = await cursor.fetchall()
        return [DBDHistoryModel(**r) for r in rs]


async def increase_retry_times(download_history_id: int):
    global g_pool
    async with g_pool.acquire() as conn:
        cursor = await conn.cursor(aiomysql.DictCursor)
        await cursor.execute(INCREASE_RETRY_TIMES, (download_history_id,))
        return cursor.lastrowid


# author
async def create_author_data(author_info) -> int:
    """
    :param author_info: AuthorInfo
    :return: 创建的用户本地id
    """
    global g_pool
    async with g_pool.acquire() as conn:
        cursor = await conn.cursor(aiomysql.DictCursor)
        await cursor.execute(CREATE_AUTHOR_SQL, (author_info.platform, author_info.name, author_info.userid))
        return cursor.lastrowid


async def query_author_id(author_info) -> int:
    """
    :param author_info: UserInfo类对象
    :return: 查询到的用户本地id
    """
    global g_pool
    async with g_pool.acquire() as conn:
        cursor = await conn.cursor(aiomysql.DictCursor)
        await cursor.execute(QUERY_AUTHOR_SQL, (author_info.platform, author_info.name, author_info.userid))
        res = await cursor.fetchone()
        return res['id'] if res else 0


async def update_filetype():
    from hikari.common.filetype import DownloadableFileType
    global g_pool
    async with g_pool.acquire() as conn:
        cursor = await conn.cursor(aiomysql.DictCursor)
        await cursor.execute(r"SELECT id, local_path FROM download_history")
        res = await cursor.fetchall()
        for row in res:
            if row['local_path'].endswith(".mov") or row['local_path'].endswith(".mp4"):
                await cursor.execute(rf"""UPDATE download_history 
                                          SET filetype={DownloadableFileType.Video.value} 
                                          WHERE id = {row['id']}""")
            elif row['local_path'].endswith(".zip"):
                await cursor.execute(rf"""UPDATE download_history 
                                          SET filetype={DownloadableFileType.ZipFile.value} 
                                          WHERE id = {row['id']}""")
            elif row['local_path'].endswith(".jpg") or row['local_path'].endswith(".png"):
                await cursor.execute(rf"""UPDATE download_history 
                                          SET filetype={DownloadableFileType.Picture.value} 
                                          WHERE id = {row['id']}""")
