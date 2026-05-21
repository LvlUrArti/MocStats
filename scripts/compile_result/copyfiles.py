"""Copy files to web_results."""

import json
from os import listdir, mkdir, path
from shutil import copyfile, copytree, rmtree
from sys import path as sys_path

sys_path.append("../")
from comp_rates_config import (
    CHAR_RESULT_PATH,
    COMP_RESULT_PATH,
    ENDGAME_INFO,
    RECENT_PHASE,
    aa_mode,
    as_mode,
    moc_mode,
    pf_mode,
)
from send2trash import send2trash

if as_mode:
    moc_suffix = "as"
elif aa_mode:
    moc_suffix = "aa"
elif pf_mode:
    moc_suffix = "pf"
else:
    moc_suffix = "moc"

source_dirs = [
    f"../../{CHAR_RESULT_PATH}",
    f"../../{CHAR_RESULT_PATH}/duos",
    f"../../{COMP_RESULT_PATH}/json",
]

if moc_mode and path.exists("../../results/web_results"):
    send2trash("../../results/web_results")
    mkdir("../../results/web_results")
mkdir("../../results/web_results/" + moc_suffix)

for source_dir in source_dirs:
    if "comp_results" in source_dir:
        target_dir = "../../results/web_results/" + moc_suffix + "/comps"
    else:
        target_dir = "../../results/web_results/" + moc_suffix + "/chars"

    temp_target_dir = ""
    file_names = listdir(source_dir)
    if path.exists(target_dir):
        send2trash(target_dir)
    mkdir(target_dir)
    for file_name in file_names:
        common_file = file_name in {"builds.json", "histograph.json"}
        if ("comp_results" in source_dir and "combined" in file_name) or (
            file_name in {"duo_usages.json", "demographic.json"}
            or (common_file and moc_mode)
        ):
            if common_file:
                temp_target_dir = target_dir
                target_dir = "../../results/web_results"
            copyfrom = path.join(source_dir, file_name)
            copyto = path.join(target_dir, file_name)
            copyfile(copyfrom, copyto)
            if common_file:
                target_dir = temp_target_dir


def copy_results() -> None:
    """Copy results to a specified location."""
    # Construct full destination path
    destination = f"../../results/final_results/{RECENT_PHASE}"

    # Check if destination already exists
    if path.exists(destination):
        overwrite = input(
            f"Warning: '{destination}' already exists. Overwrite? (y/n): ",
        )
        if overwrite != "y":
            print("Operation cancelled.")
            return

        # If it's a directory, remove it first
        if path.isdir(destination):
            try:
                rmtree(destination)
                print(f"Removed existing folder: {destination}")
            except Exception as e:
                print(f"Error removing existing folder: {e}")
                return

    # Perform the copy operation
    try:
        # Use copytree to copy entire folder
        copytree("../../results/web_results", destination)

        print("✅ Folder copied successfully!")
        print(f"   Destination: {destination}")

    except Exception as e:
        print(f"Error during copy operation: {e}")


if aa_mode and ENDGAME_INFO:
    with open("../../data/versions/aa_boss_names.json") as f:
        boss_names = json.load(f)

    with open("../../results/web_results/boss_names.json", "w") as f:
        json.dump(boss_names[ENDGAME_INFO.aa_ver], f, indent=2)

    copy_results()
