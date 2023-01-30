###############################################################
# 将输入解析为对应的任务类型
###############################################################
import logging
import os

from hikari.common.command import Command
from hikari.common.exceptions import LinktypeNotExistError
from hikari.common.link import Link
from hikari.event import create_task
from hikari.common.datebase import create_link_task_to_database, mark_task_done, mark_task_fail


# 解析输入内容
async def parse(value):
	# 是网络链接则创建解析链接任务
	if is_link(value):
		create_task(parse_link(value))

	# 是文件（夹）路径，则解析路径做对应方法
	elif is_file_path(value):
		if (value.startswith('"') and value.endswith('"')) or (value.startswith("'") and value.endswith("'")):
			value = value[1:-1]

		# 是文件则调用识图任务上传识图网站
		if os.path.isfile(value):
			create_task(parse_file(value))

		# 是文件夹就对每一个文件调用识图任务
		elif os.path.isdir(value):
			create_task(parse_folder(value))

	# 是命令
	elif execute_function := parse_command(value):
		execute_function()


# 解析粘贴板内容
async def parse_paperclip(value):
	# 是网络链接则创建解析链接任务
	if is_link(value):
		create_task(parse_link(value))


def is_file_path(value: str):
	return os.path.exists(value)


async def parse_file(value):
	create_task()


async def parse_folder(value):
	top_dir = list(os.walk(value))[0]
	root, dirs, files = top_dir
	for file in files:
		pass


def parse_command(value):
	cmd_dict = {
		"#": Command.changePaperclipListening,
	}
	return cmd_dict.get(value, Command.doNothing)


def is_link(value: str):
	return value.startswith(r"http://") or value.startswith(r"https://")


async def parse_link(value):
	# 创建Link类对象，并且自动判别链接类型及平台
	try:  # 绕过统一错误处理，只显示简单信息
		link = Link(value)  # if not match any link character, it will raise LinktypeNotExistError and print traceback info
	except LinktypeNotExistError as e:
		logging.info(e)
	else:
		await link.start()
