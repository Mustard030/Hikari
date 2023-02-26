import asyncio
import functools
import traceback

from hikari.common.exceptions import OutOfRetryError


def retry(times: int = 3, wait: int = 2):
	"""
	捕获异常时自动重试
	:param times: 重试次数
	:param wait: 每次重试之间的间隔(秒) 只对异步方法生效
	:return:
	"""

	@functools.wraps(times)
	def func_wrapper(func):

		if asyncio.iscoroutinefunction(func):
			@functools.wraps(func)
			async def wrapper(*args, **kwargs):
				last_error = None
				for _ in range(times):
					# noinspection PyBroadException
					try:
						result = await func(*args, **kwargs)
					except Exception as e:
						last_error = traceback.format_exc()
						# traceback.print_exc()
						print(e)
						print(f"将在{wait}秒后重试{func.__name__}()方法,参数为args={args}, kwargs={kwargs}")
						await asyncio.sleep(wait)
					else:
						return result

				raise OutOfRetryError(last_error)

		else:
			@functools.wraps(func)
			def wrapper(*args, **kwargs):
				last_error = None
				for i in range(times):
					# noinspection PyBroadException
					try:
						result = func(*args, **kwargs)
					except:
						last_error = traceback.format_exc()
						traceback.print_exc()
					else:
						return result

				raise OutOfRetryError(last_error)

		return wrapper

	return func_wrapper
