import flask
import hmac
import hashlib
import requests

from lokiunimore.utils.device_names import generate_device_name


class MatrixClientExtension:
    """
    Flask extension providing a extremely simple, :mod:`requests`-based, synchronous Matrix client.
    """

    def __init__(self, app: flask.Flask = None):
        if app is not None:
            self.init_app(app)

        token = hmac.new(
            key=app.config["MATRIX_USER_SECRET"].encode("utf8"),
            msg=app.config["MATRIX_USER_ID"].encode("utf8"),
            digestmod=hashlib.sha512
        ).hexdigest()

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

    def room_invite(self, room_id: str, user_id: str):
        """
        Send an invite to a Matrix user for a certain room.

        :param room_id: The room to invite the user to.
        :param user_id: The user to invite.
        """

        response = requests.post(
            f"{flask.current_app.config['MATRIX_HOMESERVER']}/_matrix/client/v3/rooms/{flask.current_app.config['MATRIX_PRIVATE_SPACE_ID']}/invite",
            json={
                "reason": "Account linked",
                "user_id": user_id,
            },
            headers={
                "Authorization": f"Bearer {self.access_token}",
            }
        )
        response.raise_for_status()
