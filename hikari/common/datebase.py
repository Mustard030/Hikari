import aiomysql


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
					host='192.168.31.230',
					port=3306,
					user='root',
					password='abcd1234',
					db='test',
					autocommit=True,  # 自动提交模式
			)
			self.pool = __pool
		except:
			pass

	# logobj.error('connect error.', exc_info=True)

	async def getCurosr(self):
		conn = await self.pool.acquire()
		# 返回字典格式
		cur = await conn.cursor(aiomysql.DictCursor)
		return conn, cur

	async def query(self, query, param=None):
		"""
		查询操作
		:param query: sql语句
		:param param: 参数
		:return:
		"""
		conn, cur = await self.getCurosr()
		try:
			await cur.execute(query, param)
			return await cur.fetchall()
		except:
			pass
		# logobj.error(traceback.format_exc())
		finally:
			if cur:
				await cur.close()
			# 释放掉conn,将连接放回到连接池中
			await self.pool.release(conn)

	async def execute(self, query, param=None):
		"""
		增删改 操作
		:param query: sql语句
		:param param: 参数
		:return:
		"""
		conn, cur = await self.getCurosr()
		try:
			await cur.execute(query, param)
			if cur.rowcount == 0:
				return False
			else:
				return True
		except:
			pass
		# logobj.error(traceback.format_exc())
		finally:
			if cur:
				await cur.close()
			# 释放掉conn,将连接放回到连接池中
			await self.pool.release(conn)


async def getAmysqlobj():
	mysqlobj = Pymysql()
	pool = await mysqlobj.initpool()
	mysqlobj.pool = pool
	return mysqlobj
