"""Config file for comp_rates.py."""

from __future__ import annotations

from argparse import ArgumentParser
from datetime import datetime
from json import load
from os.path import dirname as path_dirname
from os.path import join as path_join
from sys import exit as sys_exit

from pydantic import BaseModel, Field, field_validator

parser = ArgumentParser()
parser.add_argument("-v", "--version", help="Version to compile")
parser.add_argument("-m", "--mode", help="Set which mode to compile (moc/pf/as/aa)")
parser.add_argument("-a", "--all", action="store_true")
parser.add_argument("-cha", "--chars_all", action="store_true")
parser.add_argument("-ca", "--comps_all", action="store_true")
parser.add_argument("-t", "--top", action="store_true")
parser.add_argument("-cht", "--chars_top", action="store_true")
parser.add_argument("-ct", "--comps_top", action="store_true")
parser.add_argument("-w", "--whale", action="store_true")
parser.add_argument("-f", "--f2p", action="store_true")
# Prompt for real data (hf data)
parser.add_argument("-y", "--yes", action="store_true")
parser.add_argument("-n", "--no", action="store_true")

args = parser.parse_args()

RECENT_PHASE: str = args.version or "4.4.1"


def relative_path(relative_path: str) -> str:
    """Get absolute path to resource, works for dev and for PyInstaller."""
    script_dir = path_dirname(__file__)
    return path_join(script_dir, relative_path)


class EndgameMode(BaseModel):
    """Endgame mode version info."""

    ver: str
    name: str
    start: datetime
    end: datetime

    @field_validator("start", "end", mode="before")
    @classmethod
    def parse_date(cls, value: str) -> datetime:
        """Convert string to datetime."""
        return datetime.strptime(value, "%d/%m/%Y")


class EndgameConfig(BaseModel):
    """Endgame collect date and version info."""

    collect_date: datetime
    moc: EndgameMode | None = None
    pf: EndgameMode | None = None
    as_: EndgameMode | None = Field(None, alias="as")
    aa: EndgameMode | None = None

    @field_validator("collect_date", mode="before")
    @classmethod
    def parse_collect_date(cls, value: str) -> datetime:
        """Convert string to datetime."""
        return datetime.strptime(value, "%d/%m/%Y")


MODE_ATTR_MAP: dict[str, str] = {
    "moc": "moc",
    "pf": "pf",
    "as": "as_",
    "aa": "aa",
}


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

if not pf_mode:
    pf_mode = False
if not as_mode:
    as_mode = False


class ModeConfig(BaseModel):
    """Configuration for a game mode."""

    all_stages: list[str]
    one_stage: list[str]
    star_num_threshold: int
    include_dual_sustain: bool = False
    thresholds: list[tuple[datetime, list[str], list[str], int, bool]]


# Mode configurations
mode_configs: dict[str, ModeConfig] = {
    "as": ModeConfig(
        all_stages=["4-1", "4-2", "4-3"],
        one_stage=["4-1", "4-2", "4-3"],
        star_num_threshold=4,
        # Starward Mode added in phase 4.3.1
        thresholds=[(datetime(2026, 6, 8), ["4-1", "4-2"], ["4-1", "4-2"], 3, False)],
    ),
    "pf": ModeConfig(
        all_stages=["4-1", "4-2", "4-3"],
        one_stage=["4-1", "4-2", "4-3"],
        star_num_threshold=4,
        # Starward Mode added in phase 4.3.1
        thresholds=[(datetime(2026, 6, 22), ["4-1", "4-2"], ["4-1", "4-2"], 3, False)],
    ),
    "aa": ModeConfig(
        all_stages=["1-1", "1-2", "1-3", "2-1"],
        one_stage=["1-1", "1-2", "1-3"],
        star_num_threshold=3,
        thresholds=[],
    ),
    "moc": ModeConfig(
        all_stages=["12-1", "12-2", "12-3"],
        one_stage=["12-1", "12-2", "12-3"],
        star_num_threshold=4,
        thresholds=[
            (
                datetime(2023, 6, 26),  # Before phase 1.1.2
                [f"{i}-{j}" for i in range(3, 11) for j in (1, 2)],  # stages 3-10
                [f"{i}-{j}" for i in range(3, 6) for j in (1, 2)],  # stages 3-5
                1,
                True,
            ),
            (
                datetime(2023, 7, 24),  # Before phase 1.2.1
                [f"{i}-{j}" for i in range(6, 11) for j in (1, 2)],  # stages 6-10
                [f"{i}-{j}" for i in range(6, 9) for j in (1, 2)],  # stages 6-8
                1,
                True,
            ),
            # Floor 11 & 12 added in version 1.6.1
            (datetime(2023, 12, 27), ["10-1", "10-2"], ["10-1", "10-2"], 3, True),
            # Starward Mode added in phase 4.3.1
            (datetime(2026, 7, 6), ["12-1", "12-2"], ["12-1", "12-2"], 3, False),
        ],
    ),
}


cfg = mode_configs.get(args.mode)

if cfg is None:
    pf_filename = ""
    all_stages: list[str] = []
    one_stage: list[str] = []
    star_num_threshold = 3
else:
    # Check version exists
    if ENDGAME_INFO:
        mode_obj = getattr(ENDGAME_INFO, MODE_ATTR_MAP[args.mode])
        if not mode_obj or not mode_obj.ver:
            sys_exit()

    # Initial values
    pf_filename = f"_{args.mode}"
    all_stages = cfg.all_stages
    one_stage = cfg.one_stage
    star_num_threshold = cfg.star_num_threshold
    include_dual_sustain = cfg.include_dual_sustain

    # Apply thresholds if any
    if ENDGAME_INFO and cfg.thresholds:
        for date, stages, one_stages, star_num, set_dual_sustain in cfg.thresholds:
            if ENDGAME_INFO.collect_date <= date:
                include_dual_sustain = set_dual_sustain
                all_stages = stages
                one_stage = one_stages
                star_num_threshold = star_num
                break

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
TRIM_PROPORTION = 0.1

RECENT_PHASE_PF = RECENT_PHASE + pf_filename
BASE_RESULT_PATH = f"results/all_results/{RECENT_PHASE}/{RECENT_PHASE_PF}"
CHAR_RESULT_PATH = f"{BASE_RESULT_PATH}/chars"
COMP_RESULT_PATH = f"{BASE_RESULT_PATH}/comps"
BUILD_RESULT_PATH = f"{BASE_RESULT_PATH}/builds"
DUOS_RESULT_PATH = f"{BASE_RESULT_PATH}/duos"

skip_self = False
skip_random = False
WHALE_ONLY: bool = args.whale
F2P_ONLY: bool = args.f2p

run_commands = {
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
