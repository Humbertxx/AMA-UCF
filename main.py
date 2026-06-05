import time
import logging
from src.sheets import get_worksheet, get_all_rows, normalize_events, check_new_rows
from src.calendar import get_calendar_service, create_event, resolve_calendar_id
import config
import sys

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")


def main():
    mode = sys.argv[-1] if len(sys.argv) > 1 else "snapshot"
    if mode == "watch":
        run_watch()
    else:
        run_snapshot()
    
def run_snapshot(): 
    ws = get_worksheet()
    rows = get_all_rows(ws)
    events = normalize_events(rows)
    service = get_calendar_service()
    cal_id = resolve_calendar_id(service)
    
    for event in events:
        create_event(event, service, cal_id)
    logging.info(f"Snapshot complete: {len(events)} events pushed.")

def run_watch():
    ws = get_worksheet()
    rows = get_all_rows(ws)
    last_count = len(rows)
    logging.info(f"Watch mode started. Initial row count: {last_count}")
    
    while True:
        try:
            ws = get_worksheet()   # re-fetch to get latest data
            rows = get_all_rows(ws)
            new_rows, last_count = check_new_rows(rows, last_count)
            if new_rows:
                events = normalize_events(new_rows)
                service = get_calendar_service()
                cal_id = resolve_calendar_id(service)
                for event in events:
                    create_event(event, service, cal_id)
                logging.info(f"{len(events)} new events synced.")
        
        except Exception as e:
            logging.error(f"Error in watch loop: {e}")
        
        
        time.sleep(config.POLL_INTERVAL) 

if __name__ == "__main__":
    main()