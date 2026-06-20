"""Copy files to web_results."""

import json
from os import path
from pathlib import Path
from shutil import copy, copytree, make_archive, rmtree
from sys import path as sys_path

sys_path.append("../")
from comp_rates_config import ENDGAME_INFO, RECENT_PHASE
from utils.copy_json_files import copy_json_files


def copy_results() -> None:
    """Copy results to a specified location."""
    destination = f"../../results/final_results/{RECENT_PHASE}"

    if path.exists(destination):
        overwrite = input(
            f"Warning: '{destination}' already exists. Overwrite? (y/n): ",
        )
        if overwrite != "y":
            return
        rmtree(destination)

    copytree("../../results/web_results", destination)


if ENDGAME_INFO:
    copy_json_files(
        Path(f"../../results/all_results/{RECENT_PHASE}"),
        Path("../../results/web_results"),
    )

    copy("../../data/versions/config.json", "../../results/final_results/config.json")

    if ENDGAME_INFO.aa and ENDGAME_INFO.aa.ver:
        with open("../../data/versions/aa_boss_names.json") as f:
            boss_names = json.load(f)

        with open("../../results/web_results/boss_names.json", "w") as f:
            json.dump(boss_names[ENDGAME_INFO.aa.ver], f, indent=2)

    make_archive("../../results/results", "zip", "../../results/web_results")
    copy_results()
