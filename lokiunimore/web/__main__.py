import logging
import lokiunimore.utils.logs
from . import app

lokiunimore.utils.logs.install_log_handler(logging.getLogger("lokiunimore"))
app.run(host="127.0.0.1", port=30008, debug=True)
