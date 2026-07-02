import numpy as np
import pandas as pd
from gspread_dataframe import set_with_dataframe

from ama_ucf.utils import evaluate_response_status, unwrap_response

def analytics_tab(
    gc,
    sh,
    all_worksheets: pd.DataFrame | None = None,
    include_cross_segment_evaluation: bool = True,
    include_event_density: bool = True,
    include_event_type_mix: bool = True,
    )-> dict:

    try:
        if all_worksheets is None:
            raise ValueError("all_worksheets is required.")

        results = {}

        if include_event_density:
            results["event_density"] = unwrap_response(
                event_density(all_worksheets),
                "calculate event density",
            )
        if include_cross_segment_evaluation:
            results["cross_segment_evaluation"] = unwrap_response(
                cross_segment_evaluation(all_worksheets),
                "calculate cross segment evaluation",
            )
        if include_event_type_mix:
            results["event_type_mix"] = unwrap_response(
                event_type_mix(all_worksheets),
                "calculate event type mix",
            )
            
        success = unwrap_response(write_to_sheet(gc, sh, results), "write analytics to sheet")
        
        return evaluate_response_status(success)

    except Exception as exc:
        return evaluate_response_status(None, str(exc))

# cross segment evaluation
def cross_segment_evaluation(df : pd.DataFrame):
    try:
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

        result = segment_summary.merge(gap_summary, on=["semester", "Type"], how="left")
        return evaluate_response_status(result)
    
    except Exception as exc:
        return evaluate_response_status(None, str(exc))

# event density
def event_density(df : pd.DataFrame):
    try:
        if df.empty:
            raise ValueError("Dataframe is empty")

        df = df.copy()
        df["event_date"] = pd.to_datetime(df["event_date"], errors="coerce")
        df = df.dropna(subset=["event_date"])

        if df.empty:
            raise ValueError("Dataframe has no valid event dates.")

        weekly_count = df.set_index("event_date").resample("W").size().reset_index(name="event_count")
        
        return evaluate_response_status(weekly_count)
    
    except Exception as exc:
        return evaluate_response_status(None, str(exc))

# event type mix
def event_type_mix(df: pd.DataFrame):
    try:
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

        event_mix_df = pd.DataFrame(
            {
            "Type": event_types,
            "event_count": counts,
            "share_of_events": shares,
            "cumulative_share": cumulative_shares,
            }
        )
        return evaluate_response_status(event_mix_df)
    
    except Exception as exc:
        return evaluate_response_status(None, str(exc))
         
def write_to_sheet(client, sh,results):
    try:
        if results is None:
            return evaluate_response_status("nothing to write home about!")
        
        ws = sh[0].worksheet("Analytics")
        
        if ws is None:
            ws = client.create("Analytics")

        try:
            cell_title = ws.find("Insightful Analytics")
        
        except Exception:
            ws.update_cell(10, 12, "Insightful Analytics")
            cell_title = ws.find("Insightful Analytics")
        
        write_to = [(int(cell_title.row) +1), (int(cell_title.column) +1)]

        if "event_density" in results:
            event_density_df = results["event_density"]

            set_with_dataframe(ws, event_density_df, row=write_to[0], col=write_to[1])

        if "cross_segment_evaluation" in results:
            cross_segment_df = results["cross_segment_evaluation"]
          
            set_with_dataframe(ws, cross_segment_df, row=write_to[0], col=write_to[1] + 4)

        if "event_type_mix" in results:
            event_type_mix_df = results["event_type_mix"]

            set_with_dataframe(ws, event_type_mix_df, row=write_to[0], col=write_to[1] + 10)

        return evaluate_response_status("analytics written")
    
    except Exception as exc:
        return evaluate_response_status(None, str(exc))
