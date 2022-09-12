import re
import cfig
import sqlalchemy.engine
import dotenv


dotenv.load_dotenv()
config = cfig.Configuration()


@config.required()
def MATRIX_HOMESERVER(val: str) -> str:
    """
    The Matrix homeserver to connect to.
    """
    return val


@config.required()
def MATRIX_USER_ID(val: str) -> str:
    """
    The full user ID of the Matrix account to login as.
    https://spec.matrix.org/latest/#users
    """
    if not val.startswith("@"):
        raise ValueError("User IDs must start with `@`")
    if ":" not in val:
        raise ValueError("User IDs must contain the `:` localpart-server separator")
    return val


@config.required()
def MATRIX_USER_SECRET(val: str) -> str:
    """
    The shared secret to use for logging in to the server via com.devture.shared_secret_auth.
    https://github.com/devture/matrix-synapse-shared-secret-auth
    """
    return val


@config.optional()
def MATRIX_SKIP_EVENTS(val: str | None) -> bool:
    """
    Set this to `true` to have the Matrix client skip processing all events happened until now.
    Useful for initializing a new database on an existing bot.
    """
    return val and val.lower() == "true"


@config.required()
def MATRIX_PUBLIC_SPACE_ID(val: str) -> str:
    """
    The room ID of the public Matrix space to monitor.
    https://spec.matrix.org/latest/#room-structure
    """
    if not val.startswith("!"):
        raise ValueError("Room IDs must start with `!`")
    if ":" not in val:
        raise ValueError("Room IDs must contain the `:` localpart-server separator")
    return val


@config.required()
def MATRIX_PUBLIC_SPACE_ALIAS(val: str) -> str:
    """
    The room alias of the public Matrix space to display in various parts of the bot.
    https://spec.matrix.org/latest/#room-aliases
    """
    if not val.startswith("#"):
        raise ValueError("Room aliases must start with `#`")
    if ":" not in val:
        raise ValueError("Room aliases must contain the `:` localpart-server separator")
    return val


@config.required()
def MATRIX_PRIVATE_SPACE_ID(val: str) -> str:
    """
    The room ID of the private Matrix space to monitor and add users to.
    https://spec.matrix.org/latest/#room-structure
    """
    if not val.startswith("!"):
        raise ValueError("Room IDs must start with `!`")
    if ":" not in val:
        raise ValueError("Room IDs must contain the `:` localpart-server separator")
    return val


@config.required()
def MATRIX_HELP_ROOM_ALIAS(val: str) -> str:
    """
    The room alias of the public Matrix room to request assistance in, to display in various parts of the bot.
    https://spec.matrix.org/latest/#room-aliases
    """
    if not val.startswith("#"):
        raise ValueError("Room aliases must start with `#`")
    if ":" not in val:
        raise ValueError("Room aliases must contain the `:` localpart-server separator")
    return val


@config.required()
def SQLALCHEMY_DATABASE_URL(val: str) -> sqlalchemy.engine.URL:
    """
    The URL of the database to store data in.
    https://docs.sqlalchemy.org/en/14/core/engines.html#database-urls
    """
    return sqlalchemy.engine.url.make_url(val)


@config.required()
def FLASK_SECRET_KEY(val: str) -> str:
    """
    The secret key to use with Flask to sign session cookies.
    https://flask.palletsprojects.com/en/2.2.x/config/#SECRET_KEY
    """
    return val


@config.required()
def FLASK_SERVER_NAME(val: str) -> str:
    """
    The hostname of the server where the Flask webserver is available at.
    For example, `loki.steffo.eu`.
    """
    return val


@config.required()
def FLASK_APPLICATION_ROOT(val: str) -> str:
    """
    The path where the root of the Flask webserver will be served at.
    For example, `/`.
    """
    return val


@config.required()
def FLASK_PREFERRED_URL_SCHEME(val: str) -> str:
    """
    The protocol to prefer when building URLs outside a Flask request.
    For example, `https`
    """
    return val


@config.required()
def OIDC_CLIENT_ID(val: str) -> str:
    """
    The client ID of the OpenID Connect client used to authenticate user sign-ins.
    """
    return val


@config.required()
def OIDC_CLIENT_SECRET(val: str) -> str:
    """
    The client secret of the OpenID Connect client used to authenticate user sign-ins.
    """
    return val


@config.required()
def OIDC_CONFIGURATION_URL(val: str) -> str:
    """
    The URL to the configuration of the OpenID Connect client used to authenticate user sign-ins.
    For example, Google uses `https://accounts.google.com/.well-known/openid-configuration`.
    """
    return val


@config.required()
def OIDC_API_BASE_URL(val: str) -> str:
    """
    The base URL of the API that user sign-ins via the OpenID Connect client grant access to.
    For example, Google uses `https://www.googleapis.com/`.
    """
    return val


@config.optional()
def OIDC_SCOPES(val: str | None) -> str:
    """
    The space-separated additional scopes that the OpenID Connect client should request access to.
    The `openid` scope is added automatically.
    Defaults to requesting the `email profile` scopes.
    """
    if not val:
        return "openid email profile"
    else:
        return "openid " + val


@config.required()
def OIDC_EMAIL_REGEX(val: str) -> re.Pattern:
    """
    A regular expression to match the emails of the users who sign-in via the OpenID Connect client.
    If the email does not match the pattern, the sign-in is rejected.
    For example, `.+@studenti[.]unimore[.]it` to verify that an user is a Unimore student.
    To allow any email, you can use the `.+` regex.
    """
    return re.compile(val)


__all__ = (
    "config",
    "MATRIX_HOMESERVER",
    "MATRIX_USER_ID",
    "MATRIX_USER_SECRET",
    "MATRIX_SKIP_EVENTS",
    "MATRIX_PUBLIC_SPACE_ID",
    "MATRIX_PUBLIC_SPACE_ALIAS",
    "MATRIX_PRIVATE_SPACE_ID",
    "MATRIX_HELP_ROOM_ALIAS",
    "SQLALCHEMY_DATABASE_URL",
    "FLASK_SECRET_KEY",
    "FLASK_SERVER_NAME",
    "FLASK_APPLICATION_ROOT",
    "FLASK_PREFERRED_URL_SCHEME",
    "OIDC_CLIENT_ID",
    "OIDC_CLIENT_SECRET",
    "OIDC_CONFIGURATION_URL",
    "OIDC_API_BASE_URL",
    "OIDC_SCOPES",
    "OIDC_EMAIL_REGEX",
)
