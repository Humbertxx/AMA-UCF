import datetime
from pathlib import Path
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import os.path
from config import SCOPES
import config

   
# validation and retrieval of Google Calendar         
def retrieveKeyGCalendar():
  try:  
    token_path = config.get_token_path()
    credentials_path = config.get_calendar_credentials_path()
    creds = getCredentials(str(token_path), str(credentials_path))
    service = build("calendar", "v3", credentials=creds)
    return service
  except HttpError as error:
    print(f"An error occurred: {error}")
  
# gets the necessary credentials that the user is going to use to validate its instance in program
# creates the toke.json which is the place where validation is found 
# returns credentials 
def getCredentials(tokenFile, credentialFile):
  creds = None
  if os.path.exists(tokenFile):
    creds = Credentials.from_authorized_user_file(tokenFile, SCOPES)
  # If there are no (valid) credentials available, let the user log in.
  if not creds or not creds.valid:
    if creds and creds.expired and creds.refresh_token:
      creds.refresh(Request())
    else:
      flow = InstalledAppFlow.from_client_secrets_file(credentialFile, SCOPES)
      creds = flow.run_local_server(port=0)
    # Save the credentials for the next run
    with open(tokenFile, "w") as token:
      token.write(creds.to_json())
  return creds

def create_new_calendar(service, name, timezone="America/New_York"):
  calendar_body = {
    "summary": name,
    "timeZone": timezone
  }
  created_calendar = service.calendars().insert(body=calendar_body).execute()
  return created_calendar["id"]

# gets events that are present in Google Calendar
# is a variable output, change values to get in "maxResults="  
# if summary not found in given, returns event without summary
def getEvents(service):
  now = datetime.datetime.now(tz=datetime.timezone.utc).isoformat()
  print("Getting the upcoming 10 events")
  events_result = (
    service.events().list(calendarId="primary", timeMin=now, maxResults=10,
                            singleEvents=True, orderBy="startTime",).execute())
  events = events_result.get("items", [])
  if not events:
    print("No upcoming events found.")
    return
  # Prints the start and name of the next 10 events
  for event in events:
    start = event["start"].get("dateTime", event["start"].get("date"))
    if event.get("summary"): 
      print(start, event["summary"])
    else:
      print(start, event)

# creates an event based on the list given in first parameter, gets the service 
# (which is the gate-away to Google Calendar) and transition the values from the given list to Google Calendar
def createEvent(gsEvent=None, service=None, calendar_id=None):
    TMZ = config.get_calendar_timezone()
    if gsEvent and service:
      colorEvent = eventType(gsEvent['organizer'])
    
      event = {
        "summary" : gsEvent['summary'],
        "location" : gsEvent['location'],
        "description" : gsEvent['description'],
        "colorId" : colorEvent,
        "start" : {
            "dateTime" : gsEvent['start']['dateTime'],
            "timeZone" : TMZ, 
        },
         "end" : {
            "dateTime" : gsEvent['end']['dateTime'],
            "timeZone" : TMZ, 
        }
      }
      event = service.events().insert(calendarId=calendar_id, body=event).execute()
      print(f"event created {event.get('htmlLink')}")
    else:
      print("this is not a valid ")

# gets the color for specific event type
def eventType(eventSummary):
  color = 0
  match str(eventSummary).title():
    case "Social":
      color = 1
    case "Workshop":
      color = 2
    case "Volunteering":
      color = 3
    case "Partial Proceeds":
      color = 4
    case "Speaker":
      color = 5
    case "E-board Meeting":
      color = 6
    case "Tailgate":
      color = 7
    case "Cabinet Meeting":
      color = 8
    case _:
      color
  return color