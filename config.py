# here the elements are created. In NOT_SHARE put the workspace JSON files that are automatically will be created
# please note that is taking as given that you have a directory call python were this code is implemented

from pathlib import Path
from configStore import load_config, missing_required_fields

ROOT_DIR = Path(__file__).parent

def _config():
    return load_config()

def ensure_ready():
    missing = missing_required_fields(_config())
    if missing:
        raise RuntimeError(
            f"Missing required configuration values: {', '.join(missing)}. "
            "Visit the setup form to provide them."
        )
def _secret_dir():
    cfg = _config()
    secret_dir = cfg.get("secret_dir") or (ROOT_DIR / "NOT_SHARE")
    secret_path = Path(secret_dir)
    return secret_path

def get_api_key_path():
    ensure_ready()
    path = _secret_dir() / "googleSheet_credentials.json"
    return path

def get_token_path():
    ensure_ready()
    return _secret_dir() / "token.json"

def get_calendar_credentials_path():
    ensure_ready()
    return _secret_dir() / "googleCalendar_credentials.json"

def get_worksheet_id():
    ensure_ready()
    return str(_config()["worksheet_id"])

def get_calendar_name():
    return _config().get("calendar_name") or "AMA Calendar"

def get_calendar_timezone():
    return _config().get("calendar_timezone") or "America/New_York"

def get_target_calendar_id():
    value = str(_config().get("target_calendar_id") or "").strip()
    return value 

def get_access_code():
    ensure_ready()
    return str(_config().get("access_code", "")).strip()

# if modifying these scopes, delete the file token.json.
SCOPES = ["https://www.googleapis.com/auth/calendar"]