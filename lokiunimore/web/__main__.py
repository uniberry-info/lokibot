import flask.logging
import lokiunimore.utils.logs
from lokiunimore.config import config

from .app import app


def main():
    lokiunimore.utils.logs.install_log_handler(app.logger)
    app.logger.removeHandler(flask.logging.default_handler)

    app.run(host="127.0.0.1", port=30008, debug=True)


if __name__ == "__main__":
    config.proxies.resolve()
    main()
