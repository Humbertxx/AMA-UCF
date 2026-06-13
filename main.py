import logging

from src.sheets import (
    calendar_spreadsheet,
    get_credentials,
    get_spreadsheets,
    normalize_calendar,
    normalize_rows,
    worksheet_to_dataframe,
    get_all_worksheets,
    )
from src.calendar import (
    create_event, 
    create_calendar_service, 
    calendar_id,
    )
from src.utils import (
    parse_args,
)
from src.audit import (
    write_sync_log
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")


def main() -> None:
    args = parse_args()
    run_snapshot(semester=args.semester)
    analytics_snapshot()
    
def run_snapshot(semester=None) -> None: 
    gc = unwrap_response(get_credentials(), "get credentials")
    sh = unwrap_response(get_spreadsheets(gc), "get spreadsheets")
    cs = unwrap_response(calendar_spreadsheet(sh, semester=semester), "get calendar spreadsheet")
    df = unwrap_response(worksheet_to_dataframe(cs), "convert calendar spreadsheet to dataframe")
    rows = unwrap_response(normalize_rows(df), "normalize rows")
    events = unwrap_response(normalize_calendar(rows), "normalize events")
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
    
def analytics_snapshot():
    gc = unwrap_response(get_credentials(), "get credentials")
    sh = unwrap_response(get_spreadsheets(gc), "get spreadsheets")
    cs = unwrap_response(get_all_worksheets(sh), "get calendar spreadsheets from multiple semesters")
    df = unwrap_response(worksheet_to_dataframe(cs), "convert calendar spreadsheet to dataframe")
    all_semesters = unwrap_response(normalize_rows(df), "normalize rows")
    unwrap_response(write_sync_log(all_semesters), "write sync log")
    
def unwrap_response(response, action: str):
    if not isinstance(response, dict):
        raise RuntimeError(f"Could not {action}: expected response dictionary, got {type(response).__name__}")

    if "success" not in response or "error" not in response or "data" not in response:
        raise RuntimeError(f"Could not {action}: malformed response {response}")

    if not response["success"]:
        raise RuntimeError(f"Could not {action}: {response['error']}")
    if response["data"] is None:
        raise RuntimeError(f"Could not {action}: response data is empty")

    return response["data"]

if __name__ == "__main__":
    main()
