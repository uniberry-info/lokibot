from lokiunimore.config import MATRIX_HOMESERVER, MATRIX_USERNAME, MATRIX_STORE_PATH
from lokiunimore.matrix.extensions import ExtendedClient


# IDEA ignores the annotations of decorators <https://youtrack.jetbrains.com/issue/PY-53583/Decorator-return-type-ignored>
client = ExtendedClient(
    homeserver=MATRIX_HOMESERVER.__wrapped__,
    user=MATRIX_USERNAME.__wrapped__,
    store_path=MATRIX_STORE_PATH.__wrapped__,
)
"""
The bot's Matrix client, powered by :mod:`nio`.
"""