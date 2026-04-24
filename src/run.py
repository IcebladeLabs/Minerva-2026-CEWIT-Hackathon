#!/usr/bin/env python3
"""
Launcher for SentinelLine manufacturing monitor.
    python3 run.py
"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))

from backend.app import create_app
from backend.config import HOST, PORT, DEBUG

print(f"[SentinelLine] Starting on http://{HOST}:{PORT}")
create_app().run(host=HOST, port=PORT, debug=DEBUG, use_reloader=False, threaded=True)
