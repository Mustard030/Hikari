import aiomysql

from hikari.config.hikari_config import config
from hikari.event import loop
from hikari.common.sqltable import *

g_pool = None


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
    )


loop.create_task(init_pool())


# task
async def create_link_task_to_database(value: str) -> int:
    global g_pool
    async with g_pool.acquire() as conn:
        cursor = await conn.cursor(aiomysql.DictCursor)
        await cursor.execute(CREATE_LINK_TASK_SQL, (str(value),))
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


async def check_duplicated_task_by_content(value) -> dict:
    global g_pool
    async with g_pool.acquire() as conn:
        cursor = await conn.cursor(aiomysql.DictCursor)
        await cursor.execute(CHECK_DUPLICATED_TASK_ID_SQL, (str(value),))
        return await cursor.fetchone()


async def query_download_history_by_task_id(taskid):
    global g_pool
    async with g_pool.acquire() as conn:
        cursor = await conn.cursor(aiomysql.DictCursor)
        await cursor.execute(QUERY_HISTORY_BY_TASK_ID_SQL, (int(taskid),))
        return await cursor.fetchall()


# download_history
async def create_download_task(source, picurl, local_path, task_id: int, author_id: int) -> int:
    global g_pool
    async with g_pool.acquire() as conn:
        cursor = await conn.cursor(aiomysql.DictCursor)
        await cursor.execute(CREATE_DOWNLOAD_HISTORY_SQL, (source, picurl, local_path, task_id, author_id))
        return cursor.lastrowid


async def mark_download_task_done(task_id: int):
    global g_pool
    async with g_pool.acquire() as conn:
        cursor = await conn.cursor(aiomysql.DictCursor)
        await cursor.execute(UPDATE_DOWNLOAD_DONE_SQL, (task_id,))
        return cursor.lastrowid


# author
async def create_author_data(userinfo) -> int:
    """
    :param userinfo: UserInfo类对象
    :return: 创建的用户本地id
    """
    global g_pool
    async with g_pool.acquire() as conn:
        cursor = await conn.cursor(aiomysql.DictCursor)
        await cursor.execute(CREATE_AUTHOR_SQL, (userinfo.platform, userinfo.name, userinfo.userid))
        return cursor.lastrowid


async def query_author_id(userinfo) -> int:
    """
    :param userinfo: UserInfo类对象
    :return: 查询到的用户本地id
    """
    global g_pool
    async with g_pool.acquire() as conn:
        cursor = await conn.cursor(aiomysql.DictCursor)
        await cursor.execute(QUERY_AUTHOR_SQL, (userinfo.platform, userinfo.name, userinfo.userid))
        res = await cursor.fetchone()
        return res['id'] if res else 0
