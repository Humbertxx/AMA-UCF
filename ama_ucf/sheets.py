from pathlib import Path
from datetime import datetime, timedelta

import gspread
from gspread import Client, Worksheet, Spreadsheet
from gspread_dataframe import get_as_dataframe 
import pandas as pd

from ama_ucf.utils import SKIP_TIME, add_semester_year, get_semester, parse_time_window
from ama_ucf.config import SPREADSHEET_ID, CREDENTIALS_WORKSHEET_FILE_PATH, ARCHIVE_ID

# validation of credentials
def get_credentials() -> Client:
    api_key_path = CREDENTIALS_WORKSHEET_FILE_PATH

    if not api_key_path:
        raise ValueError("Google Sheets credential path is not configured.")

    credential_path = Path(api_key_path)

    if not credential_path.exists():
        raise FileNotFoundError(f"Google Sheets credential file not found: {credential_path}")

    return gspread.service_account(filename=str(credential_path))

# get spreadsheets from archive and the calendar event master list
def get_spreadsheets(gc: Client) -> list[Spreadsheet]:
    if not gc:
        raise ValueError("need client to continue")

    worksheet_id = SPREADSHEET_ID
    archive_id   = ARCHIVE_ID

    if not worksheet_id:
        raise ValueError("Google Sheets spreadsheet ID is not configured.")
    if not archive_id:
        raise ValueError("Google Sheets archive events ID is not configured.")

    return [gc.open_by_key(str(worksheet_id)), gc.open_by_key(str(archive_id))]

# get the worksheet intended to be use for only the calendar 
def calendar_spreadsheet(sh: list[Spreadsheet], semester=None) -> Worksheet:
    semester_name = semester or get_semester()
    return sh[0].worksheet(str(semester_name))

# convert a Google worksheet into a dataframe that downstream normalization can use
def worksheet_to_dataframe(ws: Worksheet) -> pd.DataFrame:
    if not ws:
        raise ValueError("worksheet is required.")

    df = get_as_dataframe(ws, evaluate_formulas=True)
    df["semester"] = ws.title

    return df

# get all worksheet to compare and analyze the difference worksheets
def get_all_worksheets(spreadsheets: list[Spreadsheet]) -> pd.DataFrame:
    if not spreadsheets:
        raise ValueError("spreadsheets are required.")

    all_dfs: list[pd.DataFrame] = []
    for sh in spreadsheets:
        for ws in sh.worksheets():
            if ws.title == "Analytics":
                continue
            all_dfs.append(worksheet_to_dataframe(ws))

    if not all_dfs:
        raise ValueError("No worksheet data found.")

    return pd.concat(all_dfs, ignore_index=True)

# normalize rows, drop empty rows that do not hold dates nor events, convert to dataframe
def normalize_rows(df_combine: pd.DataFrame) -> pd.DataFrame:
    if df_combine is None:
        raise ValueError("dataframe is required.")

    df = df_combine.dropna(subset=["Date", "Event"]).copy()

    numeric_dates = pd.to_numeric(df["Date"], errors="coerce")
    serial_dates = pd.to_datetime("1899-12-30") + pd.to_timedelta(numeric_dates, unit="D")

    def parse_text_date(value, semester):
        if pd.isna(value):
            return pd.NaT

        text = str(value).strip()
        if not text:
            return pd.NaT

        return pd.to_datetime(add_semester_year(text, semester), errors="coerce")

    text_date_values = df["Date"].where(numeric_dates.isna())
    text_dates = pd.Series(
        [
            parse_text_date(value, df.loc[index, "semester"]) for index, value in text_date_values.items()
        ],
        index=df.index,
    )

    df["event_date"] = serial_dates.fillna(text_dates).dt.date

    return df.dropna(subset=["event_date"])

# check and valides type none in spreadsheet
def clean_text(value) -> str:
    if pd.isna(value):
        return ""
    return str(value)

# this function get relevant dates that are numeric in FORMULA FORM, then its continues to construct API payload 
def normalize_calendar(df: pd.DataFrame) -> list[dict]:
    if df is None:
        raise ValueError("Rows are required.")

    df = df[df["event_date"] >= datetime.today().date()].copy()

    df["time_window"] = df["Time"].apply(parse_time_window)

    rows = df.to_dict("records")
    events = []

    for row in rows:
        if row["time_window"] == SKIP_TIME:
            continue

        start_time, end_time = row["time_window"]
        event_date = pd.Timestamp(row["event_date"]).date()

        if start_time is not None:
            start_dt = datetime.combine(event_date, start_time)
            end_dt = datetime.combine(event_date, end_time)
            if end_dt <= start_dt:
                end_dt = end_dt + timedelta(days=1)

            start_field = {"dateTime": start_dt.isoformat()}
            end_field = {"dateTime": end_dt.isoformat()}
        else:
            end_date = event_date + timedelta(days=1)
            start_field = {"date": event_date.isoformat()}
            end_field = {"date": end_date.isoformat()}

        events.append({
            "summary": clean_text(row.get("Event", "")),
            "description": clean_text(row.get("Description", "")),
            "location": clean_text(row.get("Location", "")),
            "organizer": clean_text(row.get("Type", "")),
            "start": start_field,
            "end": end_field,
        })

    return events
