# pyright: reportUnknownVariableType=false, reportUnknownMemberType=false
"""Hash function for comp rates."""

from itertools import count

from comp_rates_config import RECENT_PHASE
from pandas import DataFrame, read_csv

# Create sequential ID generator
id_generator = count(1000000)  # Start at 1,000,000 (7 digits)
pass_hash = {}

df_char: DataFrame = read_csv(
    "../data/raw_csvs_real/" + RECENT_PHASE + "_char.csv",
    encoding="cp1252",
).convert_dtypes()
df_spiral = read_csv(
    "../data/raw_csvs_real/" + RECENT_PHASE + ".csv",
    encoding="cp1252",
).convert_dtypes()
df_spiral_pf = read_csv(
    "../data/raw_csvs_real/" + RECENT_PHASE + "_pf.csv",
    encoding="cp1252",
).convert_dtypes()
df_spiral_as = read_csv(
    "../data/raw_csvs_real/" + RECENT_PHASE + "_as.csv",
    encoding="cp1252",
).convert_dtypes()
df_spiral_aa = read_csv(
    "../data/raw_csvs_real/" + RECENT_PHASE + "_aa.csv",
    encoding="cp1252",
).convert_dtypes()

df_stats = read_csv("../mihomo/output1.csv", encoding="cp1252").convert_dtypes()

for i in df_char["uid"].unique():
    pass_hash[i] = next(id_generator)
for i in df_spiral["uid"].unique():
    if i not in pass_hash:
        pass_hash[i] = next(id_generator)
for i in df_spiral_pf["uid"].unique():
    if i not in pass_hash:
        pass_hash[i] = next(id_generator)
for i in df_spiral_as["uid"].unique():
    if i not in pass_hash:
        pass_hash[i] = next(id_generator)
for i in df_spiral_aa["uid"].unique():
    if i not in pass_hash:
        pass_hash[i] = next(id_generator)

df_char["uid"] = df_char["uid"].replace(pass_hash)
df_spiral["uid"] = df_spiral["uid"].replace(pass_hash)
df_spiral_pf["uid"] = df_spiral_pf["uid"].replace(pass_hash)
df_spiral_as["uid"] = df_spiral_as["uid"].replace(pass_hash)
df_spiral_aa["uid"] = df_spiral_aa["uid"].replace(pass_hash)
df_stats["uid"] = df_stats["uid"].replace(pass_hash)
print("csv done")

df_char.to_csv("../data/raw_csvs/" + RECENT_PHASE + "_char.csv", index=False)
df_spiral.to_csv("../data/raw_csvs/" + RECENT_PHASE + ".csv", index=False)
df_spiral_pf.to_csv("../data/raw_csvs/" + RECENT_PHASE + "_pf.csv", index=False)
df_spiral_as.to_csv("../data/raw_csvs/" + RECENT_PHASE + "_as.csv", index=False)
df_spiral_aa.to_csv("../data/raw_csvs/" + RECENT_PHASE + "_aa.csv", index=False)
df_stats.to_csv("../mihomo/results/" + RECENT_PHASE + "_output.csv", index=False)
