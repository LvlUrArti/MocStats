"""Calculate average appearance rate and average rounds for each character.

Calculate over the last three phases of MoC, PF, and AS.
"""

import json

# Import your existing models and loader
from combine_char import FullCharacterStats, dps_base_slugs, load_full_stats
from comp_rates_config import CHARS_INFO, ENDGAME_INFOS, RECENT_PHASE, CharInfo

# ----------------------------------------------------------------------
# Configuration
# ----------------------------------------------------------------------
CHARS_BY_SLUG: dict[str, CharInfo] = {}
for char_info in CHARS_INFO.values():
    CHARS_BY_SLUG[char_info.slug] = char_info

# ----------------------------------------------------------------------
# Group versions by mode and collect data dictionaries
# ----------------------------------------------------------------------
modes = ["moc", "pf", "as"]


def get_latest_unique_versions(
    modes: list[str],
    count: int = 3,
) -> dict[str, list[str]]:
    """Get unique versions.

    For each mode, collect versions in order of appearance.
    then return the last `count` unique versions in chronological order.
    """
    # Initialize list for each mode
    mode_versions: dict[str, list[tuple[str, str]]] = {mode: [] for mode in modes}

    # Iterate over outer keys
    for patch_ver, patch_data in ENDGAME_INFOS.items():
        for mode in modes:
            match mode:
                case "pf":
                    version = patch_data.pf_ver
                case "aa":
                    version = patch_data.aa_ver
                case "as":
                    version = patch_data.as_ver
                case "moc" | _:
                    version = patch_data.moc_ver
            if version:
                mode_versions[mode].append((patch_ver, version))

    # Extract latest unique versions
    result: dict[str, list[str]] = {}
    for mode, versions in mode_versions.items():
        # Get unique versions in reverse order of appearance
        unique_ver: list[str] = []
        seen: set[str] = set()
        for ver, v in reversed(versions):
            if v not in seen:
                seen.add(v)
                unique_ver.append(ver)
                if len(unique_ver) == count:
                    break
        # Reverse back to chronological order
        result[mode] = list(reversed(unique_ver))

    return result


modes = ["moc", "pf", "as"]
selected_versions = get_latest_unique_versions(modes)

for m in modes:
    print(f"Selected phases for {m}: {selected_versions[m]}")

# Load data for all unique versions
mode_to_phases: dict[str, list[dict[str, FullCharacterStats]]] = {}

for mode, versions in selected_versions.items():
    for version in versions:
        if mode not in mode_to_phases:
            mode_to_phases[mode] = []
        folder = f"{version}_{mode}" if mode != "moc" else version
        file_path = f"../../results/char_results/{folder}/all.json"
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
