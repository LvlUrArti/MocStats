"""Calculate average appearance rate and average rounds for each character.

Calculate over the last three phases of MoC, PF, and AS.
"""

import json

# Import your existing models and loader
from combine_char import (
    BaseCharacterStats,
    dps_base_slugs,
    load_base_stats,
)
from comp_rates_config import (
    CHARS_INFO,
    ENDGAME_INFOS,
    MODE_ATTR_MAP,
    RECENT_PHASE,
    CharInfo,
)

# ----------------------------------------------------------------------
# Configuration
# ----------------------------------------------------------------------
CHARS_BY_SLUG: dict[str, CharInfo] = {}
for char_info in CHARS_INFO.values():
    CHARS_BY_SLUG[char_info.slug] = char_info

# ----------------------------------------------------------------------
# Group versions by mode and collect data dictionaries
# ----------------------------------------------------------------------
modes = ["moc", "pf", "as", "aa"]


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
            mode_obj = getattr(patch_data, MODE_ATTR_MAP[mode])
            version = mode_obj.ver if mode_obj else None
            if version:
                mode_versions[mode].append((patch_ver, version))
        if patch_ver == RECENT_PHASE:
            break

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


selected_versions = get_latest_unique_versions(modes)

for m in modes:
    print(f"Selected phases for {m}: {selected_versions[m]}")

# Load data for all unique versions
e0_data: dict[str, list[dict[str, BaseCharacterStats]]] = {}
e1_data: dict[str, list[dict[str, BaseCharacterStats]]] = {}

for mode, versions in selected_versions.items():
    e0_data[mode] = []
    e1_data[mode] = []

    for version in versions:
        base_path = f"../../results/all_results/{version}/{version}_{mode}/chars"
        e0_path = f"{base_path}/all.json"
        e1_path = f"{base_path}/all_C1.json"
        data_e0 = load_base_stats(e0_path)
        data_e1 = load_base_stats(e1_path)
        if data_e0:
            e0_data[mode].append(data_e0)
        if data_e1:
            e1_data[mode].append(data_e1)

# ----------------------------------------------------------------------
# Compute averages per character
# ----------------------------------------------------------------------
results: list[dict[str, float | int | str | None]] = []

# Determine all character names from the input data
all_chars: set[str] = set()
for phases in e0_data.values():
    for phase_data in phases:
        all_chars.update(phase_data.keys())

modes_phases_data: dict[str, dict[str, list[dict[str, BaseCharacterStats]]]] = {
    "": e0_data,
    "_e1": e1_data,
}

default_values = {
    "moc": 11,
    "pf": 22000,
    "as": 3000,
    "aa": 6,
}

cycle_modes = {"moc", "aa"}

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
    for mode in modes:
        valid_rounds = 0

        for suffix, mode_phases_data in modes_phases_data.items():
            invalid_value = 99.99 if mode in cycle_modes else 0
            phases_data = mode_phases_data.get(mode, [])

            # Appearance rate: average over phases where character exists
            app_rates: list[float] = []
            app_rates.extend(
                phase_data[char].app_rate
                for phase_data in phases_data
                if char in phase_data
            )
            if app_rates:
                entry[f"{mode}_usage{suffix}"] = round(
                    sum(app_rates) / len(app_rates),
                    2,
                )
            else:
                entry[f"{mode}_usage{suffix}"] = 0.0

            # Average rounds: average over phases where character exists
            avg_rounds: list[float | int] = []
            valid_rounds = 0

            for phase_data in phases_data:
                if char in phase_data:
                    stats = phase_data[char]

                    valid_rounds += 1
                    if stats.avg_round != invalid_value:
                        avg_rounds.append(stats.avg_round)
                    else:
                        avg_rounds.append(default_values[mode])
            if avg_rounds:
                value = round(
                    sum(avg_rounds) / len(avg_rounds),
                    2 if mode in cycle_modes else 0,
                )
                entry[f"{mode}_score{suffix}"] = (
                    int(value) if mode not in cycle_modes else value
                )
            else:
                entry[f"{mode}_score{suffix}"] = default_values[mode]

        entry[f"{mode}_new"] = valid_rounds <= 1

    results.append(entry)

# ----------------------------------------------------------------------
# Save to JSON
# ----------------------------------------------------------------------
output_path = f"../../results/all_results/{RECENT_PHASE}/histograph.json"
with open(output_path, "w") as f:
    json.dump(results, f, indent=2)
