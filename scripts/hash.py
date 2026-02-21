# pyright: reportUnknownVariableType=false, reportUnknownArgumentType=false, reportUnknownMemberType=false
"""Hash function for comp rates."""

from itertools import count
from time import time

from comp_rates_config import RECENT_PHASE
from pandas import read_csv

start_time = time()

# 1. Use a list to manage your DataFrames and paths for cleaner processing
files = {
    "char": f"../data/raw_csvs_real/{RECENT_PHASE}_char.csv",
    "spiral": f"../data/raw_csvs_real/{RECENT_PHASE}.csv",
    "pf": f"../data/raw_csvs_real/{RECENT_PHASE}_pf.csv",
    "as": f"../data/raw_csvs_real/{RECENT_PHASE}_as.csv",
    "aa": f"../data/raw_csvs_real/{RECENT_PHASE}_aa.csv",
    "build": f"../data/raw_csvs_real/{RECENT_PHASE}_build.csv",
}

# 2. Load data without convert_dtypes (unless absolutely necessary)
# Force UID to string or int immediately to save memory/time
dfs = {name: read_csv(path, encoding="cp1252") for name, path in files.items()}

# 3. Build the hash using set unions
all_uids: set[str] = set()
for df in dfs.values():
    all_uids.update(df["uid"].unique())

# Create the mapping dictionary
id_generator = count(1000000)
pass_hash = {uid: next(id_generator) for uid in all_uids}

# 4. Apply the hash
for df in dfs.values():
    df["uid"] = df["uid"].map(pass_hash)

# 5. Save back
for name, df in dfs.items():
    # Constructing the output path to match your original logic
    suffix = f"_{name}" if name != "spiral" else ""
    out_path = f"../data/raw_csvs/{RECENT_PHASE}{suffix}.csv"

    df.to_csv(out_path, index=False)

cur_time = time()
print("CSV processing complete:", round(cur_time - start_time, 2), "s")
