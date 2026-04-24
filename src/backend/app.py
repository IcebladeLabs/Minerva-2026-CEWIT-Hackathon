"""
Flask application factory.
In Docker: nginx serves the React build, Flask only serves API + snapshots.
In dev: Vite dev server proxies /api to Flask.
"""
from __future__ import annotations
import os, logging
from flask import Flask, send_from_directory
from flask_cors import CORS
from backend.config import HOST, PORT, DEBUG, SNAPSHOTS_DIR
from backend.database import init_db, close_db, get_db
from backend.routes import api, init_detection

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)

FRONTEND_DIST = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend", "dist")


def create_app() -> Flask:
    app = Flask(__name__)
    CORS(app)

    app.register_blueprint(api)

    @app.before_request
    def _ensure_db():
        get_db()

    @app.teardown_appcontext
    def _close(exc):
        close_db()

    @app.route("/snapshots/<path:filename>")
    def serve_snapshot(filename):
        return send_from_directory(SNAPSHOTS_DIR, filename)

    # Serve built React app if running without nginx (e.g. direct python3 run.py)
    if os.path.isdir(FRONTEND_DIST):
        @app.route("/")
        def index():
            return send_from_directory(FRONTEND_DIST, "index.html")

        @app.route("/<path:path>")
        def static_files(path):
            fpath = os.path.join(FRONTEND_DIST, path)
            if os.path.isfile(fpath):
                return send_from_directory(FRONTEND_DIST, path)
            return send_from_directory(FRONTEND_DIST, "index.html")

    init_db()
    os.makedirs(SNAPSHOTS_DIR, exist_ok=True)

    init_detection()

    return app


if __name__ == "__main__":
    create_app().run(host=HOST, port=PORT, debug=DEBUG, use_reloader=False)
