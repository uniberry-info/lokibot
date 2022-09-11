import re
import flask
import flask_sqlalchemy
import werkzeug.middleware.proxy_fix
import werkzeug.exceptions
import authlib.integrations.flask_client
import authlib.integrations.base_client
import logging
import requests

log = logging.getLogger(__name__)

from lokiunimore.config import config, FLASK_SECRET_KEY, SQLALCHEMY_DATABASE_URL
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
    "SECRET_KEY": FLASK_SECRET_KEY.__wrapped__,
    "SQLALCHEMY_DATABASE_URI": SQLALCHEMY_DATABASE_URL.__wrapped__,
    "SQLALCHEMY_TRACK_MODIFICATIONS": False,
})


db = flask_sqlalchemy.SQLAlchemy(app=app, metadata=TableDeclarativeBase.metadata)
"""
:mod:`sqlalchemy` database engine, usable by the whole :data:`.app`.
"""

db.create_all()


oauth = authlib.integrations.flask_client.OAuth(app=app)
"""
OAuth2 :mod:`flask` extension installed on :data:`.app`.
"""

oauth.register(
    name="oidc",
    server_metadata_url=app.config["OIDC_CONFIGURATION_URL"],
    api_base_url=app.config["OIDC_API_BASE_URL"],
    client_kwargs={
        "scope": app.config["OIDC_SCOPES"]
    },
)


matrix = MatrixClientExtension(app=app)
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
    user = db.session.query(MatrixUser).filter_by(token=token).first_or_404()
    return flask.render_template("matrix.html", user=user, token=token)


@app.route("/matrix/<token>/link")
def page_matrix_link(token):
    db.session.query(MatrixUser).filter_by(token=token).first_or_404()
    flask.session["matrix_token"] = token
    return oauth.oidc.authorize_redirect(flask.url_for("page_oidc_authorize", _external=True))


@app.route("/matrix/<token>/invite")
def page_matrix_invite(token):
    matrix_user: MatrixUser = db.session.query(MatrixUser).filter_by(token=token).first_or_404()

    log.debug(f"Sending private space invite to: {matrix_user.id}")
    matrix.room_invite(room_id=app.config["MATRIX_PRIVATE_SPACE_ID"], user_id=matrix_user.id)
    log.info(f"Sent private space invite to: {matrix_user.id}")

    return flask.redirect(flask.url_for("page_matrix_profile", token=token))


@app.route("/authorize")
def page_oidc_authorize():
    try:
        token = oauth.oidc.authorize_access_token()
    except werkzeug.exceptions.BadRequestKeyError:
        return flask.render_template(
            "error.html",
            when="""durante la verifica del login con Google""",
            details="""Mancano i parametri query necessari per effettuare l'autenticazione OAuth2.""",
            tip="""Rifai la procedura di connessione account da capo.<br>Se il problema persiste, inviami un'email a <a href="mailto:me@steffo.eu">me@steffo.eu</a>, e provvederò a risolvere il problema!"""
         )
    except authlib.integrations.base_client.errors.OAuthError:
        return flask.render_template(
            "error.html",
            when="""durante la verifica del login con Google""",
            details="""Qualcosa è inaspettatamente andato storto durante l'autenticazione OAuth2.""",
            tip="""Rifai la procedura di connessione account da capo.<br>Se il problema persiste, inviami un'email a <a href="mailto:me@steffo.eu">me@steffo.eu</a>, e provvederò a risolvere il problema!"""
        )

    # Not sure of why the nonce is now required or if I'm using it correctly
    account = oauth.oidc.parse_id_token(token=token, nonce=token["userinfo"]["nonce"])

    if not account.email_verified:
        return flask.render_template(
            "error.html",
            when="""durante la verifica del tuo account Google""",
            details="""L'email del tuo account Google non è verificata.""",
            tip="""Probabilmente hai effettuato l'accesso con l'account Google sbagliato.<br>Effettua il <a href="https://accounts.google.com/logout">logout da tutti i tuoi account Google</a> e riprova!"""
        ), 403

    # noinspection PyTypeChecker
    if not re.match(app.config["OIDC_EMAIL_REGEX"], account.email):
        return flask.render_template(
            "error.html",
            when="""durante la verifica del tuo account Google""",
            details="""Questo account Google non appartiene all'organizzazione <i>studenti@UniMoRe</i>.""",
            tip="""Probabilmente hai effettuato l'accesso con l'account Google sbagliato.<br>Effettua il <a href="https://accounts.google.com/logout">logout da tutti i tuoi account Google</a> e riprova!"""
        ), 403

    local_account = db.session.merge(Account(
        email=account.email,
        first_name=account.given_name,
        last_name=account.family_name,
    ))

    if matrix_token := flask.session.pop("matrix_token", None):
        matrix_user = db.session.query(MatrixUser).filter_by(token=matrix_token).first_or_404()
        matrix_user.account = local_account

        db.session.commit()

        return flask.redirect(flask.url_for("page_matrix_invite", token=matrix_token))

    else:
        return flask.render_template(
            "error.html",
            when="""durante il collegamento dei tuoi account""",
            details="""Non è stato possibile trovare l'account da collegare.""",
            tip="""Probabilmente hai rifiutato il cookie di sessione in cui viene salvato l'account locale da collegare. Assicurati che il tuo browser lo accetti, poi riprova!"""
        ), 403
