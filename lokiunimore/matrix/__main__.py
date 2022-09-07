import coloredlogs
import nio

coloredlogs.install("DEBUG")

import logging
from . import client
from lokiunimore import config
import asyncio

log = logging.getLogger(__name__)


async def main():
    await client.login_with_shared_secret(config.MATRIX_SHARED_SECRET.__wrapped__)
    # sync_forever is HOPELESSLY BROKEN!?!?
    since = None
    while True:
        log.debug(f"Syncing since {since}...")
        resp: nio.SyncResponse = await client.sync(since=since)
        since = resp.next_batch
        await client.run_response_callbacks([resp])


loop = asyncio.new_event_loop()
loop.run_until_complete(main())
