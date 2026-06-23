"""Compile stats."""

# pyright: reportUnknownVariableType=false, reportMissingTypeStubs=false

from contextlib import suppress
from csv import DictReader
from csv import reader as csvreader
from csv import writer as csvwriter
from io import TextIOWrapper
from json import dumps as json_dumps
from json import load as json_load
from operator import itemgetter
from os import path
from statistics import mean as stat_mean
from statistics import median as stat_median
from sys import exit as sys_exit
from time import time

from matplotlib.pyplot import hist as plt_hist
from matplotlib.pyplot import show as plt_show
from nohomo_config import (
    check_char,
    check_char_name,
    check_stats,
    print_chart,
    round_stats,
    skip_check_skew_stats,
)
from pynput import keyboard
from scipy.stats import skew
from send2trash import send2trash

from scripts.comp_rates_config import (
    BUILD_RESULT_PATH,
    CHAR_NAME_REPLACE,
    CHAR_RESULT_PATH,
    RECENT_PHASE,
    pf_filename,
    skew_num,
    skip_random,
    skip_self,
    slug_with_prefix,
)
from scripts.csv_to_pickle import PickleData, load_pickle_data
from scripts.player_phase import PlayerPhase


def read_csv(file: TextIOWrapper) -> list[dict[str, str]]:
    """Read CSV."""
    return list(DictReader(file, delimiter=","))


try:
    if path.exists("../data/raw_csvs_real/"):
        with open(
            "../data/raw_csvs_real/" + RECENT_PHASE + "_build.csv",
            encoding="UTF8",
        ) as f:
            data = list(read_csv(f))
    else:
        with open(
            "../data/raw_csvs/" + RECENT_PHASE + "_build.csv",
            encoding="UTF8",
        ) as f:
            data = list(read_csv(f))
except FileNotFoundError:
    print("No build data found.")
    data = []

with open(f"../{CHAR_RESULT_PATH}/all.csv") as f:
    build = list(read_csv(f))

archetype = "all"


stats_dict = {
    "char_lvl": "char_level",
    "light_cone_lvl": "light_cone_level",
    "attack_lvl": "attack_lvl",
    "skill_lvl": "skill_lvl",
    "ultimate_lvl": "ultimate_lvl",
    "talent_lvl": "talent_lvl",
    "max_hp": "HP",
    "atk": "ATK",
    "dfns": "DEF",
    "speed": "SPD",
    "crate": "CRIT Rate",
    "cdmg": "CRIT DMG",
    "dmg_boost": "DMG Boost",
    "heal_boost": "Outgoing Healing Boost",
    "energy_regen": "Energy Regeneration Rate",
    "effect_res": "Effect RES",
    "effect_rate": "Effect Hit Rate",
    "break_effect": "Break Effect",
    "spd_sub": "SPD sub",
    "hp_sub": "HP sub",
    "atk_sub": "ATK sub",
    "def_sub": "DEF sub",
    "crate_sub": "CRIT Rate sub",
    "cdmg_sub": "CRIT DMG sub",
    "res_sub": "Effect RES sub",
    "ehr_sub": "Effect Hit Rate sub",
    "break_sub": "Break Effect sub",
}
statkeys = list(stats_dict.keys())

substats = {
    "spd_sub": 2.3,
    "hp_sub": 0.03888,
    "atk_sub": 0.03888,
    "def_sub": 0.0486,
    "crate_sub": 0.02916,
    "cdmg_sub": 0.05832,
    "res_sub": 0.03888,
    "ehr_sub": 0.03888,
    "break_sub": 0.05832,
}

mainstat_dict = {
    "body_stats": "Body",
    "feet_stats": "Feet",
    "sphere_stats": "Sphere",
    "rope_stats": "Rope",
}

percent_stats = {
    "crate",
    "cdmg",
    "dmg_boost",
    "heal_boost",
    "energy_regen",
    "effect_res",
    "effect_rate",
    "break_effect",
    "hp_sub",
    "atk_sub",
    "def_sub",
    "crate_sub",
    "cdmg_sub",
    "res_sub",
    "ehr_sub",
    "break_sub",
}

NON_STAT_KEYS = {"name", "sample_size", "sample_size_players"}


class StatsChar:
    """Character stats."""

    def __init__(self, char: str) -> None:
        """Initialize StatsChar class."""
        self.name = char
        self.stats_count: dict[str, list[float]] = {key: [] for key in statkeys}
        self.stats_write: dict[str, float | str] = dict.fromkeys(statkeys, 0)
        self.sample_size = 0
        self.sample_size_players = 0


chars: list[str] = []
set_chars: set[str] = set()
stats: dict[str, StatsChar] = {}
median: dict[str, dict[str, float]] = {}
mean: dict[str, dict[str, float]] = {}
mainstats: dict[str, dict[str, dict[str, float]]] = {}
chars.extend(row["char"] for row in build)
set_chars.update(chars)

loaded_data: PickleData = load_pickle_data("../data/pickle/data" + pf_filename + ".pkl")

start_time = time()
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
    stats[char] = StatsChar(char)
    mean[char] = dict.fromkeys(statkeys, 0)
    median[char] = mean[char].copy()
    mainstats[char] = {stat: {} for stat in mainstat_dict}
ar = 0
count = 0
uid = "0"
mainstatkeys: list[str] = list(mainstat_dict.keys())
substatkeys: list[str] = list(substats.keys())

if (skip_self or skip_random) and path.isfile("../../uids.csv"):
    with open("../../uids.csv", encoding="UTF8") as f:
        reader = csvreader(f, delimiter=",")
        self_uids = set(next(iter(reader)))
else:
    self_uids: set[str] = set()

for row in data:
    char = str(row["character"])
    cur_uid = str(row["uid"])
    if skip_self and cur_uid in self_uids:
        continue
    if skip_random and cur_uid not in self_uids:
        continue
    if cur_uid != uid:
        uid = cur_uid
        ar += int(row["player_level"])
        count += 1
    if char not in set_chars:
        if char in CHAR_NAME_REPLACE:
            char = CHAR_NAME_REPLACE[char]
        elif char in {"Trailblazer", "March 7th"}:
            char = f"{row['path']} {char}"
        else:
            msg = f"Unknown character: {char}"
            raise ValueError(msg)
    if cur_uid in spiral_rows and char in spiral_rows[cur_uid]:
        stats[char].sample_size_players += 1

        # The more times a character is used, the more weight it has
        for _i in range(spiral_rows[cur_uid][char]):
            stats[char].sample_size += 1

            for key in statkeys:
                divisor = 100 if key in percent_stats else 1
                with suppress(ValueError):
                    dividend = float(row.get(stats_dict[key], 0))
                    stats[char].stats_count[key].append(dividend / divisor)

            for key in mainstatkeys:
                mainstat = row.get(mainstat_dict[key], None)
                if mainstat:
                    if mainstat not in mainstats[char][key]:
                        mainstats[char][key][mainstat] = 0
                    mainstats[char][key][mainstat] += 1
cur_time = time()
print("done stats:", round(cur_time - start_time, 2), "s")
start_time = cur_time

for char, stat_char in stats.items():
    if stat_char.sample_size > 0:
        for stat, stat_count in stat_char.stats_count.items():
            skewness = 0
            if not stat_count:
                stat_char.stats_write[stat] = 0
            elif stat not in NON_STAT_KEYS:
                if stat in round_stats:
                    median[char][stat] = round(stat_median(stat_count), 2)
                    mean[char][stat] = round(stat_mean(stat_count), 2)
                else:
                    median[char][stat] = round(stat_median(stat_count), 4)
                    mean[char][stat] = round(stat_mean(stat_count), 4)
                if (
                    mean[char][stat] > 0
                    and median[char][stat] > 0
                    and stat_char.sample_size > 10
                ) and stat not in skip_check_skew_stats:
                    skewness = round(skew(stat_count, axis=0, bias=True), 2)
                if abs(skewness) > skew_num:
                    if print_chart:
                        if (
                            not (check_char) or char == check_char_name
                        ) and stat in check_stats:
                            print("skewness: " + str(skewness))
                            print(
                                stat
                                + ": "
                                + str(mean[char][stat])
                                + ", "
                                + str(median[char][stat]),
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
                                    stat_char.stats_write[stat] = mean[char][stat]
                                else:
                                    stat_char.stats_write[stat] = median[char][stat]
                        else:
                            stat_char.stats_write[stat] = median[char][stat]
                    else:
                        stat_char.stats_write[stat] = median[char][stat]
                else:
                    stat_char.stats_write[stat] = mean[char][stat]

        stat_char.stats_write["sample_size_players"] = stat_char.sample_size_players

        for stat in mainstats[char]:
            sorted_stats = sorted(
                mainstats[char][stat].items(),
                key=itemgetter(1),
                reverse=True,
            )
            mainstats[char][stat] = dict(sorted_stats)
            for mainstat in mainstats[char][stat]:
                mainstats[char][stat][mainstat] = round(
                    mainstats[char][stat][mainstat] / stat_char.sample_size,
                    4,
                )
            mainstatlist = list(mainstats[char][stat])
            i = 0
            while i < 3:
                if i >= len(mainstatlist):
                    stat_char.stats_write[stat + "_" + str(i + 1)] = "-"
                    stat_char.stats_write[stat + "_" + str(i + 1) + "_app"] = "-"
                else:
                    stat_char.stats_write[stat + "_" + str(i + 1)] = mainstatlist[i]
                    stat_char.stats_write[stat + "_" + str(i + 1) + "_app"] = mainstats[
                        char
                    ][stat][mainstatlist[i]]
                i += 1

    else:
        for stat, stat_count in stat_char.stats_count.items():
            if not stat_count or (stat not in NON_STAT_KEYS):
                stat_char.stats_write[stat] = 0

        stat_char.stats_write["sample_size_players"] = 0
        for stat in mainstats[char]:
            i = 0
            while i < 3:
                stat_char.stats_write[stat + "_" + str(i + 1)] = "-"
                stat_char.stats_write[stat + "_" + str(i + 1) + "_app"] = "-"
                i += 1
cur_time = time()
print("done compile:", round(cur_time - start_time, 2), "s")
start_time = cur_time


def write_files(
    f1: TextIOWrapper,
    f2: TextIOWrapper,
) -> None:
    """Write the stats to a csv file."""
    csv_writer = csvwriter(f1)
    csv_writer2 = csvwriter(f2)
    csv_writer.writerow(["name", *stats[next(iter(chars))].stats_write.keys()])
    for char in chars:
        del stats[char].sample_size
        if not stats[char].name.startswith(("solo-", "supp-")):
            csv_writer.writerow([stats[char].name, *stats[char].stats_write.values()])
            csv_writer2.writerow([char + ": " + str(stats[char].sample_size_players)])
    f1.close()
    f2.close()


with (
    open(
        f"../{BUILD_RESULT_PATH}/chars.csv",
        "w",
        newline="",
        encoding="UTF8",
    ) as file1,
    open(
        f"../{BUILD_RESULT_PATH}/demographic.csv",
        "w",
        newline="",
        encoding="UTF8",
    ) as file2,
):
    write_files(file1, file2)


temp_stats: list[dict[str, str | float]] = []
with open(f"../{CHAR_RESULT_PATH}/all.json") as char_file:
    CHARACTERS: list[dict[str, str]] = json_load(char_file)
for iter_char, char_stat in enumerate(stats.values()):
    for key in statkeys:
        if key in percent_stats:
            char_stat.stats_write[key] = round(
                float(char_stat.stats_write[key]) * 100,
                2,
            )
    iterate_value_app: list[str] = []
    for i in range(3):
        iterate_value_app.append("body_stats_" + str(i + 1) + "_app")
        iterate_value_app.append("feet_stats_" + str(i + 1) + "_app")
        iterate_value_app.append("sphere_stats_" + str(i + 1) + "_app")
        iterate_value_app.append("rope_stats_" + str(i + 1) + "_app")
    for value in iterate_value_app:
        if isinstance(char_stat.stats_write[value], float):
            char_stat.stats_write[value] = round(
                float(char_stat.stats_write[value]) * 100,
                2,
            )
        else:
            char_stat.stats_write[value] = 0.00

    char_stat.name = slug_with_prefix(char_stat.name)
    if char_stat.name == CHARACTERS[iter_char]["char"]:
        del char_stat.name
    else:
        print(char_stat.name)
        print(CHARACTERS[iter_char]["char"])
        sys_exit()

    temp_stats.append(CHARACTERS[iter_char] | char_stat.stats_write)

send2trash(f"../{CHAR_RESULT_PATH}/all.json")
with open(f"../{CHAR_RESULT_PATH}/all.json", "w") as char_file:
    char_file.write(json_dumps(temp_stats, indent=2))
