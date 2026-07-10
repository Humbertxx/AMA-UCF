from pathlib import Path
import pandas as pd

def write_sync_log(df: pd.DataFrame, path: str = "sync_log.csv") -> Path:
    if df is None:
        raise ValueError("dataframe is required.")

    output_path = Path(path)
    df.to_csv(output_path, index=False)

    return output_path
