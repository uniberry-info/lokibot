from . import client
from lokiunimore import config
import asyncio
import coloredlogs


async def main():
    coloredlogs.install("DEBUG")
    await client.login_with_shared_secret(config.MATRIX_SHARED_SECRET.__wrapped__)
    await client.sync_forever()


loop = asyncio.new_event_loop()
loop.run_until_complete(main())
