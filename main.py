import logging

from ama_ucf.sheets import (
    calendar_spreadsheet,
    get_credentials,
    get_spreadsheets,
    normalize_calendar,
    normalize_rows,
    worksheet_to_dataframe,
    get_all_worksheets,
    )
from ama_ucf.calendar import create_event, create_calendar_service, calendar_id
from ama_ucf.utils import parse_args, unwrap_response
from ama_ucf.audit import write_sync_log
from ama_ucf.analytics import analytics_tab
    

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

def main() -> None:
    args = parse_args()
    run_snapshot(semester=args.semester)
    analytics_snapshot()
    
def run_snapshot(semester=None) -> None: 
    gc = unwrap_response(get_credentials(), "get credentials")
    sh = unwrap_response(get_spreadsheets(gc), "get spreadsheets")
    cs = unwrap_response(calendar_spreadsheet(sh, semester), "get calendar spreadsheet")
    df = unwrap_response(worksheet_to_dataframe(cs), "convert calendar spreadsheet to dataframe")
    rows = unwrap_response(normalize_rows(df), "normalize rows")
    events = unwrap_response(normalize_calendar(rows), "normalize events")
    service = unwrap_response(create_calendar_service(), "create calendar service")
    cal_id = unwrap_response(calendar_id(service), "resolve calendar ID")
    
    created_count = 0
    skipped_count = 0 # in order to see activity count 
    
    for event in events:
        result = unwrap_response(create_event(event, service, cal_id, semester), "create calendar event")
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
    df = unwrap_response(get_all_worksheets(sh), "get calendar spreadsheets from multiple semesters")
    all_semesters = unwrap_response(normalize_rows(df), "normalize rows")

    unwrap_response(write_sync_log(all_semesters), "write sync log")
    unwrap_response(analytics_tab(sh, all_semesters), "write to analytics tab")
    
    logging.info("Analytics tab created successfully.")
    
if __name__ == "__main__":
    main()
