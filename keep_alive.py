"""
Keep-alive HTTP server for Render / Heroku
"""

import os
import threading

try:
    from flask import Flask, Response
    HAS_FLASK = True
except ImportError:
    HAS_FLASK = False

if HAS_FLASK:
    app = Flask(__name__)

    @app.route("/", methods=["GET"])
    def health():
        return Response("OK", status=200)

    def _run():
        port = int(os.environ.get("PORT", 8080))
        app.run(
            host="0.0.0.0",
            port=port,
            debug=False,
            use_reloader=False
        )

    def keep_alive(*args, **kwargs):
        t = threading.Thread(target=_run)
        t.daemon = True
        t.start()
else:
    def keep_alive(*args, **kwargs):
        pass
