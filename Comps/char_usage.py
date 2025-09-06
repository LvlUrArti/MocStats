"""Compile all HSR character data."""

from __future__ import annotations

from csv import writer as csvwriter
from statistics import mean, stdev
from typing import TYPE_CHECKING
from warnings import filterwarnings

from comp_rates_config import (
    CONS_LIMIT,
    F2P_ONLY,
    RECENT_PHASE,
    WHALE_ONLY,
    load,
    pf_mode,
    sig_weaps,
)
from line_profiler import profile
from percentile import calculate_percentile
from scipy.stats import (  # pyright: ignore[reportMissingTypeStubs]
    skew,  # pyright: ignore[reportUnknownVariableType]
    trim_mean,  # pyright: ignore[reportUnknownVariableType]
)

if TYPE_CHECKING:
    from player_phase import PlayerPhase

filterwarnings("ignore", category=RuntimeWarning)
ROOMS = (
    ["1-1", "1-2", "2-1", "2-2", "3-1", "3-2", "4-1", "4-2"]
    if pf_mode
    else [
        "1-1",
        "1-2",
        "2-1",
        "2-2",
        "3-1",
        "3-2",
        "4-1",
        "4-2",
        "5-1",
        "5-2",
        "6-1",
        "6-2",
        "7-1",
        "7-2",
        "8-1",
        "8-2",
        "9-1",
        "9-2",
        "10-1",
        "10-2",
        "11-1",
        "11-2",
        "12-1",
        "12-2",
    ]
)
GEAR_APP_THRESHOLD = 0
WEAP_APP_THRESHOLD = 20
MOC_LOWER_LIMIT = 10
SKEW_LIMIT = 0.8
SKEW_APP_LIMIT = 10
EXCLUDED_LIMIT = 8
ALL_STAR_NUM = 4
DEFAULT_VALUE: float = 0 if pf_mode else 99.99
DEFAULT_ROUND: int = 0 if pf_mode else 2
SINGLE_CHAMBER: list[str] = ["4-1", "4-2"] if pf_mode else ["12-1", "12-2"]
with open("../data/characters.json") as char_file:
    CHARACTERS: dict[str, dict[str, str | int | None]] = load(char_file)


class RoundApp:
    """Class for storing appearance data for each round."""

    def __init__(self) -> None:
        """Initialize RoundApp class."""
        self.app_flat: int = 0
        self.app: float = 0
        self.round_list = {str(i): list[int]() for i in range(1, 13)}
        self.round: float = 0


class CharApp(RoundApp):
    """Class for storing appearance data for each character."""

    def __init__(self) -> None:
        """Initialize CharApp class."""
        super().__init__()
        self.app_flat_exclude: int = 0
        self.app_exclude: float = 0
        self.owned: int = 0
        self.std_dev_round: float = 0
        self.q1_round: float = 0
        self.weap_freq: dict[str, RoundApp] = {}
        self.arti_freq: dict[str, RoundApp] = {}
        self.planar_freq: dict[str, RoundApp] = {}
        self.cons_avg: float = 0
        self.sample: int = 0
        self.sample_app_flat: int = 0
        self.cons_freq = {i: RoundApp() for i in range(7)}


@profile
def appearances(
    users: dict[str, dict[str, PlayerPhase]],
    chambers: list[str] = ROOMS,
    info_char: bool = False,
) -> dict[int, dict[str, CharApp]]:
    """Calculate appearance data for each character."""
    app: dict[str, CharApp] = {}
    user_chars: dict[str, set[str]] = {}

    all_uids = set[str]()

    for char in CHARACTERS:
        user_chars[char] = set[str]()
        app[char] = CharApp()

    for user in users[RECENT_PHASE].values():
        for chamber in user.chambers:
            cur_chamber = next(iter(str(chamber).split("-")))
            if chamber not in chambers:
                continue
            all_uids.add(user.player)
            whale_comp = False
            giga_whale = False
            f2p_comp = True
            sustain_count = 0

            for char in user.chambers[chamber].characters:
                if (
                    CHARACTERS[char]["availability"] == "Limited 5*"
                    and user.chambers[chamber].char_cons
                    and user.chambers[chamber].char_cons[char] > 0
                ):
                    whale_comp = True
                    if user.chambers[chamber].char_cons[char] > CONS_LIMIT:
                        giga_whale = True
                if char in user.owned and user.owned[char].weapon in sig_weaps:
                    f2p_comp = False
                if CHARACTERS[char]["role"] == "Sustain":
                    sustain_count += 1

            if not (pf_mode):
                side_chamber = chamber[:-1] + ("2" if chamber[-1] == "1" else "1")
                for char in user.chambers[side_chamber].characters:
                    if (
                        CHARACTERS[char]["availability"] == "Limited 5*"
                        and user.chambers[side_chamber].char_cons
                        and user.chambers[side_chamber].char_cons[char] > 0
                    ):
                        whale_comp = True
                        if user.chambers[side_chamber].char_cons[char] > CONS_LIMIT:
                            giga_whale = True
                    if char in user.owned and user.owned[char].weapon in sig_weaps:
                        f2p_comp = False

            if (WHALE_ONLY and (giga_whale or not whale_comp)) or (
                F2P_ONLY and (not f2p_comp or whale_comp)
            ):
                continue

            for char in user.chambers[chamber].characters:
                user_round = user.chambers[chamber].round_num
                # to print the amount of players using a character,
                # for char infographics
                if chambers == SINGLE_CHAMBER:
                    user_chars[char].add(user.player)

                app[char].app_flat += 1
                if whale_comp == WHALE_ONLY and (not F2P_ONLY or f2p_comp):
                    app[char].app_flat_exclude += 1

                if (
                    whale_comp == WHALE_ONLY
                    and (not F2P_ONLY or f2p_comp)
                    and (sustain_count <= 1)
                ):
                    app[char].round_list[cur_chamber].append(user_round)

                if user.chambers[chamber].char_cons and chambers == SINGLE_CHAMBER:
                    char_con = user.chambers[chamber].char_cons[char]
                    app[char].cons_freq[char_con].app_flat += 1
                    if sustain_count <= 1:
                        app[char].cons_freq[char_con].round_list[cur_chamber].append(
                            user_round,
                        )
                    app[char].cons_avg += char_con
                if chambers != (SINGLE_CHAMBER):
                    continue
                if char not in user.owned:
                    continue

                user_char = user.owned[char]
                app[char].owned += 1

                if user_char.weapon != "":
                    if user_char.weapon not in app[char].weap_freq:
                        app[char].weap_freq[user_char.weapon] = RoundApp()
                    app[char].weap_freq[user_char.weapon].app_flat += 1
                    if not whale_comp and (sustain_count <= 1):
                        app[char].weap_freq[user_char.weapon].round_list[
                            cur_chamber
                        ].append(user_round)

                if user_char.artifacts != "":
                    if user_char.artifacts not in app[char].arti_freq:
                        app[char].arti_freq[user_char.artifacts] = RoundApp()
                    app[char].arti_freq[user_char.artifacts].app_flat += 1
                    if not whale_comp and (sustain_count <= 1):
                        app[char].arti_freq[user_char.artifacts].round_list[
                            cur_chamber
                        ].append(user_round)

                if user_char.planars != "":
                    if user_char.planars not in app[char].planar_freq:
                        app[char].planar_freq[user_char.planars] = RoundApp()
                    app[char].planar_freq[user_char.planars].app_flat += 1
                    if not whale_comp and (sustain_count <= 1):
                        app[char].planar_freq[user_char.planars].round_list[
                            cur_chamber
                        ].append(user_round)

    total = len(all_uids) / 100.0
    all_rounds: dict[str, dict[int, dict[int, int]]] = {}
    for char, char_item in app.items():
        all_rounds[char] = {}
        if total > 0:
            app[char].app = round(char_item.app_flat / total, 2)
            app[char].app_exclude = round(char_item.app_flat_exclude / total, 2)
        else:
            app[char].app = 0.00
        if char_item.app_flat_exclude >= EXCLUDED_LIMIT:
            avg_round: list[float] = []
            std_dev_round: list[float] = []
            q1_round: list[float] = []
            uses_room: dict[int, int] = {}

            for room_num in range(1, 13):
                if room_num >= MOC_LOWER_LIMIT:
                    all_rounds[char][room_num] = {}
                    for i in range(41):
                        all_rounds[char][room_num][i] = 0
                if char_item.round_list[str(room_num)]:
                    if room_num >= MOC_LOWER_LIMIT:
                        for round_num_iter in char_item.round_list[str(room_num)]:
                            all_rounds[char][room_num][round_num_iter] += 1
                    uses_room[room_num] = len(char_item.round_list[str(room_num)])
                    if len(char_item.round_list[str(room_num)]) > MOC_LOWER_LIMIT:
                        std_dev_round.append(stdev(char_item.round_list[str(room_num)]))
                        q1_round.append(
                            calculate_percentile(
                                char_item.round_list[str(room_num)],
                                75 if pf_mode else 25,
                            ),
                        )
                        skewness = skew(
                            char_item.round_list[str(room_num)],
                            axis=0,
                            bias=True,
                        )
                        if abs(skewness) > SKEW_LIMIT:
                            avg_round.append(
                                trim_mean(
                                    char_item.round_list[str(room_num)],
                                    0.25,
                                ),
                            )
                        else:
                            avg_round.append(mean(char_item.round_list[str(room_num)]))
                    else:
                        std_dev_round.append(0)
                        q1_round.append(0)
                        avg_round.append(mean(char_item.round_list[str(room_num)]))

            is_count_cycles = True
            if not uses_room:
                is_count_cycles = False
            elif chambers == SINGLE_CHAMBER:
                app[char].sample_app_flat = uses_room[4 if pf_mode else 12]
                if len(uses_room) != len(chambers) / 2:
                    is_count_cycles = False
            for uses_room_num in uses_room.values():
                if uses_room_num < MOC_LOWER_LIMIT:
                    is_count_cycles = False
                    break

            # if avg_round:
            if is_count_cycles:
                app[char].round = round(mean(avg_round), DEFAULT_ROUND)
                app[char].std_dev_round = round(mean(std_dev_round), DEFAULT_ROUND)
                app[char].q1_round = round(mean(q1_round), DEFAULT_ROUND)
            else:
                app[char].round = DEFAULT_VALUE
                app[char].q1_round = DEFAULT_VALUE
        else:
            app[char].round = DEFAULT_VALUE
            app[char].q1_round = DEFAULT_VALUE

        app[char].sample = len(user_chars[char])

        if chambers != SINGLE_CHAMBER:
            continue
        # Calculate constellations
        if char_item.app_flat > 0:
            app[char].cons_avg = round(
                char_item.cons_avg / char_item.app_flat,
                2,
            )
        for cons in char_item.cons_freq:
            if char_item.cons_freq[cons].app_flat > 0:
                app[char].cons_freq[cons].app = round(
                    char_item.cons_freq[cons].app_flat / char_item.app_flat * 100,
                    2,
                )
                avg_round = []
                for room_num in range(1, 13):
                    if char_item.cons_freq[cons].round_list[str(room_num)]:
                        if char_item.cons_freq[cons].app_flat > SKEW_APP_LIMIT:
                            skewness = skew(
                                char_item.cons_freq[cons].round_list[str(room_num)],
                                axis=0,
                                bias=True,
                            )
                            if abs(skewness) > SKEW_LIMIT:
                                avg_round.append(
                                    trim_mean(
                                        char_item.cons_freq[cons].round_list[
                                            str(room_num)
                                        ],
                                        0.25,
                                    ),
                                )
                            else:
                                avg_round.append(
                                    mean(
                                        char_item.cons_freq[cons].round_list[
                                            str(room_num)
                                        ],
                                    ),
                                )
                        else:
                            avg_round.append(
                                mean(
                                    char_item.cons_freq[cons].round_list[str(room_num)],
                                ),
                            )
                if avg_round:
                    app[char].cons_freq[cons].round = round(
                        mean(avg_round),
                        DEFAULT_ROUND,
                    )
                else:
                    app[char].cons_freq[cons].round = DEFAULT_VALUE
            else:
                app[char].cons_freq[cons].app = 0.00
                app[char].cons_freq[cons].round = DEFAULT_VALUE

        app_flat = char_item.owned / 100.0
        # Calculate weapons
        sorted_weapons = sorted(
            char_item.weap_freq.items(),
            key=lambda t: t[1].app_flat,
            reverse=True,
        )
        app[char].weap_freq = dict(sorted_weapons)
        for weapon in char_item.weap_freq:
            # If a gear appears >15 times, include it
            # Because there might be 1* gears
            # If it's for character infographic, include all gears
            if (
                char_item.weap_freq[weapon].app_flat > GEAR_APP_THRESHOLD
                or info_char
                or (char_item.weap_freq[weapon].app_flat / app_flat)
                > WEAP_APP_THRESHOLD
            ):
                app[char].weap_freq[weapon].app = round(
                    char_item.weap_freq[weapon].app_flat / app_flat,
                    2,
                )
                avg_round = []
                for room_num in range(1, 13):
                    if char_item.weap_freq[weapon].round_list[str(room_num)]:
                        if char_item.weap_freq[weapon].app_flat > SKEW_APP_LIMIT:
                            skewness = skew(
                                char_item.weap_freq[weapon].round_list[str(room_num)],
                                axis=0,
                                bias=True,
                            )
                            if abs(skewness) > SKEW_LIMIT:
                                avg_round.append(
                                    trim_mean(
                                        char_item.weap_freq[weapon].round_list[
                                            str(room_num)
                                        ],
                                        0.25,
                                    ),
                                )
                            else:
                                avg_round.append(
                                    mean(
                                        char_item.weap_freq[weapon].round_list[
                                            str(room_num)
                                        ],
                                    ),
                                )
                        else:
                            avg_round.append(
                                mean(
                                    char_item.weap_freq[weapon].round_list[
                                        str(room_num)
                                    ],
                                ),
                            )
                if avg_round:
                    app[char].weap_freq[weapon].round = round(
                        mean(avg_round),
                        DEFAULT_ROUND,
                    )
                else:
                    app[char].weap_freq[weapon].round = DEFAULT_VALUE
            else:
                app[char].weap_freq[weapon].app = 0
                app[char].weap_freq[weapon].round = DEFAULT_VALUE

        # Remove flex artifacts
        if "Flex" in char_item.arti_freq:
            del app[char].arti_freq["Flex"]
        # Calculate artifacts
        sorted_arti = sorted(
            char_item.arti_freq.items(),
            key=lambda t: t[1].app_flat,
            reverse=True,
        )
        app[char].arti_freq = dict(sorted_arti)
        for arti in char_item.arti_freq:
            # If a gear appears >15 times, include it
            # Because there might be 1* gears
            # If it's for character infographic, include all gears
            if (
                char_item.arti_freq[arti].app_flat > GEAR_APP_THRESHOLD or info_char
            ) and arti != "Flex":
                app[char].arti_freq[arti].app = round(
                    char_item.arti_freq[arti].app_flat / app_flat,
                    2,
                )
                avg_round = []
                for room_num in range(1, 13):
                    if char_item.arti_freq[arti].round_list[str(room_num)]:
                        if char_item.arti_freq[arti].app_flat > SKEW_APP_LIMIT:
                            skewness = skew(
                                char_item.arti_freq[arti].round_list[str(room_num)],
                                axis=0,
                                bias=True,
                            )
                            if abs(skewness) > SKEW_LIMIT:
                                avg_round.append(
                                    trim_mean(
                                        char_item.arti_freq[arti].round_list[
                                            str(room_num)
                                        ],
                                        0.25,
                                    ),
                                )
                            else:
                                avg_round.append(
                                    mean(
                                        char_item.arti_freq[arti].round_list[
                                            str(room_num)
                                        ],
                                    ),
                                )
                        else:
                            avg_round.append(
                                mean(
                                    char_item.arti_freq[arti].round_list[str(room_num)],
                                ),
                            )
                if avg_round:
                    app[char].arti_freq[arti].round = round(
                        mean(avg_round),
                        DEFAULT_ROUND,
                    )
                else:
                    app[char].arti_freq[arti].round = DEFAULT_VALUE
            else:
                app[char].arti_freq[arti].app = 0
                app[char].arti_freq[arti].round = DEFAULT_VALUE

        # Remove flex artifacts
        if "Flex" in char_item.planar_freq:
            del app[char].planar_freq["Flex"]
        # Calculate artifacts
        sorted_planars = sorted(
            char_item.planar_freq.items(),
            key=lambda t: t[1].app_flat,
            reverse=True,
        )
        app[char].planar_freq = dict(sorted_planars)
        for planar in char_item.planar_freq:
            # If a gear appears >15 times, include it
            # Because there might be 1* gears
            # If it's for character infographic, include all gears
            if (
                char_item.planar_freq[planar].app_flat > GEAR_APP_THRESHOLD or info_char
            ) and planar != "Flex":
                app[char].planar_freq[planar].app = round(
                    char_item.planar_freq[planar].app_flat / app_flat,
                    2,
                )
                avg_round = []
                for room_num in range(1, 13):
                    if char_item.planar_freq[planar].round_list[str(room_num)]:
                        if char_item.planar_freq[planar].app_flat > 1:
                            skewness = skew(
                                char_item.planar_freq[planar].round_list[str(room_num)],
                                axis=0,
                                bias=True,
                            )
                            if abs(skewness) > SKEW_LIMIT:
                                avg_round.append(
                                    trim_mean(
                                        char_item.planar_freq[planar].round_list[
                                            str(room_num)
                                        ],
                                        0.25,
                                    ),
                                )
                            else:
                                avg_round.append(
                                    mean(
                                        char_item.planar_freq[planar].round_list[
                                            str(room_num)
                                        ],
                                    ),
                                )
                        else:
                            avg_round.append(
                                mean(
                                    char_item.planar_freq[planar].round_list[
                                        str(room_num)
                                    ],
                                ),
                            )
                if avg_round:
                    app[char].planar_freq[planar].round = round(
                        mean(avg_round),
                        DEFAULT_ROUND,
                    )
                else:
                    app[char].planar_freq[planar].round = DEFAULT_VALUE
            else:
                app[char].planar_freq[planar].app = 0
                app[char].planar_freq[planar].round = DEFAULT_VALUE
    if chambers == ["12-1", "12-2"]:
        with open("../char_results/all_rounds.csv", "w", newline="") as f:
            csv_writer = csvwriter(f)
            for char, all_round_char in all_rounds.items():
                for room_num in all_round_char:
                    for round_num_iter in all_round_char[room_num]:
                        csv_writer.writerow(
                            [
                                "2/21/2024",
                                char,
                                room_num,
                                round_num_iter,
                                all_round_char[room_num][round_num_iter],
                            ],
                        )
    return {4: app}


class CharUsageData(CharApp):
    """Class for storing usage data for each character."""

    def __init__(self, char_app: CharApp, char: str) -> None:
        """Initialize CharUsageData class."""
        super().__init__()
        self.__dict__.update(char_app.__dict__)
        self.usage = 0
        self.diff = "-"
        self.diff_rounds = "-"
        self.role = str(CHARACTERS[char]["role"])
        self.rarity = str(CHARACTERS[char]["availability"])
        self.weapons: dict[str, RoundApp] = {}
        self.weapons_round: dict[str, RoundApp] = {}
        self.artifacts: dict[str, RoundApp] = {}
        self.artifacts_round: dict[str, RoundApp] = {}
        self.planars: dict[str, RoundApp] = {}
        self.cons_usage = {i: dict[str, str]() for i in range(7)}
        self.rank: int


@profile
def usages(
    app: dict[int, dict[str, CharApp]],
    past_phase: str,
    chambers: list[str] = ROOMS,
) -> dict[int, dict[str, CharUsageData]]:
    """Calculate usage data for each character."""
    uses: dict[int, dict[str, CharUsageData]] = {}
    past_usage: dict[str, dict[str, dict[str, dict[str, float]]]] = {}
    past_rounds: dict[str, dict[str, dict[str, dict[str, float]]]] = {}

    try:
        with open("../char_results/" + past_phase + "/appearance.json") as stats:
            past_usage = load(stats)
        with open("../char_results/" + past_phase + "/rounds.json") as stats:
            past_rounds = load(stats)
    except Exception:
        print("No past usage data")

    for star_num in app:
        uses[star_num] = {}
        rates: list[float] = []
        for char in app[4]:
            uses[star_num][char] = CharUsageData(app[4][char], char)
            rates.append(uses[star_num][char].app)

            stage = "all" if chambers == SINGLE_CHAMBER else chambers[0]

            if char in past_usage[stage][str(star_num)]:
                uses[star_num][char].diff = str(
                    round(
                        app[4][char].app
                        - past_usage[stage][str(star_num)][char]["app"],
                        2,
                    ),
                )

            if char in past_rounds[stage][str(star_num)]:
                uses[star_num][char].diff_rounds = str(
                    round(
                        app[4][char].round
                        - past_rounds[stage][str(star_num)][char]["round"],
                        2,
                    ),
                )

            for i in range(7):
                uses[star_num][char].cons_usage[i] = {
                    "app": "-",
                    "own": "-",
                    "usage": "-",
                }

            if chambers != SINGLE_CHAMBER or star_num != ALL_STAR_NUM:
                continue

            weapons = list(app[4][char].weap_freq)
            for i in range(len(weapons)):
                uses[star_num][char].weapons[weapons[i]] = app[4][char].weap_freq[
                    weapons[i]
                ]

            artifacts = list(app[4][char].arti_freq)
            for i in range(len(artifacts)):
                uses[star_num][char].artifacts[artifacts[i]] = app[4][char].arti_freq[
                    artifacts[i]
                ]

            planars = list(app[4][char].planar_freq)
            for i in range(len(planars)):
                uses[star_num][char].planars[planars[i]] = app[4][char].planar_freq[
                    planars[i]
                ]

            for i in range(7):
                uses[star_num][char].cons_usage[i]["app"] = str(
                    app[4][char].cons_freq[i].app,
                )
                uses[star_num][char].cons_usage[i]["round"] = str(
                    app[4][char].cons_freq[i].round,
                )
        rates.sort(reverse=True)
        for char in uses[star_num]:
            # if owns[star_num][char]["flat"] > 0:
            uses[star_num][char].rank = rates.index(uses[star_num][char].app) + 1
    return uses
