import asyncio

loop = asyncio.get_event_loop()
asyncio.set_event_loop(loop)
create_task = loop.create_task
