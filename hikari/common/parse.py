import os

from hikari.event import loop
from hikari.common.link import Link


async def parse(value):
	if is_link(value):
		print(f"L {value}")
		loop.create_task(parse_link(value))

	elif is_file_path(value):
		print(f"P {value}")
		loop.create_task(parse_link(value))


def is_file_path(value: str):
	return value.startswith('"') and value.endswith('"') and os.path.exists(value[1:-1])


async def parse_file(value):
	pass


async def parse_folder(value):
	pass


async def parse_input(value):
	print("123")


def is_link(value: str):
	return value.startswith(r"http://") or value.startswith(r"https://")


async def parse_link(value):
	link = Link(value)

