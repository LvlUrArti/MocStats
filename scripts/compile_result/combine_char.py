"""Combine JSON results from different game modes into a unified build dataset."""

import json
from os.path import exists
from sys import path as sys_path

sys_path.append("../")

from comp_rates_config import (
    CHARS_INFO,
    ENDGAME_INFO,
    ENDGAME_INFOS,
    LIGHT_CONES,
    RECENT_PHASE,
)
from pydantic import BaseModel

# ----------------------------------------------------------------------
# Constants
# ----------------------------------------------------------------------
DEFAULT_CYCLE = 99.99
DEFAULT_SCORE = 0
DEFAULT_APP = 0.0
# How many top items we keep per category (weapons, artifacts, planars, relic stats)
GEAR_COUNTS = {
    "weapons": 10,
    "artifacts": 10,
    "planars": 5,
    "body": 3,
    "feet": 3,
    "sphere": 3,
    "rope": 3,
}

# List of numeric fields that need weighted averaging across game modes
NUMERIC_STATS = [
    "app_0",
    "app_1",
    "app_2",
    "app_3",
    "app_4",
    "app_5",
    "app_6",
    "cons_avg",
    "char_lvl",
    "light_cone_lvl",
    "attack_lvl",
    "skill_lvl",
    "ultimate_lvl",
    "talent_lvl",
    "max_hp",
    "atk",
    "dfns",
    "speed",
    "crate",
    "cdmg",
    "dmg_boost",
    "heal_boost",
    "energy_regen",
    "effect_res",
    "effect_rate",
    "break_effect",
    "spd_sub",
    "hp_sub",
    "atk_sub",
    "def_sub",
    "crate_sub",
    "cdmg_sub",
    "res_sub",
    "ehr_sub",
    "break_sub",
]


# ----------------------------------------------------------------------
# Pydantic models for raw input data
# ----------------------------------------------------------------------
class BaseCharacterStats(BaseModel):
    """Base character stats from a single game mode (MoC, PF, AS, or AA)."""

    char: str
    app_rate: float
    app_rate_e0: float
    avg_round: float | int
    std_dev_round: float | int
    q1_round: float | int
    rarity: str

    # Weapons 1-10
    weapon_1: str
    weapon_1_app: float
    weapon_1_round: float | int
    weapon_2: str
    weapon_2_app: float
    weapon_2_round: float | int
    weapon_3: str
    weapon_3_app: float
    weapon_3_round: float | int
    weapon_4: str
    weapon_4_app: float
    weapon_4_round: float | int
    weapon_5: str
    weapon_5_app: float
    weapon_5_round: float | int
    weapon_6: str
    weapon_6_app: float
    weapon_6_round: float | int
    weapon_7: str
    weapon_7_app: float
    weapon_7_round: float | int
    weapon_8: str
    weapon_8_app: float
    weapon_8_round: float | int
    weapon_9: str
    weapon_9_app: float
    weapon_9_round: float | int
    weapon_10: str
    weapon_10_app: float
    weapon_10_round: float | int

    # Artifacts 1-10
    artifact_1: str
    artifact_1_1: str
    artifact_1_2: str
    artifact_1_app: float
    artifact_1_round: float | int
    artifact_2: str
    artifact_2_1: str
    artifact_2_2: str
    artifact_2_app: float
    artifact_2_round: float | int
    artifact_3: str
    artifact_3_1: str
    artifact_3_2: str
    artifact_3_app: float
    artifact_3_round: float | int
    artifact_4: str
    artifact_4_1: str
    artifact_4_2: str
    artifact_4_app: float
    artifact_4_round: float | int
    artifact_5: str
    artifact_5_1: str
    artifact_5_2: str
    artifact_5_app: float
    artifact_5_round: float | int
    artifact_6: str
    artifact_6_1: str
    artifact_6_2: str
    artifact_6_app: float
    artifact_6_round: float | int
    artifact_7: str
    artifact_7_1: str
    artifact_7_2: str
    artifact_7_app: float
    artifact_7_round: float | int
    artifact_8: str
    artifact_8_1: str
    artifact_8_2: str
    artifact_8_app: float
    artifact_8_round: float | int
    artifact_9: str
    artifact_9_1: str
    artifact_9_2: str
    artifact_9_app: float
    artifact_9_round: float | int
    artifact_10: str
    artifact_10_1: str
    artifact_10_2: str
    artifact_10_app: float
    artifact_10_round: float | int

    # Planars 1-5
    planar_1: str
    planar_1_app: float
    planar_1_round: float | int
    planar_2: str
    planar_2_app: float
    planar_2_round: float | int
    planar_3: str
    planar_3_app: float
    planar_3_round: float | int
    planar_4: str
    planar_4_app: float
    planar_4_round: float | int
    planar_5: str
    planar_5_app: float
    planar_5_round: float | int

    # Eidolon appearance rates and cycle data
    app_0: float
    round_0: float | int
    app_1: float
    round_1: float | int
    app_2: float
    round_2: float | int
    app_3: float
    round_3: float | int
    app_4: float
    round_4: float | int
    app_5: float
    round_5: float | int
    app_6: float
    round_6: float | int
    cons_avg: float
    sample: int
    sample_app_flat: int


class FullCharacterStats(BaseCharacterStats):
    """Extended stats including character levels, light cone levels, substats, etc."""

    char_lvl: float
    light_cone_lvl: float
    attack_lvl: float
    skill_lvl: float
    ultimate_lvl: float
    talent_lvl: float
    max_hp: float
    atk: float
    dfns: float
    speed: float
    crate: float
    cdmg: float
    dmg_boost: float
    heal_boost: float
    energy_regen: float
    effect_res: float
    effect_rate: float
    break_effect: float
    spd_sub: float
    hp_sub: float
    atk_sub: float
    def_sub: float
    crate_sub: float
    cdmg_sub: float
    res_sub: float
    ehr_sub: float
    break_sub: float
    sample_size_players: int

    # Main stat usage on relics (body, feet, sphere, rope)
    body_stats_1: str
    body_stats_1_app: float
    body_stats_2: str
    body_stats_2_app: float
    body_stats_3: str
    body_stats_3_app: float
    feet_stats_1: str
    feet_stats_1_app: float
    feet_stats_2: str
    feet_stats_2_app: float
    feet_stats_3: str
    feet_stats_3_app: float
    sphere_stats_1: str
    sphere_stats_1_app: float
    sphere_stats_2: str
    sphere_stats_2_app: float
    sphere_stats_3: str
    sphere_stats_3_app: float
    rope_stats_1: str
    rope_stats_1_app: float
    rope_stats_2: str
    rope_stats_2_app: float
    rope_stats_3: str
    rope_stats_3_app: float


# ----------------------------------------------------------------------
# Helper functions to load JSON data into Pydantic models
# ----------------------------------------------------------------------
def load_base_stats(file_path: str) -> dict[str, BaseCharacterStats]:
    """Load basic stats (e0s1, e1, s0 files)."""
    try:
        with open(file_path) as file:
            data = json.load(file)
        return {item["char"]: BaseCharacterStats(**item) for item in data}
    except FileNotFoundError:
        return {}


def load_full_stats(file_path: str) -> dict[str, FullCharacterStats]:
    """Load full stats (all.json files with extended info)."""
    try:
        with open(file_path) as file:
            data = json.load(file)
        return {item["char"]: FullCharacterStats(**item) for item in data}
    except FileNotFoundError:
        return {}


# ----------------------------------------------------------------------
# Load all input data for each game mode
# ----------------------------------------------------------------------
def get_read_path(ver: str, mode: str) -> str:
    """Get the path to read data from."""
    return f"../../results/all_results/{ver}/{ver}_{mode}/chars"


def get_previous_mode_phase(mode: str) -> str:
    """Get the previous phase of a mode."""
    mode_key = f"{mode}_ver"  # e.g., "aa_ver"
    prev_phase = RECENT_PHASE
    check_ver = getattr(ENDGAME_INFO, mode_key)

    for phase, inner in ENDGAME_INFOS.items():
        cur_ver = getattr(inner, mode_key)
        if cur_ver == check_ver:
            break
        prev_phase = phase

    if exists(get_read_path(prev_phase, mode)):
        return prev_phase
    return RECENT_PHASE


raw: dict[str, dict[str, BaseCharacterStats]] = {}
raw_full: dict[str, dict[str, FullCharacterStats]] = {}
modes = ["moc", "pf", "as", "aa"]

for suf in ["", "_prev"]:
    phases = {
        mode: get_previous_mode_phase(mode) if suf else RECENT_PHASE for mode in modes
    }
    for mode in modes:
        folder_dir = get_read_path(phases[mode], mode)
        raw_full[f"{mode}{suf}"] = load_full_stats(f"{folder_dir}/all.json")
        raw[f"{mode}_e1{suf}"] = load_base_stats(f"{folder_dir}/all_C1.json")
        raw[f"{mode}_s0{suf}"] = load_base_stats(f"{folder_dir}/all_E0S0.json")

    read_path = get_read_path(phases["aa"], "aa")
    boss_configs = [(1, "1-1"), (2, "1-2"), (3, "1-3"), (4, "2-1")]
    for boss_num, boss_room in boss_configs:
        file_name = f"{read_path}/{boss_room}"
        raw[f"aa_boss_{boss_num}{suf}"] = load_base_stats(f"{file_name}.json")
        raw[f"aa_boss_{boss_num}_e1{suf}"] = load_base_stats(f"{file_name}_C1.json")
        raw[f"aa_boss_{boss_num}_s0{suf}"] = load_base_stats(f"{file_name}_E0S0.json")


# ----------------------------------------------------------------------
# Pydantic models for aggregated usage (weapons, artifacts, planars, relic stats)
# ----------------------------------------------------------------------
class GearStats(BaseModel):
    """Stats for a single piece of gear (weapon, artifact, planar)."""

    app: float  # appearance percentage
    round: int | float  # average cycles
    set1: str = ""  # first artifact set (for artifacts only)
    set2: str = ""  # second artifact set (for artifacts only)


class CharacterGearUsage(BaseModel):
    """Aggregated gear and relic main stat usage for one character."""

    weapons: dict[str, GearStats]
    artifacts: dict[str, GearStats]
    planars: dict[str, GearStats]
    body_stats: dict[str, float]  # main stat name -> appearance %
    feet_stats: dict[str, float]
    sphere_stats: dict[str, float]
    rope_stats: dict[str, float]


def is_valid_name(s: str) -> bool:
    """Return True if string is not empty and not '-'."""
    return bool(s) and s != "-"


def build_gear_usage(
    raw_data: dict[str, FullCharacterStats],
) -> dict[str, CharacterGearUsage]:
    """Convert raw FullCharacterStats into a CharacterGearUsage dict for each character.

    This groups weapons, artifacts, planars, and relic main stats into dictionaries.
    """
    usage_by_char: dict[str, CharacterGearUsage] = {}

    for char_name, stats in raw_data.items():
        # --- Weapons, Artifacts, Planars ---
        gear_collections: dict[str, dict[str, GearStats]] = {}

        for category in ["weapon", "artifact", "planar"]:
            gear_dict: dict[str, GearStats] = {}
            count = GEAR_COUNTS[f"{category}s"]  # e.g., "weapons" -> 10
            for i in range(1, count + 1):
                name = getattr(stats, f"{category}_{i}")
                if is_valid_name(name):
                    gear_dict[name] = GearStats(
                        app=getattr(stats, f"{category}_{i}_app"),
                        round=getattr(stats, f"{category}_{i}_round"),
                        set1=getattr(stats, f"{category}_{i}_1", ""),
                        set2=getattr(stats, f"{category}_{i}_2", ""),
                    )
            gear_collections[category] = gear_dict

        # --- Relic main stats (body, feet, sphere, rope) ---
        relic_stats: dict[str, dict[str, float]] = {}
        for part in ["body", "feet", "sphere", "rope"]:
            part_dict: dict[str, float] = {}
            count = GEAR_COUNTS[part]
            for i in range(1, count + 1):
                name = getattr(stats, f"{part}_stats_{i}")
                if is_valid_name(name):
                    part_dict[name] = getattr(stats, f"{part}_stats_{i}_app")
            relic_stats[part] = part_dict

        usage_by_char[char_name] = CharacterGearUsage(
            weapons=gear_collections["weapon"],
            artifacts=gear_collections["artifact"],
            planars=gear_collections["planar"],
            body_stats=relic_stats["body"],
            feet_stats=relic_stats["feet"],
            sphere_stats=relic_stats["sphere"],
            rope_stats=relic_stats["rope"],
        )

    return usage_by_char


# Build usage structures for each mode
usage_dicts: dict[str, dict[str, CharacterGearUsage]] = {
    "moc": build_gear_usage(raw_full["moc"]),
    "pf": build_gear_usage(raw_full["pf"]),
    "as": build_gear_usage(raw_full["as"]),
    "aa": build_gear_usage(raw_full["aa"]),
}

# ----------------------------------------------------------------------
# Build list of all character keys (including solo/support variants)
# ----------------------------------------------------------------------
character_keys: list[str] = []
dps_base_slugs: set[str] = set()  # track base slugs of characters with multiple roles

for char_info in CHARS_INFO.values():
    character_keys.append(char_info.slug)
    if len(char_info.role) > 1:
        dps_base_slugs.add(char_info.slug)
        character_keys.append("solo-" + char_info.slug)
        character_keys.append("supp-" + char_info.slug)


def process_chars() -> None:
    """Process loop over all character keys."""

    # ----------------------------------------------------------------------
    # Pydantic model for merged gear stats (after combining modes)
    # ----------------------------------------------------------------------
    class MergedGearStats(BaseModel):
        """Gear stats after merging MoC, PF, and AS data."""

        app: float
        round_moc: float
        round_pf: int
        round_as: int
        round_aa: float
        set1: str
        set2: str

    def merge_gear_stats(
        gears_moc: dict[str, GearStats],
        gears_pf: dict[str, GearStats],
        gears_as: dict[str, GearStats],
        gears_aa: dict[str, GearStats],
    ) -> dict[str, MergedGearStats]:
        """Combine gear stats from three modes.

        Using the already computed appearance rates
        (rate_moc, rate_pf, rate_as, rate_aa) and total rate (rate_combine).
        The rates are pulled from the outer scope.
        """
        merged: dict[str, MergedGearStats] = {}
        all_gear: dict[str, GearStats] = gears_moc | gears_pf | gears_as | gears_aa

        for name, gear_set in all_gear.items():
            gear_moc = gears_moc.get(name)
            gear_pf = gears_pf.get(name)
            gear_as = gears_as.get(name)
            gear_aa = gears_aa.get(name)

            app_moc = gear_moc.app if gear_moc else DEFAULT_APP
            app_pf = gear_pf.app if gear_pf else DEFAULT_APP
            app_as = gear_as.app if gear_as else DEFAULT_APP
            app_aa = gear_aa.app if gear_aa else DEFAULT_APP

            app_moc = app_moc * rate["moc"] / rate_combine
            app_pf = app_pf * rate["pf"] / rate_combine
            app_as = app_as * rate["as"] / rate_combine
            app_aa = app_aa * rate["aa"] / rate_combine

            merged[name] = MergedGearStats(
                app=app_moc + app_pf + app_as + app_aa,
                round_moc=gear_moc.round if gear_moc else DEFAULT_CYCLE,
                round_pf=int(gear_pf.round) if gear_pf else DEFAULT_SCORE,
                round_as=int(gear_as.round) if gear_as else DEFAULT_SCORE,
                round_aa=gear_aa.round if gear_aa else DEFAULT_CYCLE,
                set1=gear_set.set1,
                set2=gear_set.set2,
            )

        return merged

    def merge_relic_stats(
        relic_moc: dict[str, float],
        relic_pf: dict[str, float],
        relic_as: dict[str, float],
        relic_aa: dict[str, float],
    ) -> dict[str, float]:
        """Combine relic main stat appearance rates from three modes."""
        merged: dict[str, float] = {}
        all_stats = (
            relic_moc.keys() | relic_pf.keys() | relic_as.keys() | relic_aa.keys()
        )

        for name in all_stats:
            app_moc = relic_moc.get(name) or DEFAULT_APP
            app_pf = relic_pf.get(name) or DEFAULT_APP
            app_as = relic_as.get(name) or DEFAULT_APP
            app_aa = relic_aa.get(name) or DEFAULT_APP

            app_moc = app_moc * rate["moc"] / rate_combine
            app_pf = app_pf * rate["pf"] / rate_combine
            app_as = app_as * rate["as"] / rate_combine
            app_aa = app_aa * rate["aa"] / rate_combine

            merged[name] = app_moc + app_pf + app_as + app_aa

        return merged

    # ----------------------------------------------------------------------
    # Helper functions to populate the output dictionary for a character
    # ----------------------------------------------------------------------
    def populate_gear_usage(
        category: str,
        merged_gear: dict[str, MergedGearStats],
        out_dict: dict[str, str | float],
    ) -> None:
        """Write the top GEAR_COUNTS[category] items into out_dict with keys.

        For example: weapons_1, weapons_1_app, weapons_1_round_moc, etc.
        """
        sorted_items = sorted(
            merged_gear.items(),
            key=lambda x: (x[1].app, x[0]),
            reverse=True,
        )
        for i in range(GEAR_COUNTS[category]):
            if i < len(sorted_items):
                name, stats = sorted_items[i]
                if name in LIGHT_CONES and "alt_name" in LIGHT_CONES[name]:
                    name = LIGHT_CONES[name]["alt_name"]
                out_dict[f"{category}_{i + 1}"] = name
                if category == "artifacts":
                    out_dict[f"{category}_{i + 1}_1"] = stats.set1
                    out_dict[f"{category}_{i + 1}_2"] = stats.set2
                out_dict[f"{category}_{i + 1}_app"] = round(stats.app, 2)
                out_dict[f"{category}_{i + 1}_round_moc"] = stats.round_moc
                out_dict[f"{category}_{i + 1}_round_pf"] = stats.round_pf
                out_dict[f"{category}_{i + 1}_round_as"] = stats.round_as
                out_dict[f"{category}_{i + 1}_round_aa"] = stats.round_aa
            else:
                out_dict[f"{category}_{i + 1}"] = ""
                if category == "artifacts":
                    out_dict[f"{category}_{i + 1}_1"] = ""
                    out_dict[f"{category}_{i + 1}_2"] = ""
                out_dict[f"{category}_{i + 1}_app"] = DEFAULT_APP
                out_dict[f"{category}_{i + 1}_round_moc"] = DEFAULT_CYCLE
                out_dict[f"{category}_{i + 1}_round_pf"] = DEFAULT_SCORE
                out_dict[f"{category}_{i + 1}_round_as"] = DEFAULT_SCORE
                out_dict[f"{category}_{i + 1}_round_aa"] = DEFAULT_CYCLE

    def populate_relic_stat_usage(
        part: str,
        merged_stats: dict[str, float],
        out_dict: dict[str, str | float],
    ) -> None:
        """Write top GEAR_COUNTS[part] main stats into out_dict.

        Write with keys like body_stats_1, body_stats_1_app, etc.
        """
        sorted_items = sorted(
            merged_stats.items(),
            key=lambda x: (x[1], x[0]),
            reverse=True,
        )
        for i in range(GEAR_COUNTS[part]):
            if i < len(sorted_items):
                name, app = sorted_items[i]
                out_dict[f"{part}_stats_{i + 1}"] = name
                out_dict[f"{part}_stats_{i + 1}_app"] = round(app, 2)
            else:
                out_dict[f"{part}_stats_{i + 1}"] = ""
                out_dict[f"{part}_stats_{i + 1}_app"] = DEFAULT_APP

    variants = ["", "_e1", "_s0"]
    fields = ["app_rate", "avg_round"]

    output_data: list[dict[str, float | str]] = []

    for char in character_keys:
        # Determine base slug by stripping known prefixes
        base_char = char[5:] if char.startswith(("solo-", "supp-")) else char

        # Base dictionary for this character (output format)
        out: dict[str, float | str] = {"char": base_char}

        # Add special_role only if this character has multiple roles
        if base_char in dps_base_slugs:
            if char.startswith("solo-"):
                out["special_role"] = "DPS"
            elif char.startswith("supp-"):
                out["special_role"] = "S-DPS"
            else:
                out["special_role"] = "ALL"
        else:
            out["special_role"] = ""

        # ----- 1. Simple fields (appearance rates, average cycles, samples) -----
        for is_prev_mode in (False, True):
            suf = "_prev" if is_prev_mode else ""

            # Mode tuples: (name, base)
            base_modes = [
                ("moc", raw_full[f"moc{suf}"]),
                ("pf", raw_full[f"pf{suf}"]),
                ("as", raw_full[f"as{suf}"]),
                ("aa", raw_full[f"aa{suf}"]),
            ]

            for mode, base in base_modes:
                # Helper to fetch an attribute with a default value
                def get_val(
                    dict_obj: dict[str, FullCharacterStats]
                    | dict[str, BaseCharacterStats],
                    attr: str,
                    char: str = char,
                    mode: str = mode,
                ) -> float | int:
                    if char in dict_obj:
                        return getattr(dict_obj[char], attr)
                    if "app_rate" in attr:
                        return DEFAULT_APP
                    if mode in ("pf", "as") or "sample" in attr:
                        return DEFAULT_SCORE
                    return DEFAULT_CYCLE

                boss_suffixes = (
                    ["", "_boss_1", "_boss_2", "_boss_3", "_boss_4"]
                    if mode == "aa"
                    else [""]
                )

                for boss_idx, boss_suf in enumerate(boss_suffixes):
                    for var_off, var_suf in enumerate(variants):
                        is_base = boss_idx + var_off == 0
                        data_dict = (
                            base if is_base else raw[f"{mode}{boss_suf}{var_suf}{suf}"]
                        )

                        # Additional e0s1 field for base variant only
                        if var_off == 0:
                            e0s1_key = f"app_rate_{mode}{boss_suf}_e0s1{suf}"
                            out[e0s1_key] = get_val(data_dict, "app_rate_e0")
                        for field in fields:
                            key = f"{field}_{mode}{boss_suf}{var_suf}{suf}"
                            out[key] = get_val(data_dict, field)

                # Overall sample info (from base_data, no boss suffix)
                out[f"sample_{mode}{suf}"] = get_val(base, "sample")
                out[f"sample_size_players_{mode}{suf}"] = get_val(
                    base,
                    "sample_size_players",
                )

        # ----- 3. Eidolon round data (0..6) for base modes -----
        round_modes = [
            ("moc", raw_full["moc"], DEFAULT_CYCLE),
            ("pf", raw_full["pf"], DEFAULT_SCORE),
            ("as", raw_full["as"], DEFAULT_SCORE),
            ("aa", raw_full["aa"], DEFAULT_CYCLE),
        ]
        for e in range(7):
            out[f"app_{e}"] = DEFAULT_APP
            for mode, base, default in round_modes:
                out[f"round_{e}_{mode}"] = (
                    getattr(base[char], f"round_{e}") if char in base else default
                )

        # Set cons_avg to 0, will be used later
        out["cons_avg"] = DEFAULT_APP

        # ----- 4. Compute mode appearance rates for weighting -----
        # These are used later to weight gear and numeric stats.
        rate: dict[str, float] = {}
        for mode in modes:
            rate[mode] = (
                raw_full[mode][char].app_rate
                if (
                    char in raw_full[mode]
                    and raw_full[mode][char].app_rate != 0
                    and raw_full[mode][char].weapon_1_app != 0
                )
                else 0
            )
        rate_combine = sum(rate.values()) or 1  # avoid division by zero

        # ----- 5. Populate output with top gear and relic stats -----
        def get_gear(
            usage_dict: dict[str, CharacterGearUsage],
            char: str,
            attr: str,
        ) -> dict[str, GearStats]:
            obj = usage_dict.get(char)
            return getattr(obj, attr) if obj is not None else {}

        def get_app(
            usage_dict: dict[str, CharacterGearUsage],
            char: str,
            attr: str,
        ) -> dict[str, float]:
            obj = usage_dict.get(char)
            return getattr(obj, attr) if obj is not None else {}

        for stat in ["weapons", "artifacts", "planars"]:
            merged_gear: dict[str, MergedGearStats] = merge_gear_stats(
                *(get_gear(usage_dicts[m], char, stat) for m in modes),
            )
            populate_gear_usage(stat, merged_gear, out)

        for stat in ["body", "feet", "sphere", "rope"]:
            merged: dict[str, float] = merge_relic_stats(
                *(get_app(usage_dicts[m], char, f"{stat}_stats") for m in modes),
            )
            populate_relic_stat_usage(stat, merged, out)

        # ----- 6. Weighted average of numeric stats -----
        for stat in NUMERIC_STATS:
            vals: dict[str, float] = {}
            for mode in modes:
                vals[mode] = (
                    getattr(raw_full[mode][char], stat) if char in raw_full[mode] else 0
                )

            dividend = sum(vals[mode] * rate[mode] for mode in vals)

            # Only modes where the stat is non-zero contribute to the denominator
            divisor = sum(rate[mode] for mode in vals if vals[mode] != 0) or 1

            out[stat] = round(
                # Eidolon data should still be divided with rate_combine
                dividend / (rate_combine if "app_" in stat else divisor),
                2,
            )

        output_data.append(out)

    # ----------------------------------------------------------------------
    # Write final JSON
    # ----------------------------------------------------------------------
    output_path = f"../../results/all_results/{RECENT_PHASE}/builds.json"
    with open(output_path, "w") as out_file:
        json.dump(output_data, out_file, indent=2)


if __name__ == "__main__":
    process_chars()
