import datetime

from ama_ucf.calendar import create_calendar_service, calendar_id

# gets events that are present in Google Calendar
def main():
  event_amount = int(input("enter amount of events to find")) or 10
  
  service = create_calendar_service()
  id = calendar_id(service)
  calendar_events = get_events(service, id, event_amount)
  
  print(calendar_events)
    
def get_events(service, id, event_amount) -> list:
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

  return events_result.get("items", [])

if __name__ == "__main__":
  main()
