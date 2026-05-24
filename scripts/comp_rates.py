"""Compile all HSR data."""

# pyright: reportUnknownVariableType=false, reportMissingTypeStubs=false

from csv import reader as csvreader
from csv import writer as csvwriter
from itertools import permutations
from json import dumps
from os import path
from statistics import mean
from sys import exit as sys_exit
from time import time

import char_usage as cu
from comp_rates_config import (
    BASE_RESULT_PATH,
    CHAR_RESULT_PATH,
    CHARS_INFO,
    COMP_RESULT_PATH,
    F2P_ONLY,
    WHALE_ONLY,
    aa_mode,
    app_rate_threshold,
    app_rate_threshold_round,
    char_app_rate_threshold,
    char_infographics,
    duo_dict_len,
    moc_mode,
    pf_filename,
    pf_mode,
    run_commands,
    slug_with_prefix,
)
from composition import Composition, Stage
from csv_to_pickle import PickleData, load_pickle_data
from line_profiler import profile
from player_phase import PlayerPhase
from scipy.stats import skew, trim_mean

loaded_data: PickleData = load_pickle_data("../data/pickle/data" + pf_filename + ".pkl")

all_players: dict[str, PlayerPhase] = loaded_data.all_players
all_comps: list[Composition] = loaded_data.all_comps
avg_round_stage: dict[int, list[int]] = loaded_data.avg_round_stage
sample_size: dict[int | str, dict[str, int | float]] = loaded_data.sample_size

if path.isfile("../../uids.csv"):
    with open("../../uids.csv", encoding="UTF8") as f:
        reader = csvreader(f, delimiter=",")
        self_uids = set(next(iter(reader)))
    with open("../../random.csv", encoding="UTF8") as f:
        reader = csvreader(f, delimiter=",")
        random_uids = set(next(iter(reader)))
    with open("../../collect/collected_stardb.csv", encoding="UTF8") as f:
        reader = csvreader(f, delimiter=",")
        star_db_uids = {item for sublist in list(reader) for item in sublist}
    with open("../../collect/collected_hoyobuddy.csv", encoding="UTF8") as f:
        reader = csvreader(f, delimiter=",")
        hoyobuddy_uids = {item for sublist in list(reader) for item in sublist}
else:
    self_uids = set[str]()
    random_uids = set[str]()
    star_db_uids = set[str]()
    hoyobuddy_uids = set[str]()


@profile
def main() -> None:
    """Compile data."""
    start_time = time()
    print("start")

    if pf_mode:
        three_stages = ["4-1", "4-2"]
        three_double_stages = [["4-1", "4-2"]]
        one_stage = ["4-1", "4-2"]
        all_stages = ["4-1", "4-2"]
    elif aa_mode:
        three_stages = ["1-1", "1-2", "1-3", "2-1"]
        three_double_stages = [["1-1", "1-2", "1-3"], ["2-1"]]
        one_stage = ["1-1", "1-2", "1-3"]
        all_stages = ["1-1", "1-2", "1-3", "2-1"]
    else:
        three_stages = ["12-1", "12-2"]
        three_double_stages = [["12-1", "12-2"]]
        one_stage = ["12-1", "12-2"]
        all_stages = ["12-1", "12-2"]

    if "Char usages all stages" in run_commands:
        char_usages(
            all_stages,
            filename="all",
        )
        cur_time = time()
        print("done char:", round(cur_time - start_time, 2), "s")
        start_time = cur_time

    if "Duos check" in run_commands:
        usage = char_usages(
            three_stages,
            filename="all",
        )
        duo_usages(
            usage,
            three_stages,
            check_duo=True,
        )

    if "Char usages 8 - 10" in run_commands:
        usage = char_usages(
            one_stage,
            filename="all",
        )
        if not F2P_ONLY:
            duo_usages(
                usage,
                one_stage,
                check_duo=False,
            )
        cur_time = time()
        print("done char 8 - 10:", round(cur_time - start_time, 2), "s")
        start_time = cur_time

        if "Char usages for each stage" in run_commands and aa_mode:
            char_chambers: dict[str, dict[str, cu.CharUsageData]] = {
                "all": usage.copy(),
            }
            for room in three_stages:
                char_chambers[room] = char_usages(
                    [room],
                    filename=room,
                )
            cur_time = time()
            print("done char stage:", round(cur_time - start_time, 2), "s")
            start_time = cur_time

        if "Char usages for each stage (combined)" in run_commands:
            char_chambers: dict[str, dict[str, cu.CharUsageData]] = {
                "all": usage.copy(),
            }
            # for room in all_double_stages:
            for room in three_double_stages:
                char_chambers[room[0]] = char_usages(
                    room,
                    filename=room[0].split("-")[0],
                )
            cur_time = time()
            print("done char stage (combine):", round(cur_time - start_time, 2), "s")
            start_time = cur_time

    if "Comp usage all stages" in run_commands:
        comp_usages(
            all_stages,
            filename="all",
            floor=True,
        )
        cur_time = time()
        print("done comp all:", round(cur_time - start_time, 2), "s")
        start_time = cur_time

    if "Comp usage 8 - 10" in run_commands:
        comp_usages(
            one_stage,
            filename="top",
            floor=True,
        )
        cur_time = time()
        print("done comp 8 - 10:", round(cur_time - start_time, 2), "s")
        start_time = cur_time

    if "Comp usages for each stage" in run_commands:
        for room in three_stages:
            comp_usages(
                [room],
                filename=room,
                offset=2,
            )

        if not WHALE_ONLY and not F2P_ONLY:
            with open(f"../{BASE_RESULT_PATH}/demographic.json", "w") as out_file:
                out_file.write(dumps(sample_size, indent=2))
        cur_time = time()
        print("done comp stage:", round(cur_time - start_time, 2), "s")
        start_time = cur_time

    if "Character specific infographics" in run_commands:
        comp_usages(
            one_stage,
            filename=char_infographics,
            info_char=True,
            floor=True,
        )
        cur_time = time()
        print("done char infographics:", round(cur_time - start_time, 2), "s")
        start_time = cur_time


@profile
def comp_usages(
    rooms: list[str],
    filename: str = "comp_usages",
    offset: int = 1,
    *,
    info_char: bool = False,
    floor: bool = False,
) -> None:
    """Comp usage."""
    global top_comps_app
    top_comps_app = {}
    comps_dict: list[dict[tuple[str, ...], CompUsage]] = used_comps(
        rooms,
        filename,
    )
    rank_usages(comps_dict, rooms, owns_offset=offset)
    comp_usages_write(comps_dict, filename, floor, info_char=info_char, sort_app=True)
    comp_usages_write(comps_dict, filename, floor, info_char=info_char, sort_app=False)


class CompUsage(Composition):
    """Comp usage class."""

    def __init__(self, comp: Composition) -> None:
        """Comp usage constructor."""
        self.__dict__.update(comp.__dict__)
        del self.player
        self.uses = 0
        self.owns = 0
        self.round_num_dict = {i: list[int]() for i in range(1, 13)}
        self.whale_count = set[str]()
        self.players = set[str]()
        self.is_count_round: bool
        self.app_rate: float
        self.round: float
        self.usage_rate: float
        self.own_rate: float
        self.app_rank: int


@profile
def used_comps(
    rooms: list[str],
    filename: str,
) -> dict[tuple[str, ...], CompUsage]:
    """Return the dictionary of all the comps used and how many times they were used."""
    comps_dict: dict[tuple[str, ...], CompUsage] = {}
    global total_comps
    total_comps = 0
    total_self_comps = 0
    total_random_comps = 0
    total_star_db_comps = 0
    total_hoyobuddy_comps = 0
    whale_count = 0
    f2p_count = 0

    for comp in all_comps:
        invalid_clear = True
        if (
            aa_mode
            and (
                (2 < comp.round_num <= 4 and comp.star_num == 2)
                or (comp.round_num > 4 and comp.star_num == 1)
            )
        ) or (comp.star_num == 3):
            invalid_clear = False

        # Check if the comp is used in the rooms that are being checked
        if str(comp.room) not in rooms or invalid_clear:
            continue

        side_comp = None
        if moc_mode:
            side_chamber = Stage(comp.room.stage, 2 if comp.room.node == 1 else 1)
            side_comp = all_players[comp.player].chambers[side_chamber]

        comp_tuple = tuple(comp.characters)

        total_comps += 1
        if comp.player in self_uids:
            total_self_comps += 1
        if comp.player in random_uids:
            total_random_comps += 1
        if comp.player in star_db_uids:
            total_star_db_comps += 1
        if comp.player in hoyobuddy_uids:
            total_hoyobuddy_comps += 1
        if len(comp_tuple) < 4:
            continue
        if side_comp and len(side_comp.characters) < 4:
            continue

        whale_comp = False
        giga_whale = False
        f2p_comp = True
        sustain_count = 0
        for char in range(4):
            comp_char = comp_tuple[char]
            char_cons = None

            if comp.char_cons:
                char_cons = comp.char_cons[comp_char]
            elif comp_char in all_players[comp.player].owned:
                char_cons = all_players[comp.player].owned[comp_char].cons

            if (
                CHARS_INFO[comp_char].availability == "Limited 5*"
                and char_cons is not None
                and char_cons > 0
            ):
                whale_comp = True
                if char_cons > 2:
                    giga_whale = True
            if "sustain" in CHARS_INFO[comp_char].role:
                sustain_count += 1

        if side_comp:
            for char in side_comp.characters:
                char_cons = None

                if side_comp.char_cons:
                    char_cons = side_comp.char_cons[char]
                elif char in all_players[side_comp.player].owned:
                    char_cons = all_players[side_comp.player].owned[char].cons

                if (
                    CHARS_INFO[char].availability == "Limited 5*"
                    and char_cons is not None
                    and char_cons > 0
                ):
                    whale_comp = True
                    if char_cons > 2:
                        giga_whale = True

        if whale_comp:
            whale_count += 1
        if f2p_comp:
            f2p_count += 1
        if (
            (WHALE_ONLY and not whale_comp)
            or (F2P_ONLY and (not f2p_comp or whale_comp))
            or giga_whale
            or comp.is_hard_mode  # Anomaly arbitration plight
        ):
            continue

        if comp_tuple not in comps_dict:
            comps_dict[comp_tuple] = CompUsage(comp)

        comp_data = comps_dict[comp_tuple]
        comp_data.uses += 1
        comp_data.players.add(comp.player)

        if whale_comp:
            comp_data.whale_count.add(comp.player)
        if whale_comp == WHALE_ONLY and (not F2P_ONLY or f2p_comp):
            cur_room = comp.room.stage
            comp_data.round_num_dict[cur_room].append(comp.round_num)
            if sustain_count <= 1:
                avg_round_stage[cur_room].append(comp.round_num)
                if (pf_mode or (aa_mode and cur_room == 2)) and comp.buff:
                    if "buff_" + comp.buff not in sample_size[cur_room]:
                        sample_size[cur_room]["buff_" + comp.buff] = 0
                    sample_size[cur_room]["buff_" + comp.buff] += 1

        # Set the current comp to the temporary variable
        comps_dict[comp_tuple] = comp_data

    for stage, stage_value in avg_round_stage.items():
        sample_size[stage]["avg_round"] = round(
            mean(stage_value or [0]),
            2,
        )

    if "-" in filename:
        chamber_num = Stage.from_string(filename)
        if chamber_num.node == 1:
            sample_size[chamber_num.stage]["total"] = total_comps
            sample_size[chamber_num.stage]["prydwen"] = total_self_comps
            sample_size[chamber_num.stage]["random"] = total_random_comps
            sample_size[chamber_num.stage]["stardb"] = total_star_db_comps
            sample_size[chamber_num.stage]["hoyobuddy"] = total_hoyobuddy_comps
    return comps_dict


@profile
def rank_usages(
    comps_dict: dict[tuple[str, ...], CompUsage],
    rooms: list[str],
    owns_offset: int = 1,
) -> None:
    """Calculate the usage rate and sort the comps according to it."""
    rates: list[float] = []
    for comp, cur_comp in comps_dict.items():
        avg_round: list[float] = []
        uses_room: dict[int, int] = {}
        # Make temporary variable for the current comp

        for room_num in range(1, 13):
            cur_round = cur_comp.round_num_dict[room_num]
            if cur_round:
                uses_room[room_num] = len(cur_round)
                if cur_comp.uses > 10:
                    skewness = skew(
                        cur_round,
                        axis=0,
                        bias=True,
                    )
                    if abs(skewness) > 0.8:
                        avg_round.append(
                            trim_mean(
                                cur_round,
                                0.25,
                            ),
                        )
                    else:
                        avg_round.append(mean(cur_round))
                else:
                    avg_round.append(mean(cur_round))

        comp_threshold = 10 if cur_comp.healer else 50
        cur_comp.is_count_round = True
        if (
            (rooms == ["12-1", "12-2"])
            or (pf_mode and rooms == ["4-1", "4-2"])
            or (aa_mode and rooms == ["1-1", "2-1", "3-1"])
        ):
            for uses_room_num in uses_room.values():
                if uses_room_num < comp_threshold:
                    cur_comp.is_count_round = False
        elif len(rooms) == 1 and cur_comp.uses < comp_threshold:
            cur_comp.is_count_round = False

        rounded_avg_round: float
        if avg_round:
            rounded_avg_round = round(mean(avg_round), 0 if pf_mode else 2)
        else:
            rounded_avg_round = 0 if pf_mode else 99.99

        app = (
            int(100.0 * cur_comp.uses / (total_comps * owns_offset) * 200 + 0.5) / 100.0
        )
        cur_comp.app_rate = app
        cur_comp.round = rounded_avg_round
        cur_comp.usage_rate = 0
        cur_comp.own_rate = 0
        rates.append(app)

        # Set the current comp to the temporary variable
        comps_dict[comp] = cur_comp

    rates.sort(reverse=True)
    for comp, cur_comp in comps_dict.items():
        comps_dict[comp].app_rank = rates.index(cur_comp.app_rate) + 1


@profile
def duo_usages(
    usage: dict[str, cu.CharUsageData],
    rooms: list[str],
    *,
    check_duo: bool = False,
) -> None:
    """Calculate duo usage."""
    duos_dict: dict[str, dict[str, cu.RoundApp]] = used_duos(
        all_comps,
        rooms,
        usage,
        check_duo=check_duo,
    )
    duo_write(duos_dict, usage, "duo_usages", check_duo=check_duo)


@profile
def used_duos(
    comps: list[Composition],
    rooms: list[str],
    usage: dict[str, cu.CharUsageData],
    *,
    check_duo: bool,
) -> dict[str, dict[str, cu.RoundApp]]:
    """Return dictionary of all the duos used and how many times they were used."""
    duos_dict: dict[tuple[str, str], cu.RoundApp] = {}

    for comp in comps:
        invalid_clear = True
        if (
            aa_mode
            and (
                (2 < comp.round_num <= 4 and comp.star_num == 2)
                or (comp.round_num > 4 and comp.star_num == 1)
            )
        ) or (comp.star_num == 3):
            invalid_clear = False

        cur_room = comp.room.stage
        if len(comp.characters) < 2 or str(comp.room) not in rooms or invalid_clear:
            continue

        whale_comp = False
        giga_whale = False
        sustain_count = 0
        for char in comp.characters:
            char_cons = None
            if comp.char_cons:
                char_cons = comp.char_cons[char]
            elif char in all_players[comp.player].owned:
                char_cons = all_players[comp.player].owned[char].cons

            if (
                CHARS_INFO[char].availability == "Limited 5*"
                and char_cons is not None
                and char_cons > 0
            ):
                whale_comp = True
                if char_cons > 2:
                    giga_whale = True
            if "sustain" in CHARS_INFO[char].role:
                sustain_count += 1

        side_comp = None
        if moc_mode:
            side_chamber = Stage(comp.room.stage, 2 if comp.room.node == 1 else 1)
            side_comp = all_players[comp.player].chambers[side_chamber]

        if side_comp:
            for char in side_comp.characters:
                char_cons = None
                if side_comp.char_cons:
                    char_cons = side_comp.char_cons[char]
                elif char in all_players[side_comp.player].owned:
                    char_cons = all_players[side_comp.player].owned[char].cons

                if (
                    CHARS_INFO[char].availability == "Limited 5*"
                    and char_cons is not None
                    and char_cons > 0
                ):
                    whale_comp = True
                    if char_cons > 2:
                        giga_whale = True

        if (
            (WHALE_ONLY and not whale_comp)
            or (F2P_ONLY and whale_comp)
            or giga_whale
            or comp.is_hard_mode
        ):
            continue

        duos = list(permutations(comp.characters, 2))
        for duo in duos:
            is_triple_dps = False

            if duo not in duos_dict:
                duos_dict[duo] = cu.RoundApp()
            duos_dict[duo].app_flat += 1

            if is_triple_dps and check_duo:
                continue
            if (whale_comp == WHALE_ONLY) and sustain_count <= 1:
                duos_dict[duo].round_list[cur_room].append(comp.round_num)

    sorted_duos = sorted(duos_dict.items(), key=lambda t: t[1].app_flat, reverse=True)
    duos_dict = dict(sorted_duos)

    return_duos: dict[str, dict[str, cu.RoundApp]] = {}
    for duo in duos_dict:
        cur_duo = duos_dict[duo]
        if usage[duo[0]].app_flat > 0:
            # Calculate the appearance rate of the duo by dividing the appearance count
            # of the duo with the appearance count of the first character
            cur_duo.app = round(cur_duo.app_flat * 100 / usage[duo[0]].app_flat, 2)
            cur_duo.app_flat = 0
            avg_round: list[float] = []
            for room_num in range(1, 13):
                duo_round = cur_duo.round_list[room_num]
                if duo_round:
                    cur_duo.app_flat += len(duo_round)
                    if len(duo_round) > 1:
                        skewness = skew(
                            duo_round,
                            axis=0,
                            bias=True,
                        )
                        if abs(skewness) > 0.8:
                            avg_round.append(trim_mean(duo_round, 0.25))
                        else:
                            avg_round.append(mean(duo_round))
                    else:
                        avg_round.append(mean(duo_round))
            if avg_round:
                cur_duo.round = round(mean(avg_round), 0 if pf_mode else 2)
            else:
                cur_duo.round = 0 if pf_mode else 99.99
            if duo[0] not in return_duos:
                return_duos[duo[0]] = {}
            return_duos[duo[0]][duo[1]] = cur_duo

    return return_duos


@profile
def char_usages(
    rooms: list[str],
    filename: str = "char_usages",
) -> dict[str, cu.CharUsageData]:
    """Calculate character usage."""
    app: dict[str, cu.CharApp] = cu.appearances(
        all_players,
        chambers=rooms,
        info_char=False,
    )
    chars_dict: dict[str, cu.CharUsageData] = cu.usages(app, chambers=rooms)
    if (
        (moc_mode and rooms == ["12-1", "12-2"] and filename != "12")
        or (pf_mode and rooms == ["4-1", "4-2"] and filename != "4")
        or (aa_mode and filename not in ["1", "2"])
    ):
        char_usages_write(chars_dict, filename)
    return chars_dict


@profile
def comp_usages_write(
    comps_dict: dict[tuple[str, ...], CompUsage],
    filename: str,
    floor: int,
    *,
    info_char: bool,
    sort_app: bool,
) -> None:
    """Write comp usage."""
    out_json: list[dict[str, str | float]] = []
    out_comps: list[dict[str, str | int]] = []
    outvar_comps: list[dict[str, str | int]] = []
    var_comps: list[dict[str, str | int]] = []
    variations: dict[str, int] = {}
    thres = app_rate_threshold if sort_app else app_rate_threshold_round

    # Sort the comps according to their usage rate

    comps_dict = dict(
        sorted(
            comps_dict.items(),
            key=lambda t: t[1].app_rate if sort_app else t[1].round,
            reverse=pf_mode or sort_app,
        ),
    )
    comp_names: list[str] = []
    dual_comp_names: list[str] = []

    for comp in comps_dict:
        if info_char and filename not in comp:
            continue
        cur_comp = comps_dict[comp]
        comp_name = cur_comp.comp_name
        # Only one variation of each comp name is included,
        # unless if it's used for a character's infographic
        if (
            (
                comp_name not in comp_names
                and comp_name not in dual_comp_names
                and cur_comp.round not in {99.99, 0}
            )
            or comp_name == "-"
            or info_char
        ):
            if sort_app:
                top_comps_app[comp_name] = cur_comp.app_rate
            elif (
                comp_name in top_comps_app
                and cur_comp.is_count_round
                and cur_comp.app_rate < top_comps_app[comp_name] / 5
            ):
                continue
            if cur_comp.is_count_round and (
                cur_comp.app_rate >= thres
                or (info_char and cur_comp.app_rate > char_app_rate_threshold)
            ):
                temp_comp_name = comp_name

                out_comps_append: dict[str, str | int] = {
                    "comp_name": temp_comp_name,
                    "char_1": comp[0],
                    "char_2": comp[1],
                    "char_3": comp[2],
                    "char_4": comp[3],
                    "app_rate": str(cur_comp.app_rate) + "%",
                    "avg_round": str(cur_comp.round),
                }

                if info_char:
                    if comp_name not in comp_names:
                        variations[comp_name] = 1
                        out_comps_append["variation"] = variations[comp_name]
                    else:
                        variations[comp_name] += 1
                        out_comps_append["variation"] = variations[comp_name]

                out_comps_append["whale_count"] = str(len(cur_comp.whale_count))
                out_comps_append["app_flat"] = str(len(cur_comp.players))
                out_comps_append["uses"] = str(cur_comp.uses)

                if info_char:
                    if comp_name not in comp_names:
                        out_comps.append(out_comps_append)
                    else:
                        var_comps.append(out_comps_append)
                else:
                    out_comps.append(out_comps_append)

                if comp_name != "-":
                    comp_names.append(comp_name)

        elif comp_name in comp_names:
            temp_comp_name = comp_name
            outvar_comps_append: dict[str, str | int] = {
                "comp_name": temp_comp_name,
                "char_1": comp[0],
                "char_2": comp[1],
                "char_3": comp[2],
                "char_4": comp[3],
            }
            outvar_comps_append["app_rate"] = str(cur_comp.app_rate) + "%"
            outvar_comps_append["avg_round"] = str(cur_comp.round)
            outvar_comps.append(outvar_comps_append)
        if not info_char:
            out = list(comp)
            for i in range(4):
                out[i] = CHARS_INFO[out[i]].slug
            out_json_dict: dict[str, str | float] = {
                "char_one": out[0],
                "char_two": out[1],
                "char_three": out[2],
                "char_four": out[3],
            }
            out_json_dict["app_rate"] = cur_comp.app_rate
            out_json_dict["rank"] = cur_comp.app_rank
            out_json_dict["avg_round"] = cur_comp.round
            out_json.append(out_json_dict)

    if info_char:
        out_comps += var_comps

    if not (sort_app):
        filename = filename + "_rounds"

    if WHALE_ONLY:
        filename = filename + "_C1"
    elif F2P_ONLY:
        filename = filename + "_E0S0"

    if floor:
        with open(
            f"../{COMP_RESULT_PATH}/comps_usage_{filename}.csv",
            "w",
            newline="",
        ) as f:
            csv_writer = csvwriter(f)
            for comps in out_comps:
                csv_writer.writerow(comps.values())

    if not info_char and sort_app:
        with open(
            f"../{COMP_RESULT_PATH}/{filename}.json",
            "w",
        ) as out_file:
            out_file.write(dumps(out_json, indent=2))


@profile
def duo_write(
    duos_dict: dict[str, dict[str, cu.RoundApp]],
    usage: dict[str, cu.CharUsageData],
    filename: str,
    *,
    check_duo: bool,
) -> None:
    """Write duo usage."""
    out_duos: list[dict[str, str | float]] = []
    for char, char_duo in duos_dict.items():
        duo_keys = list(char_duo.keys())
        if usage[char].app_flat > 0:
            out_duos_append = {
                "char": char,
                "app": usage[char].app,
            }
            for i in range(duo_dict_len):
                j = str(i + 1)
                if i < len(char_duo):
                    duo_char = char_duo[duo_keys[i]]
                    out_duos_append["char_" + j] = duo_keys[i]
                    out_duos_append["app_rate_" + j] = str(duo_char.app) + "%"
                    out_duos_append["avg_round_" + j] = duo_char.round
                    out_duos_append["app_flat_" + j] = duo_char.app_flat
                else:
                    out_duos_append["char_" + j] = "-"
                    out_duos_append["app_rate_" + j] = "0.00%"
                    out_duos_append["avg_round_" + j] = 0.00
                    out_duos_append["app_flat_" + j] = 0
            out_duos.append(out_duos_append)
    out_duos = sorted(out_duos, key=lambda t: t["app"], reverse=True)

    if WHALE_ONLY:
        filename = filename + "_C1"
    elif F2P_ONLY:
        filename = filename + "_E0S0"

    with open(f"../{BASE_RESULT_PATH}/duos/{filename}.csv", "w", newline="") as f:
        csv_writer = csvwriter(f)
        count = 0
        out_duos_check: dict[str, dict[str, dict[str, str | float]]] = {}
        out_duos_exclu: dict[str, dict[str, dict[str, str | float]]] = {}
        for duos in out_duos:
            duo_char = str(duos["char"])
            out_duos_check[duo_char] = {}
            out_duos_exclu[duo_char] = {}
            if count == 0:
                temp_duos = ["char", "app"]
                for i in range(10):
                    temp_duos += [
                        "char_" + str(i + 1),
                        "app_rate_" + str(i + 1),
                        "avg_round_" + str(i + 1),
                    ]
                csv_writer.writerow(temp_duos)
                count += 1
            temp_duos = [
                duo_char,
                duos["app"],
            ]
            for i in range(10):
                temp_duos += [
                    duos["char_" + str(i + 1)],
                    duos["app_rate_" + str(i + 1)],
                    duos["avg_round_" + str(i + 1)],
                ]
            csv_writer.writerow(temp_duos)

            if check_duo:
                for i in range(duo_dict_len):
                    j = str(i + 1)
                    duo_app_j = float(str(duos["app_rate_" + j])[:-1])
                    duo_round_j = float(duos["avg_round_" + j])
                    duo_j = str(duos["char_" + j])
                    if (
                        duo_app_j >= 1
                        and float(duos["app_flat_" + j]) >= 10
                        and (
                            (duo_round_j < usage[duo_j].round)
                            or (duo_round_j < usage[str(duo_char)].round)
                        )
                        and usage[duo_j].round != 99.99
                        and usage[duo_j].round != 0
                    ):
                        out_duos_check[duo_char][duo_j] = {
                            "app": duo_app_j,
                            "avg_round": duo_round_j,
                        }
    if check_duo:
        char_names = list(CHARS_INFO.keys())
        out_dd: dict[frozenset[str], dict[str, str | float]] = {}
        out_dd_list: list[list[str]] = []
        for char_i in char_names:
            for char_j in char_names:
                is_char_i_dps = "dps" in CHARS_INFO[char_i].role
                is_char_j_dps = "dps" in CHARS_INFO[char_j].role
                if is_char_i_dps and is_char_j_dps:
                    if char_j not in out_duos_check:
                        continue
                    if char_i not in out_duos_check:
                        continue
                    if char_i in out_duos_check[char_j]:
                        out_dd_list.append([char_j, char_i])
                        out_i_j = out_duos_check[char_i][char_j]
                        out_j_i = out_duos_check[char_j][char_i]
                        if char_j in out_duos_check[char_i]:
                            out_dd[frozenset([char_i, char_j])] = {
                                "char_i": char_i,
                                "char_i_app": str(out_i_j["app"]),
                                "char_j": char_j,
                                "char_j_app": str(out_j_i["app"]),
                                "avg_round": str(out_i_j["avg_round"]),
                            }
                        elif char_j in out_duos_exclu[char_i]:
                            out_exc = out_duos_exclu[char_i][char_j]
                            out_dd[frozenset([char_i, char_j])] = {
                                "char_i": char_i,
                                "char_i_app": str(out_exc["app"]),
                                "char_j": char_j,
                                "char_j_app": str(out_j_i["app"]),
                                "avg_round": str(out_exc["avg_round"]),
                            }

        sorted_out_dd = sorted(
            out_dd.items(),
            key=lambda t: t[1]["char_i"],
            reverse=True,
        )
        out_dd = dict(sorted_out_dd)

        with open(f"../{BASE_RESULT_PATH}/duos/duo_check.csv", "w", newline="") as f:
            csv_writer = csvwriter(f)
            for out_dd_print in out_dd_list:
                csv_writer.writerow(out_dd_print)
        for out_dd_print in out_dd:
            print(
                str(out_dd[out_dd_print]["char_i"])
                + ", "
                + str(out_dd[out_dd_print]["char_i_app"])
                + ", "
                + str(out_dd[out_dd_print]["char_j"])
                + ", "
                + str(out_dd[out_dd_print]["char_j_app"])
                + ", "
                + str(out_dd[out_dd_print]["avg_round"]),
            )
        sys_exit()

    for i in range(len(out_duos)):
        for duo_value in ["char"] + [f"char_{i}" for i in range(1, 31)]:
            if out_duos[i][duo_value] in CHARS_INFO:
                out_duos[i][duo_value] = CHARS_INFO[str(out_duos[i][duo_value])].slug
    with open(f"../{BASE_RESULT_PATH}/duos/{filename}.json", "w") as out_file:
        out_file.write(dumps(out_duos, indent=2))


@profile
def char_usages_write(
    chars_dict: dict[str, cu.CharUsageData],
    filename: str,
) -> None:
    """Write character usage."""
    out_chars: list[dict[str, str | int | float]] = []
    out_chars_csv: list[dict[str, str | int | float]] = []
    weap_len = 10
    arti_len = 10
    planar_len = 5
    chars_dict = dict(sorted(chars_dict.items(), key=lambda t: t[1].app, reverse=True))
    for char, cur_char in chars_dict.items():
        out_chars_append: dict[str, str | int | float] = {
            "char": char,
            "app_rate": str(cur_char.app) + "%",
            "app_rate_e0": str(cur_char.app_exclude) + "%",
            "avg_round": str(cur_char.round),
            "std_dev_round": str(cur_char.std_dev_round),
            "q1_round": str(cur_char.q1_round),
            "role": cur_char.role[0],
            "rarity": cur_char.rarity,
        }
        for i in ["app_rate", "app_rate_e0"]:
            if out_chars_append[i] == "-%":
                out_chars_append[i] = "-"
        if list(cur_char.weapons):
            for i in range(weap_len):
                j = str(i + 1)
                if i < len(list(cur_char.weapons)):
                    cur_weap = list(cur_char.weapons.values())
                    out_chars_append["weapon_" + j] = list(cur_char.weapons)[i]
                    out_chars_append["weapon_" + j + "_app"] = (
                        str(cur_weap[i].app) + "%"
                    )
                    out_chars_append["weapon_" + j + "_round"] = str(cur_weap[i].round)
                else:
                    out_chars_append["weapon_" + j] = ""
                    out_chars_append["weapon_" + j + "_app"] = "0.0"
                    out_chars_append["weapon_" + j + "_round"] = (
                        "0.0" if pf_mode else "99.99"
                    )
            for i in range(arti_len):
                j = str(i + 1)
                if i < len(list(cur_char.artifacts)):
                    arti_name = list(cur_char.artifacts)[i]
                    out_chars_append["artifact_" + j] = arti_name
                    arti_name = (
                        arti_name.replace("Watchmaker,", "Watchmaker")
                        .replace("Sigonia,", "Sigonia")
                        .replace("Duran,", "Duran")
                        .split(", ")
                    )
                    out_chars_append["artifact_" + j + "_1"] = (
                        arti_name[0]
                        .replace("Watchmaker", "Watchmaker,")
                        .replace("Sigonia", "Sigonia,")
                        .replace("Duran", "Duran,")
                    )
                    if len(arti_name) > 1:
                        out_chars_append["artifact_" + j + "_2"] = (
                            arti_name[1]
                            .replace("Watchmaker", "Watchmaker,")
                            .replace("Sigonia", "Sigonia,")
                            .replace("Duran", "Duran,")
                        )
                    else:
                        out_chars_append["artifact_" + j + "_2"] = ""
                    cur_arti = list(cur_char.artifacts.values())
                    out_chars_append["artifact_" + j + "_app"] = (
                        str(cur_arti[i].app) + "%"
                    )
                    out_chars_append["artifact_" + j + "_round"] = str(
                        cur_arti[i].round,
                    )
                else:
                    out_chars_append["artifact_" + j] = ""
                    out_chars_append["artifact_" + j + "_1"] = ""
                    out_chars_append["artifact_" + j + "_2"] = ""
                    out_chars_append["artifact_" + j + "_app"] = "0.0"
                    out_chars_append["artifact_" + j + "_round"] = (
                        "0.0" if pf_mode else "99.99"
                    )
            for i in range(planar_len):
                j = str(i + 1)
                if i < len(list(cur_char.planars)):
                    cur_planar = list(cur_char.planars.values())
                    out_chars_append["planar_" + j] = list(cur_char.planars)[i]
                    out_chars_append["planar_" + j + "_app"] = (
                        str(cur_planar[i].app) + "%"
                    )
                    out_chars_append["planar_" + j + "_round"] = str(
                        cur_planar[i].round,
                    )
                else:
                    out_chars_append["planar_" + j] = ""
                    out_chars_append["planar_" + j + "_app"] = "0.0"
                    out_chars_append["planar_" + j + "_round"] = (
                        "0.0" if pf_mode else "99.99"
                    )
            for i in range(7):
                out_chars_append["app_" + str(i)] = (
                    str(next(iter(list(cur_char.cons_usage.values())[i].values())))
                    + "%"
                )
                out_chars_append["round_" + str(i)] = str(
                    list(list(cur_char.cons_usage.values())[i].values())[3],
                )
                if out_chars_append["app_" + str(i)] == "-%":
                    out_chars_append["app_" + str(i)] = "-"
        else:
            for i in range(weap_len):
                j = str(i + 1)
                out_chars_append["weapon_" + j] = ""
                out_chars_append["weapon_" + j + "_app"] = "0.0"
                out_chars_append["weapon_" + j + "_round"] = (
                    "0.0" if pf_mode else "99.99"
                )
            for i in range(arti_len):
                j = str(i + 1)
                out_chars_append["artifact_" + j] = ""
                out_chars_append["artifact_" + j + "_1"] = ""
                out_chars_append["artifact_" + j + "_2"] = ""
                out_chars_append["artifact_" + j + "_app"] = "0.0"
                out_chars_append["artifact_" + j + "_round"] = (
                    "0.0" if pf_mode else "99.99"
                )
            for i in range(planar_len):
                j = str(i + 1)
                out_chars_append["planar_" + j] = ""
                out_chars_append["planar_" + j + "_app"] = "0.0"
                out_chars_append["planar_" + j + "_round"] = (
                    "0.0" if pf_mode else "99.99"
                )
            for i in range(7):
                out_chars_append["app_" + str(i)] = "0.0%"
                out_chars_append["round_" + str(i)] = "0.0" if pf_mode else "99.99"
        out_chars_append["cons_avg"] = cur_char.cons_avg
        out_chars_append["sample"] = cur_char.sample
        out_chars_append["sample_app_flat"] = cur_char.sample_app_flat
        out_chars.append(out_chars_append)
        out_chars_csv.append(out_chars_append.copy())
        if char == filename:
            break

    if WHALE_ONLY:
        filename = filename + "_C1"
    elif F2P_ONLY:
        filename = filename + "_E0S0"

    iterate_value_app = ["app_rate", "app_rate_e0"]
    iterate_value_round = ["avg_round", "std_dev_round", "q1_round"]
    iterate_name_arti: list[str] = []
    for i in range(weap_len):
        j = str(i + 1)
        iterate_value_app.append("weapon_" + j + "_app")
        iterate_value_round.append("weapon_" + j + "_round")
    for i in range(arti_len):
        j = str(i + 1)
        iterate_value_app.append("artifact_" + j + "_app")
        iterate_value_round.append("artifact_" + j + "_round")
    for i in range(planar_len):
        j = str(i + 1)
        iterate_value_app.append("planar_" + j + "_app")
        iterate_value_round.append("planar_" + j + "_round")
    for i in range(7):
        j = str(i + 1)
        iterate_value_app.append("app_" + str(i))
        iterate_value_round.append("round_" + str(i))

    for i in range(len(out_chars)):
        # for i in range(7):
        out_chars[i]["char"] = slug_with_prefix(str(out_chars[i]["char"]))
        for value in iterate_value_app:
            if (
                str(out_chars[i][value])[:-1]
                .replace(".", "")
                .replace("-", "")
                .isnumeric()
            ):
                out_chars[i][value] = float(str(out_chars[i][value])[:-1])
            else:
                out_chars[i][value] = 0.00
        for value in iterate_value_round:
            if str(out_chars[i][value]).replace(".", "").replace("-", "").isnumeric():
                out_chars[i][value] = (
                    round(float(out_chars[i][value]))
                    if pf_mode
                    else float(out_chars[i][value])
                )
            else:
                out_chars[i][value] = 0 if pf_mode else 99.99
        for value in iterate_name_arti:
            if out_chars[i][value]:
                out_chars[i][value] = (
                    str(out_chars[i][value]).replace(".", "").replace("-", "")
                )
            else:
                out_chars[i][value] = 0 if pf_mode else 99.99
    with open(f"../{CHAR_RESULT_PATH}/{filename}.json", "w") as out_file:
        out_file.write(dumps(out_chars, indent=2))

    if filename.startswith("all"):
        with open(f"../{CHAR_RESULT_PATH}/{filename}.csv", "w", newline="") as f:
            csv_writer = csvwriter(f)
            count = 0
            for chars in out_chars_csv:
                if count == 0:
                    header = chars.keys()
                    csv_writer.writerow(header)
                    count += 1
                csv_writer.writerow(chars.values())


if __name__ == "__main__":
    main()
