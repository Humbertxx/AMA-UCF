import datetime

from ama_ucf.utils import evaluate_response_status, unwrap_response
from ama_ucf.calendar import create_calendar_service

# gets events that are present in Google Calendar
# is a variable output, change values to get in "maxResults="  

def main():
    service = unwrap_response(create_calendar_service(), "create calendar service")
    calendar_events = unwrap_response(get_events(service), "get events in calendar")
    print(calendar_events)
    
def get_events(service) -> dict:
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

if __name__ == "__main__":
  main()