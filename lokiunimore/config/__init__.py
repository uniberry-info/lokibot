import re
import cfig

config = cfig.Configuration()


@config.required()
def MATRIX_HOMESERVER(val: str) -> str:
    """
    The Matrix homeserver to connect to.
    """
    return val


@config.required()
def MATRIX_USERNAME(val: str) -> str:
    """
    The full username of the Matrix account to login as.
    """
    if not val.startswith("@"):
        raise ValueError("Usernames must start with `@`")
    return val


@config.required()
def MATRIX_SHARED_SECRET(val: str) -> str:
    """
    The shared secret of the server to use to login as a certain account.
    """
    return val


@config.required()
def MATRIX_PARENT_SPACE_ID(val: str) -> str:
    """
    The internal ID of the Matrix space to monitor for new joins.
    """
    if not val.startswith("!"):
        raise ValueError("Internal IDs must start with `!`")
    return val


@config.required()
def MATRIX_PARENT_SPACE_ADDRESS(val: str) -> str:
    """
    The human-readable ID of the Matrix space to monitor for new joins.
    """
    if not val.startswith("#"):
        raise ValueError("Human-readable IDs must start with `#`")
    return val


@config.required()
def MATRIX_CHILD_SPACE_ID(val: str) -> str:
    """
    The internal ID of the Matrix space to add users to when authorized.
    """
    if not val.startswith("!"):
        raise ValueError("Internal IDs must start with `!`")
    return val


@config.required()
def SQLALCHEMY_DATABASE_URI(val: str) -> str:
    """
    The URI of the database to use.
    """
    return val


@config.required()
def SECRET_KEY(val: str) -> str:
    """
    The secret key to use with Flask to sign session cookies.
    """
    return val


@config.required()
def OAUTH_CLIENT_ID(val: str) -> str:
    """
    The client id to use to authenticate account logins.
    """
    return val


@config.required()
def OAUTH_CLIENT_SECRET(val: str) -> str:
    """
    The client secret to use to authenticate account logins.
    """
    return val


@config.required()
def OAUTH_OPENID_CONFIGURATION(val: str) -> str:
    """
    The HTTPS URL to the `.well-known/openid-configuration` file.
    For example, Google uses `https://accounts.google.com/.well-known/openid-configuration`.
    """
    if not val.startswith("https://"):
        raise ValueError("Not a valid HTTPS URL.")
    return val


@config.required()
def OAUTH_API_BASE_URL(val: str) -> str:
    """
    The HTTPS URL base to perform the OAuth2 API calls at.
    For example, Google uses `https://www.googleapis.com/`.
    """
    if not val.startswith("https://"):
        raise ValueError("Not a valid HTTPS URL.")
    return val


@config.optional()
def OAUTH_SCOPES(val: str | None) -> str:
    """
    The scopes to request during the OAuth2 authentication.
    Defaults to `email profile openid`.
    """
    if not val:
        return "email profile openid"
    else:
        return val


@config.required()
def EMAIL_REGEX(val: str) -> re.Pattern:
    """
    A regular expression that the emails of the authenticated users must match to be registered.
    For example, `.+@studenti[.]unimore[.]it`
    """
    return re.compile(val)


__all__ = (

)