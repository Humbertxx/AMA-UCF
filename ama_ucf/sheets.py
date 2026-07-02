from pathlib import Path
from datetime import datetime, timedelta

import gspread
from gspread import Client, Worksheet, Spreadsheet
from gspread_dataframe import get_as_dataframe 
import pandas as pd

from ama_ucf.utils import evaluate_response_status, fractionToTime, getSemester, unwrap_response
from ama_ucf.config import SPREADSHEET_ID, CREDENTIALS_WORKSHEET_FILE_PATH, ARCHIVE_ID

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

        return evaluate_response_status(gc)
    
    except Exception as exc:
        return evaluate_response_status(None, str(exc))

# get spreadsheets from archive and the calendar event master list
def get_spreadsheets(gc: Client) -> dict: 
    try:
        if not gc:
            raise ValueError("need client to continue")

        worksheet_id = SPREADSHEET_ID
        archive_id   = ARCHIVE_ID
    
        if not worksheet_id:
            raise ValueError("Google Sheets spreadsheet ID is not configured.")
        if not archive_id:
            raise ValueError("Google Sheets archive events ID is not configured.")
        
        spreadsheets = [gc.open_by_key(str(worksheet_id)),gc.open_by_key(str(archive_id))]
    
        return evaluate_response_status(spreadsheets)
    
    except Exception as exc:
        return evaluate_response_status(None, str(exc))

# get the worksheet intended to be use for only the calendar 
def calendar_spreadsheet(sh: list[Spreadsheet], semester=None) -> dict: 
    try: 
        semester_response = evaluate_response_status(semester) if semester else getSemester()
        semester_response = unwrap_response(semester_response, "get semester input")
        worksheet = sh[0].worksheet(str(semester_response))
    
        return evaluate_response_status(worksheet)
    
    except Exception as exc:
        return evaluate_response_status(None, str(exc))

# convert a Google worksheet into a dataframe that downstream normalization can use
def worksheet_to_dataframe(ws: Worksheet) -> dict:
    try:
        if not ws:
            raise ValueError("worksheet is required.")

        df = get_as_dataframe(ws, evaluate_formulas=True, skiprows=2)
        df["semester"] = ws.title

        return evaluate_response_status(df)

    except Exception as exc:
        return evaluate_response_status(None, str(exc))
    
# get all worksheet to compare and analyze the difference worksheets
def get_all_worksheets(spreadsheets: list[Spreadsheet]) -> dict:
    try:
        if not spreadsheets:
            raise ValueError("spreadsheets are required.")

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

        if not all_dfs:
            raise ValueError("No worksheet data found.")
                
        return evaluate_response_status(pd.concat(all_dfs, ignore_index=True))
    
    except Exception as exc:
        return evaluate_response_status(None, str(exc))
    
# normalize rows, drop empty rows that do not hold dates nor events, convert to dataframe
def normalize_rows(df_combine: pd.DataFrame) -> dict:
    try:
        if df_combine is None:
            raise ValueError("dataframe is required.")

        df = df_combine.dropna(subset=["Date", "Event"]).copy()
        df["event_date"] = (pd.to_datetime("1899-12-30") + pd.to_timedelta(df["Date"], unit="D")).dt.date
        
        return evaluate_response_status(df)
    
    except Exception as exc:
        return evaluate_response_status(None, str(exc))

# this function get relevant dates that are numeric in FORMULA FORM, then its continues to construct API payload 
def normalize_calendar(df: pd.DataFrame) -> dict:
    try:
        if df is None:
            raise ValueError("Rows are required.")

        df = df[df["event_date"] >= datetime.today().date()].copy()
        
        def parse_time(value): # TO DO: Returns Error when None should be succesful, need fix
            return unwrap_response(fractionToTime(value),"get standard date format")

        df["time"] = df["time"].apply(parse_time)
        combined_text = df["event_date"].astype(str) + " " + df["time"].astype(str)
        df["calendar_time"] = pd.to_datetime(combined_text, errors='coerce')
        
        rows = df.to_dict("records")
        events = [] 
        
        for row in rows:
            if row["time"] is not None:
                start_dt = pd.Timestamp(row["calendar_time"])
                end_dt = start_dt + pd.Timedelta(hours=1)
                start_field = {"dateTime": start_dt.isoformat()}
                end_field = {"dateTime": end_dt.isoformat()}
            else:
                start_date = pd.Timestamp(row["event_date"]).date()
                end_date = start_date + timedelta(days=1)
                start_field = {"date": start_date.isoformat()}
                end_field = {"date": end_date.isoformat()}

            events.append({
                "summary": row.get("Event", ""),
                "description": row.get("Description", ""),
                "location": row.get("Location", ""),
                "organizer": row.get("Type", ""),
                "start": start_field,
                "end": end_field,
            })

        return evaluate_response_status(events)
    
    except Exception as exc:
        return evaluate_response_status(None, str(exc))