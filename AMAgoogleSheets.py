
import gspread 
from datetime import datetime, timedelta, date, time
from time import sleep
import config


# validation and retrieval of Google Sheets
def retrievingKeyGspread():
    api_key_path = config.get_api_key_path()
    worksheet_id = config.get_worksheet_id()
    if not api_key_path.exists():
        raise FileNotFoundError(api_key_path)
    gc = gspread.service_account(filename=str(worksheet))
    sh = gc.open_by_key(str(worksheet_id))
    worksheet = sh.worksheet(str(getSemester()))
    return worksheet

def getAllWorksheet(ws):
    rows = ws.get_all_records(value_render_option='FORMULA')[2:]
    return rows

# this function get relevant dates that are numeric in FORMULA FORM, then its continues to get standard way 
# of getting dates in Google Calendar API 
# returns the list of events that matched criteria 
def normalizingEvents(rows):
    events = []
    for row in rows:
        serial = row.get("Date")
        if not serial:
            continue
        try:
            event_date = serialToDate(serial)
            today = datetime.today().date()
            if event_date < today:
                continue
            
            time_frac = row.get("Time")
            time_normal = fractionToTime(time_frac)
            if time_normal:
                try:
                    start_dt = datetime.combine(event_date, time_normal)
                    end_dt = start_dt + timedelta(hours=1)
                    start_field = {"dateTime": start_dt.isoformat()}
                    end_field = {"dateTime": end_dt.isoformat()}
                except ValueError:
                    start_field = {"date": event_date.isoformat()}
                    end_field = {"date": event_date.isoformat()}
            else:
                start_field = {"date": event_date.isoformat()}
                end_field = {"date": event_date.isoformat()}
                
            events.append({
                "summary": row.get("Event", ""),
                "description": row.get("Description", ""),
                "location": row.get("Location", ""),
                "organizer": row.get("Type", ""),
                "start": start_field,
                "end": end_field,
             })
        except Exception:
            continue
        
    return events

# gets the current semester based on current month
# return a string object
def getSemester():
    current_date = date.today()
    yr = current_date.year
    mth = current_date.month
    if mth > 7:
        mth = "Fall"
    else:
        mth = "Spring"   
    if yr:
        yr = yr % 100
    return f"{mth} '{yr}"

# gets the serial number as given in FORMULA in Google Sheet and standardize it to a simple date
# returns date object
def serialToDate(serial):
    return date(1899, 12, 30) + timedelta(days=float(serial))

# gets the fraction time give in FORMULA in Google Sheet and standardize it to a simple time
# returns time object 
def fractionToTime(fraction):
    total_seconds = fraction * 24 * 60 * 60 
    hours = int(total_seconds // 3600)
    minutes = int((total_seconds % 3600) // 60)
    return time(hours, minutes)

# check if new rows in google sheet are detected, in formula form
def checkForNewRows(initial, last_row_count):
    try:
        all_records =  initial #worksheet.get_all_records(value_render_option='FORMULA')[2:]
        current_row_count = len(all_records)
        
        if current_row_count > last_row_count:
                                                                                                        #print(f"New row(s) detected at {datetime.now()}")
            new_data = all_records[last_row_count:]
            return new_data, current_row_count
        
        elif current_row_count < last_row_count:
            # rows were deleted, reset
                                                                                                        #print(f"Row count decreased. Resetting at {datetime.now()}")
            return [], current_row_count
        # no new rows
        return [], last_row_count
    except Exception as e:
        print(f"Error checking rows: {e}")
        return [], last_row_count
    
# using the function in checkForNewRows validates if there are new rows, if true then, was rows to normalizingEvents
# returns list of events that where not previously found, does this once a week 
def autoUpdate(initial_records):
    #initial_records = worksheet.get_all_records(value_render_option='FORMULA')[2:]
    last_row_count = len(initial_records)
                                                                                                        #print(f"Starting auto-update. Initial row count: {last_row_count}")
    while True:
        try:
            new_records, last_row_count = checkForNewRows(initial_records, last_row_count)
            if new_records:
                                                                                                        #print(f"Processing {len(new_records)} new row(s)...")
                events = normalizingEvents(new_records)
                if events:
                                                                                                        #print(f"Found {len(events)} valid event(s)")
                    return events  # Return the new events
                
        except Exception as e:
            print(f"Error in main loop: {e}")
        #sleep(5) # 604800 seconds in a week
