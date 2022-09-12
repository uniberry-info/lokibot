import flask.logging
import lokiunimore.utils.logs

from .app import app

lokiunimore.utils.logs.install_log_handler(app.logger)
app.logger.removeHandler(flask.logging.default_handler)

app.run(host="127.0.0.1", port=30008, debug=True)
