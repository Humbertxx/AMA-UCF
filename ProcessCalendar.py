from AMAflex import retrievingKeyGspread, normalizingEvents, \
                    autoUpdate, getAllWorksheet, \
                    retrieveKeyGCalendar, createEvent, \
                    create_new_calendar
from AMAflex import config


def resolve_calendar_id(service):
    """Reuse a provided calendar id or create a new calendar on demand."""
    target_calendar = config.get_target_calendar_id()
    if target_calendar:
        return target_calendar
    calendar_name = config.get_calendar_name()
    calendar_timezone = config.get_calendar_timezone()
    created_calendar_id = create_new_calendar(service, calendar_name, calendar_timezone)
    print(f"Created calendar {calendar_name} ({created_calendar_id})")
    return created_calendar_id


def sync_events(run_mode = "snapshot"):
    """
    Fetch rows from Google Sheets and sync them to Google Calendar.

    run_mode:
        - snapshot (default): converts every valid row into an event.
        - watch: waits for new rows (uses autoUpdate) before creating events.
    """
    worksheet = retrievingKeyGspread()
    rows = getAllWorksheet(worksheet)

    if run_mode == "watch":
        candidate_events = autoUpdate(rows)
    else:
        candidate_events = normalizingEvents(rows)

    calendar = retrieveKeyGCalendar()
    calendar_id = resolve_calendar_id(calendar)

    created_events = []
    for event in candidate_events:
        created = createEvent(event, calendar, calendar_id)
        if created:
            created_events.append(
                {
                    "summary": created.get("summary", "Untitled Event"),
                    "link": created.get("htmlLink", ""),
                }
            )

    return {
        "run_mode": run_mode,
        "events_found": len(candidate_events),
        "events_created": len(created_events),
        "calendar_id": calendar_id,
        "created_events": created_events,
    }


