import pyperclip

from hikari.common.parse import parse_paperclip
from hikari.config.hikari_config import config
from hikari.event import loop


def paperclip(last=None):
	if last is None:
		try:
			last = pyperclip.paste().strip()
		except pyperclip.PyperclipWindowsException:
			last = ''

	try:
		data = pyperclip.paste().strip()
	except pyperclip.PyperclipWindowsException:
		loop.call_later(0.1, paperclip)
	else:
		if last != data and config.listen_paperclip:
			loop.create_task(parse_paperclip(data))

		loop.call_later(0.1, paperclip, data)
