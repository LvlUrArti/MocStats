"""Compile all HSR character data."""

from __future__ import annotations

from csv import writer as csvwriter
from statistics import mean, stdev
from typing import TYPE_CHECKING
from warnings import filterwarnings

from comp_rates_config import (
    CONS_LIMIT,
    DPS_APPEND_LIST,
    DPS_LIST,
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
        self.app_flat_all: int = 0
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


def include_dps(char: str) -> bool:
    """Check if character is a DPS character."""
    return char in [*DPS_LIST, *DPS_APPEND_LIST]


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

        if include_dps(char):
            user_chars["solo-" + char] = set[str]()
            app["solo-" + char] = CharApp()

            user_chars["supp-" + char] = set[str]()
            app["supp-" + char] = CharApp()

    for user in users[RECENT_PHASE].values():
        for chamber, user_chamber in user.chambers.items():
            cur_chamber = next(iter(str(chamber).split("-")))
            if chamber not in chambers:
                continue
            all_uids.add(user.player)
            whale_comp = False
            giga_whale = False
            f2p_comp = True
            sustain_count = 0

            for char in user_chamber.characters:
                if (
                    CHARACTERS[char]["availability"] == "Limited 5*"
                    and user_chamber.char_cons
                    and user_chamber.char_cons[char] > 0
                ):
                    whale_comp = True
                    if user_chamber.char_cons[char] > CONS_LIMIT:
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

            # >E2 clears should still be included to calculate
            # characters' average score for all eidolons
            if (WHALE_ONLY and (giga_whale or not whale_comp)) or (
                F2P_ONLY and (not f2p_comp or whale_comp)
            ):
                continue

            for comp_char in user_chamber.characters:
                solo_dps = include_dps(comp_char)
                supp_dps = solo_dps

                if len(user_chamber.dps) > 1:
                    solo_dps = False
                else:
                    supp_dps = False

                loop_char = [comp_char]
                if solo_dps:
                    loop_char.append("solo-" + comp_char)
                if supp_dps:
                    loop_char.append("supp-" + comp_char)

                for char in loop_char:
                    user_round = user_chamber.round_num

                    app[char].app_flat_all += 1
                    if user_chamber.char_cons and chambers == SINGLE_CHAMBER:
                        char_con = user_chamber.char_cons[comp_char]
                        app[char].cons_freq[char_con].app_flat += 1
                        if sustain_count <= 1:
                            app[char].cons_freq[char_con].round_list[
                                cur_chamber
                            ].append(
                                user_round,
                            )
                        app[char].cons_avg += char_con

                    if giga_whale:
                        continue

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

                    if chambers != (SINGLE_CHAMBER):
                        continue
                    if comp_char not in user.owned:
                        continue

                    user_char = user.owned[comp_char]
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
        if char_item.app_flat_all > 0:
            app[char].cons_avg = round(
                char_item.cons_avg / char_item.app_flat_all,
                2,
            )
        for cons, cons_freq in char_item.cons_freq.items():
            if cons_freq.app_flat > 0:
                app[char].cons_freq[cons].app = round(
                    cons_freq.app_flat / char_item.app_flat_all * 100,
                    2,
                )
                avg_round = []
                for room_num in range(1, 13):
                    if cons_freq.round_list[str(room_num)]:
                        if cons_freq.app_flat > SKEW_APP_LIMIT:
                            skewness = skew(
                                cons_freq.round_list[str(room_num)],
                                axis=0,
                                bias=True,
                            )
                            if abs(skewness) > SKEW_LIMIT:
                                avg_round.append(
                                    trim_mean(
                                        cons_freq.round_list[str(room_num)],
                                        0.25,
                                    ),
                                )
                            else:
                                avg_round.append(
                                    mean(
                                        cons_freq.round_list[str(room_num)],
                                    ),
                                )
                        else:
                            avg_round.append(
                                mean(
                                    cons_freq.round_list[str(room_num)],
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
        for weapon, weap_freq in char_item.weap_freq.items():
            # If a gear appears >15 times, include it
            # Because there might be 1* gears
            # If it's for character infographic, include all gears
            if (
                weap_freq.app_flat > GEAR_APP_THRESHOLD
                or info_char
                or (weap_freq.app_flat / app_flat) > WEAP_APP_THRESHOLD
            ):
                app[char].weap_freq[weapon].app = round(
                    weap_freq.app_flat / app_flat,
                    2,
                )
                avg_round = []
                for room_num in range(1, 13):
                    if weap_freq.round_list[str(room_num)]:
                        if weap_freq.app_flat > SKEW_APP_LIMIT:
                            skewness = skew(
                                weap_freq.round_list[str(room_num)],
                                axis=0,
                                bias=True,
                            )
                            if abs(skewness) > SKEW_LIMIT:
                                avg_round.append(
                                    trim_mean(
                                        weap_freq.round_list[str(room_num)],
                                        0.25,
                                    ),
                                )
                            else:
                                avg_round.append(
                                    mean(
                                        weap_freq.round_list[str(room_num)],
                                    ),
                                )
                        else:
                            avg_round.append(
                                mean(
                                    weap_freq.round_list[str(room_num)],
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
        for arti, arti_freq in char_item.arti_freq.items():
            # If a gear appears >15 times, include it
            # Because there might be 1* gears
            # If it's for character infographic, include all gears
            if (
                arti_freq.app_flat > GEAR_APP_THRESHOLD or info_char
            ) and arti != "Flex":
                app[char].arti_freq[arti].app = round(
                    arti_freq.app_flat / app_flat,
                    2,
                )
                avg_round = []
                for room_num in range(1, 13):
                    if arti_freq.round_list[str(room_num)]:
                        if arti_freq.app_flat > SKEW_APP_LIMIT:
                            skewness = skew(
                                arti_freq.round_list[str(room_num)],
                                axis=0,
                                bias=True,
                            )
                            if abs(skewness) > SKEW_LIMIT:
                                avg_round.append(
                                    trim_mean(
                                        arti_freq.round_list[str(room_num)],
                                        0.25,
                                    ),
                                )
                            else:
                                avg_round.append(
                                    mean(
                                        arti_freq.round_list[str(room_num)],
                                    ),
                                )
                        else:
                            avg_round.append(
                                mean(
                                    arti_freq.round_list[str(room_num)],
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
        for planar, planar_freq in char_item.planar_freq.items():
            # If a gear appears >15 times, include it
            # Because there might be 1* gears
            # If it's for character infographic, include all gears
            if (
                planar_freq.app_flat > GEAR_APP_THRESHOLD or info_char
            ) and planar != "Flex":
                app[char].planar_freq[planar].app = round(
                    planar_freq.app_flat / app_flat,
                    2,
                )
                avg_round = []
                for room_num in range(1, 13):
                    if planar_freq.round_list[str(room_num)]:
                        if planar_freq.app_flat > 1:
                            skewness = skew(
                                planar_freq.round_list[str(room_num)],
                                axis=0,
                                bias=True,
                            )
                            if abs(skewness) > SKEW_LIMIT:
                                avg_round.append(
                                    trim_mean(
                                        planar_freq.round_list[str(room_num)],
                                        0.25,
                                    ),
                                )
                            else:
                                avg_round.append(
                                    mean(
                                        planar_freq.round_list[str(room_num)],
                                    ),
                                )
                        else:
                            avg_round.append(
                                mean(
                                    planar_freq.round_list[str(room_num)],
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
                for room_num, all_round_num in all_round_char.items():
                    for round_num_iter in all_round_num:
                        csv_writer.writerow(
                            [
                                "2/21/2024",
                                char,
                                room_num,
                                round_num_iter,
                                all_round_num[round_num_iter],
                            ],
                        )
    return {4: app}


class CharUsageData(CharApp):
    """Class for storing usage data for each character."""

    def __init__(self, char_app: CharApp, char: str) -> None:
        """Initialize CharUsageData class."""
        if "solo-" in char:
            char = char.replace("solo-", "")
        if "supp-" in char:
            char = char.replace("supp-", "")
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
        for char, app_char in app[4].items():
            uses[star_num][char] = CharUsageData(app_char, char)
            rates.append(uses[star_num][char].app)

            stage = "all" if chambers == SINGLE_CHAMBER else chambers[0]

            if char in past_usage[stage][str(star_num)]:
                uses[star_num][char].diff = str(
                    round(
                        app_char.app - past_usage[stage][str(star_num)][char]["app"],
                        2,
                    ),
                )

            if char in past_rounds[stage][str(star_num)]:
                uses[star_num][char].diff_rounds = str(
                    round(
                        app_char.round
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

            weapons = list(app_char.weap_freq)
            for i in range(len(weapons)):
                uses[star_num][char].weapons[weapons[i]] = app_char.weap_freq[
                    weapons[i]
                ]

            artifacts = list(app_char.arti_freq)
            for i in range(len(artifacts)):
                uses[star_num][char].artifacts[artifacts[i]] = app_char.arti_freq[
                    artifacts[i]
                ]

            planars = list(app_char.planar_freq)
            for i in range(len(planars)):
                uses[star_num][char].planars[planars[i]] = app_char.planar_freq[
                    planars[i]
                ]

            for i in range(7):
                uses[star_num][char].cons_usage[i]["app"] = str(
                    app_char.cons_freq[i].app,
                )
                uses[star_num][char].cons_usage[i]["round"] = str(
                    app_char.cons_freq[i].round,
                )
        rates.sort(reverse=True)
        for char in uses[star_num]:
            # if owns[star_num][char]["flat"] > 0:
            uses[star_num][char].rank = rates.index(uses[star_num][char].app) + 1
    return uses
