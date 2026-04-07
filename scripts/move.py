"""Move files."""

import shutil
from os import listdir, mkdir, path

from comp_rates_config import RECENT_PHASE, RECENT_PHASE_PF, aa_mode, pf_filename

source_dirs = [
    "../results/char_results",
    "../results/comp_results",
    "../results/comp_results/json",
    "../results/mihomo",
]

for source_dir in source_dirs:
    if source_dir == "../results/comp_results/json":
        target_dir = "../results/comp_results/" + RECENT_PHASE_PF + "/json"
    elif source_dir == "../results/mihomo":
        target_dir = source_dir + "/" + RECENT_PHASE
    else:
        target_dir = source_dir + "/" + RECENT_PHASE_PF

    file_names = listdir(source_dir)
    if not path.exists(target_dir):
        mkdir(target_dir)
    for file_name in file_names:
        if file_name.endswith((".json", ".csv")) and (
            "demographic_collect" not in file_name
            or file_name == ("demographic_collect" + pf_filename + ".json")
            or (aa_mode and file_name == ("boss_names.json"))
        ):
            shutil.move(path.join(source_dir, file_name), target_dir)
            if source_dir == "../results/mihomo":
                if not path.exists(target_dir + "/" + RECENT_PHASE_PF):
                    mkdir(target_dir + "/" + RECENT_PHASE_PF)
                shutil.move(
                    path.join(target_dir, file_name),
                    target_dir + "/" + RECENT_PHASE_PF,
                )
