import numpy as np

from src.sheets import get_worksheet

ws = get_worksheet



data = ws.get_all_values()
arr = np.array(data[1:], dtype=object)  # skip header row

# count events by type (column index 5 = "Type")
types, counts = np.unique(arr[:, 5], return_counts=True)

