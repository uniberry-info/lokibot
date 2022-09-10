import coloredlogs

coloredlogs.install("DEBUG")

from . import app

app.run(host="127.0.0.1", port=30008, debug=True)
