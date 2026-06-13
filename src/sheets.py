from pathlib import Path
from datetime import datetime

import gspread
from gspread import Client, Worksheet, Spreadsheet
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
def get_spreadsheets(gc: Client) -> dict: 
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
def calendar_spreadsheet(sh: list[Spreadsheet]) -> dict: 
    try: 
        semester_response = getSemester()
        if not semester_response["success"]:
            raise ValueError(semester_response["error"])
        if semester_response["data"] is None:
            raise ValueError("semester is required.")

        worksheet = sh[0].worksheet(str(semester_response["data"]))
    
        return {"success": True, "error": None, "data": worksheet}
    
    except Exception as exc:
        return {"success": False, "error": str(exc), "data": None}

# convert a Google worksheet into a dataframe that downstream normalization can use
def worksheet_to_dataframe(ws: Worksheet) -> dict:
    try:
        if not ws:
            raise ValueError("worksheet is required.")

        df = get_as_dataframe(ws, evaluate_formulas=True, skiprows=2)
        df["semester"] = ws.title

        return {"success": True, "error": None, "data": df}

    except Exception as exc:
        return {"success": False, "error": str(exc), "data": None}
    
# get all worksheet to compare and analyze the difference worksheets
def get_all_worksheets(spreadsheets: list[Spreadsheet]) -> pd.DataFrame:
    all_dfs: list[pd.DataFrame] = []
    for sh in spreadsheets:
        for ws in sh.worksheets():
            if ws.title == "Analytics":
                continue
            try:
                df_response = worksheet_to_dataframe(ws)
                if not df_response["success"] or df_response["data"] is None:
                    continue

                all_dfs.append(df_response["data"])
            
            except Exception:
                continue
    return pd.concat(all_dfs, ignore_index=True)
    
# normalize rows, drop empty rows that do not hold dates nor events, convert to dataframe
def normalize_rows(df_combine: pd.DataFrame) -> dict:
    try:
        if df_combine is None:
            raise ValueError("dataframe is required.")

        df = df_combine.copy()
        df = df.dropna(subset=["Date", "Event"])
        df["event_date"] = (pd.to_datetime("1899-12-30") + pd.to_timedelta(df["Date"], unit="D")).dt.date
        
        return {"success": True, "error": None, "data": df}
    
    except Exception as exc:
        return {"success": False, "error": str(exc), "data": None}

# this function get relevant dates that are numeric in FORMULA FORM, then its continues to construct API payload 
def normalize_calendar(df_dict: dict) -> dict:
    try:
        if not df_dict:
            raise ValueError("Rows are required.")
        if df_dict["data"] is None:
            raise ValueError("Rows are required.")
        
        df = df_dict["data"].copy()
        
        df = df[df["event_date"] >= datetime.today().date()]
        df["time"] = df["time"].apply(lambda x: fractionToTime(x).get("data"))
        
        combined_text = df["event_date"].astype(str) + " " + df["time"].astype(str)
        df["calendar_time"] = pd.to_datetime(combined_text, errors='coerce')
        
        events: list[dict] = []
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
