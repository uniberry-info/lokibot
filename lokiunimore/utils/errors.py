import sentry_sdk
import sentry_sdk._types as sentry_typing
import sentry_sdk.integrations.flask
import sentry_sdk.integrations.sqlalchemy
import pkg_resources
import socket

from lokiunimore.config import SENTRY_DSN


version = pkg_resources.get_distribution("lokiunimore").version


def clean_events(event: sentry_typing.Event, hint: sentry_typing.Hint):
    # TODO: Clean events so that they do not leak personal information
    ...


def install_sentry():
    sentry_sdk.init(
        dsn=SENTRY_DSN.__wrapped__,
        server_name=socket.gethostname(),
        debug=__debug__,
        release=f"{version}+dev" if __debug__ else version,
        environment="Development" if __debug__ else "Production",
        integrations=(
            sentry_sdk.integrations.flask.FlaskIntegration(),
            sentry_sdk.integrations.sqlalchemy.SqlalchemyIntegration(),
        ),
        before_send=clean_events,
    )


__all__ = (
    "sentry"
)
