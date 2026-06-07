import logging
from src.sheets import get_worksheet, get_all_rows, normalizingEvents
from src.calendar import createEvent, createCalendarService, calendar_id


logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

def main():
        run_snapshot()
    
def run_snapshot(): 
    ws = get_worksheet()
    rows = get_all_rows(ws)
    events = normalizingEvents(rows)
    service = createCalendarService()
    cal_id = calendar_id(service)
    
    for event in events:
        createEvent(event, service, cal_id)
    logging.info(f"Snapshot complete: {len(events)} events pushed to {cal_id}.")

if __name__ == "__main__":
    main()