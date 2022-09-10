import flask
import nio
import contextlib
import threading
import hmac
import hashlib
import requests

from lokiunimore.matrix.device import generate_device_id, generate_device_name


class MatrixClientExtension:
    def __init__(self, app: flask.Flask = None):
        if app is not None:
            self.init_app(app)

        token = hmac.new(key=app.config["MATRIX_USER_SECRET"].encode("utf8"), msg=app.config["MATRIX_USER_ID"].encode("utf8"), digestmod=hashlib.sha512).hexdigest()

        response = requests.post(f"{app.config['MATRIX_HOMESERVER']}/_matrix/client/v3/login", json={
            "type": "com.devture.shared_secret_auth",
            "identifier": {
                "type": "m.id.user",
                "user": app.config["MATRIX_USER_ID"],
            },
            "token": token,
            "initial_device_display_name": generate_device_name(__name__),
        })
        response.raise_for_status()
        response = response.json()

        self.access_token = response["access_token"]
        self.device_id = response["device_id"]

    def init_app(self, app: flask.Flask):
        pass
