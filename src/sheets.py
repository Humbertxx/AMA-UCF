from pathlib import Path
from datetime import datetime

import gspread
from gspread import Worksheet, Spreadsheet, Client
from gspread_dataframe import get_as_dataframe 
import pandas as pd

from src.utils import getSemester, fractionToTime
from src.config import SPREADSHEET_ID, CREDENTIALS_WORKSHEET_FILE_PATH, ARCHIVE_ID

# validation of credentials
def get_credentials() -> dict:
    try:
        api_key_path = CREDENTIALS_WORKSHEET_FILE_PATH
        
        if not api_key_path:
            raise ValueError("Google Sheets credential path is not configured.")
        
        credential_path = Path(api_key_path)

        if not credential_path.exists():
            raise FileNotFoundError(f"Google Sheets credential file not found: {credential_path}")

        gc = gspread.service_account(filename=str(credential_path))

        return {"success": True, "error": None, "data": gc}
    
    except Exception as exc:
        return {"success": False, "error": str(exc), "data": None}

# get spreadsheets from archive and the calendar event master list
def get_spreadsheets(gc): 
    if not gc:
        raise ValueError("need client to continue")
    try:
        worksheet_id = SPREADSHEET_ID
        archive_id   = ARCHIVE_ID
    
        if not worksheet_id:
            raise ValueError("Google Sheets spreadsheet ID is not configured.")
        if not archive_id:
            raise ValueError("Google Sheets archive events ID is not configured.")
        
        spreadsheets = [gc.open_by_key(str(worksheet_id)),gc.open_by_key(str(archive_id))]
    
        return {"success": True, "error": None, "data": spreadsheets}
    
    except Exception as exc:
        return {"success": False, "error": str(exc), "data": None}

# get the worksheet intended to be use for only the calendar 
def calendar_spreadsheet(sh: Spreadsheet) -> dict: 
    try: 
        worksheet = sh[0].worksheet(str(getSemester()))
    
        return {"success": True, "error": None, "data": worksheet}
    
    except Exception as exc:
        return {"success": False, "error": str(exc), "data": None}
    
# get all worksheet to compare and analyze the difference worksheets
def get_all_worksheets(spreadsheets: dict[list[Spreadsheet]]):
    all_dfs = []
    for sh in spreadsheets:
        for ws in sh.worksheets():
            if ws.title == "Analytics":
                continue
            try:
                df = get_as_dataframe(ws, evaluate_formulas=True, skiprows=2)
                df["semester"] = ws.title
                all_dfs.append(df)
            
            except Exception:
                continue
    return pd.concat(all_dfs, ignore_index=True)
    
# normalize rows, drop empty rows that do not hold dates nor events, convert to dataframe
def normalize_rows(df_combine) -> dict:
    try:
        if not df_combine:
            raise ValueError("dataframe is required.")

        df = df.dropna(subset=["Date", "Event"])  
        df["event_date"] = pd.to_datetime("1899-12-30") + pd.to_timedelta(df["Date"], unit="D")
        
        return {"success": True, "error": None, "data": df}
    
    except Exception as exc:
        return {"success": False, "error": str(exc), "data": None}

# this function get relevant dates that are numeric in FORMULA FORM, then its continues to construct API payload 
def normalize_calendar(df_dict: dict) -> dict:
    try:
        if not df_dict:
            raise ValueError("Rows are required.")
        
        df = df_dict["data"].copy()
        
        df = df[df['event_date'] >= datetime.today().date()]
        df["time"] = df["time"].apply(lambda x: fractionToTime(x).get("data"), axis=1)
        df["calendar_time"] = df.apply(lambda r: datetime.combine(r["event_date"], r["time"]),axis=1)
        
        events = []
        rows = df.to_dict("records")
        
        for row in rows:
            if row["time"] is not None:
                start_dt = row["calendar_time"]
                end_dt = start_dt + pd.Timedelta(hours=1)
                start_field = {"dateTime": start_dt.isoformat()}
                end_field = {"dateTime": end_dt.isoformat()}
            else:
                start_field = {"date": row["event_date"].isoformat()}
                end_field = {"date": row["event_date"].isoformat()}

            events.append({
                "summary": row.get("Event", ""),
                "description": row.get("Description", ""),
                "location": row.get("Location", ""),
                "organizer": row.get("Type", ""),
                "start": start_field,
                "end": end_field,
            })

        return {"success": True, "error": None, "data": events}
    
    except Exception as exc:
        return {"success": False, "error": str(exc), "data": None}
