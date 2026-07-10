import numpy as np
import pandas as pd

from gspread.exceptions import WorksheetNotFound
from gspread_dataframe import set_with_dataframe

def analytics_tab(
    sh,
    all_worksheets: pd.DataFrame | None = None,
    include_cross_segment_evaluation: bool = True,
    include_event_density: bool = True,
    include_event_type_mix: bool = True,
    ) -> str:

    if all_worksheets is None:
        raise ValueError("all_worksheets is required.")

    results = {}

    if include_event_density:
        results["event_density"] = event_density(all_worksheets)
    if include_cross_segment_evaluation:
        results["cross_segment_evaluation"] = cross_segment_evaluation(all_worksheets)
    if include_event_type_mix:
        results["event_type_mix"] = event_type_mix(all_worksheets)

    return write_to_sheet(sh, results)

# cross segment evaluation
def cross_segment_evaluation(df : pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        raise ValueError("Dataframe is empty")

    df = df.copy()
    df["event_date"] = pd.to_datetime(df["event_date"], errors="coerce")
    df = df.dropna(subset=["semester", "Type", "event_date"])

    if df.empty:
        raise ValueError("Dataframe has no valid segment rows.")

    segment_summary = (
        df.groupby(["semester", "Type"])
        .agg(
            event_count=("Event", "count"),
            first_event_date=("event_date", "min"),
            last_event_date=("event_date", "max"),
            )
        .reset_index()
    )
    sorted_df = df.sort_values(["semester", "Type", "event_date"])
    sorted_df["days_since_previous_event"] = (sorted_df.groupby(["semester", "Type"])["event_date"].diff().dt.days)
    gap_summary = (sorted_df.groupby(["semester", "Type"])["days_since_previous_event"].max().reset_index(name="largest_gap_days"))

    return segment_summary.merge(gap_summary, on=["semester", "Type"], how="left")

# event density
def event_density(df : pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        raise ValueError("Dataframe is empty")

    df = df.copy()
    df["event_date"] = pd.to_datetime(df["event_date"], errors="coerce")
    df = df.dropna(subset=["event_date"])

    if df.empty:
        raise ValueError("Dataframe has no valid event dates.")

    return df.set_index("event_date").resample("W").size().reset_index(name="event_count")

# event type mix
def event_type_mix(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        raise ValueError("Dataframe is empty")

    event_types, counts = np.unique(df["Type"].dropna().to_numpy(), return_counts=True)

    if counts.size == 0:
        raise ValueError("Dataframe has no valid event types.")

    order = np.argsort(counts)[::-1]
    event_types = event_types[order]
    counts = counts[order]

    shares = counts / counts.sum()
    cumulative_shares = np.cumsum(shares)

    return pd.DataFrame(
        {
        "Type": event_types,
        "event_count": counts,
        "share_of_events": shares,
        "cumulative_share": cumulative_shares,
        }
    )

def write_to_sheet(sh,results) -> str:
    if results is None:
        return "nothing to write home about!"

    spreadsheet = sh[0]

    try:
        ws = spreadsheet.worksheet("Analytics")
    except WorksheetNotFound:
        ws = spreadsheet.add_worksheet(title="Analytics", rows=100, cols=30)

    cell_title = ws.find("Insightful Analytics")
    if cell_title is None:
        ws.update_cell(10, 12, "Insightful Analytics")
        cell_title = ws.find("Insightful Analytics")

    if cell_title is None:
        raise ValueError("Could not find or create the Analytics title cell.")

    write_to = [(int(cell_title.row) +1), (int(cell_title.col) +1)]

    if "event_density" in results:
        event_density_df = results["event_density"]

        set_with_dataframe(ws, event_density_df, row=write_to[0], col=write_to[1])

    if "cross_segment_evaluation" in results:
        cross_segment_df = results["cross_segment_evaluation"]

        set_with_dataframe(ws, cross_segment_df, row=write_to[0], col=write_to[1] + 4)

    if "event_type_mix" in results:
        event_type_mix_df = results["event_type_mix"]

        set_with_dataframe(ws, event_type_mix_df, row=write_to[0], col=write_to[1] + 10)

    return "analytics written"
