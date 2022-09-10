import coloredlogs
import logging
import asyncio

coloredlogs.install("DEBUG", isatty=True)

from lokiunimore.matrix.client import client
from lokiunimore.matrix.callbacks import register_callbacks
from lokiunimore.config import MATRIX_USER_SECRET

loop = asyncio.new_event_loop()
log = logging.getLogger(__name__)


async def main():
    register_callbacks()
    await client.login_with_shared_secret(MATRIX_USER_SECRET)
    await client.sync_forever(60_000, full_state=True)


async def cleanup():
    await client.logout()


try:
    loop.run_until_complete(main())
finally:
    loop.run_until_complete(cleanup())
