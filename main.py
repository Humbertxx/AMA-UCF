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
from ama_ucf.utils import parse_args
from ama_ucf.audit import write_sync_log
from ama_ucf.analytics import analytics_tab
    

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

def main() -> None:
    args = parse_args()
    run_snapshot(semester=args.semester)
    analytics_snapshot()
    
def run_snapshot(semester=None) -> None: 
    gc = get_credentials()
    sh = get_spreadsheets(gc)
    cs = calendar_spreadsheet(sh, semester)
    df = worksheet_to_dataframe(cs)
    rows = normalize_rows(df)
    events = normalize_calendar(rows)
    service = create_calendar_service()
    cal_id = calendar_id(service)
    
    created_count = 0
    skipped_count = 0 # in order to see activity count 
    
    for event in events:
        result = create_event(event, service, cal_id, semester)
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
    
def analytics_snapshot() -> None:
    gc = get_credentials()
    sh = get_spreadsheets(gc)
    df = get_all_worksheets(sh)
    all_semesters = normalize_rows(df)

    write_sync_log(all_semesters)
    analytics_tab(sh, all_semesters)
    
    logging.info("Analytics tab created successfully.")
    
if __name__ == "__main__":
    main()
