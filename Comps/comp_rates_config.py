from argparse import ArgumentParser
from json import load
from os.path import dirname as path_dirname
from os.path import join as path_join

# don't add underscore, i.e. 2.2.1"_pf"
RECENT_PHASE = "3.4.3"

# if no past phase, leave blank
# add underscore, i.e. 2.2.1"_pf"
past_phase = "3.4.2"

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


global pf_mode
global as_mode
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


# threshold for comps in character infographics, non-inclusive
global char_app_rate_threshold
char_app_rate_threshold = 0.25

# threshold for comps, not inclusive
global app_rate_threshold
global app_rate_threshold_round
global f2p_app_rate_threshold
app_rate_threshold = 0.1
app_rate_threshold_round = 0
json_threshold = 0
f2p_app_rate_threshold = 0.1
skew_num = 0.8
duo_dict_len = 30
duo_dict_len_print = 10

skip_self = False
skip_random = False
archetype = "all"
whaleOnly: bool = args.whale
f2pOnly: bool = args.f2p

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
    script_dir = path_dirname(__file__)
    return path_join(script_dir, relative_path)


with open(relative_path("../data/characters.json")) as char_file:
    CHARACTERS: dict[str, dict[str, str | int | None]] = load(char_file)

with open(relative_path("../data/light_cones.json")) as char_file:
    LIGHT_CONES: dict[str, dict[str, str | int | None]] = load(char_file)

sigWeaps: list[str] = []
standWeaps = [
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
for light_cone in LIGHT_CONES:
    if (
        LIGHT_CONES[light_cone]["rarity"] == 5
        and LIGHT_CONES[light_cone]["name"] not in standWeaps
    ):
        sigWeaps += [str(LIGHT_CONES[light_cone]["name"])]
