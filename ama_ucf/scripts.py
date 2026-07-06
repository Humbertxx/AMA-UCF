import datetime

from ama_ucf.utils import evaluate_response_status, unwrap_response
from ama_ucf.calendar import create_calendar_service, calendar_id

# gets events that are present in Google Calendar
def main():
  event_amount = int(input("enter amount of events to find", 10))
  
  service = unwrap_response(create_calendar_service(), "create calendar service")
  id = unwrap_response(calendar_id(service), "get current env calendar")
  calendar_events = unwrap_response(get_events(service, id, event_amount), "get events in calendar")
  
  print(calendar_events)
    
def get_events(service, id, event_amount) -> dict:
  try:
    if not service:
      raise ValueError("Calendar service is required.")

    now = datetime.datetime.now(tz=datetime.timezone.utc).isoformat()
    
    events_result = (
      service.events().list(
        calendarId=id, 
        timeMin=now, 
        maxResults=event_amount, 
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