"""Compile stats for single character."""

# pyright: reportUnknownVariableType=false, reportMissingTypeStubs=false

from csv import reader as csvreader
from csv import writer as csvwriter
from io import TextIOWrapper
from os import path
from statistics import mean as stat_mean
from statistics import median as stat_median
from sys import path as sys_path

from matplotlib.pyplot import hist as plt_hist
from matplotlib.pyplot import show as plt_show
from send2trash import send2trash

sys_path.append("../scripts/")
from comp_rates_config import (
    BUILD_RESULT_PATH,
    CHAR_NAME_REPLACE,
    CHAR_RESULT_PATH,
    RECENT_PHASE,
    pf_filename,
    run_all_chars,
    run_chars_name,
    skew_num,
)
from csv_to_pickle import PickleData, load_pickle_data
from nohomo_config import print_chart, round_stats, skip_check_skew_stats
from player_phase import PlayerPhase
from pynput import keyboard
from scipy.stats import skew


def read_csv(file: TextIOWrapper) -> list[list[str]]:
    """Read CSV."""
    reader = csvreader(file, delimiter=",")
    next(reader)
    return list(reader)


if path.exists("../data/raw_csvs_real/"):
    with open(
        "../data/raw_csvs_real/" + RECENT_PHASE + "_build.csv",
        encoding="UTF8",
    ) as f:
        data = list(read_csv(f))
else:
    with open("../data/raw_csvs/" + RECENT_PHASE + "_build.csv", encoding="UTF8") as f:
        data = list(read_csv(f))

with open(f"../{CHAR_RESULT_PATH}/all.csv") as f:
    reader = csvreader(f, delimiter=",")
    col_names_build = next(reader)
    build = list(read_csv(f))

archetype = "all"


statkeys = [
    "char_lvl",
    "light_cone_lvl",
    "attack_lvl",
    "skill_lvl",
    "ultimate_lvl",
    "talent_lvl",
    "max_hp",
    "atk",
    "dfns",
    "speed",
    "crate",
    "cdmg",
    "dmg_boost",
    "heal_boost",
    "energy_regen",
    "effect_res",
    "effect_rate",
    "break_effect",
]


class StatsWeap:
    """Character stats."""

    def __init__(self, char: str, weap: str) -> None:
        """Initialize StatsChar class."""
        self.name = char
        self.weap = weap
        self.stats_count: dict[str, list[float]] = {key: [] for key in statkeys}
        self.stats_write: dict[str, float | str] = dict.fromkeys(statkeys, 0)
        self.sample_size = 0
        self.sample_size_players = 0


RESULT_FILE = f"../{BUILD_RESULT_PATH}/char_weapons.csv"

if path.exists(RESULT_FILE):
    send2trash(RESULT_FILE)

chars: list[str] = []
set_chars: set[str] = set()
stats: dict[str, dict[str, StatsWeap]] = {}
median: dict[str, dict[str, dict[str, float]]] = {}
mean: dict[str, dict[str, dict[str, float]]] = {}
chars.extend((row[0] for row in build) if run_all_chars else run_chars_name)
set_chars.update(chars)

loaded_data: PickleData = load_pickle_data("../data/pickle/data" + pf_filename + ".pkl")

all_players: dict[str, PlayerPhase] = loaded_data.all_players
spiral_rows: dict[str, dict[str, int]] = {}
for cur_uid, cur_player in all_players.items():
    spiral_rows[cur_uid] = {}
    for player_comp in cur_player.chambers.values():
        for char in player_comp.comp_chars:
            if char not in spiral_rows[cur_uid]:
                spiral_rows[cur_uid][char] = 0
            spiral_rows[cur_uid][char] += 1

for char in chars:
    stats[char] = {}
    median[char] = {}
    mean[char] = {}

for row in data:
    char = str(row[2])
    cur_uid = str(row[0])
    if char in CHAR_NAME_REPLACE:
        char = CHAR_NAME_REPLACE[char]
    elif char in {"Trailblazer", "March 7th"}:
        char = f"{row[4]} {char}"
    if char not in set_chars:
        continue
    if cur_uid in spiral_rows and char in spiral_rows[cur_uid]:
        weap = row[5]
        if weap == "":
            continue

        if weap not in stats[char]:
            stats[char][weap] = StatsWeap(char, weap)
            mean[char][weap] = dict.fromkeys(statkeys, 0)
            median[char][weap] = mean[char][weap].copy()
            stats[char][weap].sample_size = 0

        stats[char][weap].sample_size += 1
        stats[char][weap].stats_count["char_lvl"].append(float(row[3]))

        if row[6].isnumeric():
            stats[char][weap].stats_count["light_cone_lvl"].append(float(row[6]))
        for j in range(2, 10):
            stats[char][weap].stats_count[statkeys[j]].append(float(row[j + 5]))
        for j in range(10, 18):
            stats[char][weap].stats_count[statkeys[j]].append(
                float(row[j + 5]) / 100,
            )

for char, stat_char in stats.items():
    for weap, stat_weap in stat_char.items():
        if stat_weap.sample_size > 0:
            for stat, stat_count in stat_weap.stats_count.items():
                skewness = 0
                if stat != "name":
                    if stat in round_stats:
                        median[char][weap][stat] = round(stat_median(stat_count), 2)
                        mean[char][weap][stat] = round(stat_mean(stat_count), 2)
                    else:
                        median[char][weap][stat] = round(stat_median(stat_count), 4)
                        mean[char][weap][stat] = round(stat_mean(stat_count), 4)
                    if (
                        mean[char][weap][stat] > 0
                        and median[char][weap][stat] > 0
                        and stat_weap.sample_size > 10
                    ) and stat not in skip_check_skew_stats:
                        skewness = round(skew(stat_count, axis=0, bias=True), 2)
                    if abs(skewness) > skew_num:
                        if print_chart:
                            print("skewness: " + str(skewness))
                            print(
                                stat
                                + ": "
                                + str(mean[char][weap][stat])
                                + ", "
                                + str(median[char][weap][stat]),
                            )
                            try:
                                plt_hist(stat_count)
                                plt_show()
                            except Exception:
                                print("error plt")
                            print("1 - Mean, 2 - Median: ")
                            with keyboard.Events() as events:
                                event = events.get(1e6)
                                if (
                                    event is not None
                                    and event.key == keyboard.KeyCode.from_char("1")
                                ):
                                    stat_weap.stats_write[stat] = mean[char][weap][stat]
                                else:
                                    stat_weap.stats_write[stat] = median[char][weap][
                                        stat
                                    ]
                        else:
                            stat_weap.stats_write[stat] = median[char][weap][stat]
                    else:
                        stat_weap.stats_write[stat] = mean[char][weap][stat]

    if stat_char:
        stat_char_write = dict(
            sorted(stat_char.items(), key=lambda t: t[1].sample_size, reverse=True),
        )
        with open(RESULT_FILE, "a", newline="") as file:
            csv_writer = csvwriter(file)

            if not file.tell():
                csv_writer.writerow(["char", "weap", *statkeys, "sample_size"])

            for stat_weap in stat_char_write.values():
                csv_writer.writerow(
                    [
                        char,
                        stat_weap.weap,
                        *stat_weap.stats_write.values(),
                        stat_weap.sample_size,
                    ],
                )
