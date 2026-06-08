"""Update JSON data."""

# ruff: noqa: N815, ANN401, D101, D102

import json
from io import StringIO
from typing import Any

import requests
from pydantic import BaseModel, field_validator


def load_from_url(url: str) -> Any:
    """Load data from URL."""
    download = requests.get(url, timeout=10).content.decode("utf-8")
    return json.load(StringIO(download))


relic_sets: dict[str, dict[str, str]] = load_from_url(
    "https://github.com/Mar-7th/StarRailRes/raw/master/index_new/en/relic_sets.json",
)

with open("../data/relic_affixes.json") as file:
    relic_affixes: dict[str, list[str]] = json.load(file)

relics_affixes: dict[str, list[str]] = {}
for relic in relic_sets.values():
    if relic["id"][0] == "1":
        affix = relic["desc"][0]

        if affix[-1] == ".":
            affix = affix[:-1]

        if "Increases " in affix:
            affix = affix.replace("Increases ", "")
            affix = affix.replace("by ", "+")
        if "Reduces " in affix:
            affix = affix.replace("Reduces ", "")
            affix = affix.replace("by ", "-")

        replacements = {
            "increases by ": "+",
            "DMG ": "",
            "CRIT Rate": "CR",
            "CRIT": "CDMG",
            "Physical": "Phys",
            "Break Effect": "BE",
            "Imaginary": "Imag.",
            "Quantum": "Quan.",
            "Lightning": "Light.",
            "Outgoing Healing": "Heal",
        }
        for old, new in replacements.items():
            affix = affix.replace(old, new)

        if affix not in relics_affixes:
            relics_affixes[affix] = []
        relics_affixes[affix].append(relic["name"])

for relic in list(relics_affixes.keys()):
    if len(relics_affixes[relic]) > 1 and relic not in relic_affixes:
        if len(relic) > 12:
            print("Set name too long: " + relic)
        else:
            add_arti = input("Add " + relic + "? (y/n): ")
            if add_arti == "y":
                relic_affixes[relic] = relics_affixes[relic]
    else:
        del relics_affixes[relic]

with open("../data/relic_sets.json", "w") as out_file:
    out_file.write(json.dumps(relic_sets, indent=2))

with open("../data/relic_affixes.json", "w") as out_file:
    out_file.write(json.dumps(relic_affixes, indent=2))

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

    en: str
    rank: str
    baseType: str
    damageType: str
    release: int | None = None


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

latest_ver: str = load_from_url("https://static.nanoka.cc/manifest.json")["hsr"][
    "latest"
]
download = load_from_url(f"https://static.nanoka.cc/hsr/{latest_ver}/character.json")
raw_chars = {char_id: RawCharInfo(**item) for char_id, item in download.items()}

for char_id, char in raw_chars.items():
    char_name = char.en.replace("<unbreak>", "").replace("</unbreak>", "")
    multi_elem_char = False

    if char.damageType == "Thunder":
        char.damageType = "Lightning"

    if char_name in MULTI_ELEM_CHARS:
        multi_elem_char = True
        char_name = char.damageType.capitalize() + MULTI_ELEM_CHARS[char_name]

    if char_name not in chars_data:
        add_char = input("Add " + char_name + "? (y/n): ")
        if add_char == "y":
            char_add: dict[str, str | int | list[str] | None] = {
                "id": char_id,
                "rarity": int("".join(filter(str.isdigit, char.rank))),
                "path": PATH_MAP[char.baseType],
                "element": char.damageType,
                "availability": "4*",
                "slug": char_name.lower().replace(" ", "-"),
                "release": char.release,
            }

            if char_add["rarity"] == 5:
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
        if char_id not in trailblazer_id_list:
            trailblazer_id_list.append(char_id)
        chars_data[char_name]["trailblazer_ids"] = trailblazer_id_list

with open("../data/characters.json", "w") as out_file:
    out_file.write(json.dumps(chars_data, indent=2))


class EndgameEnemy(BaseModel):
    id: str


class EndgameWave(BaseModel):
    enemies: list[EndgameEnemy]


class EndgameSide(BaseModel):
    waves: list[EndgameWave]


class EndgameSides(BaseModel):
    sides: list[EndgameSide]

    @field_validator("sides", mode="before")
    @classmethod
    def normalize_waves(cls, value: list[dict[str, str]]) -> list[dict[str, Any]]:
        # If the input has 'enemies' but no 'waves', wrap it into a waves array
        if "enemies" in value[0]:
            return [{"waves": value}]
        return value


class EndgameNodes(BaseModel):
    nodes: list[EndgameSides]


class EndgameConfig(BaseModel):
    versionTime: str
    versionName: str
    versionEnemies: EndgameNodes  # Always expect nodes after normalization

    @field_validator("versionEnemies", mode="before")
    @classmethod
    def normalize_enemies(cls, value: dict[str, Any]) -> dict[str, list[Any]]:
        # If the input has 'sides' but no 'nodes', wrap it into a nodes array
        if "sides" in value:
            return {"nodes": [value]}
        return value


def add_endgame(versions_dict: dict[str, dict[str, Any]]) -> dict[str, dict[str, str]]:
    """Add endgame versions."""
    versions: dict[str, dict[str, Any]] = {}
    for version, version_item in versions_dict.items():
        config = EndgameConfig(**version_item)
        version_time = config.versionTime
        if version_time != "xx/xx/20xx - xx/xx/20xx":
            versions[version] = {
                "name": config.versionName,
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
