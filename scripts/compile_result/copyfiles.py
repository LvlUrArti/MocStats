"""Copy files to web_results."""

from os import mkdir
from pathlib import Path
from sys import path as sys_path

sys_path.append("../")
from comp_rates_config import BASE_RESULT_PATH, pf_filename
from utils.copy_json_files import copy_json_files

moc_suffix = pf_filename.replace("_", "")

mkdir("../../results/web_results/" + moc_suffix)

source_dirs = {
    "": "/chars",
    "/duos": "/chars",
    "/comps": "/comps",
}

for source, target in source_dirs.items():
    source_dir = Path(f"../../{BASE_RESULT_PATH}{source}")
    target_dir = Path(f"../../results/web_results/{moc_suffix}{target}")
    copy_json_files(source_dir, target_dir)
