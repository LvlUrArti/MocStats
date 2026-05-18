"""Config file for enka.network."""

import csv
import json
import os.path
import sys

sys.path.append("../scripts/")
from comp_rates_config import (
    CHAR_RESULT_PATH,
    CHARS_INFO,
    RECENT_PHASE,
    as_mode,
    pf_mode,
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


phase_num = RECENT_PHASE
if as_mode:
    phase_num = phase_num + "_as"
elif pf_mode:
    phase_num = phase_num + "_pf"

with open("../data/relics.json") as f:
    relics_data = json.load(f)

trailblazer_ids: list[str] = []
for char in CHARS_INFO.values():
    if char.trailblazer_ids:
        trailblazer_ids.extend(
            trailblazer_id for trailblazer_id in char.trailblazer_ids
        )

if os.path.exists(f"../{CHAR_RESULT_PATH}/uids.csv"):
    with open(f"../{CHAR_RESULT_PATH}/uids.csv", encoding="UTF8") as f:
        reader = csv.reader(f, delimiter=",")
        uids = list(reader)
        uids = [int(uid[0]) for uid in uids]
        uids = list(dict.fromkeys(uids))
else:
    uids = [806411333]

filename = "../data/raw_csvs_real/" + RECENT_PHASE + "_build"
char_filename = filename + "_char.csv"
filename = filename + ".csv"
