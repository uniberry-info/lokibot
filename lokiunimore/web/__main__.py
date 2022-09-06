from . import app
import coloredlogs


coloredlogs.install("DEBUG")
app.run(host="127.0.0.1", port=30008, debug=True)
