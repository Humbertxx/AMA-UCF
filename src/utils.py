from datetime import date, time

from src.config import SEMESTER_FORMAT


# gets the current semester based on current year and month
def getSemester() -> dict:
    try:
        current_date = date.today()
        full_yr = current_date.year        # 2026
        short_yr = current_date.year % 100 # 26
        season = "Fall" if current_date.month > 7 else "Spring"
    
        fmt = SEMESTER_FORMAT
        semester = fmt.format(season=season, short_yr=short_yr, full_yr=full_yr)
        return {"success": True, "error": None, "data": semester}
    
    except Exception as exc:
        return {"success": False, "error": str(exc), "data": None}

# gets the fraction time give in FORMULA in Google Sheet and standardize it to a simple time
def fractionToTime(fraction: float) -> dict:
    try:
        if fraction in (None, ""):
            return {"success": True, "error": None, "data": None} # all day calendar
        
        fraction = float(fraction)
        if not (0 <= fraction < 1):
            raise ValueError(f"Invalid time fraction: {fraction}")

        total_seconds = fraction * 24 * 60 * 60
        hours = int(total_seconds // 3600)
        minutes = int((total_seconds % 3600) // 60)
            
        return {"success": True, "error": None, "data": time(hours, minutes)}
    
    except Exception as exc:
        return {"success": False, "error": str(exc), "data": None}
    
