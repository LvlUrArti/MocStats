import io
import json

import requests

download = requests.get(
    "https://github.com/Mar-7th/StarRailRes/raw/master/index_new/en/relic_sets.json"
).content.decode("utf-8")
artifacts = json.load(io.StringIO(download))

with open("../data/relic_affixes.json") as artifact_file:
    artifacts2 = json.load(artifact_file)
# artifacts2 = {}

artifacts_affixes: dict[str, list[str]] = {}
for artifact in artifacts:
    if artifacts[artifact]["id"][0] == "1":
        affix = artifacts[artifact]["desc"][0]

        if affix[-1] == ".":
            affix = affix[:-1]
        for i in ["DMG "]:
            affix = affix.replace(i, "")

        affix = affix.replace("increases by ", "+")
        if "Increases " in affix:
            affix = affix.replace("Increases ", "")
            affix = affix.replace("by ", "+")
        if "Reduces " in affix:
            affix = affix.replace("Reduces ", "")
            affix = affix.replace("by ", "-")
            # split = affix.split(" ")
            # affix = split[1] + " +" + split[0]

        affix = affix.replace("CRIT Rate", "CR")
        affix = affix.replace("Physical", "Phys")
        affix = affix.replace("Break Effect", "BE")
        affix = affix.replace("Imaginary", "Imag.")
        affix = affix.replace("Quantum", "Quan.")
        affix = affix.replace("Lightning", "Light.")
        affix = affix.replace("Outgoing Healing", "Heal")

        if affix not in artifacts_affixes:
            artifacts_affixes[affix] = []
        artifacts_affixes[affix].append(artifacts[artifact]["name"])

for artifact in list(artifacts_affixes.keys()):
    if len(artifacts_affixes[artifact]) > 1 and artifact not in artifacts2:
        if len(artifact) > 12:
            print("Set name too long: " + artifact)
        else:
            add_arti = input("Add " + artifact + "? (y/n): ")
            if add_arti == "y":
                artifacts2[artifact] = artifacts_affixes[artifact]
    else:
        del artifacts_affixes[artifact]
print()

with open("../data/relic_sets.json", "w") as out_file:
    out_file.write(json.dumps(artifacts, indent=4))

with open("../data/relic_affixes.json", "w") as out_file:
    out_file.write(json.dumps(artifacts2, indent=4))

download = requests.get(
    "https://github.com/Mar-7th/StarRailRes/raw/master/index_new/en/relics.json"
).content.decode("utf-8")
with open("../data/relics.json", "w") as out_file:
    out_file.write(json.dumps(json.load(io.StringIO(download)), indent=4))

download = requests.get(
    "https://github.com/Mar-7th/StarRailRes/raw/master/index_new/en/light_cones.json"
).content.decode("utf-8")
with open("../data/light_cones.json", "w") as out_file:
    out_file.write(json.dumps(json.load(io.StringIO(download)), indent=4))

download = requests.get(
    "https://github.com/Mar-7th/StarRailRes/raw/master/index_new/en/simulated_blessings.json"
).content.decode("utf-8")
with open("../data/simulated_blessings.json", "w") as out_file:
    out_file.write(json.dumps(json.load(io.StringIO(download)), indent=4))

download = requests.get(
    "https://github.com/Mar-7th/StarRailRes/raw/master/index_new/en/simulated_curios.json"
).content.decode("utf-8")
curio_json = json.load(io.StringIO(download))
curio_json["901"] = curio_json["109"].copy()
curio_json["902"] = curio_json["109"].copy()
curio_json["901"]["id"] = "901"
curio_json["902"]["id"] = "902"
with open("../data/simulated_curios.json", "w") as out_file:
    out_file.write(json.dumps(curio_json, indent=4))

# download = requests.get("https://github.com/Mar-7th/StarRailRes/raw/master/index_new/en/simulated_blocks.json").content.decode('utf-8')
# with open("../data/simulated_blocks.json", "w") as out_file:
#     out_file.write(json.dumps(json.load(io.StringIO(download)),indent=4))

with open("../data/characters.json") as char_file:
    chars1 = json.load(char_file)
download = requests.get(
    "https://github.com/Mar-7th/StarRailRes/raw/master/index_new/en/characters.json"
).content.decode("utf-8")
chars2 = json.load(io.StringIO(download))

path_map: dict[str, str] = {
    "Warlock": "Nihility",
    "Elation": "Elation",
    "Rogue": "Hunt",
    "Mage": "Erudition",
    "Warrior": "Destruction",
    "Shaman": "Harmony",
    "Knight": "Preservation",
    "Priest": "Abundance",
    "Memory": "Remembrance",
}

for char in chars2.values():
    char_name = char["name"]
    if char_name == "{NICKNAME}":
        char_name = char["element"].capitalize() + " Trailblazer"
        if char_name in chars1:
            if "trailblazer_ids" not in chars1[char_name]:
                chars1[char_name]["trailblazer_ids"] = []
            if char["id"] not in chars1[char_name]["trailblazer_ids"]:
                chars1[char_name]["trailblazer_ids"].append(char["id"])
    elif char_name == "March 7th":
        char_name = char["element"].capitalize() + " March 7th"
        if char_name in chars1:
            if "trailblazer_ids" not in chars1[char_name]:
                chars1[char_name]["trailblazer_ids"] = []
            if char["id"] not in chars1[char_name]["trailblazer_ids"]:
                chars1[char_name]["trailblazer_ids"].append(char["id"])
    if char_name not in chars1:
        add_char = input("Add " + char_name + "? (y/n): ")
        if add_char == "y":
            chars1[char_name] = char.copy()
            chars1[char_name]["path"] = path_map[char["path"]]

            if char["rarity"] == 4:
                chars1[char_name]["availability"] = "4*"
            elif char["rarity"] == 5:
                if "Trailblazer" in char_name:
                    chars1[char_name]["rarity"] = 4
                    chars1[char_name]["availability"] = "4*"
                    chars1[char_name]["name"] = "Trailblazer"
                    chars1[char_name]["trailblazer_ids"] = [char["id"]]
                else:
                    chars1[char_name]["availability"] = "Limited 5*"

            char_roles: list[str] = []
            while True:
                print("Role? 0: DPS, 1: Specialist, 2: Amplifier, 3: Sustain")
                role_char = input()
                match str(role_char):
                    case "0":
                        char_roles.append("dps")
                    case "1":
                        char_roles.append("specialist")
                    case "2":
                        char_roles.append("amplifier")
                    case "3":
                        char_roles.append("sustain")
                    case _:
                        pass
                print("Another role? (y/n)")
                another_role = input()
                if another_role != "y":
                    break
                chars1[char_name]["role"] = char_roles

with open("../data/characters.json", "w") as out_file:
    out_file.write(json.dumps(chars1, indent=4))
