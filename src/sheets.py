import os
from pathlib import Path
from datetime import datetime, timedelta
from config import SPREADSHEET_ID, CREDENTIALS_WORKSHEET_FILE_PATH
import gspread
from gspread import Worksheet
from typing import Dict, List
from utils import serialToDate, getSemester, fractionToTime

# validation and retrieval of Google Sheets
def get_worksheet() -> Worksheet:
    try:
        api_key_path = CREDENTIALS_WORKSHEET_FILE_PATH
        worksheet_id = SPREADSHEET_ID
        
        if not os.path.exists(api_key_path):
            raise ValueError("Google Sheets credential path is not configured.")
        if not worksheet_id:
            raise ValueError("Google Sheets spreadsheet ID is not configured.")
        
        credential_path = Path(api_key_path)

        if not credential_path.exists():
            raise FileNotFoundError(f"Google Sheets credential file not found: {credential_path}")

        gc = gspread.service_account(filename=str(credential_path))
        
        spreadsheet = gc.open_by_key(str(worksheet_id))
        worksheet = spreadsheet.worksheet(str(getSemester()))

        return worksheet
    
    except Exception as exc:
        return {"error": exc, "data": None, "success": "false"}

def get_all_rows(ws: Worksheet) -> List[Dict[str, int | float | str]]:
    try:
        if not ws:
            return ValueError("Worksheet is required.")

        rows = ws.get_all_records(value_render_option="FORMULA")[2:]
        return rows
    
    except Exception as exc:
        return {"error": exc, "data": None, "success": "false"}

# this function get relevant dates that are numeric in FORMULA FORM, then its continues to get standard way 
# of getting dates in Google Calendar API 
def normalizingEvents(rows) -> list:
    try:
        if rows is None:
            return ValueError("Rows are required.")

        events = []
        for row in rows:
            serial = row.get("Date")
            if not serial:
                continue

            try:
                event_date_response = serialToDate(serial)
                if not event_date_response["success"]:
                    return event_date_response # fix here

                event_date = event_date_response["data"]
                today = datetime.today().date()
                if event_date < today:
                    continue

                time_frac = row.get("Time")
                time_response = fractionToTime(time_frac)
                time_normal = time_response.get("data") if time_response["success"] else None

                if time_normal:
                    start_dt = datetime.combine(event_date, time_normal)
                    end_dt = start_dt + timedelta(hours=1)
                    start_field = {"dateTime": start_dt.isoformat()}
                    end_field = {"dateTime": end_dt.isoformat()}
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
            except Exception as exc:
                return {"error": exc, "data": None, "success": "false"}

        return events
    
    except Exception as exc:
        return {"error": exc, "data": None, "success": "false"}