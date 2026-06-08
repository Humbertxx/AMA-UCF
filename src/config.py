import os

SPREADSHEET_ID    = os.getenv("SPREADSHEET_ID")
CALENDAR_NAME     = os.getenv("CALENDAR_NAME")

SERVICE_ACCT_KEY  = os.getenv("SERVICE_ACCT_KEY")
CALENDAR_TZ       = os.getenv("CALENDAR_TIMEZONE", "America/New_York")
CALENDAR_NAME     = os.getenv("CALENDAR_NAME", "AMA Calendar")
CALENDAR_ID       = os.getenv("CALENDAR_ID", None)
POLL_INTERVAL     = int(os.getenv("POLL_INTERVAL_SECONDS", "300"))

CREDENTIALS_WORKSHEET_FILE_PATH = os.getenv("CREDENTIALS_WORKSHEET_FILE_PATH")
CREDENTIALS_CALENDAR_FILE_PATH = os.getenv("CREDENTIALS_CALENDAR_FILE_PATH")
TOKEN_FILE_PATH = os.getenv("TOKEN_FILE_PATH")

SCOPES_CALENDAR   = ["https://www.googleapis.com/auth/calendar"]

SEMESTER_FORMAT = os.getenv("SEMESTER_FORMAT", "{season} '{short_yr}")
AUTO_CREATE_CALENDAR=True

EVENT_TYPE_MAP = {
  "Social": 1,
  "Workshop": 2,
  "Volunteering": 3,
  "Partial Proceeds": 4,
  "Speaker": 5,
  "E-Board Meeting": 6,
  "Tailgate": 7,
  "Cabinet Meeting": 8,
}