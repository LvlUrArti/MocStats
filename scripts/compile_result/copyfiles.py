"""Copy files to web_results."""

import json
from os import mkdir, path
from pathlib import Path
from shutil import copyfile, copytree, make_archive, rmtree
from sys import path as sys_path

sys_path.append("../")
from comp_rates_config import (
    BASE_RESULT_PATH,
    ENDGAME_INFO,
    RECENT_PHASE,
    aa_mode,
    moc_mode,
    pf_filename,
)
from send2trash import send2trash


def copy_json_files(src_dir: Path, dst_dir: Path) -> None:
    """Copy all .json files from src_dir to dst_dir, creating dst_dir if needed."""
    dst_dir.mkdir(parents=True, exist_ok=True)
    for json_file in src_dir.glob("*.json"):
        copyfile(json_file, dst_dir / json_file.name)


moc_suffix = pf_filename.replace("_", "")

if moc_mode and path.exists("../../results/web_results"):
    send2trash("../../results/web_results")
    mkdir("../../results/web_results")
mkdir("../../results/web_results/" + moc_suffix)

if aa_mode:
    copy_json_files(
        Path(f"../../results/all_results/{RECENT_PHASE}"),
        Path("../../results/web_results"),
    )

source_dirs = {
    "": "/chars",
    "/duos": "/chars",
    "/comps": "/comps",
}

for source, target in source_dirs.items():
    source_dir = Path(f"../../{BASE_RESULT_PATH}{source}")
    target_dir = Path(f"../../results/web_results/{moc_suffix}{target}")
    copy_json_files(source_dir, target_dir)


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


if aa_mode and ENDGAME_INFO:
    make_archive("../../results/results", "zip", "../../results/web_results")
    with open("../../data/versions/aa_boss_names.json") as f:
        boss_names = json.load(f)

    with open("../../results/web_results/boss_names.json", "w") as f:
        json.dump(boss_names[ENDGAME_INFO.aa_ver], f, indent=2)

    copy_results()
