import json

from comp_rates_config import RECENT_PHASE, as_mode, pf_mode

file_names = ["top"]
moc_names = ["10-1", "10-2", "11-1", "11-2", "12-1", "12-2"]
pf_names = ["4-1", "4-2"]

if pf_mode:
    file_names.extend(pf_names)
else:
    file_names.extend(moc_names)

suffix = ""
if as_mode:
    suffix = "_as"
elif pf_mode:
    suffix = "_pf"

RECENT_PHASE_PF = RECENT_PHASE + suffix

for file_name in file_names:
    # Load the JSON files
    with open(
        "../comp_results/" + RECENT_PHASE_PF + "/json/" + file_name + ".json"
    ) as f:
        team_data: list[dict[str, str | float]] = json.load(f)

    with open(
        "../comp_results/" + RECENT_PHASE_PF + "/json/" + file_name + "_C1.json"
    ) as f:
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
    for team_key in matched_teams:
        if team_key in matched_teams_c1:
            matched_teams[team_key]["avg_round_c1"] = matched_teams_c1[team_key][
                "avg_round"
            ]
        else:
            matched_teams[team_key]["avg_round_c1"] = 0 if pf_mode else 99.99

    # Write the updated data back to the top.json file
    with open(
        "../comp_results/" + RECENT_PHASE_PF + "/json/" + file_name + "_combined.json",
        "w",
    ) as f:
        json.dump(team_data, f, indent=2)
