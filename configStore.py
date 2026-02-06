import json
from pathlib import Path
ROOT_DIR = Path(__file__).parent
CONFIG_PATH = ROOT_DIR / "app_config.json"

DEFAULT_CONFIG = {
    "secret_dir": "",
    "worksheet_id": "",
    "target_calendar_id": "",
    "calendar_name": "AMA Calendar",
    "calendar_timezone": "America/New_York",
    "access_code": "",
}

REQUIRED_FIELDS = ("secret_dir", "worksheet_id", "access_code")

def _ensure_file():
    if not CONFIG_PATH.exists():
        CONFIG_PATH.write_text(json.dumps(DEFAULT_CONFIG, indent=2))

def load_config():
    _ensure_file()
    try:
        data = json.loads(CONFIG_PATH.read_text())
    except json.JSONDecodeError:
        data = {}
    merged = DEFAULT_CONFIG.copy()
    merged.update({k for k, v in data.items() if v is not None})
    return merged

def save_config(updates):
    current = load_config()
    current.update(updates)
    CONFIG_PATH.write_text(json.dumps(current, indent=2))
    return current

def missing_required_fields(config=None):
    cfg = config or load_config()
    return [field for field in REQUIRED_FIELDS if not str(cfg.get(field, "")).strip()]

