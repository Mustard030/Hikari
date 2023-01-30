import logging

import aiomysql

from hikari.config.hikari_config import config
from hikari.common.sqltable import *


class Pymysql:
	def __init__(self):
		self.coon = None
		self.pool = None

	async def initpool(self):
		try:
			# logobj.debug("will connect mysql~")
			__pool = await aiomysql.create_pool(
					minsize=5,  # 连接池最小值
					maxsize=10,  # 连接池最大值
					host=config.get("database").get("host"),
					port=config.get("database").get("port"),
					user=config.get("database").get("username"),
					password=config.get("database").get("password"),
					db=config.get("database").get("db_name"),
					autocommit=True,  # 自动提交模式
			)
			self.pool = __pool
		except:
			raise

	# logobj.error('connect error.', exc_info=True)

	async def get_cursor(self):
		conn = await self.pool.acquire()
		# 返回字典格式
		cur = await conn.cursor(aiomysql.DictCursor)
		return conn, cur

	async def query(self, query, param=None) -> list:
		"""
		查询操作
		:param query: sql语句
		:param param: 参数
		:return:
		"""
		conn, cur = await self.get_cursor()
		try:
			await cur.execute(query, param)
			return await cur.fetchall()
		except:
			pass
		finally:
			if cur:
				await cur.close()
			# 释放掉conn,将连接放回到连接池中
			await self.pool.release(conn)

	async def execute(self, query, param=None) -> bool:
		"""
		增删改 操作
		:param query: sql语句
		:param param: 参数
		:return:
		"""

		conn, cur = await self.get_cursor()
		try:
			rowcount = await cur.execute(query, param)
			if rowcount == 0:
				return False
			else:
				return cur.lastrowid
		except Exception as e:
			logging.warning(e)
		finally:
			if cur:
				await cur.close()
			# 释放掉conn,将连接放回到连接池中
			await self.pool.release(conn)


async def get_mysqlobj() -> Pymysql:
	mysqlobj = Pymysql()
	await mysqlobj.initpool()
	return mysqlobj


# task
async def create_link_task_to_database(value: str) -> int:
	mysqlobj = await get_mysqlobj()
	lastrowid = await mysqlobj.execute(CREATE_LINK_TASK_SQL, (str(value),))
	if lastrowid:
		return int(lastrowid)


async def mark_task_done(taskid) -> bool:
	mysqlobj = await get_mysqlobj()
	return await mysqlobj.execute(UPDATE_TASK_DONE_SQL, (int(taskid),))


async def mark_task_fail(reason, taskid) -> bool:
	mysqlobj = await get_mysqlobj()
	return await mysqlobj.execute(UPDATE_TASK_FAIL_SQL, (str(reason), int(taskid),))


async def check_duplicated_task(value) -> dict:
	mysqlobj = await get_mysqlobj()
	res_list = await mysqlobj.query(CHECK_DUPLICATED_TASK_ID_SQL, (str(value),))
	if res_list:
		return res_list[0]
	else:
		return {}


async def query_download_history_by_task_id(taskid):
	mysqlobj = await get_mysqlobj()
	res_list = await mysqlobj.query(QUERY_HISTORY_BY_TASK_ID_SQL, (int(taskid),))
	return res_list


# download_history
async def create_download_task(source, picurl, local_path, task_id: int, author_id: int) -> int:
	mysqlobj = await get_mysqlobj()
	return await mysqlobj.execute(CREATE_DOWNLOAD_HISTORY_SQL, (source, picurl, local_path, task_id, author_id))


async def mark_download_task_done(task_id: int):
	mysqlobj = await get_mysqlobj()
	return await mysqlobj.execute(UPDATE_DOWNLOAD_DONE_SQL, (task_id,))


# author
async def create_author_data(userinfo) -> int:
	"""
	:param userinfo: UserInfo类对象
	:return: 创建的用户本地id
	"""
	mysqlobj = await get_mysqlobj()
	return await mysqlobj.execute(CREATE_AUTHOR_SQL, (userinfo.platform, userinfo.name, userinfo.userid))


async def query_author_id(userinfo) -> int:
	"""
	:param userinfo: UserInfo类对象
	:return: 查询到的用户本地id
	"""
	mysqlobj = await get_mysqlobj()
	res_list = await mysqlobj.query(QUERY_AUTHOR_SQL, (userinfo.platform, userinfo.name, userinfo.userid))
	return res_list[0]['id'] if res_list else 0
