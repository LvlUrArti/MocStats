from csv import reader as csvreader
from csv import writer as csvwriter
from itertools import permutations
from json import dumps
from os import makedirs, path
from statistics import mean
from time import sleep, time

import char_usage as cu
from comp_rates_config import (
    CHARACTERS,
    RECENT_PHASE,
    alt_comps,
    app_rate_threshold,
    app_rate_threshold_round,
    archetype,
    as_mode,
    char_app_rate_threshold,
    char_infographics,
    duo_dict_len,
    f2pOnly,
    json_threshold,
    load,
    past_phase,
    pf_mode,
    run_commands,
    sigWeaps,
    skip_random,
    skip_self,
    whaleOnly,
)
from composition import Composition
from line_profiler import profile
from player_phase import PlayerPhase
from plyer import notification  # type: ignore
from scipy.stats import skew, trim_mean  # type: ignore

with open("prydwen-slug.json") as slug_file:
    slug = load(slug_file)


@profile
def main() -> None:
    start_time = time()
    print("start")

    for make_path in [
        "../comp_results",
        "../comp_results/json",
        "../mihomo/results_real",
        "../char_results",
        "../rogue_results",
    ]:
        if not path.exists(make_path):
            makedirs(make_path)

    global self_uids
    if path.isfile("../../uids.csv"):
        with open("../../uids.csv", encoding="UTF8") as f:
            reader = csvreader(f, delimiter=",")
            self_uids = list(reader)[0]
    else:
        self_uids = []

    pf_filename = ""
    if as_mode:
        pf_filename = "_as"
    elif pf_mode:
        pf_filename = "_pf"
    if path.exists("../data/raw_csvs_real/"):
        stats = open("../data/raw_csvs_real/" + RECENT_PHASE + pf_filename + ".csv")
    else:
        stats = open("../data/raw_csvs/" + RECENT_PHASE + pf_filename + ".csv")

    # uid_freq_comp will help detect duplicate UIDs
    reader = csvreader(stats)
    next(reader)
    all_comps: list[Composition] = []
    if pf_mode:
        all_chambers = ["1", "2", "3", "4"]
    else:
        all_chambers = ["1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "11", "12"]
    three_star_sample = {}
    for chamber_num in all_chambers:
        three_star_sample[chamber_num] = 0
    uid_freq_comp: dict[str, int] = {}
    self_freq_comp: dict[str, int] = {}
    # dps_freq_comp = {}
    last_uid = "0"
    skip_uid = False

    for line in reader:
        # stage = "".join(filter(str.isdigit, line[1]))
        stage = str(line[1])
        if skip_self and line[0] in self_uids:
            continue
        if skip_random and line[0] not in self_uids:
            continue
        if line[0] != last_uid:
            skip_uid = False
            if line[0] in uid_freq_comp:
                skip_uid = True
                # print("duplicate UID in comp: " + line[0])
            elif (not pf_mode and int(stage) > 11 and int(line[4]) == 3) or (
                pf_mode and int(stage) > 3 and int(line[4]) == 3
            ):
                uid_freq_comp[line[0]] = 1
                if line[0] in self_uids:
                    self_freq_comp[line[0]] = 1
            else:
                skip_uid = True
        # else:
        #     uid_freq_comp[line[0]] += 1
        last_uid = line[0]
        if not skip_uid:
            comp_chars_temp: list[str] = []
            for i in range(5, 9):
                if line[i] != "":
                    if "Imbibitor" in line[i]:
                        line[i] = "Dan Heng • Imbibitor Lunae"
                    elif "Topaz and Numby" == line[i]:
                        line[i] = "Topaz & Numby"
                    elif "March 7th" == line[i]:
                        line[i] = "Ice March 7th"
                    comp_chars_temp.append(line[i])
            cons_chars_temp: list[int] = []
            if len(line) > 10:
                for i in range(9, 13):
                    if line[i] != "":
                        cons_chars_temp.append(int(float(line[i])))
                pf_buff = line[13] if pf_mode else ""
            else:
                pf_buff = line[9] if pf_mode else ""
            if comp_chars_temp:
                comp = Composition(
                    line[0],
                    comp_chars_temp,
                    RECENT_PHASE,
                    line[3],
                    line[4],
                    stage + "-" + str(line[2]),
                    alt_comps,
                    pf_buff,
                    cons_chars_temp,
                )
                # if int(stage) > 7:
                #     if line[0] not in dps_freq_comp:
                #         dps_freq_comp[line[0]] = set()
                #     if comp.dps == []:
                #         if comp.sub != []:
                #             dps_freq_comp[line[0]].add(frozenset([comp.sub[0]]))
                #     else:
                #         dps_freq_comp[line[0]].add(frozenset([comp.dps[0]]))
                all_comps.append(comp)
                if int(line[4]) == 3:
                    three_star_sample[stage] += 1

    # len_dps_freq_comp = {}
    # for i in dps_freq_comp:
    #     if len(dps_freq_comp[i]) not in len_dps_freq_comp:
    #         len_dps_freq_comp[len(dps_freq_comp[i])] = 0
    #     len_dps_freq_comp[len(dps_freq_comp[i])] += 1
    #     if len(dps_freq_comp[i]) == 1:
    #         print(str(i) + ": " + str(dps_freq_comp[i]))
    # print(len_dps_freq_comp)
    # exit()

    global sample_size
    sample_size = {}
    for chamber_num in all_chambers:
        sample_size[chamber_num] = {}
    avg_round_stage: dict[str, list[int]] = {}
    for chamber_num in all_chambers:
        avg_round_stage[chamber_num] = []
    global valid_duo_dps
    if path.exists("../char_results/duo_check.csv"):
        with open("../char_results/duo_check.csv") as f:
            valid_duo_dps = list(csvreader(f, delimiter=","))
    else:
        valid_duo_dps = []
    # max_weight = 0
    sample_size["all"] = {
        "total": len(uid_freq_comp),
        "self_report": len(self_freq_comp),
        "random": len(uid_freq_comp) - len(self_freq_comp),
    }

    # global stage_weight
    # stage_weight = {}
    # for stage in avg_round_stage:
    #     stage_weight[stage] = max_weight / sample_size[stage]["avg_round_stage"]
    #     sample_size[stage]["weight"] = stage_weight[stage]

    if path.exists("../data/raw_csvs_real/"):
        stats = open("../data/raw_csvs_real/" + RECENT_PHASE + "_char.csv")
    else:
        stats = open("../data/raw_csvs/" + RECENT_PHASE + "_char.csv")

    # uid_freq_char and last_uid will help detect duplicate UIDs
    reader = csvreader(stats)
    next(reader)
    all_players: dict[str, dict[str, PlayerPhase]] = {}
    all_players[RECENT_PHASE] = {}
    last_uid = "0"
    player = PlayerPhase(last_uid, RECENT_PHASE)
    uid_freq_char: list[str] = []

    # Append lines
    for line in reader:
        line[1] = RECENT_PHASE
        if line[0] in uid_freq_comp:
            if line[0] != last_uid:
                skip_uid = False
                if line[0] in uid_freq_char:
                    skip_uid = True
                    # print("duplicate UID in char: " + line[0])
                else:
                    uid_freq_char.append(line[0])
            if not skip_uid:
                if line[0] != last_uid:
                    all_players[RECENT_PHASE][last_uid] = player
                    last_uid = line[0]
                    player = PlayerPhase(last_uid, RECENT_PHASE)
                if "Imbibitor" in line[2]:
                    line[2] = "Dan Heng • Imbibitor Lunae"
                elif "Topaz and Numby" == line[2]:
                    line[2] = "Topaz & Numby"
                elif "March 7th" == line[2]:
                    line[2] = "Ice March 7th"
                player.add_character(
                    line[2], line[3], line[4], line[5], line[6], line[7], line[8]
                )
    all_players[RECENT_PHASE][last_uid] = player

    for comp in all_comps:
        if comp.player not in all_players[comp.phase]:
            all_players[comp.phase][comp.player] = PlayerPhase(comp.player, comp.phase)
        all_players[comp.phase][comp.player].add_comp(comp)

    csv_writer = csvwriter(open("../char_results/uids.csv", "w", newline=""))
    for uid in uid_freq_comp.keys():
        csv_writer.writerow([uid])

    cur_time = time()
    print("done csv:", round(cur_time - start_time, 2), "s")
    start_time = cur_time

    if pf_mode:
        three_stages = ["4-1", "4-2"]
        three_double_stages = [["4-1", "4-2"]]
        one_stage = ["4-1", "4-2"]
        all_stages = ["1-1", "1-2", "2-1", "2-2", "3-1", "3-2", "4-1", "4-2"]
        # all_double_stages = [
        #     ["1-1", "1-2"],
        #     ["2-1", "2-2"],
        #     ["3-1", "3-2"],
        #     ["4-1", "4-2"],
        # ]
    else:
        three_stages = ["10-1", "10-2", "11-1", "11-2", "12-1", "12-2"]
        three_double_stages = [["10-1", "10-2"], ["11-1", "11-2"], ["12-1", "12-2"]]
        one_stage = ["12-1", "12-2"]
        all_stages = [
            "1-1",
            "1-2",
            "2-1",
            "2-2",
            "3-1",
            "3-2",
            "4-1",
            "4-2",
            "5-1",
            "5-2",
            "6-1",
            "6-2",
            "7-1",
            "7-2",
            "8-1",
            "8-2",
            "9-1",
            "9-2",
            "10-1",
            "10-2",
            "11-1",
            "11-2",
            "12-1",
            "12-2",
        ]

    if "Char usages all stages" in run_commands:
        char_usages(
            all_players, archetype, past_phase, all_stages, filename="all", floor=True
        )
        cur_time = time()
        print("done char:", round(cur_time - start_time, 2), "s")
        start_time = cur_time

    if "Duos check" in run_commands:
        usage = char_usages(
            all_players, archetype, past_phase, three_stages, filename="all", floor=True
        )
        duo_usages(
            all_comps, all_players, usage, archetype, three_stages, check_duo=True
        )

    if "Char usages 8 - 10" in run_commands:
        usage = char_usages(
            all_players, archetype, past_phase, one_stage, filename="all", floor=True
        )
        if not whaleOnly and not f2pOnly:
            duo_usages(
                all_comps, all_players, usage, archetype, one_stage, check_duo=False
            )
        cur_time = time()
        print("done char 8 - 10:", round(cur_time - start_time, 2), "s")
        start_time = cur_time

        if "Char usages for each stage" in run_commands:
            char_chambers: dict[str, dict[int, dict[str, cu.CharUsageData]]] = {
                "all": {}
            }
            for star_num in usage:
                char_chambers["all"][star_num] = usage[star_num].copy()
            # for room in all_stages:
            for room in three_stages:
                char_chambers[room] = char_usages(
                    all_players, archetype, past_phase, [room], filename=room, offset=2
                )
            appearances = {}
            rounds = {}
            for room in char_chambers:
                appearances[room] = {}
                rounds[room] = {}
                for star_num in char_chambers[room]:
                    appearances[room][star_num] = dict(
                        sorted(
                            char_chambers[room][star_num].items(),
                            key=lambda t: t[1].app,
                            reverse=True,
                        )
                    )
                    if pf_mode:
                        rounds[room][star_num] = dict(
                            sorted(
                                char_chambers[room][star_num].items(),
                                key=lambda t: t[1].round,
                                reverse=True,
                            )
                        )
                    else:
                        rounds[room][star_num] = dict(
                            sorted(
                                char_chambers[room][star_num].items(),
                                key=lambda t: t[1].round,
                                reverse=False,
                            )
                        )
                    for char in char_chambers[room][star_num]:
                        appearances[room][star_num][char] = {
                            "app": char_chambers[room][star_num][char].app,
                            "rarity": char_chambers[room][star_num][char].rarity,
                            "diff": char_chambers[room][star_num][char].diff,
                        }
                        if char_chambers[room][star_num][char].round == 0:
                            continue
                        rounds[room][star_num][char] = {
                            "round": char_chambers[room][star_num][char].round,
                            # "prev_round": prev_chambers[room][str(star_num)][char],
                            "rarity": char_chambers[room][star_num][char].rarity,
                            "diff": char_chambers[room][star_num][char].diff_rounds,
                        }
            if not whaleOnly and not f2pOnly:
                with open("../char_results/appearance.json", "w") as out_file:
                    out_file.write(dumps(appearances, indent=2))
                with open("../char_results/rounds.json", "w") as out_file:
                    out_file.write(dumps(rounds, indent=2))
            cur_time = time()
            print("done char stage:", round(cur_time - start_time, 2), "s")
            start_time = cur_time

        if "Char usages for each stage (combined)" in run_commands:
            char_chambers: dict[str, dict[int, dict[str, cu.CharUsageData]]] = {
                "all": {}
            }
            for star_num in usage:
                char_chambers["all"][star_num] = usage[star_num].copy()
            # for room in all_double_stages:
            for room in three_double_stages:
                char_chambers[room[0]] = char_usages(
                    all_players,
                    archetype,
                    past_phase,
                    room,
                    filename=room[0].split("-")[0],
                )
            appearances = {}
            rounds = {}
            for room in char_chambers:
                appearances[room] = {}
                rounds[room] = {}
                for star_num in char_chambers[room]:
                    appearances[room][star_num] = dict(
                        sorted(
                            char_chambers[room][star_num].items(),
                            key=lambda t: t[1].app,
                            reverse=True,
                        )
                    )
                    if pf_mode:
                        rounds[room][star_num] = dict(
                            sorted(
                                char_chambers[room][star_num].items(),
                                key=lambda t: t[1].round,
                                reverse=True,
                            )
                        )
                    else:
                        rounds[room][star_num] = dict(
                            sorted(
                                char_chambers[room][star_num].items(),
                                key=lambda t: t[1].round,
                                reverse=False,
                            )
                        )
                    for char in char_chambers[room][star_num]:
                        appearances[room][star_num][char] = {
                            "app": char_chambers[room][star_num][char].app,
                            "rarity": char_chambers[room][star_num][char].rarity,
                            "diff": char_chambers[room][star_num][char].diff,
                        }
                        if char_chambers[room][star_num][char].round == 0:
                            continue
                        rounds[room][star_num][char] = {
                            "round": char_chambers[room][star_num][char].round,
                            # "prev_round": prev_chambers[room][str(star_num)][char],
                            "rarity": char_chambers[room][star_num][char].rarity,
                            "diff": char_chambers[room][star_num][char].diff_rounds,
                        }
            if not whaleOnly and not f2pOnly:
                with open("../char_results/appearance_combine.json", "w") as out_file:
                    out_file.write(dumps(appearances, indent=2))
                with open("../char_results/rounds_combine.json", "w") as out_file:
                    out_file.write(dumps(rounds, indent=2))
            cur_time = time()
            print("done char stage (combine):", round(cur_time - start_time, 2), "s")
            start_time = cur_time

    global all_comps_json
    all_comps_json = {}
    if "Comp usage all stages" in run_commands:
        comp_usages(
            all_comps,
            all_players,
            all_stages,
            avg_round_stage,
            filename="all",
            floor=True,
        )
        cur_time = time()
        print("done comp all:", round(cur_time - start_time, 2), "s")
        start_time = cur_time

    if "Comp usage 8 - 10" in run_commands:
        comp_usages(
            all_comps,
            all_players,
            one_stage,
            avg_round_stage,
            filename="top",
            floor=True,
        )
        cur_time = time()
        print("done comp 8 - 10:", round(cur_time - start_time, 2), "s")
        start_time = cur_time

    if "Comp usages for each stage" in run_commands:
        # for room in all_stages:
        for room in three_stages:
            comp_usages(
                all_comps, all_players, [room], avg_round_stage, filename=room, offset=2
            )

        if not whaleOnly and not f2pOnly:
            with open("../char_results/demographic.json", "w") as out_file:
                out_file.write(dumps(sample_size, indent=2))
        cur_time = time()
        print("done comp stage:", round(cur_time - start_time, 2), "s")
        start_time = cur_time

    if "Character specific infographics" in run_commands:
        comp_usages(
            all_comps,
            all_players,
            one_stage,
            avg_round_stage,
            filename=char_infographics,
            info_char=True,
            floor=True,
        )
        cur_time = time()
        print("done char infographics:", round(cur_time - start_time, 2), "s")
        start_time = cur_time

    if (
        "Comp usage 8 - 10" in run_commands
        and "Comp usages for each stage" in run_commands
        and not whaleOnly
        and not f2pOnly
    ):
        with open("../comp_results/json/all_comps.json", "w") as out_file:
            out_file.write(dumps(all_comps_json, indent=2))

    if __name__ == "__main__":
        notification.notify(
            title="Finished",
            message="Finished executing comp_rates",
            # displaying time
            timeout=2,
        )  # type: ignore
        # waiting time
        sleep(2)


@profile
def comp_usages(
    comps: list[Composition],
    players: dict[str, dict[str, PlayerPhase]],
    rooms: list[str],
    avg_round_stage: dict[str, list[int]],
    filename: str = "comp_usages",
    offset: int = 1,
    info_char: bool = False,
    floor: bool = False,
) -> None:
    global top_comps_app
    top_comps_app = {}
    comps_dict: list[dict[tuple[str, ...], CompUsage]] = used_comps(
        players, comps, rooms, filename, avg_round_stage, floor=floor, offset=offset
    )
    rank_usages(comps_dict, rooms, owns_offset=offset)
    comp_usages_write(comps_dict, filename, floor, info_char, True)
    comp_usages_write(comps_dict, filename, floor, info_char, False)


class CompUsage(Composition):
    def __init__(self, comp: Composition) -> None:
        self.__dict__.update(comp.__dict__)
        del self.player
        self.uses = 0
        self.owns = 0
        self.round_num = {str(i): list[int]() for i in range(1, 13)}
        self.whale_count = set[str]()
        self.players = set[str]()
        self.is_count_round: bool
        self.is_count_round_print: bool
        self.app_rate: float
        self.round: float
        self.usage_rate: float
        self.own_rate: float
        self.app_rank: int


@profile
def used_comps(
    players: dict[str, dict[str, PlayerPhase]],
    comps: list[Composition],
    rooms: list[str],
    filename: str,
    avg_round_stage: dict[str, list[int]],
    phase: str = RECENT_PHASE,
    floor: bool = False,
    offset: int = 1,
) -> list[dict[tuple[str, ...], CompUsage]]:
    # Returns the dictionary of all the comps used and how many times they were used
    comps_dict: list[dict[tuple[str, ...], CompUsage]] = [{}, {}, {}, {}, {}]
    # error_uids = []
    # lessFour = []
    # lessFourComps = {}
    global total_comps
    total_comps = 0
    total_self_comps = 0
    whale_count = 0
    f2p_count = 0
    # dual_dps = {}
    # total_char_comps = {}

    # For storing the prev and next comps
    comp_iter = 0
    for comp in comps:
        # Check if the comp is used in the rooms that are being checked
        if comp.room not in rooms:
            continue

        side_comp = None
        if comp_iter - 1 >= 0:
            if (
                comps[comp_iter - 1].player == comp.player
                and comps[comp_iter - 1].room == comp.room
            ):
                side_comp = comps[comp_iter - 1]
        if not side_comp and comp_iter + 1 < len(comps):
            if (
                comps[comp_iter + 1].player == comp.player
                and comps[comp_iter + 1].room == comp.room
            ):
                side_comp = comps[comp_iter + 1]
        comp_iter += 1

        comp_tuple = tuple(comp.characters)
        if side_comp:
            side_comp_tuple = tuple(side_comp.characters)
        else:
            side_comp_tuple = None

        total_comps += 1
        if comp.player in self_uids:
            total_self_comps += 1
        if len(comp_tuple) < 4:
            #     lessFour.append(comp.player)
            continue
        if side_comp_tuple and len(side_comp_tuple) < 4:
            continue

        whale_comp = False
        f2p_comp = True
        sustain_count = 0
        owned_chars = players[phase][comp.player].owned
        for char in range(4):
            comp_char = comp_tuple[char]
            if CHARACTERS[comp_char]["availability"] == "Limited 5*":
                if comp.char_cons and comp.char_cons[comp_char] > 0:
                    whale_comp = True
                elif comp_char in owned_chars:
                    if owned_chars[comp_char].cons > 0:
                        whale_comp = True
                    if owned_chars[comp_char].weapon not in sigWeaps:
                        f2p_comp = False
            if (
                not pf_mode
                and not as_mode
                and side_comp_tuple
                and CHARACTERS[side_comp_tuple[char]]["availability"] == "Limited 5*"
                and not whale_comp
                and side_comp
            ):
                side_owned_chars = players[phase][side_comp.player].owned
                side_comp_char = side_comp_tuple[char]
                if side_comp.char_cons and side_comp.char_cons[side_comp_char] > 0:
                    whale_comp = True
                elif (
                    side_comp_char in side_owned_chars
                    and side_owned_chars[side_comp_char].cons > 0
                ):
                    whale_comp = True
            # if comp_char not in total_char_comps:
            #     total_char_comps[comp_char] = 0
            # total_char_comps[comp_char] += 1
            if CHARACTERS[comp_char]["role"] == "Sustain":
                sustain_count += 1
        # check_comp_tuple = (
        #     "Firefly",
        #     "Fugue",
        #     "Imaginary Trailblazer",
        #     "Ruan Mei",
        # )
        # if check_comp_tuple == comp_tuple and side_comp and whale_comp:
        #     print(comp.player)
        #     print(side_comp.player)

        if whale_comp:
            whale_count += 1
        if whaleOnly and not whale_comp:
            continue
        if f2p_comp:
            f2p_count += 1
        if f2pOnly and (not f2p_comp or whale_comp):
            continue

        if comp_tuple not in comps_dict[4]:
            comps_dict[4][comp_tuple] = CompUsage(comp)

        # Make temporary variable for the current comp
        comp_data = comps_dict[4][comp_tuple]
        comp_data.uses += 1
        comp_data.players.add(comp.player)

        if whale_comp:
            comp_data.whale_count.add(comp.player)
        if whale_comp == whaleOnly and (not f2pOnly or f2p_comp):
            cur_room = list(str(comp.room).split("-"))[0]
            comp_data.round_num[cur_room].append(comp.round_num)
            if 4 == 4 and sustain_count <= 1:
                avg_round_stage[cur_room].append(comp.round_num)
                if pf_mode:
                    if "buff_" + comp.buff not in sample_size[cur_room]:
                        sample_size[cur_room]["buff_" + comp.buff] = 0
                    sample_size[cur_room]["buff_" + comp.buff] += 1

        # Set the current comp to the temporary variable
        comps_dict[4][comp_tuple] = comp_data

    for stage in avg_round_stage:
        sample_size[stage]["avg_round"] = round(
            mean(avg_round_stage[stage] if avg_round_stage[stage] else [0]),
            2,
        )
        # "3_star": three_star_sample[stage]
        # if sample_size[stage]["avg_round_stage"] > max_weight:
        #     max_weight = sample_size[stage]["avg_round_stage"]

    chamber_num = list(str(filename).split("-"))
    if len(chamber_num) > 1:
        if chamber_num[1] == "1":
            sample_size[chamber_num[0]]["total"] = total_comps
            sample_size[chamber_num[0]]["self_report"] = total_self_comps
            sample_size[chamber_num[0]]["random"] = total_comps - total_self_comps
        # if total_comps == 0:
        #     del sample_size[chamber_num[0]]
    # if whaleOnly:
    #     print("Whale percentage: " + str(whale_count / total_comps))
    return comps_dict


@profile
def rank_usages(
    comps_dict: list[dict[tuple[str, ...], CompUsage]],
    rooms: list[str],
    owns_offset: int = 1,
) -> None:
    # Calculate the usage rate and sort the comps according to it
    rates: list[float] = []
    # rounds = []
    for comp in comps_dict[4]:
        avg_round: list[float] = []
        uses_room: dict[int, int] = {}
        # Make temporary variable for the current comp
        cur_comp = comps_dict[4][comp]

        for room_num in range(1, 13):
            cur_round = cur_comp.round_num[str(room_num)]
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
                            )
                        )
                    else:
                        avg_round.append(mean(cur_round))
                else:
                    avg_round.append(mean(cur_round))
                # avg_round.append(mean(cur_round))
                # avg_round += cur_round

        cur_comp.is_count_round = True
        cur_comp.is_count_round_print = True
        if (rooms == ["12-1", "12-2"]) or (pf_mode and rooms == ["4-1", "4-2"]):
            for room_num in uses_room:
                if uses_room[room_num] < 15:
                    if whaleOnly and uses_room[room_num] < 10:
                        cur_comp.is_count_round = False
                    else:
                        cur_comp.is_count_round = False
                    if uses_room[room_num] < 2:
                        cur_comp.is_count_round_print = False
        elif len(rooms) == 1 and cur_comp.uses < 15:
            if whaleOnly and cur_comp.uses < 10:
                cur_comp.is_count_round = False
            else:
                cur_comp.is_count_round = False
            if cur_comp.uses < 2:
                cur_comp.is_count_round_print = False

        rounded_avg_round: float
        if avg_round:
            rounded_avg_round = round(mean(avg_round), 2)
            if pf_mode:
                rounded_avg_round = round(rounded_avg_round)
        else:
            rounded_avg_round = 99.99
            if pf_mode:
                rounded_avg_round = 0

        app = (
            int(100.0 * cur_comp.uses / (total_comps * owns_offset) * 200 + 0.5) / 100.0
        )
        cur_comp.app_rate = app
        cur_comp.round = rounded_avg_round
        cur_comp.usage_rate = 0
        cur_comp.own_rate = 0
        rates.append(app)
        # rounds.append(rounded_avg_round)

        # Set the current comp to the temporary variable
        comps_dict[4][comp] = cur_comp

    rates.sort(reverse=True)
    # rounds.sort(reverse=False)
    for comp in comps_dict[4]:
        comps_dict[4][comp].app_rank = rates.index(comps_dict[4][comp].app_rate) + 1
        # cur_comp.round_rank = rounds.index(cur_comp.round) + 1

    # comp_tuples = [
    #     ("Firefly", "Fugue", "Imaginary Trailblazer", "Ruan Mei"),
    #     # ("Firefly", "Imaginary Trailblazer", "Ruan Mei", "Gallagher"),
    # ]
    # for comp_tuple in comp_tuples:
    #     print(comp_tuple)
    #     print("   round_num: " + str(comps_dict[4][comp_tuple]["round_num"][str(12)]))
    #     print("   App: " + str(comps_dict[4][comp_tuple]["app_rate"]))
    #     print("   5* Count: " + str(comps_dict[4][comp_tuple]["fivecount"]))
    #     if comps_dict[4][comp_tuple]["fivecount"] <= 1:
    #         print("   F2P App: " + str(comps_dict[4][comp_tuple]["app_rate"]))
    #     print()


@profile
def duo_usages(
    comps: list[Composition],
    players: dict[str, dict[str, PlayerPhase]],
    usage: dict[int, dict[str, cu.CharUsageData]],
    archetype: str,
    rooms: list[str],
    check_duo: bool = False,
    filename: str = "duo_usages",
) -> None:
    duos_dict = used_duos(players, comps, rooms, usage, check_duo, archetype)
    duo_write(duos_dict, usage, filename, archetype, check_duo)


@profile
def used_duos(
    players: dict[str, dict[str, PlayerPhase]],
    comps: list[Composition],
    rooms: list[str],
    usage: dict[int, dict[str, cu.CharUsageData]],
    archetype: str,
    check_duo: bool,
    phase: str = RECENT_PHASE,
):
    # Returns dictionary of all the duos used and how many times they were used
    duos_dict = {}

    for comp in comps:
        if len(comp.characters) < 2 or comp.room not in rooms:
            continue

        whale_comp = False
        sustain_count = 0
        for char in comp.characters:
            if CHARACTERS[char]["availability"] == "Limited 5*":
                if comp.char_cons:
                    if comp.char_cons[char] > 0:
                        whale_comp = True
            if CHARACTERS[char]["role"] == "Sustain":
                sustain_count += 1

        duos = list(permutations(comp.characters, 2))
        for duo in duos:
            is_triple_dps = False

            if duo not in duos_dict:
                duos_dict[duo] = {
                    "app_flat": 0,
                    "round_num": {
                        "1": [],
                        "2": [],
                        "3": [],
                        "4": [],
                        "5": [],
                        "6": [],
                        "7": [],
                        "8": [],
                        "9": [],
                        "10": [],
                        "11": [],
                        "12": [],
                    },
                }
            duos_dict[duo]["app_flat"] += 1

            if is_triple_dps and check_duo:
                continue
            if (not whale_comp) and sustain_count <= 1:
                duos_dict[duo]["round_num"][list(str(comp.room).split("-"))[0]].append(
                    comp.round_num
                )

    sorted_duos = sorted(
        duos_dict.items(), key=lambda t: t[1]["app_flat"], reverse=True
    )
    duos_dict = {k: v for k, v in sorted_duos}

    sorted_duos = {}
    for duo in duos_dict:
        cur_duo = duos_dict[duo]
        if usage[4][duo[0]].app_flat > 0:
            # Calculate the appearance rate of the duo by dividing the appearance count
            # of the duo with the appearance count of the first character
            cur_duo["uses"] = round(
                cur_duo["app_flat"] * 100 / usage[4][duo[0]].app_flat, 2
            )
            cur_duo["app_flat"] = 0
            avg_round = []
            for room_num in range(1, 13):
                duo_round = cur_duo["round_num"][str(room_num)]
                if duo_round:
                    cur_duo["app_flat"] += len(duo_round)
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
                    # avg_round.append(mean(duo_round))
                    # avg_round += duo_round
            if avg_round:
                cur_duo["round_num"] = round(mean(avg_round), 2)
                if pf_mode:
                    cur_duo["round_num"] = round(cur_duo["round_num"])
            else:
                cur_duo["round_num"] = 99.99
                if pf_mode:
                    cur_duo["round_num"] = 0
            if duo[0] not in sorted_duos:
                sorted_duos[duo[0]] = []
            sorted_duos[duo[0]].append(
                [
                    duo[1],
                    cur_duo["uses"],
                    cur_duo["round_num"],
                    cur_duo["app_flat"],
                ]
            )

    return sorted_duos


@profile
def char_usages(
    players: dict[str, dict[str, PlayerPhase]],
    archetype: str,
    past_phase: str,
    rooms: list[str],
    filename: str = "char_usages",
    offset: int = 1,
    info_char: bool = False,
    floor: bool = False,
) -> dict[int, dict[str, cu.CharUsageData]]:
    app = cu.appearances(players, chambers=rooms, offset=offset, info_char=info_char)
    chars_dict: dict[int, dict[str, cu.CharUsageData]] = cu.usages(
        app, past_phase, chambers=rooms
    )
    # # Print the list of weapons and artifacts used for a character
    # if floor:
    #     print(app[RECENT_PHASE][filename])
    if (not pf_mode and rooms == ["12-1", "12-2"]) or (
        pf_mode and rooms == ["4-1", "4-2"]
    ):
        char_usages_write(chars_dict[4], filename, archetype)
    return chars_dict


@profile
def comp_usages_write(
    comps_dict: list[dict[tuple[str, ...], CompUsage]],
    filename: str,
    floor: int,
    info_char: bool,
    sort_app: bool,
) -> None:
    out_json: list[dict[str, str | float]] = []
    out_comps: list[dict[str, str | int]] = []
    outvar_comps: list[dict[str, str | int]] = []
    var_comps: list[dict[str, str | int]] = []
    # exc_comps: list[dict[str, str | int]] = []
    variations: dict[str, int] = {}
    if sort_app:
        thres = app_rate_threshold
    else:
        thres = app_rate_threshold_round

    # Sort the comps according to their usage rate

    if sort_app:
        comps_dict[4] = dict(
            sorted(
                comps_dict[4].items(),
                key=lambda t: t[1].app_rate,
                reverse=True,
            )
        )
    elif pf_mode:
        comps_dict[4] = dict(
            sorted(
                comps_dict[4].items(),
                key=lambda t: t[1].round,
                reverse=True,
            )
        )
    else:
        comps_dict[4] = dict(
            sorted(
                comps_dict[4].items(),
                key=lambda t: t[1].round,
                reverse=False,
            )
        )
    comp_names: list[str] = []
    dual_comp_names: list[str] = []

    for comp in comps_dict[4]:
        if info_char and filename not in comp:
            continue
        cur_comp = comps_dict[4][comp]
        comp_name = cur_comp.comp_name
        dual_comp_name = cur_comp.dual_comp_name
        alt_comp_name = cur_comp.alt_comp_name
        # Only one variation of each comp name is included,
        # unless if it's used for a character's infographic
        if (
            (
                comp_name not in comp_names
                and comp_name not in dual_comp_names
                and dual_comp_name not in comp_names
                and alt_comp_name not in comp_names
                and cur_comp.round != 99.99
                and cur_comp.round != 0
            )
            or comp_name == "-"
            or info_char
        ):
            if sort_app:
                top_comps_app[comp_name] = cur_comp.app_rate
            elif comp_name in top_comps_app:
                if (
                    cur_comp.is_count_round
                    and cur_comp.app_rate < top_comps_app[comp_name] / 5
                ):
                    continue
            if cur_comp.is_count_round and (
                cur_comp.app_rate >= thres
                or (info_char and cur_comp.app_rate > char_app_rate_threshold)
            ):
                temp_comp_name = "-"
                if alt_comp_name != "-":
                    temp_comp_name = alt_comp_name
                else:
                    temp_comp_name = comp_name

                out_comps_append: dict[str, str | int] = {
                    "comp_name": temp_comp_name,
                    "char_1": comp[0],
                    "char_2": comp[1],
                    "char_3": comp[2],
                    "char_4": comp[3],
                    "app_rate": str(cur_comp.app_rate) + "%",
                    "avg_round": str(cur_comp.round),
                    # "own_rate": str(cur_c["own_rate"]) + "%",
                    # "usage_rate": str(cur_c["usage_rate"]) + "%"
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
                if dual_comp_name != "-":
                    dual_comp_names.append(dual_comp_name)
                if alt_comp_name != "-":
                    comp_names.append(alt_comp_name)

            # elif floor:
            #     temp_comp_name = "-"
            #     if alt_comp_name != "-":
            #         temp_comp_name = alt_comp_name
            #     else:
            #         temp_comp_name = comp_name
            #     exc_comps_append = {
            #         "comp_name": temp_comp_name,
            #         "char_1": comp[0],
            #         "char_2": comp[1],
            #         "char_3": comp[2],
            #         "char_4": comp[3],
            #         # "own_rate": str(cur_c["own_rate"]) + "%",
            #         # "usage_rate": str(cur_c["usage_rate"]) + "%",
            #     }
            #     exc_comps_append["app_rate"] = str(cur_c["app_rate"]) + "%"
            #     exc_comps_append["avg_round"] = str(cur_c["round"])
            #     exc_comps.append(exc_comps_append)
        elif comp_name in comp_names:
            if alt_comp_name != "-":
                temp_comp_name = alt_comp_name
            else:
                temp_comp_name = comp_name
            outvar_comps_append: dict[str, str | int] = {
                "comp_name": temp_comp_name,
                "char_1": comp[0],
                "char_2": comp[1],
                "char_3": comp[2],
                "char_4": comp[3],
                # "own_rate": str(cur_c["own_rate"]) + "%",
                # "usage_rate": str(cur_c["usage_rate"]) + "%"
            }
            outvar_comps_append["app_rate"] = str(cur_comp.app_rate) + "%"
            outvar_comps_append["avg_round"] = str(cur_comp.round)
            outvar_comps.append(outvar_comps_append)
        if not info_char and (
            cur_comp.is_count_round_print and (cur_comp.app_rate >= json_threshold)
        ):
            out = name_filter(comp, mode="out")
            for i in range(0, 4):
                out[i] = out[i].lower().replace(" ", "-")
                if out[i] in slug:
                    out[i] = slug[out[i]]
            out_json_dict: dict[str, str | float] = {
                "char_one": out[0],
                "char_two": out[1],
                "char_three": out[2],
                "char_four": out[3],
            }
            out_json_dict["app_rate"] = cur_comp.app_rate
            out_json_dict["rank"] = cur_comp.app_rank
            out_json_dict["avg_round"] = cur_comp.round
            out_json_dict["star_num"] = str(4)
            # out_json_dict["rank"] = cur_c["round_rank"]
            out_json.append(out_json_dict)

    if info_char:
        out_comps += var_comps

    if archetype != "all":
        filename = filename + "_" + archetype

    if not (sort_app):
        filename = filename + "_rounds"

    if whaleOnly:
        filename = filename + "_C1"
    elif f2pOnly:
        filename = filename + "_E0S0"

    if floor:
        csv_writer = csvwriter(
            open("../comp_results/comps_usage_" + filename + ".csv", "w", newline="")
        )
        for comps in out_comps:
            csv_writer.writerow(comps.values())
        # with open("../comp_results/exc_" + filename + ".json", "w") as out_file:
        #     out_file.write(dumps(exc_comps,indent=2))

    if not info_char and sort_app:
        all_comps_json[filename] = out_json.copy()
        with open("../comp_results/json/" + filename + ".json", "w") as out_file:
            out_file.write(dumps(out_json, indent=2))


@profile
def duo_write(
    duos_dict,
    usage: dict[int, dict[str, cu.CharUsageData]],
    filename: str,
    archetype: str,
    check_duo: bool,
) -> None:
    out_duos = []
    for char in duos_dict:
        if usage[4][char].app_flat > 0:
            out_duos_append = {
                "char": char,
                "app": usage[4][char].app,
            }
            for i in range(duo_dict_len):
                j = str(i + 1)
                if i < len(duos_dict[char]):
                    duo_char = duos_dict[char][i]
                    out_duos_append["char_" + j] = duo_char[0]
                    out_duos_append["app_rate_" + j] = str(duo_char[1]) + "%"
                    out_duos_append["avg_round_" + j] = duo_char[2]
                    out_duos_append["app_flat_" + j] = duo_char[3]
                else:
                    out_duos_append["char_" + j] = "-"
                    out_duos_append["app_rate_" + j] = "0.00%"
                    out_duos_append["avg_round_" + j] = 0.00
                    out_duos_append["app_flat_" + j] = 0
            out_duos.append(out_duos_append)
    out_duos = sorted(out_duos, key=lambda t: t["app"], reverse=True)

    if archetype != "all":
        filename = filename + "_" + archetype
    csv_writer = csvwriter(
        open("../char_results/" + filename + ".csv", "w", newline="")
    )
    count = 0
    out_duos_check = {}
    out_duos_exclu = {}
    for duos in out_duos:
        out_duos_check[duos["char"]] = {}
        out_duos_exclu[duos["char"]] = {}
        if count == 0:
            # csv_writer.writerow(duos.keys())
            temp_duos = ["char", "app"]
            for i in range(10):
                temp_duos += [
                    "char_" + str(i + 1),
                    "app_rate_" + str(i + 1),
                    "avg_round_" + str(i + 1),
                ]
            csv_writer.writerow(temp_duos)
            count += 1
        # csv_writer.writerow(duos.values())
        temp_duos = [
            duos["char"],
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
                duos["app_rate_" + j] = float(duos["app_rate_" + j][:-1])
                if (
                    duos["app_rate_" + j] >= 1
                    and duos["app_flat_" + j] >= 10
                    and (
                        (duos["avg_round_" + j] < usage[4][duos["char_" + j]]["round"])
                        or (duos["avg_round_" + j] < usage[4][duos["char"]]["round"])
                    )
                    and usage[4][duos["char_" + j]]["round"] != 99.99
                    and usage[4][duos["char_" + j]]["round"] != 0
                ):
                    # out_duos_exclu[duos["char"]][duos["char_" + j]] = {
                    #     "app": duos["app_rate_" + j],
                    #     "avg_round": duos["avg_round_" + j]
                    # }
                    # duos.pop("char_" + j)
                    # duos.pop("app_rate_" + j)
                    # duos.pop("avg_round_" + j)
                    # continue
                    out_duos_check[duos["char"]][duos["char_" + j]] = {
                        "app": duos["app_rate_" + j],
                        "avg_round": duos["avg_round_" + j],
                    }
    if check_duo:
        char_names = list(CHARACTERS.keys())
        out_dd = {}
        out_dd_list = []
        csv_writer = csvwriter(open("../char_results/duo_check.csv", "w", newline=""))
        for char_i in char_names:
            for char_j in char_names:
                is_char_i_dps = CHARACTERS[char_i]["role"] == "Damage Dealer"
                is_char_j_dps = CHARACTERS[char_j]["role"] == "Damage Dealer"
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
            out_dd.items(), key=lambda t: t[1]["char_i"], reverse=True
        )
        out_dd = {k: v for k, v in sorted_out_dd}

        for out_dd_print in out_dd_list:
            csv_writer.writerow(out_dd_print)
            # print(out_dd_print)
        for out_dd_print in out_dd:
            print(
                out_dd[out_dd_print]["char_i"]
                + ", "
                + out_dd[out_dd_print]["char_i_app"]
                + ", "
                + out_dd[out_dd_print]["char_j"]
                + ", "
                + out_dd[out_dd_print]["char_j_app"]
                + ", "
                + out_dd[out_dd_print]["avg_round"]
            )
        if __name__ == "__main__":
            notification.notify(
                title="Finished",
                message="Finished executing comp_rates",
                # displaying time
                timeout=2,
            )  # type: ignore
            # waiting time
            sleep(1)
        exit()

    for i in range(len(out_duos)):
        for duo_value in ["char"] + [f"char_{i}" for i in range(1, 31)]:
            if out_duos[i][duo_value]:
                out_duos[i][duo_value] = (
                    out_duos[i][duo_value].lower().replace(" ", "-")
                )
                if out_duos[i][duo_value] in slug:
                    out_duos[i][duo_value] = slug[out_duos[i][duo_value]]
    with open("../char_results/" + filename + ".json", "w") as out_file:
        out_file.write(dumps(out_duos, indent=2))


@profile
def char_usages_write(
    chars_dict: dict[str, cu.CharUsageData], filename: str, archetype: str
) -> None:
    out_chars: list[dict[str, str | int | float]] = []
    out_chars_csv: list[dict[str, str | int | float]] = []
    weap_len = 10
    arti_len = 10
    planar_len = 5
    chars_dict = dict(sorted(chars_dict.items(), key=lambda t: t[1].app, reverse=True))
    for char in chars_dict:
        cur_char = chars_dict[char]
        out_chars_append: dict[str, str | int | float] = {
            "char": char,
            "app_rate": str(cur_char.app) + "%",
            "app_rate_e0": str(cur_char.app_exclude) + "%",
            "avg_round": str(cur_char.round),
            # "prev_avg_round": str(prev_round.get(char, 99.99)),
            "std_dev_round": str(cur_char.std_dev_round),
            "q1_round": str(cur_char.q1_round),
            # "usage_rate": str(cur_char.usage) + "%",
            # "own_rate": str(cur_char.own) + "%",
            "role": cur_char.role,
            "rarity": cur_char.rarity,
            "diff": str(cur_char.diff) + "%",
            "diff_rounds": str(cur_char.diff_rounds),
        }
        for i in ["app_rate", "app_rate_e0", "diff", "diff_rounds"]:
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
                    out_chars_append["weapon_" + j + "_round"] = "99.99"
                    if pf_mode:
                        out_chars_append["weapon_" + j + "_round"] = "0.0"
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
                        cur_arti[i].round
                    )
                else:
                    out_chars_append["artifact_" + j] = ""
                    out_chars_append["artifact_" + j + "_1"] = ""
                    out_chars_append["artifact_" + j + "_2"] = ""
                    out_chars_append["artifact_" + j + "_app"] = "0.0"
                    out_chars_append["artifact_" + j + "_round"] = "99.99"
                    if pf_mode:
                        out_chars_append["artifact_" + j + "_round"] = "0.0"
            for i in range(planar_len):
                j = str(i + 1)
                if i < len(list(cur_char.planars)):
                    cur_planar = list(cur_char.planars.values())
                    out_chars_append["planar_" + j] = list(cur_char.planars)[i]
                    out_chars_append["planar_" + j + "_app"] = (
                        str(cur_planar[i].app) + "%"
                    )
                    out_chars_append["planar_" + j + "_round"] = str(
                        cur_planar[i].round
                    )
                else:
                    out_chars_append["planar_" + j] = ""
                    out_chars_append["planar_" + j + "_app"] = "0.0"
                    out_chars_append["planar_" + j + "_round"] = "99.99"
                    if pf_mode:
                        out_chars_append["planar_" + j + "_round"] = "0.0"
            for i in range(7):
                out_chars_append["app_" + str(i)] = (
                    str(list(list(cur_char.cons_usage.values())[i].values())[0]) + "%"
                )
                out_chars_append["round_" + str(i)] = str(
                    list(list(cur_char.cons_usage.values())[i].values())[3]
                )
                if out_chars_append["app_" + str(i)] == "-%":
                    out_chars_append["app_" + str(i)] = "-"
        else:
            for i in range(weap_len):
                j = str(i + 1)
                out_chars_append["weapon_" + j] = ""
                out_chars_append["weapon_" + j + "_app"] = "0.0"
                out_chars_append["weapon_" + j + "_round"] = "99.99"
                if pf_mode:
                    out_chars_append["weapon_" + j + "_round"] = "0.0"
            for i in range(arti_len):
                j = str(i + 1)
                out_chars_append["artifact_" + j] = ""
                out_chars_append["artifact_" + j + "_1"] = ""
                out_chars_append["artifact_" + j + "_2"] = ""
                out_chars_append["artifact_" + j + "_app"] = "0.0"
                out_chars_append["artifact_" + j + "_round"] = "99.99"
                if pf_mode:
                    out_chars_append["artifact_" + j + "_round"] = "0.0"
            for i in range(planar_len):
                j = str(i + 1)
                out_chars_append["planar_" + j] = ""
                out_chars_append["planar_" + j + "_app"] = "0.0"
                out_chars_append["planar_" + j + "_round"] = "99.99"
                if pf_mode:
                    out_chars_append["planar_" + j + "_round"] = "0.0"
            for i in range(7):
                out_chars_append["app_" + str(i)] = "0.0%"
                out_chars_append["round_" + str(i)] = "99.99"
                if pf_mode:
                    out_chars_append["round_" + str(i)] = "0.0"
        out_chars_append["cons_avg"] = cur_char.cons_avg
        out_chars_append["sample"] = cur_char.sample
        out_chars_append["sample_app_flat"] = cur_char.sample_app_flat
        out_chars.append(out_chars_append)
        out_chars_csv.append(out_chars_append.copy())
        if char == filename:
            break

    if archetype != "all":
        filename = filename + "_" + archetype
    if whaleOnly:
        filename = filename + "_C1"
    elif f2pOnly:
        filename = filename + "_E0S0"

    iterate_value_app = ["app_rate", "app_rate_e0", "diff"]
    iterate_value_round = ["avg_round", "std_dev_round", "q1_round", "diff_rounds"]
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
        out_chars[i]["char"] = str(out_chars[i]["char"]).lower().replace(" ", "-")
        if out_chars[i]["char"] in slug:
            out_chars[i]["char"] = slug[out_chars[i]["char"]]
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
                out_chars[i][value] = 99.99
                if pf_mode:
                    out_chars[i][value] = 0
        for value in iterate_name_arti:
            if out_chars[i][value]:
                out_chars[i][value] = (
                    str(out_chars[i][value]).replace(".", "").replace("-", "")
                )
            else:
                out_chars[i][value] = 99.99
                if pf_mode:
                    out_chars[i][value] = 0
    with open("../char_results/" + filename + ".json", "w") as out_file:
        out_file.write(dumps(out_chars, indent=2))

    csv_writer = csvwriter(
        open("../char_results/" + filename + ".csv", "w", newline="")
    )
    count = 0
    for chars in out_chars_csv:
        if count == 0:
            header = chars.keys()
            csv_writer.writerow(header)
            count += 1
        csv_writer.writerow(chars.values())


@profile
def name_filter(comp: list[str], mode: str = "out") -> list[str]:
    filtered: list[str] = []
    if mode == "out":
        for char in comp:
            if CHARACTERS[char]["out_name"]:
                filtered.append(str(CHARACTERS[char]["alt_name"]))
            else:
                filtered.append(char)
    return filtered


if __name__ == "__main__":
    main()
