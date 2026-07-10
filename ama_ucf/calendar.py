import hashlib
import os.path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

from ama_ucf.config import (
  AUTO_CREATE_CALENDAR,
  CALENDAR_ID,
  CALENDAR_NAME,
  CALENDAR_TZ,
  CREDENTIALS_CALENDAR_FILE_PATH,
  EVENT_TYPE_MAP,
  SCOPES_CALENDAR,
  TOKEN_FILE_PATH,
)
from ama_ucf.utils import get_semester


# validation and retrieval of Google Calendar
def create_calendar_service():
  api_key_path = CREDENTIALS_CALENDAR_FILE_PATH
  token_path = TOKEN_FILE_PATH

  if not api_key_path or not os.path.exists(api_key_path):
    raise FileNotFoundError("Google Calendar credential path is not configured or file is missing.")

  creds = get_credentials(token_path, api_key_path)
  return build("calendar", "v3", credentials=creds)


# get the calendar ID based on its name if ID not present, if not creates one
def calendar_id(service):
  if not service:
    raise ValueError("Calendar service is required.")

  if CALENDAR_ID:
    return CALENDAR_ID

  calendars_results = service.calendarList().list().execute()
  calendars = calendars_results.get("items", [])

  for calendar in calendars:
    if calendar.get("summary") == CALENDAR_NAME:
      return calendar["id"]

  if AUTO_CREATE_CALENDAR:
    return create_new_calendar(CALENDAR_NAME, service)

  raise ValueError(f"Calendar not found: {CALENDAR_NAME}")


# gets the necessary credentials that the user is going to use to validate its instance in program creates the toke.json. Returns credentials
def get_credentials(tokenFile: str, credentialFile: str):
  creds = None
  if not tokenFile:
    raise ValueError("OAuth token file path is not configured.")
  if not credentialFile:
    raise ValueError("OAuth credential file path is not configured.")

  if os.path.exists(tokenFile):
    try:
      creds = Credentials.from_authorized_user_file(tokenFile, SCOPES_CALENDAR)
    except Exception:
      creds = None

  if not creds or not creds.valid:
    if creds and creds.expired and creds.refresh_token:
      try:
        creds.refresh(Request())
      except Exception:
        flow = InstalledAppFlow.from_client_secrets_file(credentialFile, SCOPES_CALENDAR)
        creds = flow.run_local_server(port=0)
    else:
      if not os.path.exists(credentialFile):
        raise FileNotFoundError(f"OAuth Client Secrets file missing at: {credentialFile}")

      flow = InstalledAppFlow.from_client_secrets_file(credentialFile, SCOPES_CALENDAR)
      creds = flow.run_local_server(port=0)

    # Save the credentials for the next run
    with open(tokenFile, "w") as token:
      token.write(creds.to_json())

  return creds


# creates secondary calendar
def create_new_calendar(name: str, service) -> str:
  if not name:
    raise ValueError("Calendar name is required.")
  if not service:
    raise ValueError("Calendar service is required.")

  calendar_body = {
    "summary": name,
    "timeZone": CALENDAR_TZ
  }
  created_calendar = service.calendars().insert(body=calendar_body).execute()
  return created_calendar["id"]


# creates an event based on the list given in first parameter, gets the service
# (which is the gate-away to Google Calendar) and transition the values from the given list to Google Calendar
def create_event(gsEvent: dict, service, calendar_id: str, semester: str) -> dict:
  if not gsEvent:
    raise ValueError("Google Sheets event is required.")
  if not service:
    raise ValueError("Calendar service is required.")
  if not calendar_id:
    raise ValueError("Calendar ID is required.")

  event_key = build_event_key(gsEvent, calendar_id, semester)
  exists_response = event_already_exists(service, calendar_id, event_key)

  if exists_response:
    print(f"Skipping duplicate: {event_key}")
    return {"status": "skipped_duplicate", "event_key": event_key, "event": None}

  color_response = event_type(gsEvent["organizer"])

  start_dt = dict(gsEvent["start"])
  end_dt = dict(gsEvent["end"])

  if "dateTime" in start_dt:
    start_dt["timeZone"] = CALENDAR_TZ
  if "dateTime" in end_dt:
    end_dt["timeZone"] = CALENDAR_TZ

  body = {
    "summary" : gsEvent["summary"],
    "location" : gsEvent["location"],
    "description" : gsEvent["description"],
    "colorId" : color_response,
    "start" : start_dt,
    "end" : end_dt,
    "extendedProperties": {
      "private": {
          "ama_row_key": event_key
        }
    }
  }
  event = service.events().insert(calendarId=calendar_id, body=body).execute()
  print(f"event created {event.get('htmlLink')}")

  return {"status": "created", "event_key": event_key, "event": event}


# helper to skip already existing events
def event_already_exists(service, calendar_id: str, event_key: str) -> bool:
  if not service:
    raise ValueError("Calendar service is required.")
  if not calendar_id:
    raise ValueError("Calendar ID is required.")
  if not event_key:
    raise ValueError("Event key is required.")

  results = service.events().list(calendarId=calendar_id, privateExtendedProperty=f"ama_row_key={event_key}").execute()
  return len(results.get("items", [])) > 0


# helper to get the color for specific event type
def event_type(eventSummary):
  key = str(eventSummary).strip().title()
  return EVENT_TYPE_MAP.get(key, 0)


# build unique identifier to sync worksheet to calendar efficiently
def build_event_key(gsEvent: dict, calendar_id: str, semester) -> str:
  semester_name = semester or get_semester()

  parts = "|".join([
    semester_name,
    gsEvent.get("summary", ""),
    gsEvent.get("organizer", ""),
    str(gsEvent.get("start", "")),
    gsEvent.get("location", ""),
    calendar_id,
  ]) # i.e. "Fall '26|Disney Speaker_Workshop|2026-09-14T08:00:00|BA2|{AMA Calendar ID}"
  return hashlib.sha256(parts.encode("utf-8")).hexdigest()
