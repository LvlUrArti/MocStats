"""Filter artifact characters."""

from __future__ import annotations

import json

from comp_rates_config import RECENT_PHASE, as_mode, pf_mode

suffix = ""
if as_mode:
    suffix = "_as"
elif pf_mode:
    suffix = "_pf"
RECENT_PHASE_PF = RECENT_PHASE + suffix

# Load the data from the JSON file
with open("../results/char_results/" + RECENT_PHASE_PF + "/builds.json") as f:
    data: list[dict[str, str | float]] = json.load(f)

# Define the list of characters to exclude
exclude_chars = [
    "march-7th-swordmaster",
    "dan-heng",
    "welt",
    "arlan",
    "asta",
    "gepard",
    "natasha",
    "sampo",
    "hook",
    "jing-yuan",
    "sushang",
    "luocha",
    "yukong",
    "yanqing",
    "bailu",
    "trailblazer-destruction",
    "trailblazer-preservation",
    "kafka",
    "luka",
    "imbibitor-lunae",
    "lynx",
    "guinaifen",
    "hanya",
    "argenti",
    "xueyi",
    "black-swan",
    "misha",
    "boothill",
    "jade",
    "yunli",
    "march-7th",
    "rappa",
]

# Filter the data to only include objects with "char" key not in the exclude_chars list
filtered_data = [obj for obj in data if obj.get("char") not in exclude_chars]

# Find all unique artifacts
artifacts: set[str] = set()
for char_data in filtered_data:
    for i in range(1, 4):  # Check top 3 most used artifacts
        artifact_name = str(char_data.get(f"artifacts_{i}"))
        if artifact_name:
            artifacts.add(str(artifact_name))

# Find all unique planars
planars: set[str] = set()
for char_data in filtered_data:
    for i in range(1, 4):  # Check top 3 most used planars
        planar_name = str(char_data.get(f"planars_{i}"))
        if planar_name:
            planars.add(str(planar_name))

# Create a dictionary to store the results
results: dict[str, dict[str, dict[str, dict[str, list[float | str]]]]] = {}

# Loop through each artifact
for artifact in artifacts:
    # Filter the characters that have this artifact as
    # one of their three most used artifacts, or used at least 25% of the time
    artifact_chars: list[dict[str, str | float]] = []
    for char_data in filtered_data:
        for i in range(1, 4):  # Check top 3 most used artifacts
            artifact_name = str(char_data.get(f"artifacts_{i}"))
            artifact_app = float(char_data.get(f"artifacts_{i}_app", 0))
            if artifact_name == artifact and (artifact_app >= 25 or i == 1):
                artifact_chars.append(char_data)
                break

    # Find the character that uses the most of each
    # body stat and feet stat for this artifact
    body_stats: dict[str, dict[str, list[float | str]]] = {}
    feet_stats: dict[str, dict[str, list[float | str]]] = {}
    for char_data in artifact_chars:
        char_name = str(char_data.get("char"))
        for i in range(1, 4):  # Check top 3 body stats
            body_stat_name = str(char_data.get(f"body_stats_{i}"))
            body_stat_app = float(char_data.get(f"body_stats_{i}_app", 0))
            if body_stat_name and body_stat_app > 25:
                if body_stat_name not in body_stats:
                    body_stats[body_stat_name] = {
                        "app": [body_stat_app],
                        "char": [char_name],
                    }
                if char_name not in body_stats[body_stat_name]["char"]:
                    body_stats[body_stat_name]["app"].append(body_stat_app)
                    body_stats[body_stat_name]["char"].append(char_name)
        for i in range(1, 4):  # Check top 3 feet stats
            feet_stat_name = str(char_data.get(f"feet_stats_{i}"))
            feet_stat_app = float(char_data.get(f"feet_stats_{i}_app", 0))
            if feet_stat_name and feet_stat_app > 25:
                if feet_stat_name not in feet_stats:
                    feet_stats[feet_stat_name] = {
                        "app": [feet_stat_app],
                        "char": [char_name],
                    }
                if char_name not in feet_stats[feet_stat_name]["char"]:
                    feet_stats[feet_stat_name]["app"].append(feet_stat_app)
                    feet_stats[feet_stat_name]["char"].append(char_name)

    # Add the results to the main dictionary
    if body_stats or feet_stats:
        results[artifact] = {"Body": body_stats, "Feet": feet_stats}

# Loop through each artifact
for planar in planars:
    # Filter the characters that have this planar as
    # one of their three most used planars, or used at least 25% of the time
    planar_chars: list[dict[str, str | float]] = []
    for char_data in filtered_data:
        for i in range(1, 4):  # Check top 3 most used planars
            planar_name = str(char_data.get(f"planars_{i}"))
            planar_app = float(char_data.get(f"planars_{i}_app", 0))
            if planar_name == planar and (planar_app >= 25 or i == 1):
                planar_chars.append(char_data)
                break

    # Find the character that uses the most of each
    # sphere stat and rope stat for this planar
    sphere_stats: dict[str, dict[str, list[float | str]]] = {}
    rope_stats: dict[str, dict[str, list[float | str]]] = {}
    for char_data in planar_chars:
        char_name = str(char_data.get("char"))
        for i in range(1, 4):  # Check top 3 sphere stats
            sphere_stat_name = str(char_data.get(f"sphere_stats_{i}"))
            sphere_stat_app = float(char_data.get(f"sphere_stats_{i}_app", 0))
            if sphere_stat_name and sphere_stat_app > 25:
                if sphere_stat_name not in sphere_stats:
                    sphere_stats[sphere_stat_name] = {
                        "app": [sphere_stat_app],
                        "char": [char_name],
                    }
                if char_name not in sphere_stats[sphere_stat_name]["char"]:
                    sphere_stats[sphere_stat_name]["app"].append(sphere_stat_app)
                    sphere_stats[sphere_stat_name]["char"].append(char_name)
        for i in range(1, 4):  # Check top 3 rope stats
            rope_stat_name = str(char_data.get(f"rope_stats_{i}"))
            rope_stat_app = float(char_data.get(f"rope_stats_{i}_app", 0))
            if rope_stat_name and rope_stat_app > 25:
                if rope_stat_name not in rope_stats:
                    rope_stats[rope_stat_name] = {
                        "app": [rope_stat_app],
                        "char": [char_name],
                    }
                if char_name not in rope_stats[rope_stat_name]["char"]:
                    rope_stats[rope_stat_name]["app"].append(rope_stat_app)
                    rope_stats[rope_stat_name]["char"].append(char_name)

    # Add the results to the main dictionary
    if sphere_stats or rope_stats:
        results[planar] = {"Sphere": sphere_stats, "Rope": rope_stats}

# Export the results to a JSON file
with open(
    "../results/char_results/" + RECENT_PHASE_PF + "/artifact_stats.json",
    "w",
) as f:
    json.dump(results, f, indent=2)
