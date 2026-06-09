import os

def _load_env(path: str):
    if not os.path.exists(path):
        return
    with open(path) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, val = line.partition("=")
            os.environ.setdefault(key.strip(), val.strip())

_BASE = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
_load_env(os.path.join(_BASE, "config/settings.env"))

BASE_DIR       = _BASE
DOWNLOAD_DIR   = os.environ.get("DOWNLOAD_DIR",  os.path.join(_BASE, "downloads"))
LOG_PATH       = os.environ.get("LOG_PATH",      os.path.join(_BASE, "logs/app.log"))
FLASK_HOST     = os.environ.get("FLASK_HOST",    "0.0.0.0")
FLASK_PORT     = int(os.environ.get("FLASK_PORT", 8080))
MAX_CONCURRENT = int(os.environ.get("MAX_CONCURRENT", 1))
DISCORD_TOKEN  = os.environ.get("DISCORD_TOKEN", "")

os.makedirs(DOWNLOAD_DIR, exist_ok=True)
os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)
