from datetime import date, time
import argparse
import pandas as pd

from ama_ucf.config import SEMESTER_FORMAT

# gets the current semester based on current year and month
def get_semester() -> str:
    current_date = date.today()
    full_yr = current_date.year        # 2026
    short_yr = current_date.year % 100 # 26
    season = "Fall" if current_date.month > 6 else "Spring"

    fmt = SEMESTER_FORMAT
    return fmt.format(season=season, short_yr=short_yr, full_yr=full_yr)

# converts the fraction time give in FORMULA in Google Sheet and standardize it to a simple time
def fractionToTime(fraction: float) -> time | None:
    if fraction in (None, "") or pd.isna(fraction):
        return None # all day calendar

    fraction = float(fraction)
    if not (0 <= fraction < 1):
        raise ValueError(f"Invalid time fraction: {fraction}")

    total_seconds = fraction * 24 * 60 * 60
    hours = int(total_seconds // 3600)
    minutes = int((total_seconds % 3600) // 60)

    return time(hours, minutes)

# manual parsing of events
def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--semester")
    return parser.parse_args()
