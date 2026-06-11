import logging
from src.sheets import get_spreadsheets, get_credentials, calendar_spreadsheet, normalize_calendar
from src.calendar import create_event, create_calendar_service, calendar_id


logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

def main():
    run_snapshot()
    
def run_snapshot(): 
    gc = unwrap_response(get_credentials(), "get credentials")
    sh = unwrap_response(get_spreadsheets(gc), "get spreadsheet")
    cs = unwrap_response(calendar_spreadsheet(sh), "get calendar spreadsheet")
    events = unwrap_response(normalize_calendar(cs), "normalize events")
    service = unwrap_response(create_calendar_service(), "create calendar service")
    cal_id = unwrap_response(calendar_id(service), "resolve calendar ID")
    
    created_count = 0
    skipped_count = 0 # in order to see activity count 
    
    for event in events:
        result = unwrap_response(create_event(event, service, cal_id), "create calendar event")
        if result["status"] == "created":
            created_count += 1
        elif result["status"] == "skipped_duplicate":
            skipped_count += 1

    logging.info(
        "Snapshot complete: %s events found, %s created, %s skipped for %s.",
        len(events),
        created_count,
        skipped_count,
        cal_id,
    )

def unwrap_response(response, action):
    if not isinstance(response, dict):
        raise RuntimeError(f"Could not {action}: expected response dictionary, got {type(response).__name__}")

    if "success" not in response or "error" not in response or "data" not in response:
        raise RuntimeError(f"Could not {action}: malformed response {response}")

    if not response["success"]:
        raise RuntimeError(f"Could not {action}: {response['error']}")

    return response["data"]

if __name__ == "__main__":
    main()