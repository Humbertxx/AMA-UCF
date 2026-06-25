from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

import datetime
import os.path
import hashlib

from ama_ucf.utils import evaluate_response_status, getSemester
from ama_ucf.config import SCOPES_CALENDAR, TOKEN_FILE_PATH, \
  CREDENTIALS_CALENDAR_FILE_PATH, CALENDAR_TZ, CALENDAR_NAME, \
    EVENT_TYPE_MAP, CALENDAR_ID, AUTO_CREATE_CALENDAR
    
# validation and retrieval of Google Calendar         
def create_calendar_service():
  try:  
    api_key_path = CREDENTIALS_CALENDAR_FILE_PATH
    token_path = TOKEN_FILE_PATH
    
    if not api_key_path or not os.path.exists(api_key_path):
      raise FileNotFoundError("Google Calendar credential path is not configured or file is missing.")

    credentials_response = get_credentials(str(token_path), str(api_key_path))
    if not credentials_response["success"]:
      return credentials_response

    creds = credentials_response["data"]
    service = build("calendar", "v3", credentials=creds)
    
    return evaluate_response_status(service)
  
  except Exception as exc:
    return evaluate_response_status(None, str(exc))
  
# get the calendar ID based on its name
def calendar_id(service):
  try:
    if not service:
      raise ValueError("Calendar service is required.")

    if CALENDAR_ID is not None:
      return evaluate_response_status(CALENDAR_ID)
  
    calendars_results = service.calendarList().list().execute()
    calendars = calendars_results.get("items", [])
  
    for calendar in calendars:
      if calendar.get("summary") == CALENDAR_NAME:
        return evaluate_response_status(calendar["id"])
  
    if AUTO_CREATE_CALENDAR is True:
      return create_new_calendar(CALENDAR_NAME, service)
    
    raise ValueError(f"Calendar not found: {CALENDAR_NAME}")
  
  except Exception as exc:
    return evaluate_response_status(None, str(exc))
    
    
# gets the necessary credentials that the user is going to use to validate its instance in program
# creates the toke.json which is the place where validation is found 
# returns credentials 
def get_credentials(tokenFile: str, credentialFile: str):
  try:
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
              
    return evaluate_response_status(creds)
  
  except Exception as exc:
    return evaluate_response_status(None, str(exc))

# creates secondary calendar
def create_new_calendar(name: str, service) -> str:
  try:
    if not name:
      raise ValueError("Calendar name is required.")
    if not service:
      raise ValueError("Calendar service is required.")

    calendar_body = {
      "summary": name,
      "timeZone": CALENDAR_TZ
    }
    created_calendar = service.calendars().insert(body=calendar_body).execute()
    return evaluate_response_status(created_calendar["id"])
  
  except Exception as exc:
    return evaluate_response_status(None, str(exc))

# gets events that are present in Google Calendar
# is a variable output, change values to get in "maxResults="  
# if summary not found in given, returns event without summary
# debugging code
def get_events(service):
  try:
    if not service:
      raise ValueError("Calendar service is required.")

    now = datetime.datetime.now(tz=datetime.timezone.utc).isoformat()
    
    events_result = (
      service.events().list(
        calendarId="primary", 
        timeMin=now, 
        maxResults=10, 
        singleEvents=True, 
        orderBy="startTime",
        )
      .execute()
      )
    
    return evaluate_response_status(events_result.get("items", []))
  
  except Exception as exc:
    return evaluate_response_status(None, str(exc))

# creates an event based on the list given in first parameter, gets the service 
# (which is the gate-away to Google Calendar) and transition the values from the given list to Google Calendar
def create_event(gsEvent: dict, service, calendar_id: str):
  try:
    if not gsEvent:
      raise ValueError("Google Sheets event is required.")
    if not service:
      raise ValueError("Calendar service is required.")
    if not calendar_id:
      raise ValueError("Calendar ID is required.")

    event_key_response = build_event_key(gsEvent, calendar_id)
    if not event_key_response["success"]:
      return event_key_response

    event_key = event_key_response["data"]
    
    exists_response = event_already_exists(service, calendar_id, event_key)
    if not exists_response["success"]:
      return exists_response

    if exists_response["data"]:
      print(f"Skipping duplicate: {event_key}")
      return evaluate_response_status({"status": "skipped_duplicate", "event_key": event_key, "event": None})
    
    color_response = event_type(gsEvent["organizer"])
    if not color_response["success"]:
      return color_response

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
      "colorId" : color_response["data"],
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
    
    return evaluate_response_status({"status": "created", "event_key": event_key, "event": event})
  
  except Exception as exc:
    return evaluate_response_status(None, str(exc))

# helper to skip already existing events
def event_already_exists(service, calendar_id: str, event_key):
  try:
    if not service:
      raise ValueError("Calendar service is required.")
    if not calendar_id:
      raise ValueError("Calendar ID is required.")
    if not event_key:
      raise ValueError("Event key is required.")

    results = service.events().list(calendarId=calendar_id, privateExtendedProperty=f"ama_row_key={event_key}").execute()
    return evaluate_response_status(len(results.get("items", [])) > 0)
  
  except Exception as exc:
    return evaluate_response_status(None, str(exc))

# helper to get the color for specific event type
def event_type(eventSummary):
  try:
    key = str(eventSummary).strip().title()
    return evaluate_response_status(EVENT_TYPE_MAP.get(key, 0))
  
  except Exception as exc:
    return evaluate_response_status(None, str(exc))

# build unique identifier to sync worksheet to calendar efficiently
def build_event_key(gsEvent: dict, calendar_id: str):
  try:
    semester_response = getSemester()
    if not semester_response["success"]:
      return semester_response

    parts = "|".join([
      semester_response["data"],
      gsEvent.get("summary", ""),
      gsEvent.get("organizer", ""),
      str(gsEvent.get("start", "")),
      gsEvent.get("location", ""),
      calendar_id,
    ]) # "Fall '26|Disney Speaker_Workshop|2026-09-14T08:00:00|BA2|{AMA Calendar ID}"
    event_key = hashlib.sha256(parts.encode("utf-8")).hexdigest()
    
    return evaluate_response_status(event_key)
  
  except Exception as exc:
    return evaluate_response_status(None, str(exc))
