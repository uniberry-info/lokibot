import nio.store.database

from lokiunimore.config import MATRIX_HOMESERVER, MATRIX_USER_ID, MATRIX_STORE_DIR
from lokiunimore.matrix.extensions import ExtendedAsyncClient
from lokiunimore.matrix.device import generate_device_id


client = ExtendedAsyncClient(
    homeserver=MATRIX_HOMESERVER.__wrapped__,
    user=MATRIX_USER_ID.__wrapped__,
    store_path=str(MATRIX_STORE_DIR.__wrapped__),
    device_id=generate_device_id(__name__),
    config=nio.AsyncClientConfig(
        store_sync_tokens=True,
        store=nio.store.database.DefaultStore,
    ),
)
"""
The bot's Matrix client, powered by :mod:`nio`.
"""