"""Config file for comp_rates.py."""

from __future__ import annotations

from argparse import ArgumentParser
from json import load
from os.path import dirname as path_dirname
from os.path import join as path_join

# don't add underscore, i.e. 2.2.1"_pf"
RECENT_PHASE = "3.5.3"

# if no past phase, leave blank
# add underscore, i.e. 2.2.1"_pf"
past_phase = "3.5.2"

parser = ArgumentParser()
parser.add_argument("-a", "--all", action="store_true")
parser.add_argument("-ca", "--comps_all", action="store_true")
parser.add_argument("-d", "--duos", action="store_true")
parser.add_argument("-t", "--top", action="store_true")
parser.add_argument("-cht", "--chars_top", action="store_true")
parser.add_argument("-ct", "--comps_top", action="store_true")
parser.add_argument("-w", "--whale", action="store_true")
parser.add_argument("-f", "--f2p", action="store_true")

parser.add_argument(
    "-moc",
    "--memory_of_chaos",
    action="store_true",
)
parser.add_argument(
    "-pf",
    "--pure_fic",
    action="store_true",
)
parser.add_argument(
    "-as",
    "--apoc_shadow",
    action="store_true",
)

args = parser.parse_args()


# if as: pf_mode = True
pf_mode: bool = args.pure_fic or args.apoc_shadow
as_mode: bool = args.apoc_shadow

if not pf_mode:
    pf_mode = False
if not as_mode:
    as_mode = False

suffix = ""
if as_mode:
    suffix = "_as"
elif pf_mode:
    suffix = "_pf"
RECENT_PHASE_PF = RECENT_PHASE + suffix
past_phase = past_phase + suffix

run_all_chars = False
run_chars_name = ["Aglaea", "Boothill", "Robin", "Silver Wolf"]
char_infographics = run_chars_name[1]

DPS_SUB_LIST = ["Anaxa", "Argenti", "Blade", "Evernight"]

DPS_LIST = [
    "Yanqing",
    "Hook",
    "Seele",
    "Dan Heng • Imbibitor Lunae",
    "Dr. Ratio",
    "Argenti",
    "Rappa",
    "Jing Yuan",
    "Firefly",
    "Boothill",
    "Feixiao",
    "Acheron",
    "The Herta",
    "Saber",
    "Aglaea",
    "Phainon",
    "Hysilens",
    "Castorice",
    "Archer",
]

DPS_APPEND_LIST = [
    "Xueyi",
    "Physical Trailblazer",
    "Sushang",
    "Misha",
    "Dan Heng",
    "Arlan",
    "Qingque",
    "Luka",
    "Clara",
    "Himeko",
    "Yunli",
    "Jingliu",
    "Blade",
    "Mydei",
    "Anaxa",
]

SUB_DPS_LIST = [
    "Black Swan",
    "Jade",
    "Kafka",
]

SUB_DPS_APPEND_LIST = [
    "Imaginary March 7th",
    "Moze",
    "Welt",
    "Serval",
    "Herta",
    "Topaz & Numby",
    "Cipher",
]

DOT_SUPPORT_LIST = ["Sampo", "Guinaifen"]

HARMONY_LIST = [
    "Bronya",
    "Silver Wolf",
    "Asta",
    "Tingyun",
    "Pela",
    "Yukong",
    "Hanya",
    "Ruan Mei",
    "Sparkle",
    "Robin",
    "Imaginary Trailblazer",
    "Jiaoqiu",
    "Sunday",
    "Fugue",
    "Ice Trailblazer",
    "Tribbie",
    "Cerydra",
]

HEALER_LIST = [
    "Natasha",
    "Luocha",
    "Bailu",
    "Lynx",
    "Huohuo",
    "Gallagher",
    "Hyacine",
]

PRESERVATION_LIST = [
    "Ice March 7th",
    "Gepard",
    "Fire Trailblazer",
    "Fu Xuan",
    "Aventurine",
    "Lingsha",
]

DOT_LIST = [
    "Kafka",
    "Black Swan",
    "Serval",
    "Sampo",
    "Luka",
    "Guinaifen",
]

FUA_LIST = [
    "Topaz & Numby",
    "Dr. Ratio",
    "Clara",
    "Yunli",
    "Jing Yuan",
    "Himeko",
    "Kafka",
    "Blade",
    "Herta",
    "Xueyi",
    "Jade",
    "Feixiao",
    "Moze",
]

SUPER_BREAK_LIST = ["Imaginary Trailblazer", "Fugue"]


# threshold for comps in character infographics, non-inclusive
char_app_rate_threshold = 0.25

# threshold for comps, not inclusive
app_rate_threshold = 0.1
app_rate_threshold_round = 0
json_threshold = 0
f2p_app_rate_threshold = 0.1
skew_num = 0.8
duo_dict_len = 30
duo_dict_len_print = 10
LAST_MOC_FLOOR = 12
CONS_LIMIT = 2

skip_self = False
skip_random = False
archetype = "all"
WHALE_ONLY: bool = args.whale
F2P_ONLY: bool = args.f2p

# Char infographics should be separated from overall comp rankings
run_commands = [
    # "Duos check",
    "Char usages 8 - 10",
    "Char usages for each stage",
    "Char usages for each stage (combined)",
    "Comp usage 8 - 10",
    "Comp usages for each stage",
    # "Character specific infographics",
    # "Char usages all stages",
    # "Comp usage all stages",
]

if args.top or args.f2p:
    run_commands = [
        "Char usages 8 - 10",
        "Comp usage 8 - 10",
    ]

elif args.whale:
    run_commands = [
        "Char usages 8 - 10",
        "Comp usage 8 - 10",
        "Comp usages for each stage",
    ]

elif args.chars_top:
    run_commands = [
        "Char usages 8 - 10",
    ]

elif args.comps_top:
    run_commands = [
        "Comp usage 8 - 10",
    ]

elif args.all:
    run_commands = [
        "Char usages 8 - 10",
        "Char usages for each stage",
        "Char usages for each stage (combined)",
        "Comp usage 8 - 10",
        "Comp usages for each stage",
    ]

elif args.comps_all:
    run_commands = [
        "Comp usage 8 - 10",
        "Comp usages for each stage",
    ]

elif args.duos:
    run_commands = [
        "Duos check",
    ]

alt_comps = "Character specific infographics" in run_commands
if alt_comps and char_app_rate_threshold > app_rate_threshold:
    app_rate_threshold = char_app_rate_threshold


def relative_path(relative_path: str) -> str:
    """Get absolute path to resource, works for dev and for PyInstaller."""
    script_dir = path_dirname(__file__)
    return path_join(script_dir, relative_path)


with open(relative_path("../data/characters.json")) as char_file:
    CHARACTERS: dict[str, dict[str, str | int | None]] = load(char_file)

with open(relative_path("../data/light_cones.json")) as char_file:
    LIGHT_CONES: dict[str, dict[str, str | int | None]] = load(char_file)

sig_weaps: list[str] = []
STAND_WEAPS = [
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
]
MAX_LC_RARITY = 5
for light_cone in LIGHT_CONES:
    if (
        LIGHT_CONES[light_cone]["rarity"] == MAX_LC_RARITY
        and LIGHT_CONES[light_cone]["name"] not in STAND_WEAPS
    ):
        sig_weaps += [str(LIGHT_CONES[light_cone]["name"])]
