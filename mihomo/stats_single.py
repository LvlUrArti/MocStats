"""Compile stats for single character."""

# pyright: reportUnknownVariableType=false, reportMissingTypeStubs=false
from __future__ import annotations

import sys

sys.path.append("../scripts/")

import os
from csv import reader as csvreader
from csv import writer as csvwriter
from statistics import mean as stat_mean
from statistics import median as stat_median
from typing import TYPE_CHECKING, cast

from comp_rates_config import (
    RECENT_PHASE_PF,
    pf_mode,
    run_all_chars,
    run_chars_name,
    skew_num,
    skip_random,
    skip_self,
)
from matplotlib.pyplot import hist as plt_hist
from matplotlib.pyplot import show as plt_show
from nohomo_config import print_chart
from numpy import array as nparray
from pynput import keyboard
from scipy.stats import skew

if TYPE_CHECKING:
    from io import TextIOWrapper


def read_csv(file: TextIOWrapper) -> list[list[str]]:
    """Read CSV."""
    reader = csvreader(file, delimiter=",")
    next(reader)
    return list(reader)


if os.path.isfile("../../uids.csv"):
    with open("../../uids.csv", encoding="UTF8") as f:
        reader = csvreader(f, delimiter=",")
        self_uids = next(iter(reader))
else:
    self_uids = []

with open("output1.csv") as f:
    reader = csvreader(f, delimiter=",")
    headers = next(reader)
    data = nparray(list(reader))

if os.path.exists("../data/raw_csvs_real/"):
    with open("../data/raw_csvs_real/" + RECENT_PHASE_PF + ".csv") as f:
        spiral = read_csv(f)
else:
    with open("../data/raw_csvs/" + RECENT_PHASE_PF + ".csv") as f:
        spiral = read_csv(f)

with open("../results/char_results/all.csv") as f:
    reader = csvreader(f, delimiter=",")
    col_names_build = next(reader)
    build = nparray(list(reader))

archetype = "all"

chars: set[str] = set()
chars = {row[0] for row in build} if run_all_chars else run_chars_name
stats: dict[str, dict[str, dict[str, list[float | str]]]] = {}
median: dict[str, dict[str, dict[str, float]]] = {}
mean: dict[str, dict[str, dict[str, float]]] = {}
sample: dict[str, dict[str, int]] = {}
weapons: dict[str, list[str]] = {}
copy_weapons: dict[str, list[str]] = {}

spiral_rows: dict[str, set[str]] = {}
for spiral_row in spiral:
    if (
        int("".join(filter(str.isdigit, spiral_row[1]))) > 11
        or (pf_mode and int("".join(filter(str.isdigit, spiral_row[1]))) > 3)
    ) and int(spiral_row[4]) == 3:
        if spiral_row[0] not in spiral_rows:
            spiral_rows[spiral_row[0]] = set()
        spiral_rows[spiral_row[0]].update(
            [spiral_row[5], spiral_row[6], spiral_row[7], spiral_row[8]],
        )

for char in chars:
    stats[char] = {}
    median[char] = {}
    mean[char] = {}
    sample[char] = {}
    weapons[char] = []

    for row in build:
        if row[0] == char:
            for j in range(
                col_names_build.index("weapon_1"),
                col_names_build.index("weapon_1") + 27,
                3,
            ):
                if row[j] != "":
                    weapons[char].append(row[j])
                    stats[char][row[j]] = {
                        "name": row[j],
                        "char_lvl": [],
                        "light_cone_lvl": [],
                        "attack_lvl": [],
                        "skill_lvl": [],
                        "ultimate_lvl": [],
                        "talent_lvl": [],
                        "max_hp": [],
                        "atk": [],
                        "dfns": [],
                        "speed": [],
                        "crate": [],
                        "cdmg": [],
                        "dmg_boost": [],
                        "heal_boost": [],
                        "energy_regen": [],
                        "effect_res": [],
                        "effect_rate": [],
                        "break_effect": [],
                    }
                    median[char][row[j]] = {
                        "attack_lvl": 0,
                        "skill_lvl": 0,
                        "ultimate_lvl": 0,
                        "talent_lvl": 0,
                        "max_hp": 0,
                        "atk": 0,
                        "dfns": 0,
                        "speed": 0,
                        "crate": 0,
                        "cdmg": 0,
                        "dmg_boost": 0,
                        "heal_boost": 0,
                        "energy_regen": 0,
                        "effect_res": 0,
                        "effect_rate": 0,
                        "break_effect": 0,
                    }
                    mean[char][row[j]] = {
                        "attack_lvl": 0,
                        "skill_lvl": 0,
                        "ultimate_lvl": 0,
                        "talent_lvl": 0,
                        "max_hp": 0,
                        "atk": 0,
                        "dfns": 0,
                        "speed": 0,
                        "crate": 0,
                        "cdmg": 0,
                        "dmg_boost": 0,
                        "heal_boost": 0,
                        "energy_regen": 0,
                        "effect_res": 0,
                        "effect_rate": 0,
                        "break_effect": 0,
                    }
                    sample[char][row[j]] = 0
            break

first_char = next(iter(chars))
statkeys = list(stats[first_char][weapons[first_char][0]].keys())

for row in data:
    cur_char = row[2]
    if skip_self and row[0] in self_uids:
        continue
    if skip_random and row[0] not in self_uids:
        continue
    if "Dan Heng â€¢ Imbibitor Lunae" in cur_char:
        cur_char = "Dan Heng • Imbibitor Lunae"
    if "Topaz and Numby" in cur_char:
        cur_char = "Topaz & Numby"
    if cur_char in {"Trailblazer", "March 7th"}:
        match row[4]:
            case "Fire":
                cur_char = "Fire " + cur_char
            case "Physical":
                cur_char = "Physical " + cur_char
            case "Ice":
                cur_char = "Ice " + cur_char
            case "Lightning":
                cur_char = "Lightning " + cur_char
            case "Wind":
                cur_char = "Wind " + cur_char
            case "Quantum":
                cur_char = "Quantum " + cur_char
            case "Imaginary":
                cur_char = "Imaginary " + cur_char
            case _:
                pass
    if cur_char in chars:
        found = False
        if row[0] in spiral_rows:
            if cur_char in spiral_rows[row[0]] or (
                "Trailblazer" in spiral_rows[row[0]] and "Trailblazer" in cur_char
            ):
                found = True
            if found and row[5] in weapons[cur_char]:
                sample[cur_char][row[5]] += 1
                stats[cur_char][row[5]]["char_lvl"].append(float(row[3]))
                if row[6].isnumeric():
                    stats[cur_char][row[5]]["light_cone_lvl"].append(float(row[6]))
                for i in range(3, 11):
                    stats[cur_char][row[5]][statkeys[i]].append(float(row[i + 4]))
                for i in range(11, 19):
                    stats[cur_char][row[5]][statkeys[i]].append(
                        float(row[i + 4]) / 100,
                    )

for char in chars:
    copy_weapons[char] = weapons[char].copy()
    for weapon in copy_weapons[char]:
        if sample[char][weapon] > 0:
            for stat in stats[char][weapon]:
                skewness = 0
                if stat != "name":
                    if stat in [
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
                    ]:
                        median[char][weapon][stat] = round(
                            stat_median(cast("list[float]", stats[char][weapon][stat])),
                            2,
                        )
                        mean[char][weapon][stat] = round(
                            stat_mean(cast("list[float]", stats[char][weapon][stat])),
                            2,
                        )
                    else:
                        median[char][weapon][stat] = round(
                            stat_median(cast("list[float]", stats[char][weapon][stat])),
                            4,
                        )
                        mean[char][weapon][stat] = round(
                            stat_mean(cast("list[float]", stats[char][weapon][stat])),
                            4,
                        )
                    if (
                        mean[char][weapon][stat] > 0
                        and median[char][weapon][stat] > 0
                        and sample[char][weapon] > 5
                    ) and stat not in [
                        "char_lvl",
                        "light_cone_lvl",
                        "attack_lvl",
                        "skill_lvl",
                        "ultimate_lvl",
                        "talent_lvl",
                        "energy_regen",
                        "dmg_boost",
                    ]:
                        skewness = round(
                            skew(stats[char][weapon][stat], axis=0, bias=True),
                            2,
                        )
                    if abs(skewness) > skew_num:
                        if print_chart:
                            print("skewness: " + str(skewness))
                            print(
                                stat
                                + ": "
                                + str(mean[char][weapon][stat])
                                + ", "
                                + str(median[char][weapon][stat]),
                            )
                            try:
                                plt_hist(stats[char][weapon][stat])
                                plt_show()
                            except Exception:
                                print("error in plt_hist")
                            print("1 - Mean, 2 - Median: ")
                            with keyboard.Events() as events:
                                event = events.get(1e6)
                                if event and event.key == keyboard.KeyCode.from_char(
                                    "1",
                                ):
                                    stats[char][weapon][stat] = str(
                                        mean[char][weapon][stat],
                                    )
                                else:
                                    stats[char][weapon][stat] = str(
                                        median[char][weapon][stat],
                                    )
                        else:
                            stats[char][weapon][stat] = str(median[char][weapon][stat])
                    else:
                        stats[char][weapon][stat] = str(mean[char][weapon][stat])
        else:
            del stats[char][weapon]
            weapons[char].remove(weapon)

    if stats[char]:
        print()
        print()
        if os.path.exists("results_real"):
            with open("results_real/" + char + "_weapons.csv", "w", newline="") as f:
                csv_writer = csvwriter(f)
                for weapon in weapons[char]:
                    print(weapon + ": " + str(sample[char][weapon]))
                    csv_writer.writerow(stats[char][weapon].values())
