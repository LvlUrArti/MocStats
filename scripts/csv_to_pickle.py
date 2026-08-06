"""Convert CSV files to pickle."""

from __future__ import annotations

from csv import DictReader
from csv import reader as csvreader
from csv import writer as csvwriter
from dataclasses import dataclass
from os import makedirs, path
from pickle import dump as pickle_dump
from pickle import load as pickle_load
from time import time

from comp_rates_config import (
    BASE_RESULT_PATH,
    BUILD_RESULT_PATH,
    CHAR_NAME_REPLACE,
    CHAR_RESULT_PATH,
    COMP_RESULT_PATH,
    DUOS_RESULT_PATH,
    RECENT_PHASE,
    RECENT_PHASE_PF,
    aa_mode,
    pf_filename,
    pf_mode,
    skip_random,
    skip_self,
)
from composition import Composition, Stage
from player_phase import OwnedChars, PlayerPhase

EXT_CHAR_NAME_REPLACE = {
    **CHAR_NAME_REPLACE,
    "March 7th": "Ice March 7th",
}

all_players: dict[str, PlayerPhase] = {}
all_comps: list[Composition] = []
avg_round_stage: dict[int, list[int]] = {}

if path.isfile("../../uids.csv"):
    with open("../../uids.csv", encoding="UTF8") as f:
        reader = csvreader(f, delimiter=",")
        self_uids = set(next(iter(reader)))
    with open("../../random.csv", encoding="UTF8") as f:
        reader = csvreader(f, delimiter=",")
        random_uids = set(next(iter(reader)))
    with open("../../collect/collected_stardb.csv", encoding="UTF8") as f:
        reader = csvreader(f, delimiter=",")
        star_db = {item for sublist in list(reader) for item in sublist}
    with open("../../collect/collected_hoyobuddy.csv", encoding="UTF8") as f:
        reader = csvreader(f, delimiter=",")
        hoyo_buddy = {item for sublist in list(reader) for item in sublist}
else:
    self_uids: set[str] = set()
    random_uids: set[str] = set()
    star_db: set[str] = set()
    hoyo_buddy: set[str] = set()


@dataclass
class PickleData:
    """Container for pickle data."""

    all_players: dict[str, PlayerPhase]
    all_comps: list[Composition]
    avg_round_stage: dict[int, list[int]]


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
        f"../{COMP_RESULT_PATH}",
        f"../{BUILD_RESULT_PATH}",
        f"../{CHAR_RESULT_PATH}",
        f"../{DUOS_RESULT_PATH}",
        "../data/pickle",
    ]:
        if not path.exists(make_path):
            makedirs(make_path)

    filename = RECENT_PHASE_PF.replace("_moc", "")
    with (
        open(f"../data/raw_csvs_real/{filename}.csv")
        if path.exists("../data/raw_csvs_real/")
        else open(f"../data/raw_csvs/{filename}.csv")
    ) as f:
        reader = list(DictReader(f))

    # uid_freq_comp will help detect duplicate UIDs
    if pf_mode:
        all_chambers: list[int] = [1, 2, 3, 4]
    elif aa_mode:
        all_chambers: list[int] = [1, 2]
    else:
        all_chambers: list[int] = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]
    uid_freq_comp: dict[str, int] = {}
    last_uid = "0"
    skip_uid = False

    for line in reader:
        player = line["uid"]
        stage = int(line["floor"])
        node = (stage if stage != 4 else 1) if aa_mode else int(line["node"])
        if aa_mode:
            stage = 1 if stage <= 3 else 2

        round_num = int(line["round_num"])
        if skip_self and player in self_uids:
            continue
        if skip_random and player not in self_uids:
            continue
        if player != last_uid:
            skip_uid = False
            if player in uid_freq_comp:
                skip_uid = True
            else:
                uid_freq_comp[player] = 1
        last_uid = player
        if not skip_uid:
            comp_chars_temp: list[str] = []
            for i in range(1, 5):
                char = line[f"ch{i}"]
                if char != "":
                    if char in EXT_CHAR_NAME_REPLACE:
                        char = EXT_CHAR_NAME_REPLACE[char]
                    comp_chars_temp.append(char)

            cons_chars_temp: list[int] = []
            if "cons1" in line:
                cons_chars_temp.extend(
                    int(float(line[f"cons{i}"]))
                    for i in (range(1, 5))
                    if line[f"cons{i}"] != ""
                )

            if comp_chars_temp:
                comp = Composition(
                    player=player,
                    comp_chars=comp_chars_temp,
                    round_num=round_num,
                    star_num=int(line["star_num"]),
                    room=Stage(stage, node),
                    buff=line.get("buff", None),
                    comp_chars_cons=cons_chars_temp,
                    is_hard_mode=line["hard_mode"] == "True" if aa_mode else None,
                )
                all_comps.append(comp)

    cur_time = time()
    print("done csv comps:", round(cur_time - start_time, 2), "s")
    start_time = cur_time

    for chamber_num in all_chambers:
        avg_round_stage[chamber_num] = []

    with (
        open("../data/raw_csvs_real/" + RECENT_PHASE + "_char.csv")
        if path.exists("../data/raw_csvs_real/")
        else open("../data/raw_csvs/" + RECENT_PHASE + "_char.csv")
    ) as f:
        reader = list(DictReader(f))

    # uid_freq_char and last_uid will help detect duplicate UIDs
    last_uid = "0"
    player = PlayerPhase(last_uid)
    uid_freq_char: set[str] = set()

    # Append lines
    for line in reader:
        if line["uid"] in uid_freq_comp:
            if line["uid"] != last_uid:
                skip_uid = False
                if line["uid"] in uid_freq_char:
                    skip_uid = True
                else:
                    uid_freq_char.add(line["uid"])
            if not skip_uid:
                if line["uid"] != last_uid:
                    all_players[last_uid] = player
                    last_uid = line["uid"]
                    player = PlayerPhase(last_uid)
                if line["name"] in EXT_CHAR_NAME_REPLACE:
                    line["name"] = EXT_CHAR_NAME_REPLACE[line["name"]]
                player.add_character(
                    line["name"],
                    OwnedChars(
                        level=int(line["level"]),
                        cons=int(line["cons"]),
                        weapon=line["weapon"],
                        element=line["element"],
                        artifacts=line.get("artifacts", ""),
                        planars=line.get("relics", ""),
                    ),
                )
    all_players[last_uid] = player

    for comp in all_comps:
        if comp.player not in all_players:
            all_players[comp.player] = PlayerPhase(comp.player)
        all_players[comp.player].add_comp(comp)

    with open(f"../{BASE_RESULT_PATH}/uids.csv", "w", newline="") as f:
        csv_writer = csvwriter(f)
        for uid in uid_freq_comp:
            csv_writer.writerow([uid])

    data = PickleData(
        all_players=all_players,
        all_comps=all_comps,
        avg_round_stage=avg_round_stage,
    )

    save_pickle_data("../data/pickle/data" + pf_filename + ".pkl", data)

    cur_time = time()
    print("done csv:", round(cur_time - start_time, 2), "s")
    start_time = cur_time


if __name__ == "__main__":
    main()
