"""Update JSON data."""

import json
from io import StringIO
from typing import Any

import requests
from comp_rates_config import RECENT_PHASE
from pydantic import BaseModel


def load_from_url(url: str) -> Any:  # noqa: ANN401
    """Load data from URL."""
    download = requests.get(url, timeout=10).content.decode("utf-8")
    return json.load(StringIO(download))


artifacts: dict[str, dict[str, str]] = load_from_url(
    "https://github.com/Mar-7th/StarRailRes/raw/master/index_new/en/relic_sets.json",
)

with open("../data/relic_affixes.json") as artifact_file:
    artifacts2: dict[str, list[str]] = json.load(artifact_file)

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

        affix = affix.replace("CRIT Rate", "CR")
        affix = affix.replace("CRIT", "CDMG")
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
    out_file.write(json.dumps(artifacts, indent=2))

with open("../data/relic_affixes.json", "w") as out_file:
    out_file.write(json.dumps(artifacts2, indent=2))

download = load_from_url(
    "https://github.com/Mar-7th/StarRailRes/raw/master/index_new/en/relics.json",
)
with open("../data/relics.json", "w") as out_file:
    out_file.write(json.dumps(download, indent=2))

download = load_from_url(
    "https://github.com/Mar-7th/StarRailRes/raw/master/index_new/en/light_cones.json",
)
lc_data = {item["name"]: item for item in download.values()}

alt_lc_names = {
    "Shadowed by Night": "Shadowed By Night",
    "Sailing Towards a Second Life": "Sailing Towards A Second Life",
}
for alt_lc, alt_name in alt_lc_names.items():
    lc_data[alt_lc]["alt_name"] = alt_name

with open("../data/light_cones.json", "w") as out_file:
    out_file.write(json.dumps(lc_data, indent=2))


# Characters update


class RawCharInfo(BaseModel):
    """Character info from characters.json."""

    id: str
    name: str
    rarity: int
    path: str
    element: str
    availability: str | None = None


PATH_MAP: dict[str, str] = {
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

MULTI_ELEM_CHARS: dict[str, str] = {
    "{NICKNAME}": " Trailblazer",
    "March 7th": " March 7th",
}

ROLES = [
    "DPS",
    "Specialist",
    "Amplifier",
    "Sustain",
]

with open("../data/characters.json") as char_file:
    chars_data: dict[str, dict[str, str | int | list[str] | None]] = json.load(
        char_file,
    )

download = load_from_url(
    "https://github.com/Mar-7th/StarRailRes/raw/master/index_new/en/characters.json",
)
raw_chars = {char_name: RawCharInfo(**item) for char_name, item in download.items()}

for char in raw_chars.values():
    char_name = char.name
    multi_elem_char = False

    if char.element == "Thunder":
        char.element = "Lightning"

    if char_name in MULTI_ELEM_CHARS:
        multi_elem_char = True
        char_name = char.element.capitalize() + MULTI_ELEM_CHARS[char_name]

    if char_name not in chars_data:
        add_char = input("Add " + char_name + "? (y/n): ")
        if add_char == "y":
            char_add: dict[str, str | int | list[str] | None] = {
                "id": char.id,
                "rarity": char.rarity,
                "path": PATH_MAP[char.path],
                "element": char.element,
                "availability": char.availability,
                "slug": char_name.lower().replace(" ", "-"),
                "release_phase": RECENT_PHASE,
            }

            if char.rarity == 4:
                char_add["availability"] = "4*"
            elif char.rarity == 5:
                if "Trailblazer" in char_name:
                    char_add["rarity"] = 4
                    char_add["availability"] = "4*"
                else:
                    char_add["availability"] = "Limited 5*"

            char_roles: list[str] = []
            while True:
                role_char = int(input(f"Role? (0-{len(ROLES)}): {ROLES}: "))
                if 0 <= role_char < len(ROLES):
                    char_roles.append(ROLES[role_char].lower())

                another_role = input("Another role? (y/n): ")
                if another_role != "y":
                    break

            char_add["role"] = char_roles
            chars_data[char_name] = char_add

    if multi_elem_char:
        trailblazer_id_list: list[str] = []
        if "trailblazer_ids" in chars_data[char_name]:
            trailblazer_id_list += chars_data[char_name]["trailblazer_ids"]
        if char.id not in trailblazer_id_list:
            trailblazer_id_list.append(char.id)
        chars_data[char_name]["trailblazer_ids"] = trailblazer_id_list

with open("../data/characters.json", "w") as out_file:
    out_file.write(json.dumps(chars_data, indent=2))


def add_endgame(versions_dict: dict[str, dict[str, str]]) -> dict[str, dict[str, str]]:
    """Add endgame versions."""
    versions: dict[str, dict[str, str]] = {}
    for version, version_item in versions_dict.items():
        version_time = version_item["versionTime"]
        if version_time != "xx/xx/20xx - xx/xx/20xx":
            versions[version] = {
                "name": version_item["versionName"],
                "time_start": version_time.split(" - ")[0],
                "time_end": version_time.split(" - ")[1],
            }
    return versions


# Endgame versions update
save_entries: dict[str, dict[str, dict[str, str]]] = {}

moc_data: list[dict[str, dict[str, dict[str, str]]]] = load_from_url(
    "https://www.buhflipexplode.org/hsr/fh/fh-versions.json",
)
for entry in moc_data:
    name = str(entry["name"])
    if name == "Memory of Chaos":
        save_entries[name] = add_endgame(entry["versions"])

pf_data: dict[str, dict[str, str]] = load_from_url(
    "https://www.buhflipexplode.org/hsr/pf/pf-versions.json",
)
save_entries["Pure Fiction"] = add_endgame(pf_data)

as_data: dict[str, dict[str, str]] = load_from_url(
    "https://www.buhflipexplode.org/hsr/as/as-versions.json",
)
save_entries["Apocalyptic Shadow"] = add_endgame(as_data)

aa_data: dict[str, dict[str, str]] = load_from_url(
    "https://www.buhflipexplode.org/hsr/aa/aa-versions.json",
)
save_entries["Anomaly Arbitration"] = add_endgame(aa_data)

with open("../data/versions/endgame_versions.json", "w") as out_file:
    out_file.write(json.dumps(save_entries, indent=2))
