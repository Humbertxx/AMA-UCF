from datetime import date, time
import argparse

from ama_ucf.config import SEMESTER_FORMAT

# gets the current semester based on current year and month
def getSemester() -> dict:
    try:
        current_date = date.today()
        full_yr = current_date.year        # 2026
        short_yr = current_date.year % 100 # 26
        season = "Fall" if current_date.month > 7 else "Spring"
    
        fmt = SEMESTER_FORMAT
        semester = fmt.format(season=season, short_yr=short_yr, full_yr=full_yr)
        return evaluate_response_status(semester)
    
    except Exception as exc:
        return evaluate_response_status(None, str(exc))

# gets the fraction time give in FORMULA in Google Sheet and standardize it to a simple time
def fractionToTime(fraction: float) -> dict:
    try:
        if fraction in (None, ""):
            return evaluate_response_status(None) # all day calendar
        
        fraction = float(fraction)
        if not (0 <= fraction < 1):
            raise ValueError(f"Invalid time fraction: {fraction}")

        total_seconds = fraction * 24 * 60 * 60
        hours = int(total_seconds // 3600)
        minutes = int((total_seconds % 3600) // 60)
            
        return evaluate_response_status(time(hours, minutes))
    
    except Exception as exc:
        return evaluate_response_status(None, str(exc))

# manual parsing of events
def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--semester")
    return parser.parse_args()

# standard way to return function in dictionaries
def evaluate_response_status(data, error: str | None = None):
    if error:
        return {"success": False, "error": error, "data": None}

    return {"success": True, "error": None, "data": data}

# unwrap responses, return only data that contains the dict if success
def unwrap_response(response: dict, action: str):
    if not isinstance(response, dict):
        raise RuntimeError(f"Could not {action}: expected response dictionary, got {type(response).__name__}")

    if "success" not in response or "error" not in response or "data" not in response:
        raise RuntimeError(f"Could not {action}: malformed response {response}")

    if not response["success"]:
        raise RuntimeError(f"Could not {action}: {response['error']}")
    if response["data"] is None:
        raise RuntimeError(f"Could not {action}: response data is empty")

    return response["data"]
