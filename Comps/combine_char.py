# pyright: reportGeneralTypeIssues=false, reportUnknownArgumentType=false, reportOperatorIssue=false, reportIndexIssue=false, reportArgumentType=false, reportUnknownMemberType=false, reportAttributeAccessIssue=false, reportUnnecessaryComparison=false, reportUnknownVariableType=false
"""Combine JSON results."""

from __future__ import annotations

import json
import re
from typing import cast

from comp_rates_config import (
    DPS_APPEND_LIST,
    DPS_LIST,
    RECENT_PHASE,
)
from slugify import slugify

with open("../Comps/prydwen-slug.json") as slug_file:
    slug = json.load(slug_file)

moc_phase = RECENT_PHASE
pf_phase = RECENT_PHASE
as_phase = RECENT_PHASE
aa_phase = RECENT_PHASE

with open("../data/characters.json") as char_file:
    CHARACTERS: dict[str, dict[str, str | int | None]] = json.load(char_file)
with open("../char_results/" + moc_phase + "/all2.json") as stats:
    moc_dict = json.load(stats)
with open("../char_results/" + pf_phase + "_pf/all2.json") as stats:
    pf_dict = json.load(stats)
with open("../char_results/" + as_phase + "_as/all2.json") as stats:
    as_dict = json.load(stats)
with open("../char_results/" + aa_phase + "_aa/all.json") as stats:
    aa_dict = json.load(stats)

with open("../char_results/" + moc_phase + "/all_C1.json") as stats:
    moc_dict_e1 = json.load(stats)
with open("../char_results/" + pf_phase + "_pf/all_C1.json") as stats:
    pf_dict_e1 = json.load(stats)
with open("../char_results/" + as_phase + "_as/all_C1.json") as stats:
    as_dict_e1 = json.load(stats)
with open("../char_results/" + aa_phase + "_aa/all_C1.json") as stats:
    aa_dict_e1 = json.load(stats)

with open("../char_results/" + moc_phase + "/all_E0S0.json") as stats:
    moc_dict_s0 = json.load(stats)
with open("../char_results/" + pf_phase + "_pf/all_E0S0.json") as stats:
    pf_dict_s0 = json.load(stats)
with open("../char_results/" + as_phase + "_as/all_E0S0.json") as stats:
    as_dict_s0 = json.load(stats)
with open("../char_results/" + aa_phase + "_aa/all_E0S0.json") as stats:
    aa_dict_s0 = json.load(stats)

with open("../char_results/" + aa_phase + "_aa/1-1.json") as stats:
    aa_dict_boss_1 = json.load(stats)
with open("../char_results/" + aa_phase + "_aa/1-2.json") as stats:
    aa_dict_boss_2 = json.load(stats)
with open("../char_results/" + aa_phase + "_aa/1-3.json") as stats:
    aa_dict_boss_3 = json.load(stats)
with open("../char_results/" + aa_phase + "_aa/2-1.json") as stats:
    aa_dict_boss_4 = json.load(stats)

with open("../char_results/" + aa_phase + "_aa/1-1_C1.json") as stats:
    aa_dict_boss_1_e1 = json.load(stats)
with open("../char_results/" + aa_phase + "_aa/1-2_C1.json") as stats:
    aa_dict_boss_2_e1 = json.load(stats)
with open("../char_results/" + aa_phase + "_aa/1-3_C1.json") as stats:
    aa_dict_boss_3_e1 = json.load(stats)
with open("../char_results/" + aa_phase + "_aa/2-1_C1.json") as stats:
    aa_dict_boss_4_e1 = json.load(stats)

with open("../char_results/" + aa_phase + "_aa/1-1_E0S0.json") as stats:
    aa_dict_boss_1_s0 = json.load(stats)
with open("../char_results/" + aa_phase + "_aa/1-2_E0S0.json") as stats:
    aa_dict_boss_2_s0 = json.load(stats)
with open("../char_results/" + aa_phase + "_aa/1-3_E0S0.json") as stats:
    aa_dict_boss_3_s0 = json.load(stats)
with open("../char_results/" + aa_phase + "_aa/2-1_E0S0.json") as stats:
    aa_dict_boss_4_s0 = json.load(stats)

uses: list[dict[str, float | str | dict[str, dict[str, float]]]] = []
uses_moc: dict[str, dict[str, dict[str, dict[str, float]]]] = {}
uses_pf: dict[str, dict[str, dict[str, dict[str, float]]]] = {}
uses_as: dict[str, dict[str, dict[str, dict[str, float]]]] = {}
stats_len = {
    "weapons": 10,
    "artifacts": 10,
    "planars": 5,
    "body_stats": 3,
    "feet_stats": 3,
    "sphere_stats": 3,
    "rope_stats": 3,
}

for char in moc_dict:
    char["char"] = slugify(char["char"])
    if char["char"] in slug:
        char["char"] = slug[char["char"]]
    uses_moc[char["char"]] = char.copy()
    uses_moc[char["char"]]["weapons"] = {}
    uses_moc[char["char"]]["artifacts"] = {}
    uses_moc[char["char"]]["planars"] = {}
    uses_moc[char["char"]]["body_stats"] = {}
    uses_moc[char["char"]]["feet_stats"] = {}
    uses_moc[char["char"]]["sphere_stats"] = {}
    uses_moc[char["char"]]["rope_stats"] = {}
    for stat in char:
        for stat_name in [
            "weapon",
            "artifact",
            "planar",
            "body_stats",
            "feet_stats",
            "sphere_stats",
            "rope_stats",
        ]:
            r_stat_name = stat_name
            if (
                re.sub(r"\d", "", stat) == r_stat_name + "_"
                and char[stat] != ""
                and char[stat] != "-"
            ):
                temp_dict = {}
                if r_stat_name == "artifact":
                    temp_dict["1"] = char[stat + "_1"]
                    temp_dict["2"] = char[stat + "_2"]
                temp_dict["app"] = char[stat + "_app"]
                if r_stat_name in ["weapon", "artifact", "planar"]:
                    temp_dict["round_moc"] = char[stat + "_round"]
                    temp_dict["round_pf"] = 0.0
                    temp_dict["round_as"] = 0.0
                else:
                    r_stat_name = r_stat_name[:-1]
                uses_moc[char["char"]][r_stat_name + "s"][char[stat]] = temp_dict
for char in pf_dict:
    char["char"] = slugify(char["char"])
    if char["char"] in slug:
        char["char"] = slug[char["char"]]
    uses_pf[char["char"]] = char.copy()
    uses_pf[char["char"]]["weapons"] = {}
    uses_pf[char["char"]]["artifacts"] = {}
    uses_pf[char["char"]]["planars"] = {}
    uses_pf[char["char"]]["body_stats"] = {}
    uses_pf[char["char"]]["feet_stats"] = {}
    uses_pf[char["char"]]["sphere_stats"] = {}
    uses_pf[char["char"]]["rope_stats"] = {}
    for stat in char:
        for stat_name in [
            "weapon",
            "artifact",
            "planar",
            "body_stats",
            "feet_stats",
            "sphere_stats",
            "rope_stats",
        ]:
            r_stat_name = stat_name
            if (
                re.sub(r"\d", "", stat) == r_stat_name + "_"
                and char[stat] != ""
                and char[stat] != "-"
            ):
                temp_dict = {}
                if r_stat_name == "artifact":
                    temp_dict["1"] = char[stat + "_1"]
                    temp_dict["2"] = char[stat + "_2"]
                temp_dict["app"] = char[stat + "_app"]
                if r_stat_name in ["weapon", "artifact", "planar"]:
                    temp_dict["round_moc"] = 99.99
                    temp_dict["round_pf"] = char[stat + "_round"]
                    temp_dict["round_as"] = 0.0
                else:
                    r_stat_name = r_stat_name[:-1]
                uses_pf[char["char"]][r_stat_name + "s"][char[stat]] = temp_dict
for char in as_dict:
    char["char"] = slugify(char["char"])
    if char["char"] in slug:
        char["char"] = slug[char["char"]]
    uses_as[char["char"]] = char.copy()
    uses_as[char["char"]]["weapons"] = {}
    uses_as[char["char"]]["artifacts"] = {}
    uses_as[char["char"]]["planars"] = {}
    uses_as[char["char"]]["body_stats"] = {}
    uses_as[char["char"]]["feet_stats"] = {}
    uses_as[char["char"]]["sphere_stats"] = {}
    uses_as[char["char"]]["rope_stats"] = {}
    for stat in char:
        for stat_name in [
            "weapon",
            "artifact",
            "planar",
            "body_stats",
            "feet_stats",
            "sphere_stats",
            "rope_stats",
        ]:
            r_stat_name = stat_name
            if (
                re.sub(r"\d", "", stat) == r_stat_name + "_"
                and char[stat] != ""
                and char[stat] != "-"
            ):
                temp_dict = {}
                if r_stat_name == "artifact":
                    temp_dict["1"] = char[stat + "_1"]
                    temp_dict["2"] = char[stat + "_2"]
                temp_dict["app"] = char[stat + "_app"]
                if r_stat_name in ["weapon", "artifact", "planar"]:
                    temp_dict["round_moc"] = 99.99
                    temp_dict["round_pf"] = 0.0
                    temp_dict["round_as"] = char[stat + "_round"]
                else:
                    r_stat_name = r_stat_name[:-1]
                uses_as[char["char"]][r_stat_name + "s"][char[stat]] = temp_dict

char_array: list[str] = []
for char_iter in CHARACTERS:
    char = slugify(char_iter)
    if char in slug:
        char = slug[char]
    char_array.append(char)
    if char_iter in [*DPS_LIST, *DPS_APPEND_LIST]:
        char_array.append("solo-" + char)
        char_array.append("supp-" + char)


for char in char_array:
    moc_dict_e1_char: dict[str, float] = next(
        (x for x in moc_dict_e1 if x["char"] == char),
        dict[str, float](),
    )
    moc_dict_s0_char: dict[str, float] = next(
        (x for x in moc_dict_s0 if x["char"] == char),
        dict[str, float](),
    )

    pf_dict_e1_char: dict[str, float] = next(
        (x for x in pf_dict_e1 if x["char"] == char),
        dict[str, float](),
    )
    pf_dict_s0_char: dict[str, float] = next(
        (x for x in pf_dict_s0 if x["char"] == char),
        dict[str, float](),
    )

    as_dict_e1_char: dict[str, float] = next(
        (x for x in as_dict_e1 if x["char"] == char),
        dict[str, float](),
    )
    as_dict_s0_char: dict[str, float] = next(
        (x for x in as_dict_s0 if x["char"] == char),
        dict[str, float](),
    )

    aa_dict_char: dict[str, float] = next(
        (x for x in aa_dict if x["char"] == char),
        dict[str, float](),
    )
    aa_dict_e1_char: dict[str, float] = next(
        (x for x in aa_dict_e1 if x["char"] == char),
        dict[str, float](),
    )
    aa_dict_s0_char: dict[str, float] = next(
        (x for x in aa_dict_s0 if x["char"] == char),
        dict[str, float](),
    )

    aa_dict_boss_1_char: dict[str, float] = next(
        (x for x in aa_dict_boss_1 if x["char"] == char),
        dict[str, float](),
    )
    aa_dict_boss_1_e1_char: dict[str, float] = next(
        (x for x in aa_dict_boss_1_e1 if x["char"] == char),
        dict[str, float](),
    )
    aa_dict_boss_1_s0_char: dict[str, float] = next(
        (x for x in aa_dict_boss_1_s0 if x["char"] == char),
        dict[str, float](),
    )

    aa_dict_boss_2_char: dict[str, float] = next(
        (x for x in aa_dict_boss_2 if x["char"] == char),
        dict[str, float](),
    )
    aa_dict_boss_2_e1_char: dict[str, float] = next(
        (x for x in aa_dict_boss_2_e1 if x["char"] == char),
        dict[str, float](),
    )
    aa_dict_boss_2_s0_char: dict[str, float] = next(
        (x for x in aa_dict_boss_2_s0 if x["char"] == char),
        dict[str, float](),
    )

    aa_dict_boss_3_char: dict[str, float] = next(
        (x for x in aa_dict_boss_3 if x["char"] == char),
        dict[str, float](),
    )
    aa_dict_boss_3_e1_char: dict[str, float] = next(
        (x for x in aa_dict_boss_3_e1 if x["char"] == char),
        dict[str, float](),
    )
    aa_dict_boss_3_s0_char: dict[str, float] = next(
        (x for x in aa_dict_boss_3_s0 if x["char"] == char),
        dict[str, float](),
    )

    aa_dict_boss_4_char: dict[str, float] = next(
        (x for x in aa_dict_boss_4 if x["char"] == char),
        dict[str, float](),
    )
    aa_dict_boss_4_e1_char: dict[str, float] = next(
        (x for x in aa_dict_boss_4_e1 if x["char"] == char),
        dict[str, float](),
    )
    aa_dict_boss_4_s0_char: dict[str, float] = next(
        (x for x in aa_dict_boss_4_s0 if x["char"] == char),
        dict[str, float](),
    )

    uses_temp: dict[str, float | str | dict[str, dict[str, float]]] = {
        "char": char,
        "app_rate_moc": uses_moc.get(char, {}).get("app_rate", 0),
        "app_rate_moc_e0s1": uses_moc.get(char, {}).get("app_rate_e0", 0),
        "app_rate_moc_e1": moc_dict_e1_char.get("app_rate", 0),
        "app_rate_moc_s0": moc_dict_s0_char.get("app_rate", 0),
        "avg_round_moc": uses_moc.get(char, {}).get("avg_round", 99.99),
        "avg_round_moc_e1": moc_dict_e1_char.get("avg_round", 99.99),
        "avg_round_moc_s0": moc_dict_s0_char.get("avg_round", 99.99),
        "sample_moc": uses_moc.get(char, {}).get("sample", 0),
        "sample_size_players_moc": uses_moc.get(char, {}).get(
            "sample_size_players",
            0,
        ),
        "app_rate_pf": uses_pf.get(char, {}).get("app_rate", 0),
        "app_rate_pf_e0s1": uses_pf.get(char, {}).get("app_rate_e0", 0),
        "app_rate_pf_e1": pf_dict_e1_char.get("app_rate", 0),
        "app_rate_pf_s0": pf_dict_s0_char.get("app_rate", 0),
        "avg_round_pf": uses_pf.get(char, {}).get("avg_round", 0),
        "avg_round_pf_e1": pf_dict_e1_char.get("avg_round", 0),
        "avg_round_pf_s0": pf_dict_s0_char.get("avg_round", 0),
        "sample_pf": uses_pf.get(char, {}).get("sample", 0),
        "sample_size_players_pf": uses_pf.get(char, {}).get(
            "sample_size_players",
            0,
        ),
        "app_rate_as": uses_as.get(char, {}).get("app_rate", 0),
        "app_rate_as_e0s1": uses_as.get(char, {}).get("app_rate_e0", 0),
        "app_rate_as_e1": as_dict_e1_char.get("app_rate", 0),
        "app_rate_as_s0": as_dict_s0_char.get("app_rate", 0),
        "avg_round_as": uses_as.get(char, {}).get("avg_round", 0),
        "avg_round_as_e1": as_dict_e1_char.get("avg_round", 0),
        "avg_round_as_s0": as_dict_s0_char.get("avg_round", 0),
        "sample_as": uses_as.get(char, {}).get("sample", 0),
        "sample_size_players_as": uses_as.get(char, {}).get(
            "sample_size_players",
            0,
        ),
        "app_rate_aa": aa_dict_char.get("app_rate", 0),
        "app_rate_aa_e0s1": aa_dict_char.get("app_rate_e0", 0),
        "app_rate_aa_e1": aa_dict_e1_char.get("app_rate", 0),
        "app_rate_aa_s0": aa_dict_s0_char.get("app_rate", 0),
        "avg_round_aa": aa_dict_char.get("avg_round", 0),
        "avg_round_aa_e1": aa_dict_e1_char.get("avg_round", 0),
        "avg_round_aa_s0": aa_dict_s0_char.get("avg_round", 0),
        "app_rate_aa_boss_1": aa_dict_boss_1_char.get("app_rate", 0),
        "app_rate_aa_boss_1_e0s1": aa_dict_boss_1_char.get(
            "app_rate_e0",
            0,
        ),
        "app_rate_aa_boss_1_e1": aa_dict_boss_1_e1_char.get("app_rate", 0),
        "app_rate_aa_boss_1_s0": aa_dict_boss_1_s0_char.get("app_rate", 0),
        "avg_round_boss_1_aa": aa_dict_boss_1_char.get("avg_round", 0),
        "avg_round_boss_1_aa_e1": aa_dict_boss_1_e1_char.get("avg_round", 0),
        "avg_round_boss_1_aa_s0": aa_dict_boss_1_s0_char.get("avg_round", 0),
        "app_rate_aa_boss_2": aa_dict_boss_2_char.get("app_rate", 0),
        "app_rate_aa_boss_2_e0s1": aa_dict_boss_2_char.get(
            "app_rate_e0",
            0,
        ),
        "app_rate_aa_boss_2_e1": aa_dict_boss_2_e1_char.get("app_rate", 0),
        "app_rate_aa_boss_2_s0": aa_dict_boss_2_s0_char.get("app_rate", 0),
        "avg_round_boss_2_aa": aa_dict_boss_2_char.get("avg_round", 0),
        "avg_round_boss_2_aa_e1": aa_dict_boss_2_e1_char.get("avg_round", 0),
        "avg_round_boss_2_aa_s0": aa_dict_boss_2_s0_char.get("avg_round", 0),
        "app_rate_aa_boss_3": aa_dict_boss_3_char.get("app_rate", 0),
        "app_rate_aa_boss_3_e0s1": aa_dict_boss_3_char.get(
            "app_rate_e0",
            0,
        ),
        "app_rate_aa_boss_3_e1": aa_dict_boss_3_e1_char.get("app_rate", 0),
        "app_rate_aa_boss_3_s0": aa_dict_boss_3_s0_char.get("app_rate", 0),
        "avg_round_boss_3_aa": aa_dict_boss_3_char.get("avg_round", 0),
        "avg_round_boss_3_aa_e1": aa_dict_boss_3_e1_char.get("avg_round", 0),
        "avg_round_boss_3_aa_s0": aa_dict_boss_3_s0_char.get("avg_round", 0),
        "app_rate_aa_boss_4": aa_dict_boss_4_char.get("app_rate", 0),
        "app_rate_aa_boss_4_e0s1": aa_dict_boss_4_char.get(
            "app_rate_e0",
            0,
        ),
        "app_rate_aa_boss_4_e1": aa_dict_boss_4_e1_char.get("app_rate", 0),
        "app_rate_aa_boss_4_s0": aa_dict_boss_4_s0_char.get("app_rate", 0),
        "avg_round_boss_4_aa": aa_dict_boss_4_char.get("avg_round", 0),
        "avg_round_boss_4_aa_e1": aa_dict_boss_4_e1_char.get("avg_round", 0),
        "avg_round_boss_4_aa_s0": aa_dict_boss_4_s0_char.get("avg_round", 0),
        "sample_aa": aa_dict_char.get("sample", 0),
        "sample_size_players_aa": aa_dict_char.get(
            "sample_app_flat",
            0,
        ),
        "app_0": 0,
        "round_0_moc": uses_moc.get(char, {}).get("round_0", 99.99),
        "round_0_pf": uses_pf.get(char, {}).get("round_0", 0),
        "round_0_as": uses_as.get(char, {}).get("round_0", 0),
        "round_0_aa": aa_dict_char.get("round_0", 99.99),
        "app_1": 0,
        "round_1_moc": uses_moc.get(char, {}).get("round_1", 99.99),
        "round_1_pf": uses_pf.get(char, {}).get("round_1", 0),
        "round_1_as": uses_as.get(char, {}).get("round_1", 0),
        "round_1_aa": aa_dict_char.get("round_1", 99.99),
        "app_2": 0,
        "round_2_moc": uses_moc.get(char, {}).get("round_2", 99.99),
        "round_2_pf": uses_pf.get(char, {}).get("round_2", 0),
        "round_2_as": uses_as.get(char, {}).get("round_2", 0),
        "round_2_aa": aa_dict_char.get("round_2", 99.99),
        "app_3": 0,
        "round_3_moc": uses_moc.get(char, {}).get("round_3", 99.99),
        "round_3_pf": uses_pf.get(char, {}).get("round_3", 0),
        "round_3_as": uses_as.get(char, {}).get("round_3", 0),
        "round_3_aa": aa_dict_char.get("round_3", 99.99),
        "app_4": 0,
        "round_4_moc": uses_moc.get(char, {}).get("round_4", 99.99),
        "round_4_pf": uses_pf.get(char, {}).get("round_4", 0),
        "round_4_as": uses_as.get(char, {}).get("round_4", 0),
        "round_4_aa": aa_dict_char.get("round_4", 99.99),
        "app_5": 0,
        "round_5_moc": uses_moc.get(char, {}).get("round_5", 99.99),
        "round_5_pf": uses_pf.get(char, {}).get("round_5", 0),
        "round_5_as": uses_as.get(char, {}).get("round_5", 0),
        "round_5_aa": aa_dict_char.get("round_5", 99.99),
        "app_6": 0,
        "round_6_moc": uses_moc.get(char, {}).get("round_6", 99.99),
        "round_6_pf": uses_pf.get(char, {}).get("round_6", 0),
        "round_6_as": uses_as.get(char, {}).get("round_6", 0),
        "round_6_aa": aa_dict_char.get("round_6", 99.99),
        "cons_avg": 0,
        "weapons": uses_moc.get(char, {}).get("weapons", {}),
        "artifacts": uses_moc.get(char, {}).get("artifacts", {}),
        "planars": uses_moc.get(char, {}).get("planars", {}),
        "body_stats": uses_moc.get(char, {}).get("body_stats", {}),
        "feet_stats": uses_moc.get(char, {}).get("feet_stats", {}),
        "sphere_stats": uses_moc.get(char, {}).get("sphere_stats", {}),
        "rope_stats": uses_moc.get(char, {}).get("rope_stats", {}),
    }

    rate_moc: float = cast(
        "float",
        uses_temp["app_rate_moc"]
        if (uses_temp["app_rate_moc"] == 0)
        == (uses_moc.get(char, {}).get("weapon_1_app", {}) == 0)
        else 0,
    )
    rate_pf: float = cast(
        "float",
        uses_temp["app_rate_pf"]
        if (uses_temp["app_rate_pf"] == 0)
        == (uses_pf.get(char, {}).get("weapon_1_app", {}) == 0)
        else 0,
    )
    rate_as: float = cast(
        "float",
        uses_temp["app_rate_as"]
        if (uses_temp["app_rate_as"] == 0)
        == (uses_as.get(char, {}).get("weapon_1_app", {}) == 0)
        else 0,
    )
    rate_combine = rate_moc + rate_pf + rate_as
    rate_combine = rate_combine if rate_combine else 1

    for stat, stat_len in stats_len.items():
        for item in uses_temp[stat]:
            uses_temp[stat][item]["app"] = round(
                uses_temp[stat][item]["app"] * rate_moc / rate_combine,
                2,
            )
        for item in uses_pf.get(char, {}).get(stat, {}):
            if item not in {"", "-"}:
                if item in uses_temp[stat]:  # pyright: ignore[reportOperatorIssue]
                    uses_temp[stat][item]["app"] = round(  # pyright: ignore[reportIndexIssue] # pyright: ignore[reportArgumentType]
                        uses_temp[stat][item]["app"]  # pyright: ignore[reportIndexIssue]
                        + uses_pf[char][stat][item]["app"] * rate_pf / rate_combine,
                        2,
                    )
                    if stat in ["weapons", "artifacts", "planars"]:
                        uses_temp[stat][item]["round_pf"] = uses_pf[char][stat][item][
                            "round_pf"
                        ]
                else:
                    uses_temp[stat][item] = uses_pf[char][stat][item].copy()
                    uses_temp[stat][item]["app"] = round(
                        uses_temp[stat][item]["app"] * rate_pf / rate_combine,
                        2,
                    )
        for item in uses_as.get(char, {}).get(stat, {}):
            if item not in {"", "-"}:
                if item in uses_temp[stat]:
                    uses_temp[stat][item]["app"] = round(
                        uses_temp[stat][item]["app"]
                        + uses_as[char][stat][item]["app"] * rate_as / rate_combine,
                        2,
                    )
                    if stat in ["weapons", "artifacts", "planars"]:
                        uses_temp[stat][item]["round_as"] = uses_as[char][stat][item][
                            "round_as"
                        ]
                else:
                    uses_temp[stat][item] = uses_as[char][stat][item].copy()
                    uses_temp[stat][item]["app"] = round(
                        uses_temp[stat][item]["app"] * rate_as / rate_combine,
                        2,
                    )

        sorted_items = sorted(
            uses_temp[stat].items(),
            key=lambda t: t[1]["app"],
            reverse=True,
        )
        uses_temp[stat] = dict(sorted_items)

        for i in range(stat_len):
            if i < len(list(uses_temp[stat])):
                uses_temp[stat + "_" + str(i + 1)] = list(uses_temp[stat])[i]
                if stat == "artifacts":
                    uses_temp[stat + "_" + str(i + 1) + "_1"] = list(
                        uses_temp[stat].values(),
                    )[i]["1"]
                    uses_temp[stat + "_" + str(i + 1) + "_2"] = list(
                        uses_temp[stat].values(),
                    )[i]["2"]
                uses_temp[stat + "_" + str(i + 1) + "_app"] = list(
                    uses_temp[stat].values(),
                )[i]["app"]
                if stat in ["weapons", "artifacts", "planars"]:
                    uses_temp[stat + "_" + str(i + 1) + "_round_moc"] = list(
                        uses_temp[stat].values(),
                    )[i]["round_moc"]
                    uses_temp[stat + "_" + str(i + 1) + "_round_pf"] = list(
                        uses_temp[stat].values(),
                    )[i]["round_pf"]
                    uses_temp[stat + "_" + str(i + 1) + "_round_as"] = list(
                        uses_temp[stat].values(),
                    )[i]["round_as"]
            else:
                uses_temp[stat + "_" + str(i + 1)] = ""
                if stat == "artifacts":
                    uses_temp[stat + "_" + str(i + 1) + "_1"] = ""
                    uses_temp[stat + "_" + str(i + 1) + "_2"] = ""
                uses_temp[stat + "_" + str(i + 1) + "_app"] = 0.0
                if stat in ["weapons", "artifacts", "planars"]:
                    uses_temp[stat + "_" + str(i + 1) + "_round_moc"] = 99.99
                    uses_temp[stat + "_" + str(i + 1) + "_round_pf"] = 0.0
                    uses_temp[stat + "_" + str(i + 1) + "_round_as"] = 0.0
        del uses_temp[stat]

    stats_iter = [
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
    for stat in stats_iter:
        stat_moc = uses_moc.get(char, {}).get(stat) or 0
        stat_pf = uses_pf.get(char, {}).get(stat) or 0
        stat_as = uses_as.get(char, {}).get(stat) or 0
        uses_temp[stat] = round(
            ((stat_moc * rate_moc) + (stat_pf * rate_pf) + (stat_as * rate_as))
            / (
                ((rate_moc) if stat_moc != 0 else 0)
                + ((rate_pf) if stat_pf != 0 else 0)
                + ((rate_as) if stat_as != 0 else 0)
            )
            if (rate_moc * stat_moc + rate_pf * stat_pf + rate_as * stat_as != 0)
            else 1,
            2,
        )
    uses.append(uses_temp)

with open("../char_results/" + RECENT_PHASE + "/builds.json", "w") as out_file:
    out_file.write(json.dumps(uses, indent=2))
