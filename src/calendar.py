from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

import datetime
import os.path
from config import SCOPES_CALENDAR, TOKEN_FILE_PATH, \
  CREDENTIALS_CALENDAR_FILE_PATH, CALENDAR_TZ, CALENDAR_NAME, \
    EVENT_TYPE_MAP, CALENDAR_ID, AUTO_CREATE_CALENDAR
    
from utils import getSemester


# validation and retrieval of Google Calendar         
def createCalendarService():
  try:  
    api_key_path = CREDENTIALS_CALENDAR_FILE_PATH
    token_path = TOKEN_FILE_PATH
    
    if not api_key_path or not os.path.exists(api_key_path):
      raise FileNotFoundError("Google Calendar credential path is not configured or file is missing.")

    creds = getCredentials(str(token_path), str(api_key_path))
    service = build("calendar", "v3", credentials=creds)
    
    return service
  
  except FileNotFoundError as exc:
    return {"error": exc, "data": None, "success": "false"}
  
# get the calendar ID based on its name
def calendar_id(service):
  try:
    if CALENDAR_ID is not None:
      return CALENDAR_ID
  
    calendars_results = service.calendarList().list.execute()
    calendars = calendars_results.get("items", [])
  
    for calendar in calendars:
      if calendar.get(CALENDAR_NAME):
        return calendar["id"]
  
    if AUTO_CREATE_CALENDAR is True:
      calendar = createNewCalendar(CALENDAR_NAME)
    
      return calendar["id"]
  
  except Exception as exc:
    return {"error": exc, "data": None, "success": "false"}
    
    
# gets the necessary credentials that the user is going to use to validate its instance in program
# creates the toke.json which is the place where validation is found 
# returns credentials 
def getCredentials(tokenFile: str, credentialFile: str):
  creds = None
  
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
def createNewCalendar(name: str, service) -> str:
  tz = CALENDAR_TZ
  
  calendar_body = {
    "summary": name,
    "timeZone": tz
  }
  created_calendar = service.calendars().insert(body=calendar_body).execute()
  return created_calendar["id"]

# gets events that are present in Google Calendar
# is a variable output, change values to get in "maxResults="  
# if summary not found in given, returns event without summary
# debugging code
def getEvents(service):
  now = datetime.datetime.now(tz=datetime.timezone.utc).isoformat()
  
  print("Getting the upcoming 10 events")
  
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
  
  events = events_result.get("items", [])
  if not events:
    print("No upcoming events found.")
    return
  # Prints the start and name of the next 10 events
  for event in events:
    start = event["start"].get("dateTime") or event["start"].get("date")
    
    if event.get("summary"): 
      print(start, event, event["summary"])
    else:
      print(start, event)

# creates an event based on the list given in first parameter, gets the service 
# (which is the gate-away to Google Calendar) and transition the values from the given list to Google Calendar
def createEvent(gsEvent: str, service, calendar_id: str):
  tz = CALENDAR_TZ
  if gsEvent and service:
    event_key = f"{gsEvent['timestamp']}_{getSemester()}_{gsEvent['summary']}_{gsEvent['start']}_{gsEvent['location']}_{calendar_id}"
    
    if event_already_exists(service,calendar_id, event_key):
      print(f"Skipping duplicate: {event_key}")
      return None
    
    colorEvent = eventType(gsEvent['organizer'])
    if "DateTime" in gsEvent["start"]:
      start_dt =  {"dateTime" : gsEvent['start']['dateTime'],"timeZone" : tz},
      end_dt = {"dateTime" : gsEvent['end']['dateTime'], "timeZone" : tz}
    
    else:
      start_dt =  {"dateTime" : gsEvent['start'],"timeZone" : tz},
      end_dt = {"dateTime" : gsEvent['end'], "timeZone" : tz}
    
    body = {
      "summary" : gsEvent['summary'],
      "location" : gsEvent['location'],
      "description" : gsEvent['description'],
      "colorId" : colorEvent,
      "start" : start_dt,
      "end" : end_dt,
      "extendedProperties": {
        "private": {
            "ama_row_key": event_key  # e.g. "2026-08-01_Workshop"
          }
      }
    }
    event = service.events().insert(calendarId=calendar_id, body=body).execute()
    print(f"event created {event.get('htmlLink')}")
    
    return event 
  
  else:
    raise HttpError("this is not a valid htmlLink")

# helper to skip already existing events
def event_already_exists(service, calendar_id: str, event_key):
    results = service.events().list(calendarId=calendar_id, privateExtendedProperty=f"ama_row_key={event_key}").execute()
    return len(results.get("items", [])) > 0

# helper to get the color for specific event type
def eventType(eventSummary):
  key = str(eventSummary).strip().title()
  return EVENT_TYPE_MAP.get(key, 0)