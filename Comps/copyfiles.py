"""Copy files to web_results."""

import shutil
from os import listdir, mkdir, path

from comp_rates_config import RECENT_PHASE, as_mode, pf_mode
from send2trash import send2trash

suffix = ""
moc_suffix = ""
if as_mode:
    suffix = "_as"
    moc_suffix = "as"
elif pf_mode:
    suffix = "_pf"
    moc_suffix = "pf"
else:
    moc_suffix = "moc"

RECENT_PHASE_PF = RECENT_PHASE + suffix

source_dirs = [
    "../char_results/" + RECENT_PHASE_PF,
    "../comp_results/" + RECENT_PHASE_PF + "/json",
]

for source_dir in source_dirs:
    if "comp_results" in source_dir:
        target_dir = "../web_results/" + moc_suffix + "/comps"
    else:
        target_dir = "../web_results/" + moc_suffix + "/chars"

    temp_target_dir = ""
    file_names = listdir(source_dir)
    if path.exists(target_dir):
        send2trash(target_dir)
    mkdir(target_dir)
    for file_name in file_names:
        if ("comp_results" in source_dir and "combined" in file_name) or (
            file_name == "duo_usages.json"
            or file_name == ("demographic_collect" + suffix + ".json")
            or (file_name == "builds.json" and (RECENT_PHASE + "_as") in source_dir)
        ):
            if file_name == "builds.json":
                temp_target_dir = target_dir
                target_dir = "../web_results"
            copyfrom = path.join(source_dir, file_name)
            copyto = path.join(target_dir, file_name)
            shutil.copyfile(copyfrom, copyto)
            if file_name == "builds.json":
                target_dir = temp_target_dir

if as_mode:
    shutil.make_archive("../results", "zip", "../web_results")
