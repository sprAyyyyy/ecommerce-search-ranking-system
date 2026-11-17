
import os
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent

api = subprocess.Popen([
    sys.executable,
    "-m",
    "uvicorn",
    "amazon_search_service.main:app",
    "--host",
    "127.0.0.1",
    "--port",
    "8000",
], cwd=ROOT)

time.sleep(3)

env = os.environ.copy()
env["API_URL"] = "http://127.0.0.1:8000"

try:
    ui = subprocess.Popen([
        sys.executable,
        "-m",
        "streamlit",
        "run",
        "streamlit_app.py",
        "--server.address",
        "0.0.0.0",
        "--server.port",
        "8501",
    ], cwd=ROOT, env=env)

    ui.wait()

finally:
    api.terminate()
