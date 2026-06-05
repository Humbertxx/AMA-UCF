import os

SPREADSHEET_ID    = os.getenv("SPREADSHEET_ID")
CALENDAR_ID       = os.getenv("CALENDAR_ID")
SERVICE_ACCT_KEY  = os.getenv("SERVICE_ACCT_KEY")
CALENDAR_TZ       = os.getenv("CALENDAR_TIMEZONE", "America/New_York")
CALENDAR_NAME     = os.getenv("CALENDAR_NAME", "AMA Calendar")
POLL_INTERVAL     = int(os.getenv("POLL_INTERVAL_SECONDS", "300"))

SCOPES_CALENDAR   = ["https://www.googleapis.com/auth/calendar"]

