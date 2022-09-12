import asyncio

from lokiunimore.utils.logs import install_log_handler
from lokiunimore.matrix.client import LokiClient
from lokiunimore.config import MATRIX_USER_SECRET, MATRIX_HOMESERVER, MATRIX_USER_ID, SQLALCHEMY_DATABASE_URL

install_log_handler()
loop = asyncio.new_event_loop()


client = LokiClient(
    homeserver=MATRIX_HOMESERVER.__wrapped__,
    user=MATRIX_USER_ID.__wrapped__,
    database_url=SQLALCHEMY_DATABASE_URL.__wrapped__
)


async def main():
    await client.login_with_shared_secret(MATRIX_USER_SECRET.__wrapped__)
    await client.sync_forever(60_000, full_state=True)


async def cleanup():
    await client.logout()


try:
    loop.run_until_complete(main())
finally:
    loop.run_until_complete(cleanup())
