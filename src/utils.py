from datetime import timedelta, date, time
from config import SEMESTER_FORMAT
# gets the current semester based on current year and month
def getSemester() -> str:
    try:
        current_date = date.today()
        full_yr = current_date.year        # 2026
        short_yr = current_date.year % 100 # 26
        season = "Fall" if current_date.month > 7 else "Spring"
    
        fmt = (SEMESTER_FORMAT, "{season} '{short_yr}")
        return fmt.format(season=season, short_yr=short_yr, full_yr=full_yr)
    
    except Exception as exc:
        return {"error": exc, "data": None, "success": "false"}

# gets the serial number as given in FORMULA in Google Sheet and standardize it to simple date
def serialToDate(serial: float) -> date:
    try:
        if serial in (None, ""):
            raise ValueError("Date serial is required.")

        return date(1899, 12, 30) + timedelta(days=float(serial))
    
    except Exception as exc:
        return {"error": exc, "data": None, "success": "false"}

# gets the fraction time give in FORMULA in Google Sheet and standardize it to a simple time
def fractionToTime(fraction: float) -> time:
    if fraction in (None, ""):
        return None # all day calendar
    
    if not (0 <= fraction < 1):
        raise ValueError(f"Invalid time fraction: {fraction}")

    total_seconds = float(fraction) * 24 * 60 * 60
    hours = int(total_seconds // 3600)
    minutes = int((total_seconds % 3600) // 60)
        
    return time(hours, minutes)
    