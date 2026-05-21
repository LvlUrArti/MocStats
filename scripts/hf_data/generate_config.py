"""Generate a list of configs from a folder of csv files."""

from datetime import datetime
from json import dumps as json_dumps
from json import load as json_load

KNOWN_SUFFIXES = ["char", "pf", "as", "aa", "build"]

ENDGAME_NAMES = {
    "moc": "Memory of Chaos",
    "pf": "Pure Fiction",
    "as": "Apocalyptic Shadow",
    "aa": "Anomaly Arbitration",
}

IGNORE_SUFFIXES = ["rogue", "nous", "tourn"]


def get_version_map(filenames: list[str]) -> dict[str, dict[str, str | bool | None]]:
    """Group filenames by version and identifies their splits.

    Returns: { "version_str": [{"split": "split_name", "path": "filename.csv"}, ...] }.
    """
    version_map: dict[str, dict[str, str | bool | None]] = {}

    def get_date(date: str) -> datetime:
        return datetime.strptime(date, "%d/%m/%Y")

    with open("../../data/versions/endgame_versions.json") as f:
        endgame_versions: dict[str, dict[str, dict[str, str]]] = json_load(f)

    def get_ver(split_name: str, collect_date: str) -> str | None:
        collect_datetime = get_date(collect_date)
        for endgame, versions in reversed(
            endgame_versions[ENDGAME_NAMES[split_name]].items(),
        ):
            start_datetime = get_date(versions["time_start"])
            end_datetime = get_date(versions["time_end"])

            if start_datetime <= collect_datetime <= end_datetime:
                return endgame
        return None

    with open("../../data/versions/collect_dates.json") as f:
        collect_dates: dict[str, str] = json_load(f)

    for version, collect_date in collect_dates.items():
        version_map[version] = {
            "collect_date": collect_date,
            "moc_ver": None,
            "pf_ver": None,
            "as_ver": None,
            "aa_ver": None,
        }

    for filename in sorted(filenames):
        # Remove supported extensions
        name_no_ext: str = filename.replace(".csv", "").replace(".json", "")
        if any(name_no_ext.endswith(f"_{suffix}") for suffix in IGNORE_SUFFIXES):
            continue

        version: str = ""
        split_name: str = ""

        # Logic: Check if filename ends with a known suffix
        matched_suffix: bool = False
        for suffix in KNOWN_SUFFIXES:
            if name_no_ext.endswith(f"_{suffix}"):
                split_name = suffix
                version = name_no_ext[: -(len(suffix) + 1)]
                matched_suffix = True
                break

        if not matched_suffix:
            version = name_no_ext
            split_name = "moc"

        if version not in collect_dates:
            print("collect date not found:  ", version)
            continue

        if split_name not in {"pf", "as", "aa", "moc"}:
            continue

        version_map[version][f"{split_name}_ver"] = get_ver(
            split_name,
            collect_dates[version],
        )

    return version_map


# Read files from repo_files.csv
repo_files: list[str] = []

with open("../../data/repo_files_real.csv") as f:
    repo_files.extend(line.strip() for line in f)

save_entries = get_version_map(repo_files)

with open("../../data/versions/config.json", "w") as out_file:
    out_file.write(json_dumps(save_entries, indent=2))
