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

sys_path.append("../Comps/")
from comp_rates_config import (
    RECENT_PHASE,
    RECENT_PHASE_PF,
    pf_mode,
    skew_num,
    skip_random,
    skip_self,
)
from nohomo_config import (
    check_char,
    check_char_name,
    check_stats,
    print_chart,
)
from numpy import array as nparray
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
    with open("results_real/" + RECENT_PHASE + "/output1.csv") as f:
        data = nparray(read_csv(f))
else:
    with open("results/" + RECENT_PHASE + "_output.csv") as f:
        data = nparray(read_csv(f))

with open("../data/light_cones.json") as f:
    LIGHT_CONES = json_load(f)
with open("../Comps/prydwen-slug.json") as slug_file:
    slug = json_load(slug_file)

if path.exists("../data/raw_csvs_real/"):
    with open("../data/raw_csvs_real/" + RECENT_PHASE_PF + ".csv") as f:
        spiral = read_csv(f)
else:
    with open("../data/raw_csvs/" + RECENT_PHASE_PF + ".csv") as f:
        spiral = read_csv(f)

with open("../char_results/" + RECENT_PHASE_PF + "/all.csv") as f:
    build = nparray(read_csv(f))

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

spiral_rows: dict[str, dict[str, int]] = {}
for spiral_row in spiral:
    if (
        int("".join(filter(str.isdigit, spiral_row[1]))) > 11
        or (pf_mode and int("".join(filter(str.isdigit, spiral_row[1]))) > 3)
    ) and int(spiral_row[4]) == 3:
        if spiral_row[0] not in spiral_rows:
            spiral_rows[spiral_row[0]] = {}
        for i in range(5, 9):
            if spiral_row[i] in [
                "Dan Heng â€¢ Imbibitor Lunae",
                "Dan Heng \u2022 Imbibitor Lunae",
            ]:
                spiral_row[i] = "Dan Heng • Imbibitor Lunae"
            if "Topaz and Numby" in spiral_row[i]:
                spiral_row[i] = "Topaz & Numby"
            if spiral_row[i] not in spiral_rows[spiral_row[0]]:
                spiral_rows[spiral_row[0]][spiral_row[i]] = 1
            else:
                spiral_rows[spiral_row[0]][spiral_row[i]] += 1

chars.extend(row[0] for row in build)

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
uid = 0
mainstatkeys: list[str] = list(mainstats[chars[0]].keys())
substatkeys: list[str] = list(substats.keys())

if path.isfile("../../uids.csv"):
    with open("../../uids.csv", encoding="UTF8") as f:
        reader = csvreader(f, delimiter=",")
        self_uids = next(iter(reader))
else:
    self_uids = []

for row in data:
    char = row[2]
    cur_uid = row[0]
    if skip_self and cur_uid in self_uids:
        continue
    if skip_random and cur_uid not in self_uids:
        continue
    if cur_uid != uid:
        uid = cur_uid
        ar += int(row[1])
        count += 1
    if char not in chars:
        if char in [
            "Dan Heng â€¢ Imbibitor Lunae",
            "Dan Heng Ã¢â,¬Â¢ Imbibitor Lunae",
            "Dan Heng \u2022 Imbibitor Lunae",
        ]:
            char = "Dan Heng • Imbibitor Lunae"
        elif "Topaz and Numby" in char:
            char = "Topaz & Numby"
        elif "Trailblazer" in char:
            char = "Trailblazer"
        elif "March 7th" in char:
            char = "March 7th"
        else:
            print(char)
            sys_exit()
    if char in {"Trailblazer", "March 7th"}:
        match row[4]:
            case "Fire":
                char = "Fire " + char
            case "Physical":
                char = "Physical " + char
            case "Ice":
                char = "Ice " + char
            case "Lightning":
                char = "Lightning " + char
            case "Wind":
                char = "Wind " + char
            case "Quantum":
                char = "Quantum " + char
            case "Imaginary":
                char = "Imaginary " + char
            case _:
                pass
    found = False
    if cur_uid in spiral_rows:
        if char in spiral_rows[cur_uid] or (
            "Trailblazer" in spiral_rows[cur_uid] and "Trailblazer" in char
        ):
            found = True

        if found:
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
                    and stats[char].sample_size > 5
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
        open("results_real/chars.csv", "w", newline="") as file1,
        open("results_real/demographic.csv", "w", newline="") as file2,
    ):
        write_files(file1, file2)
else:
    with (
        open("results/chars.csv", "w", newline="") as file1,
        open("results/demographic.csv", "w", newline="") as file2,
    ):
        write_files(file1, file2)


temp_stats: list[str] = []
iter_char = 0
with open("../char_results/" + RECENT_PHASE_PF + "/all.json") as char_file:
    CHARACTERS = json_load(char_file)
with open(
    "../char_results/" + RECENT_PHASE_PF + "/appearance_combine.json",
) as app_char_file:
    APP = json_load(app_char_file)
with open(
    "../char_results/" + RECENT_PHASE_PF + "/rounds_combine.json",
) as round_char_file:
    ROUND = json_load(round_char_file)
for char, char_stat in stats.items():
    for i in chain(range(10, 18), range(19, 27)):
        stats[char].stats_write[statkeys[i]] = round(
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
            stats[char].stats_write[value] = round(
                float(char_stat.stats_write[value]) * 100,
                2,
            )
        else:
            stats[char].stats_write[value] = 0.00

    stats[char].name = char_stat.name.replace(" ", "-").lower()
    if char_stat.name in slug:
        stats[char].name = slug[char_stat.name]
    if char_stat.name == CHARACTERS[iter_char]["char"]:
        del stats[char].name
    else:
        print(char_stat.name)
        print(CHARACTERS[iter_char]["char"])
        sys_exit()

    temp_stats.append(CHARACTERS[iter_char] | char_stat.stats_write)
    iter_char += 1

if not path.exists("../char_results/" + RECENT_PHASE_PF):
    mkdir("../char_results/" + RECENT_PHASE_PF)

with open("../char_results/" + RECENT_PHASE_PF + "/all2.json", "w") as char_file:
    char_file.write(json_dumps(temp_stats, indent=2))

print("Average AR: ", (ar / count))
