import pyperclip
from hikari.event import loop
from hikari.common.parse import parse


def paperclip(last=None):
	if last is None:
		last = pyperclip.paste().strip()

	data = pyperclip.paste().strip()

	if last != data:
		loop.create_task(parse(data))

	loop.call_later(0.1, paperclip, data)
