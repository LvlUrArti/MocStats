"""Compile stats."""

from csv import reader as csvreader
from csv import writer as csvwriter
from io import TextIOWrapper
from itertools import chain
from json import dumps as json_dumps
from json import load as json_load
from operator import itemgetter
from os import mkdir, path
from statistics import mean as stat_mean
from statistics import median as stat_median
from sys import exit as sys_exit
from sys import path as sys_path

from matplotlib.pyplot import (
    hist as plt_hist,  # pyright: ignore[reportUnknownVariableType]
)
from matplotlib.pyplot import (
    show as plt_show,  # pyright: ignore[reportUnknownVariableType]
)

sys_path.append("../scripts/")
from comp_rates_config import (
    CHAR_NAME_REPLACE,
    RECENT_PHASE,
    RECENT_PHASE_PF,
    pf_filename,
    skew_num,
    skip_random,
    skip_self,
    slug_with_prefix,
)
from csv_to_pickle import PickleData, load_pickle_data
from nohomo_config import (
    check_char,
    check_char_name,
    check_stats,
    print_chart,
)
from player_phase import PlayerPhase
from pynput import keyboard
from scipy.stats import (  # pyright: ignore[reportMissingTypeStubs]
    skew,  # pyright: ignore[reportUnknownVariableType]
)


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

with open("../data/light_cones.json") as f:
    LIGHT_CONES = json_load(f)

with open("../results/char_results/" + RECENT_PHASE_PF + "/all.csv") as f:
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
    "spd_sub",
    "hp_sub",
    "atk_sub",
    "def_sub",
    "crate_sub",
    "cdmg_sub",
    "res_sub",
    "ehr_sub",
    "break_sub",
]
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
stats: dict[str, StatsChar] = {}
median: dict[str, dict[str, float]] = {}
mean: dict[str, dict[str, float]] = {}
mainstats: dict[str, dict[str, dict[str, float]]] = {}
chars.extend(row[0] for row in build)

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
    stats[char] = StatsChar(char)
    mean[char] = dict.fromkeys(statkeys, 0)
    median[char] = mean[char].copy()
    mainstats[char] = {
        "body_stats": {},
        "feet_stats": {},
        "sphere_stats": {},
        "rope_stats": {},
    }
ar = 0
count = 0
uid = "0"
mainstatkeys: list[str] = list(mainstats[chars[0]].keys())
substatkeys: list[str] = list(substats.keys())

if path.isfile("../../uids.csv"):
    with open("../../uids.csv", encoding="UTF8") as f:
        reader = csvreader(f, delimiter=",")
        self_uids = next(iter(reader))
else:
    self_uids = []

for row in data:
    char = str(row[2])
    cur_uid = str(row[0])
    if skip_self and cur_uid in self_uids:
        continue
    if skip_random and cur_uid not in self_uids:
        continue
    if cur_uid != uid:
        uid = cur_uid
        ar += int(row[1])
        count += 1
    if char not in chars:
        if char in CHAR_NAME_REPLACE:
            char = CHAR_NAME_REPLACE[char]
        elif char in {"Trailblazer", "March 7th"}:
            char = f"{row[4]} {char}"
        else:
            print(char)
            sys_exit()
    if cur_uid in spiral_rows and char in spiral_rows[cur_uid]:
        # if isValidChar:
        stats[char].sample_size_players += 1
        for _i in range(spiral_rows[cur_uid][char]):
            stats[char].stats_count["char_lvl"].append(float(row[3]))
            stats[char].sample_size += 1
            stats[char].stats_count["spd_sub"].append(float(row[23]))
            if row[6].isnumeric():
                stats[char].stats_count["light_cone_lvl"].append(float(row[6]))
            for j in range(2, 10):
                stats[char].stats_count[statkeys[j]].append(float(row[j + 5]))
            for j in chain(range(10, 18), range(19, 27)):
                stats[char].stats_count[statkeys[j]].append(float(row[j + 5]) / 100)
            for j in range(4):
                if row[j + 32] in mainstats[char][mainstatkeys[j]]:
                    mainstats[char][mainstatkeys[j]][row[j + 32]] += 1
                else:
                    mainstats[char][mainstatkeys[j]][row[j + 32]] = 1

copy_chars = chars.copy()
for char in copy_chars:
    if stats[char].sample_size > 0:
        for stat in stats[char].stats_count:
            skewness = 0
            if not stats[char].stats_count[stat]:
                stats[char].stats_write[stat] = 0
            elif stat != "name" and "sample_size" not in stat:
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
                    median[char][stat] = round(
                        stat_median(stats[char].stats_count[stat]),
                        2,
                    )
                    mean[char][stat] = round(
                        stat_mean(stats[char].stats_count[stat]),
                        2,
                    )
                else:
                    median[char][stat] = round(
                        stat_median(stats[char].stats_count[stat]),
                        4,
                    )
                    mean[char][stat] = round(
                        stat_mean(stats[char].stats_count[stat]),
                        4,
                    )
                if (
                    mean[char][stat] > 0
                    and median[char][stat] > 0
                    and stats[char].sample_size > 10
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
                        skew(stats[char].stats_count[stat], axis=0, bias=True),
                        2,
                    )
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
                                plt_hist(stats[char].stats_count[stat])
                                plt_show()
                            except Exception:
                                print("error plt")
                            with keyboard.Events() as events:
                                event = events.get(1e6)
                                if (
                                    event is not None
                                    and event.key == keyboard.KeyCode.from_char("1")
                                ):
                                    stats[char].stats_write[stat] = str(
                                        mean[char][stat],
                                    )
                                else:
                                    stats[char].stats_write[stat] = str(
                                        median[char][stat],
                                    )
                        else:
                            stats[char].stats_write[stat] = median[char][stat]
                    else:
                        stats[char].stats_write[stat] = median[char][stat]
                else:
                    stats[char].stats_write[stat] = mean[char][stat]

        stats[char].stats_write["sample_size_players"] = stats[char].sample_size_players

        for stat in mainstats[char]:
            sorted_stats = sorted(
                mainstats[char][stat].items(),
                key=itemgetter(1),
                reverse=True,
            )
            mainstats[char][stat] = dict(sorted_stats)
            for mainstat in mainstats[char][stat]:
                mainstats[char][stat][mainstat] = round(
                    mainstats[char][stat][mainstat] / stats[char].sample_size,
                    4,
                )
            mainstatlist = list(mainstats[char][stat])
            i = 0
            while i < 3:
                if i >= len(mainstatlist):
                    stats[char].stats_write[stat + "_" + str(i + 1)] = "-"
                    stats[char].stats_write[stat + "_" + str(i + 1) + "_app"] = "-"
                else:
                    stats[char].stats_write[stat + "_" + str(i + 1)] = mainstatlist[i]
                    stats[char].stats_write[stat + "_" + str(i + 1) + "_app"] = (
                        mainstats[char][stat][mainstatlist[i]]
                    )
                i += 1

    else:
        for stat in stats[char].stats_count:
            if not stats[char].stats_count[stat] or (
                stat != "name" and "sample_size" not in stat
            ):
                stats[char].stats_write[stat] = 0

        stats[char].stats_write["sample_size_players"] = 0
        for stat in mainstats[char]:
            i = 0
            while i < 3:
                stats[char].stats_write[stat + "_" + str(i + 1)] = "-"
                stats[char].stats_write[stat + "_" + str(i + 1) + "_app"] = "-"
                i += 1


def write_files(
    f1: TextIOWrapper,
    f2: TextIOWrapper,
) -> None:
    """Write the stats to a csv file."""
    csv_writer = csvwriter(f1)
    csv_writer2 = csvwriter(f2)
    del stats[chars[0]].sample_size
    csv_writer.writerow(["name", *stats[chars[0]].stats_write.keys()])
    for char in chars:
        if char != chars[0]:
            del stats[char].sample_size
        csv_writer.writerow([stats[char].name, *stats[char].stats_write.values()])
        csv_writer2.writerow([char + ": " + str(stats[char].sample_size_players)])
    f1.close()
    f2.close()


if path.exists("results_real"):
    with (
        open("results_real/chars.csv", "w", newline="", encoding="UTF8") as file1,
        open("results_real/demographic.csv", "w", newline="", encoding="UTF8") as file2,
    ):
        write_files(file1, file2)
else:
    with (
        open("results/chars.csv", "w", newline="", encoding="UTF8") as file1,
        open("results/demographic.csv", "w", newline="", encoding="UTF8") as file2,
    ):
        write_files(file1, file2)


temp_stats: list[dict[str, str | float]] = []
with open("../results/char_results/" + RECENT_PHASE_PF + "/all.json") as char_file:
    CHARACTERS: list[dict[str, str]] = json_load(char_file)
for iter_char, char_stat in enumerate(stats.values()):
    for i in chain(range(10, 18), range(19, 27)):
        char_stat.stats_write[statkeys[i]] = round(
            float(char_stat.stats_write[statkeys[i]]) * 100,
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

if not path.exists("../results/char_results/" + RECENT_PHASE_PF):
    mkdir("../results/char_results/" + RECENT_PHASE_PF)

with open(
    "../results/char_results/" + RECENT_PHASE_PF + "/all2.json",
    "w",
) as char_file:
    char_file.write(json_dumps(temp_stats, indent=2))

print("Average AR: ", (ar / count))
