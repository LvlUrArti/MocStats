"""Calculate average appearance rate and average rounds for each character.

Calculate over the last three phases of MoC, PF, and AS.
"""

import json

# Import your existing models and loader
from combine_char import FullCharacterStats, dps_base_slugs, load_full_stats
from comp_rates_config import CHARS_INFO, RECENT_PHASE, CharInfo

# ----------------------------------------------------------------------
# Configuration
# ----------------------------------------------------------------------
# TODO: Move this to a JSON file
VERSIONS: list[tuple[str, str]] = [
    ("3.6.3", "moc"),
    ("3.7.1", "as"),
    ("3.7.2", "pf"),
    ("3.7.3", "moc"),
    ("3.8.1", "as"),
    ("3.8.2", "pf"),
    ("3.8.3", "moc"),
    ("3.8.4", "as"),
    ("4.0.1", "pf"),
]

CHARS_BY_SLUG: dict[str, CharInfo] = {}
for char_info in CHARS_INFO.values():
    CHARS_BY_SLUG[char_info.slug] = char_info

# ----------------------------------------------------------------------
# Group versions by mode and collect data dictionaries
# ----------------------------------------------------------------------
snapshots = [(v, mode) for v, mode in VERSIONS]  # list of (version, updated_mode)
modes = ["moc", "pf", "as"]

# Precompute for each snapshot index the last update index for each mode
# list of dicts: last_update_idx[i][mode]
# = index of most recent ≤ i where mode was updated
last_update_idx: list[dict[str, int | None]] = []
for i, _snapshot in enumerate(snapshots):
    row: dict[str, int | None] = {}
    for m in modes:
        # search backwards from i to find the most recent snapshot where mode == m
        idx = None
        for j in range(i, -1, -1):
            if snapshots[j][1] == m:
                idx = j
                break
        row[m] = idx
    last_update_idx.append(row)

# Collect up to 3 snapshots per mode, starting from the most recent overall version
selected_versions: dict[str, list[str]] = {m: [] for m in modes}
used_updates: dict[str, set[str]] = {
    m: set() for m in modes
}  # track underlying update versions already covered

for i in range(len(snapshots) - 1, -1, -1):  # from newest to oldest
    v, updated_mode = snapshots[i]
    for m in modes:
        if len(selected_versions[m]) >= 3:
            continue
        last_i = last_update_idx[i][m]
        if last_i is None:
            continue  # mode never appears before this snapshot - shouldn't happen here
        underlying = snapshots[last_i][
            0
        ]  # version string of the last update for mode m
        if underlying not in used_updates[m]:
            selected_versions[m].append(v)
            used_updates[m].add(underlying)

# Reverse each list so that they are in chronological order (oldest first)
for m in modes:
    selected_versions[m].reverse()
    print(f"Selected snapshots for {m}: {selected_versions[m]}")

# Load data for all unique versions
mode_to_phases: dict[str, list[dict[str, FullCharacterStats]]] = {}

for mode, versions in selected_versions.items():
    for version in versions:
        if mode not in mode_to_phases:
            mode_to_phases[mode] = []
        folder = f"{version}_{mode}" if mode != "moc" else version
        file_path = f"../../results/char_results/{folder}/all2.json"
        try:
            data = load_full_stats(file_path)
            mode_to_phases[mode].append(data)
        except FileNotFoundError:
            print(f"Warning: File not found for version {version} ({mode}), skipping.")
            continue

# ----------------------------------------------------------------------
# Compute averages per character
# ----------------------------------------------------------------------
results: list[dict[str, float | int | str | None]] = []

# Determine all character names from the input data
all_chars: set[str] = set()
for phases in mode_to_phases.values():
    for phase_data in phases:
        all_chars.update(phase_data.keys())

for char in sorted(all_chars):
    # Determine base slug by stripping known prefixes
    base_char = char[5:] if char.startswith(("solo-", "supp-")) else char

    # Prepare output entry
    entry: dict[str, float | int | str | None] = {
        "char": base_char,
    }

    # Add special_role only if this character has multiple roles
    if base_char in dps_base_slugs:
        if char.startswith("solo-"):
            entry["role"] = "dps"
        elif char.startswith("supp-"):
            entry["role"] = "specialist"
        else:
            continue
    elif base_char in CHARS_BY_SLUG:
        entry["role"] = CHARS_BY_SLUG[base_char].role[0]

    # Process each mode
    for mode in ["moc", "pf", "as"]:
        invalid_value = 99.99 if mode == "moc" else 0
        if mode == "moc":
            default_value = 11
        elif mode == "pf":
            default_value = 22000
        else:
            default_value = 3000
        phases = mode_to_phases.get(mode, [])

        # Appearance rate: average over phases where character exists
        app_rates: list[float] = []
        app_rates.extend(
            phase_data[char].app_rate for phase_data in phases if char in phase_data
        )
        if app_rates:
            entry[f"{mode}_usage"] = round(sum(app_rates) / len(app_rates), 2)
        else:
            entry[f"{mode}_usage"] = 0.0

        # Average rounds: average over phases where character exists
        avg_rounds: list[float | int] = []
        valid_rounds = 0

        for phase_data in phases:
            if char in phase_data:
                stats = phase_data[char]

                valid_rounds += 1
                if stats.avg_round != invalid_value:
                    avg_rounds.append(stats.avg_round)
                else:
                    avg_rounds.append(default_value)
        if avg_rounds:
            value = round(
                sum(avg_rounds) / len(avg_rounds),
                2 if mode == "moc" else 0,
            )
            entry[f"{mode}_score"] = int(value) if mode != "moc" else value
        else:
            entry[f"{mode}_score"] = default_value

        entry[f"{mode}_new"] = valid_rounds <= 1

    results.append(entry)

# ----------------------------------------------------------------------
# Save to JSON
# ----------------------------------------------------------------------
output_path = f"../../results/char_results/{RECENT_PHASE}/histograph.json"
with open(output_path, "w") as f:
    json.dump(results, f, indent=2)
