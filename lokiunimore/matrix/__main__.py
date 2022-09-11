import coloredlogs
import logging
import asyncio

coloredlogs.install(
    logger=logging.getLogger("lokiunimore"),
    level="DEBUG",
    fmt="{asctime} | {name:<32} | {levelname:>8} | {message}",
    style="{",
    level_styles=dict(
        debug=dict(color="white"),
        info=dict(color="cyan"),
        warning=dict(color="yellow"),
        error=dict(color="red"),
        critical=dict(color="red", bold=True),
    ),
    field_styles=dict(
        asctime=dict(color='magenta'),
        levelname=dict(color='blue', bold=True),
        name=dict(color='blue'),
    ),
    isatty=True,
)

from lokiunimore.matrix.client import client
from lokiunimore.config import MATRIX_USER_SECRET

loop = asyncio.new_event_loop()
log = logging.getLogger(__name__)


async def main():
    await client.login_with_shared_secret(MATRIX_USER_SECRET)
    await client.sync_forever(60_000, full_state=True)


async def cleanup():
    await client.logout()


try:
    loop.run_until_complete(main())
finally:
    loop.run_until_complete(cleanup())
