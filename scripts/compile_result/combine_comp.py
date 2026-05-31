"""Combine JSON results."""

from __future__ import annotations

import json
from sys import path as sys_path

sys_path.append("../")
from comp_rates_config import COMP_RESULT_PATH, all_stages, pf_mode
from send2trash import send2trash

file_names = ["top", *all_stages]
exclude_value = 0 if pf_mode else 99.99

for file_name in file_names:
    combine_path = f"../../{COMP_RESULT_PATH}/{file_name}"

    # Load the JSON files
    with open(f"{combine_path}.json") as f:
        team_data: list[dict[str, str | float]] = json.load(f)

    with open(f"{combine_path}_C1.json") as f:
        team_c1_data = json.load(f)

    # Create a dictionary to store the matched teams
    matched_teams: dict[tuple[str | float, ...], dict[str, str | float]] = {}
    matched_teams_c1: dict[tuple[str | float, ...], dict[str, str | float]] = {}

    # Iterate over the team_data and create a tuple key for each team
    for team in team_data:
        team_key = (
            team["char_one"],
            team["char_two"],
            team["char_three"],
            team["char_four"],
        )
        matched_teams[team_key] = team

    for team in team_c1_data:
        team_key = (
            team["char_one"],
            team["char_two"],
            team["char_three"],
            team["char_four"],
        )
        matched_teams_c1[team_key] = team

    # Iterate over the matched_teams_c1 and add the avg_round to the matched teams
    for team_key in matched_teams:  # noqa: PLC0206
        if team_key in matched_teams_c1:
            matched_teams[team_key]["app_rate_c1"] = matched_teams_c1[team_key][
                "app_rate"
            ]
            matched_teams[team_key]["avg_round_c1"] = matched_teams_c1[team_key][
                "avg_round"
            ]
        else:
            matched_teams[team_key]["app_rate_c1"] = 0
            matched_teams[team_key]["avg_round_c1"] = exclude_value

    team_data = [
        value
        for value in matched_teams.values()
        if value["avg_round_c1"] != exclude_value or value["avg_round"] != exclude_value
    ]

    # Write the updated data back to the top.json file
    with open(f"{combine_path}_combined.json", "w") as f:
        json.dump(team_data, f, indent=2)

    send2trash(f"{combine_path}.json")
    send2trash(f"{combine_path}_C1.json")
