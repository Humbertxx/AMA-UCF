from pathlib import Path
import pandas as pd

from ama_ucf.utils import evaluate_response_status

def write_sync_log(df: pd.DataFrame, path: str = "sync_log.csv") -> dict:
    try:
        if df is None:
            raise ValueError("dataframe is required.")

        output_path = Path(path)
        df.to_csv(output_path, index=False)

        return evaluate_response_status(output_path)
    
    except Exception as exc:
        return evaluate_response_status(None, str(exc))
