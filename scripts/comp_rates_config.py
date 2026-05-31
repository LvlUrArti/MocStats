"""Config file for comp_rates.py."""

from __future__ import annotations

from argparse import ArgumentParser
from datetime import datetime
from json import load
from os.path import dirname as path_dirname
from os.path import join as path_join
from sys import exit as sys_exit

from pydantic import BaseModel, field_validator

parser = ArgumentParser()
parser.add_argument("-v", "--version", help="Version to compile")
parser.add_argument("-m", "--mode", help="Set which mode to compile (moc/pf/as/aa)")
parser.add_argument("-a", "--all", action="store_true")
parser.add_argument("-cha", "--chars_all", action="store_true")
parser.add_argument("-ca", "--comps_all", action="store_true")
parser.add_argument("-d", "--duos", action="store_true")
parser.add_argument("-t", "--top", action="store_true")
parser.add_argument("-cht", "--chars_top", action="store_true")
parser.add_argument("-ct", "--comps_top", action="store_true")
parser.add_argument("-w", "--whale", action="store_true")
parser.add_argument("-f", "--f2p", action="store_true")
# Prompt for real data (hf data)
parser.add_argument("-y", "--yes", action="store_true")
parser.add_argument("-n", "--no", action="store_true")

args = parser.parse_args()

RECENT_PHASE: str = args.version or "4.2.3"


def relative_path(relative_path: str) -> str:
    """Get absolute path to resource, works for dev and for PyInstaller."""
    script_dir = path_dirname(__file__)
    return path_join(script_dir, relative_path)


class EndgameConfig(BaseModel):
    """Endgame collect date and version info."""

    collect_date: datetime
    moc_ver: str | None
    pf_ver: str | None
    as_ver: str | None
    aa_ver: str | None

    @field_validator("collect_date", mode="before")
    @classmethod
    def parse_collect_date(cls, value: str) -> datetime:
        """Convert string to datetime."""
        return datetime.strptime(value, "%d/%m/%Y")


with open(relative_path("../data/versions/config.json")) as f:
    raw_config = load(f)
    ENDGAME_INFOS: dict[str, EndgameConfig] = {
        char_name: EndgameConfig(**item) for char_name, item in raw_config.items()
    }
    ENDGAME_INFO: EndgameConfig | None = ENDGAME_INFOS.get(RECENT_PHASE)


moc_mode: bool = args.mode == "moc"
pf_mode: bool = args.mode in {"pf", "as"}
as_mode: bool = args.mode == "as"
aa_mode: bool = args.mode == "aa"
include_dual_sustain = False
star_num_threshold = 3

if not pf_mode:
    pf_mode = False
if not as_mode:
    as_mode = False

match args.mode:
    case "as":
        if ENDGAME_INFO and not ENDGAME_INFO.as_ver:
            sys_exit()
        pf_filename = "_as"
        all_stages = ["4-1", "4-2"]
        one_stage = ["4-1", "4-2"]
    case "pf":
        if ENDGAME_INFO and not ENDGAME_INFO.pf_ver:
            sys_exit()
        pf_filename = "_pf"
        all_stages = ["4-1", "4-2"]
        one_stage = ["4-1", "4-2"]
    case "aa":
        if ENDGAME_INFO and not ENDGAME_INFO.aa_ver:
            sys_exit()
        pf_filename = "_aa"
        all_stages = ["1-1", "1-2", "1-3", "2-1"]
        one_stage = ["1-1", "1-2", "1-3"]
    case "moc":
        if ENDGAME_INFO and not ENDGAME_INFO.moc_ver:
            sys_exit()
        pf_filename = "_moc"
        all_stages = ["12-1", "12-2"]
        one_stage = ["12-1", "12-2"]

        if ENDGAME_INFO:
            thresholds = [
                # Due to lack of sample, include <= 2* clears and adjust stages
                # for versions 1.0 - 1.1
                (datetime(2023, 6, 26), ["3-1", "3-2", "4-1", "4-2", "5-1", "5-2"], 1),
                (datetime(2023, 7, 24), ["6-1", "6-2", "7-1", "7-2", "8-1", "8-2"], 1),
                # Floor 11 & 12 added in version 1.6.1
                (datetime(2023, 12, 27), ["10-1", "10-2"], 3),
            ]
            for date, stages, star_num in thresholds:
                if ENDGAME_INFO.collect_date <= date:
                    include_dual_sustain = True
                    all_stages = one_stage = stages
                    star_num_threshold = star_num
                    break
    case _:
        pf_filename = ""

run_all_chars = True
run_chars_name = {"Aglaea", "Boothill", "Robin", "Silver Wolf"}
char_infographics = next(iter(run_chars_name))

CHAR_NAME_REPLACE = {
    "Dan Heng â€¢ Imbibitor Lunae": "Dan Heng • Imbibitor Lunae",
    "Dan Heng Ã¢â,¬Â¢ Imbibitor Lunae": "Dan Heng • Imbibitor Lunae",
    "Dan Heng \u2022 Imbibitor Lunae": "Dan Heng • Imbibitor Lunae",
    "Topaz and Numby": "Topaz & Numby",
}

# threshold for comps in character infographics, non-inclusive
char_app_rate_threshold = 0.25

# threshold for comps, not inclusive
app_rate_threshold = 0.1
app_rate_threshold_round = 0
skew_num = 0.8
duo_dict_len = 30
duo_dict_len_print = 10
CONS_LIMIT = 2

RECENT_PHASE_PF = RECENT_PHASE + pf_filename
BASE_RESULT_PATH = f"results/all_results/{RECENT_PHASE}/{RECENT_PHASE_PF}"
CHAR_RESULT_PATH = f"results/all_results/{RECENT_PHASE}/{RECENT_PHASE_PF}/chars"
COMP_RESULT_PATH = f"results/all_results/{RECENT_PHASE}/{RECENT_PHASE_PF}/comps"
BUILD_RESULT_PATH = f"results/all_results/{RECENT_PHASE}/{RECENT_PHASE_PF}/builds"

skip_self = False
skip_random = False
WHALE_ONLY: bool = args.whale
F2P_ONLY: bool = args.f2p

run_commands = {
    # "Duos check",
    "Char usages all stages",
    "Char usages for each stage",
    "Comp usage all stages",
    "Comp usages for each stage",
    # "Character specific infographics",
}

if args.top or args.f2p:
    run_commands = {
        "Char usages all stages",
        "Char usages for each stage",
    }

elif args.whale:
    run_commands = {
        "Char usages all stages",
        "Char usages for each stage",
        "Comp usage all stages",
        "Comp usages for each stage",
    }

elif args.chars_top:
    run_commands = {
        "Char usages all stages",
    }

elif args.comps_top:
    run_commands = {
        "Comp usage all stages",
    }

elif args.all:
    run_commands = {
        "Char usages all stages",
        "Char usages for each stage",
        "Comp usage all stages",
        "Comp usages for each stage",
    }

elif args.chars_all:
    run_commands = {
        "Char usages all stages",
    }

elif args.comps_all:
    run_commands = {
        "Comp usage all stages",
        "Comp usages for each stage",
    }

elif args.duos:
    run_commands = {
        "Duos check",
    }

alt_comps = "Character specific infographics" in run_commands
if alt_comps and char_app_rate_threshold > app_rate_threshold:
    app_rate_threshold = char_app_rate_threshold


class CharInfo(BaseModel):
    """Character info from characters.json."""

    id: str
    rarity: int
    path: str
    element: str
    availability: str
    slug: str
    release: datetime
    role: list[str]
    trailblazer_ids: list[str] | None = None

    @field_validator("release", mode="before")
    @classmethod
    def parse_epoch(cls, value: int) -> datetime:
        """Convert epoch timestamp to datetime."""
        return datetime.fromtimestamp(value)


with open(relative_path("../data/characters.json")) as char_file:
    raw_characters = load(char_file)
    CHARS_INFO: dict[str, CharInfo] = {
        char_name: CharInfo(**item)
        for char_name, item in raw_characters.items()
        if (
            not ENDGAME_INFO
            or (datetime.fromtimestamp(item["release"]) < ENDGAME_INFO.collect_date)
        )
    }

with open(relative_path("../data/light_cones.json")) as char_file:
    LIGHT_CONES: dict[str, dict[str, str | int]] = load(char_file)

sig_weaps: set[str] = set()
STAND_WEAPS = {
    "Night on the Milky Way",
    "Something Irreplaceable",
    "But the Battle Isn't Over",
    "In the Name of the World",
    "Moment of Victory",
    "Time Waits for No One",
    "Sleep Like the Dead",
    "On the Fall of an Aeon",
    "Cruising in the Stellar Sea",
    "Texture of Memories",
    "Solitary Healing",
    "Eternal Calculus",
}
MAX_LC_RARITY = 5
for light_cone in LIGHT_CONES:
    if (
        LIGHT_CONES[light_cone]["rarity"] == MAX_LC_RARITY
        and LIGHT_CONES[light_cone]["name"] not in STAND_WEAPS
    ):
        sig_weaps.add(str(LIGHT_CONES[light_cone]["name"]))


def slug_with_prefix(char_name: str) -> str:
    """Get character slug with prefix."""
    prefix = char_name[:5] if char_name.startswith(("solo-", "supp-")) else ""
    slug = CHARS_INFO[char_name[5:] if prefix else char_name].slug

    return f"{prefix}{slug}" if prefix else slug
