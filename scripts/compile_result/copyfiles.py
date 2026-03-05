"""Copy files to web_results."""

import shutil
from os import listdir, mkdir, path
from sys import path as sys_path

sys_path.append("../")
from comp_rates_config import (
    RECENT_PHASE_PF,
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
    "../../results/char_results/" + RECENT_PHASE_PF,
    "../../results/comp_results/" + RECENT_PHASE_PF + "/json",
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
        common_file = file_name in ["builds.json", "boss_names.json", "histograph.json"]
        if ("comp_results" in source_dir and "combined" in file_name) or (
            file_name in {"duo_usages.json", "demographic.json"}
            or (common_file and moc_mode)
        ):
            if common_file:
                temp_target_dir = target_dir
                target_dir = "../../results/web_results"
            copyfrom = path.join(source_dir, file_name)
            copyto = path.join(target_dir, file_name)
            shutil.copyfile(copyfrom, copyto)
            if common_file:
                target_dir = temp_target_dir

if aa_mode:
    shutil.make_archive("../../results/results", "zip", "../../results/web_results")
