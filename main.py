import logging
import threading

from hikari.event import loop
from hikari.config.hikari_config import config
from hikari.common.parse import parse
from hikari.common.paperListen import paperclip
from hikari.common.scheduler import schedule

logging.basicConfig(format="[%(levelname)s][%(asctime)s]: %(message)s ", level=logging.INFO)
logging.getLogger('apscheduler.executors.default').propagate = False


def input_forever():
	while True:
		try:
			value = input(">>")
		except UnicodeDecodeError:
			pass
		else:
			if value:
				# print(value)
				loop.create_task(parse(value))


async def main():
	loop.call_soon(paperclip)
	threading.Thread(target=input_forever, name="input_forever").start()
	schedule.start()


if __name__ == '__main__':
	try:
		loop.create_task(main())
		loop.run_forever()
	except KeyboardInterrupt:
		logging.warning("键盘退出！")
	except Exception as e:
		logging.warning(e)
	finally:
		config.save()
		loop.stop()
		exit()
