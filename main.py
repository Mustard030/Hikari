from hikari.event import loop
from hikari.common.paperListen import paperclip


async def main():
	loop.call_soon(paperclip)


if __name__ == '__main__':
	try:
		loop.create_task(main())
		loop.run_forever()
	except KeyboardInterrupt as ki:
		loop.stop()
