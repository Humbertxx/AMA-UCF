from datetime import date, datetime, time, timedelta
import argparse
import re

from ama_ucf.config import SEMESTER_FORMAT

SKIP_TIME = "skip"
YEAR_RE = re.compile(r"\b(?:19|20)\d{2}\b")
SHORT_YEAR_RE = re.compile(r"'?(\d{2})\b")

# gets the current semester based on current year and month
def get_semester() -> str:
    current_date = date.today()
    full_yr = current_date.year        # 2026
    short_yr = current_date.year % 100 # 26
    season = "Fall" if current_date.month > 6 else "Spring"

    fmt = SEMESTER_FORMAT
    return fmt.format(season=season, short_yr=short_yr, full_yr=full_yr)

# get year out of the semester inference 
def semester_year(value) -> int | None:
    text = str(value)
    full_year = YEAR_RE.search(text)
    if full_year:
        return int(full_year.group(0))

    short_year = SHORT_YEAR_RE.search(text)
    if short_year:
        return 2000 + int(short_year.group(1))

    return None

# search if df already have date if not get year using function semester_year
def add_semester_year(text: str, semester) -> str:
    if YEAR_RE.search(text):
        return text

    year = semester_year(semester)
    if year is None:
        return text

    return f"{text} {year}"

# check if text have meridiem if it does removes and format to desire specs and return time 
def parse_time_text(value: str) -> time | None:
    text = str(value).strip().lower()
    for meridiem in ("am", "pm"):
        if not text.endswith(meridiem):
            continue

        clock_text = text.removesuffix(meridiem).strip()
        fmt = "%I:%M %p" if ":" in clock_text else "%I %p"
        return datetime.strptime(f"{clock_text} {meridiem}", fmt).time()

    return None

# adds one whole hour (or 60 minutes)
def add_one_hour(value: time) -> time:
    return (datetime.combine(datetime.today().date(), value) + timedelta(hours=1)).time()

# parse the text to see what time it is the event at from end to finsih adding hour as end
def parse_time_window(value) -> tuple[time | None, time | None] | str:
    text = str(value).strip().lower()

    if text == "all day":
        return None, None

    parts = [part.strip() for part in text.split("-", maxsplit=1)]
    if len(parts) == 2:
        start_text, end_text = parts
        start_time = parse_time_text(start_text)
        end_time = parse_time_text(end_text)
        if start_time is None or end_time is None:
            return SKIP_TIME
    else:
        start_time = parse_time_text(text)
        if start_time is None:
            return SKIP_TIME
        end_time = add_one_hour(start_time)

    return start_time, end_time

# manual parsing of events
def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--semester")
    return parser.parse_args()
