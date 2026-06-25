"""Config file for enka.network."""

import csv
import json
import os.path
import sys
from pathlib import Path

sys.path.append("../scripts/")
from comp_rates_config import (
    BASE_RESULT_PATH,
    CHARS_INFO,
    RECENT_PHASE,
)

skip_self = False
skip_random = False
print_chart = False

comp_stats = []
check_char = True
check_char_name = "Yanqing"
check_stats = []

# stat.py
run_all_chars = True
run_chars_name = ["Firefly", "Ruan Mei", "Gallagher", "Misha", "Xueyi"]

with open("../data/relics.json") as f:
    relics_data = json.load(f)

trailblazer_ids: set[str] = set()
for char in CHARS_INFO.values():
    if char.trailblazer_ids:
        trailblazer_ids.update(
            trailblazer_id for trailblazer_id in char.trailblazer_ids
        )

if os.path.exists(f"../{BASE_RESULT_PATH}/uids.csv"):
    with open(f"../{BASE_RESULT_PATH}/uids.csv", encoding="UTF8") as f:
        reader = csv.reader(f, delimiter=",")
        uids = list(reader)
        uids = [int(uid[0]) for uid in uids]
        uids = list(dict.fromkeys(uids))
else:
    uids = [806411333]

filename = "../data/raw_csvs_real/" + RECENT_PHASE + "_build"
char_filename = filename + "_char.csv"
filename = filename + ".csv"


def get_start_index(id_list: list[int]) -> int:
    """Determine the index in `id_list` from which to start collecting new data."""
    # If CSV doesn't exist, start from the beginning
    if not Path(filename).exists():
        return 0

    # Read the last row of the CSV
    with open(filename, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        # Get the last row by iterating to the end
        last_row = None
        for row in reader:
            last_row = row
        if last_row is None:  # only header or empty
            return 0

    # Find the index of the last ID in the original list
    try:
        idx = id_list.index(int(last_row["uid"]))
    except ValueError:
        # ID is not in the list
        return 0

    # Resume from the next ID
    return idx + 1


start_index = get_start_index(uids)
