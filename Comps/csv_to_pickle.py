"""Convert CSV files to pickle."""

from __future__ import annotations

from csv import reader as csvreader
from csv import writer as csvwriter
from dataclasses import dataclass
from os import makedirs, path
from pickle import dump as pickle_dump
from pickle import load as pickle_load
from time import time

from comp_rates_config import (
    LAST_MOC_FLOOR,
    RECENT_PHASE,
    RECENT_PHASE_PF,
    aa_mode,
    load,
    moc_mode,
    pf_filename,
    pf_mode,
    skip_random,
    skip_self,
)
from composition import Composition, Stage
from player_phase import PlayerPhase

with open("prydwen-slug.json") as slug_file:
    slug = load(slug_file)

all_players: dict[str, PlayerPhase] = {}
all_comps: list[Composition] = []
avg_round_stage: dict[int, list[int]] = {}
sample_size: dict[int | str, dict[str, int | float]] = {}

if path.isfile("../../uids.csv"):
    with open("../../uids.csv", encoding="UTF8") as f:
        reader = csvreader(f, delimiter=",")
        self_uids = next(iter(reader))
else:
    self_uids = []


@dataclass
class PickleData:
    """Container for pickle data."""

    all_players: dict[str, PlayerPhase]
    all_comps: list[Composition]
    avg_round_stage: dict[int, list[int]]
    sample_size: dict[int | str, dict[str, int | float]]


def save_pickle_data(filename: str, data: PickleData) -> None:
    """Save data to a pickle file."""
    with open(filename, "wb") as f:
        pickle_dump(data, f)


def load_pickle_data(filename: str) -> PickleData:
    """Load data from a pickle file."""
    with open(filename, "rb") as f:
        return pickle_load(f)


def main() -> None:
    """Compile data."""
    start_time = time()
    print("start")

    for make_path in [
        "../comp_results",
        "../comp_results/json",
        "../mihomo/results_real",
        "../char_results",
        "../data/pickle",
        "../rogue_results",
    ]:
        if not path.exists(make_path):
            makedirs(make_path)

    with (
        open("../data/raw_csvs_real/" + RECENT_PHASE_PF + ".csv")
        if path.exists("../data/raw_csvs_real/")
        else open("../data/raw_csvs/" + RECENT_PHASE_PF + ".csv")
    ) as f:
        stats = csvreader(f)
        reader = stats
        next(reader)
        reader = list(reader)

    # uid_freq_comp will help detect duplicate UIDs
    if pf_mode:
        all_chambers: list[int] = [1, 2, 3, 4]
    elif aa_mode:
        all_chambers: list[int] = [1, 2]
    else:
        all_chambers: list[int] = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]
    uid_freq_comp: dict[str, int] = {}
    self_freq_comp: dict[str, int] = {}
    last_uid = "0"
    skip_uid = False

    for line in reader:
        player = line[0]
        stage = int(line[1])
        node = (stage if stage != 4 else 1) if aa_mode else int(line[2])
        if aa_mode:
            stage = 1 if stage <= 3 else 2

        round_num = int(line[2] if aa_mode else line[3])
        star_num = int(line[3] if aa_mode else line[4])
        if skip_self and player in self_uids:
            continue
        if skip_random and player not in self_uids:
            continue
        if player != last_uid:
            skip_uid = False
            if player in uid_freq_comp:
                skip_uid = True
                print("duplicate UID in comp: " + player)
            elif (
                (aa_mode and (stage == 2 or round_num <= 4) and star_num >= 1)
                or (moc_mode and stage >= LAST_MOC_FLOOR and star_num == 3)
                or (pf_mode and stage > 3 and star_num == 3)
            ):
                uid_freq_comp[player] = 1
                if player in self_uids:
                    self_freq_comp[player] = 1
            else:
                skip_uid = True
        last_uid = player
        if not skip_uid:
            comp_chars_temp: list[str] = []
            for i in range(4, 8) if aa_mode else range(5, 9):
                if line[i] != "":
                    if line[i] == "Topaz and Numby":
                        line[i] = "Topaz & Numby"
                    elif line[i] == "March 7th":
                        line[i] = "Ice March 7th"
                    comp_chars_temp.append(line[i])
            cons_chars_temp: list[int] = []
            if len(line) > 10:
                cons_chars_temp.extend(
                    int(float(line[i]))
                    for i in (range(8, 12) if aa_mode else range(9, 13))
                    if line[i] != ""
                )
                pf_buff = line[13] if pf_mode else None
            else:
                pf_buff = line[9] if pf_mode else None
            if comp_chars_temp:
                comp = Composition(
                    player=player,
                    comp_chars=comp_chars_temp,
                    round_num=round_num,
                    room=Stage(stage, node),
                    buff=line[12] if aa_mode else pf_buff,
                    comp_chars_cons=cons_chars_temp,
                    is_hard_mode=bool(line[13]) if aa_mode else None,
                )
                all_comps.append(comp)

    cur_time = time()
    print("done csv comps:", round(cur_time - start_time, 2), "s")
    start_time = cur_time

    for chamber_num in all_chambers:
        sample_size[chamber_num] = {}
    for chamber_num in all_chambers:
        avg_round_stage[chamber_num] = []
    sample_size["all"] = {
        "total": len(uid_freq_comp),
        "self_report": len(self_freq_comp),
        "random": len(uid_freq_comp) - len(self_freq_comp),
    }

    with (
        open("../data/raw_csvs_real/" + RECENT_PHASE + "_char.csv")
        if path.exists("../data/raw_csvs_real/")
        else open("../data/raw_csvs/" + RECENT_PHASE + "_char.csv")
    ) as f:
        stats = f
        reader = csvreader(stats)
        next(reader)
        reader = list(reader)

    # uid_freq_char and last_uid will help detect duplicate UIDs
    last_uid = "0"
    player = PlayerPhase(last_uid)
    uid_freq_char: list[str] = []

    # Append lines
    for line in reader:
        if line[0] in uid_freq_comp:
            if line[0] != last_uid:
                skip_uid = False
                if line[0] in uid_freq_char:
                    skip_uid = True
                else:
                    uid_freq_char.append(line[0])
            if not skip_uid:
                if line[0] != last_uid:
                    all_players[last_uid] = player
                    last_uid = line[0]
                    player = PlayerPhase(last_uid)
                if line[2] == "Topaz and Numby":
                    line[2] = "Topaz & Numby"
                elif line[2] == "March 7th":
                    line[2] = "Ice March 7th"
                player.add_character(
                    line[2],
                    line[3],
                    line[4],
                    line[5],
                    line[6],
                    line[7],
                    line[8],
                )
    all_players[last_uid] = player

    for comp in all_comps:
        if comp.player not in all_players:
            all_players[comp.player] = PlayerPhase(comp.player)
        all_players[comp.player].add_comp(comp)

    with open("../char_results/uids.csv", "w", newline="") as f:
        csv_writer = csvwriter(f)
        for uid in uid_freq_comp:
            csv_writer.writerow([uid])

    data = PickleData(
        all_players=all_players,
        all_comps=all_comps,
        avg_round_stage=avg_round_stage,
        sample_size=sample_size,
    )

    save_pickle_data("../data/pickle/data" + pf_filename + ".pkl", data)

    cur_time = time()
    print("done csv:", round(cur_time - start_time, 2), "s")
    start_time = cur_time


if __name__ == "__main__":
    main()
