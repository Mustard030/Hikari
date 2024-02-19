from apscheduler.schedulers.asyncio import AsyncIOScheduler
from hikari.common.countdown import count_down_to_retry
from hikari.common.function import print_yes
from hikari.common.link import Link

schedule = AsyncIOScheduler()


async def retry_download():
    if count_down_to_retry.check():
        count_down_to_retry.reset()
        await Link().retry()


schedule.add_job(retry_download, 'interval', seconds=60)
