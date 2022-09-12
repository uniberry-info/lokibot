import re
import flask
import flask_sqlalchemy
import werkzeug.middleware.proxy_fix
import werkzeug.exceptions
import authlib.integrations.flask_client
import authlib.integrations.base_client
import requests

from lokiunimore.config import config, FLASK_SECRET_KEY, SQLALCHEMY_DATABASE_URL, FLASK_SERVER_NAME, FLASK_APPLICATION_ROOT, FLASK_PREFERRED_URL_SCHEME
from lokiunimore.sql.tables import Base as TableDeclarativeBase
from lokiunimore.sql.tables import Account, MatrixUser
from lokiunimore.web.extensions.matrix_client import MatrixClientExtension


app = flask.Flask(__name__)
"""
The main :mod:`flask` application object.
"""

rp_app = werkzeug.middleware.proxy_fix.ProxyFix(app=app, x_for=1, x_proto=1, x_host=1, x_port=0, x_prefix=0)
"""
Reverse proxied instance of :data:`.app`, to use in production with a Caddy server.
"""

app.config.update({
    **config.proxies.resolve(),
    "SERVER_NAME": FLASK_SERVER_NAME.__wrapped__,
    "APPLICATION_ROOT": FLASK_APPLICATION_ROOT.__wrapped__,
    "PREFERRED_URL_SCHEME": FLASK_PREFERRED_URL_SCHEME.__wrapped__,
    "SECRET_KEY": FLASK_SECRET_KEY.__wrapped__,
    "SQLALCHEMY_DATABASE_URI": SQLALCHEMY_DATABASE_URL.__wrapped__,
    "SQLALCHEMY_TRACK_MODIFICATIONS": False,
})


sqla_extension = flask_sqlalchemy.SQLAlchemy(app=app, metadata=TableDeclarativeBase.metadata)
"""
:mod:`sqlalchemy` database engine, usable by the whole :data:`.app`.
"""


oauth_extension = authlib.integrations.flask_client.OAuth(app=app)
"""
OAuth2 :mod:`flask` extension installed on :data:`.app`.
"""

oauth_extension.register(
    name="oidc",
    server_metadata_url=app.config["OIDC_CONFIGURATION_URL"],
    api_base_url=app.config["OIDC_API_BASE_URL"],
    client_kwargs={
        "scope": app.config["OIDC_SCOPES"]
    },
)


matrix_extension = MatrixClientExtension(app=app)
"""
Synchronous Matrix client for use with Flask.
"""


### Setup the app routes

@app.route("/")
def page_root():
    return flask.render_template("root.html")


@app.route("/privacy")
def page_privacy():
    return flask.render_template("privacy.html")


@app.route("/matrix/<token>/")
def page_matrix_profile(token):
    user: MatrixUser = sqla_extension.session.query(MatrixUser).filter_by(token=token).first_or_404()
    if user.account is None:
        return flask.render_template("matrix/verify.html", user=user, token=token)
    elif not user.joined_private_space:
        return flask.render_template("matrix/join.html", user=user, token=token)
    else:
        return flask.render_template("matrix/complete.html", user=user, token=token)


@app.route("/matrix/<token>/link")
def page_matrix_link(token):
    sqla_extension.session.query(MatrixUser).filter_by(token=token).first_or_404()
    flask.session["matrix_token"] = token
    return oauth_extension.oidc.authorize_redirect(flask.url_for("page_oidc_authorize", _external=True))


@app.route("/matrix/<token>/invite")
def page_matrix_invite(token):
    matrix_user: MatrixUser = sqla_extension.session.query(MatrixUser).filter_by(token=token).first_or_404()

    app.logger.debug(f"Sending private space invite to: {matrix_user.id}")
    try:
        matrix_extension.room_invite(room_id=app.config["MATRIX_PRIVATE_SPACE_ID"], user_id=matrix_user.id)
    except requests.exceptions.HTTPError as e:
        app.logger.warning(f"Failed to send private space invite to {matrix_user.id}: {e}")
        if e.response.status_code == 403:
            return flask.render_template("errors/failed-invite.html"), 500
        if e.response.status_code == 429:
            return flask.render_template("errors/rate-invite.html"), 500

    app.logger.info(f"Sent private space invite to: {matrix_user.id}")

    return flask.redirect(flask.url_for("page_matrix_profile", token=token))


@app.route("/authorize")
def page_oidc_authorize():
    try:
        token = oauth_extension.oidc.authorize_access_token()
    except (authlib.integrations.base_client.errors.OAuthError, werkzeug.exceptions.BadRequestKeyError):
        return flask.render_template("errors/oidc.html"), 400

    # Not sure of why the nonce is now required or if I'm using it correctly
    account = oauth_extension.oidc.parse_id_token(token=token, nonce=token["userinfo"]["nonce"])

    if not account.email_verified:
        return flask.render_template("errors/not-verified.html"), 403

    # noinspection PyTypeChecker
    if not re.match(app.config["OIDC_EMAIL_REGEX"], account.email):
        return flask.render_template("errors/not-student.html"), 403

    local_account = sqla_extension.session.merge(Account(
        email=account.email,
        first_name=account.given_name,
        last_name=account.family_name,
    ))

    if matrix_token := flask.session.pop("matrix_token", None):
        matrix_user = sqla_extension.session.query(MatrixUser).filter_by(token=matrix_token).first_or_404()
        matrix_user.account = local_account

        sqla_extension.session.commit()

        return flask.redirect(flask.url_for("page_matrix_invite", token=matrix_token))

    else:
        return flask.render_template("errors/no-link.html"), 403


@app.errorhandler(404)
def page_404(_):
    return flask.render_template("errors/not-found.html"), 404


__all__ = (
    "app",
    "rp_app",
    "sqla_extension",
    "oauth_extension",
    "oauth_extension",
    "matrix_extension",
    "page_root",
    "page_privacy",
    "page_matrix_profile",
    "page_matrix_link",
    "page_matrix_invite",
    "page_oidc_authorize",
)
