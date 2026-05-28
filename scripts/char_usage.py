"""Compile all HSR character data."""

# pyright: reportUnknownVariableType=false, reportMissingTypeStubs=false
from __future__ import annotations

from statistics import mean, stdev
from typing import TYPE_CHECKING
from warnings import filterwarnings

from comp_rates_config import (
    CHARS_INFO,
    CONS_LIMIT,
    F2P_ONLY,
    WHALE_ONLY,
    aa_mode,
    moc_mode,
    one_stage,
    pf_mode,
    sig_weaps,
)
from composition import Stage
from line_profiler import profile
from scipy.stats import skew, trim_mean
from utils.percentile import calculate_percentile

if TYPE_CHECKING:
    from player_phase import PlayerPhase

filterwarnings("ignore", category=RuntimeWarning)
GEAR_APP_THRESHOLD = 0
WEAP_APP_THRESHOLD = 20
MOC_LOWER_LIMIT = 10
MIN_APP_LIMIT = 10
SKEW_LIMIT = 0.8
SKEW_APP_LIMIT = 10
EXCLUDED_LIMIT = 8
DEFAULT_VALUE: float = 0 if pf_mode else 99.99
DEFAULT_ROUND: int = 0 if pf_mode else 2


class RoundApp:
    """Class for storing appearance data for each round."""

    def __init__(self) -> None:
        """Initialize RoundApp class."""
        self.app_flat: int = 0
        self.app_flat_all: int = 0
        self.app: float = 0
        self.round_list = {i: list[int]() for i in range(1, 13)}
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
    """Check if character is a DPS and a sub-DPS character."""
    return len(CHARS_INFO[char].role) > 1


@profile
def appearances(
    users: dict[str, PlayerPhase],
    chambers: list[str],
    *,
    info_char: bool = False,
) -> dict[str, CharApp]:
    """Calculate appearance data for each character."""
    app: dict[str, CharApp] = {}
    user_chars: dict[str, set[str]] = {}

    all_uids = set[str]()

    for char in CHARS_INFO:
        user_chars[char] = set[str]()
        app[char] = CharApp()

        if include_dps(char):
            user_chars["solo-" + char] = set[str]()
            app["solo-" + char] = CharApp()

            user_chars["supp-" + char] = set[str]()
            app["supp-" + char] = CharApp()

    for user in users.values():
        for chamber, user_chamber in user.chambers.items():
            invalid_clear = True
            if (
                aa_mode
                and (
                    (2 < user_chamber.round_num <= 4 and user_chamber.star_num == 2)
                    or (user_chamber.round_num > 4 and user_chamber.star_num == 1)
                )
            ) or (user_chamber.star_num == 3):
                invalid_clear = False

            cur_chamber = chamber.stage
            if str(chamber) not in chambers or invalid_clear:
                continue
            all_uids.add(user.player)
            whale_comp = False
            giga_whale = False
            f2p_comp = True
            sustain_count = 0

            for char in user_chamber.characters:
                char_cons = None
                if user_chamber.char_cons:
                    char_cons = user_chamber.char_cons[char]
                elif char in user.owned:
                    char_cons = user.owned[char].cons

                if (
                    CHARS_INFO[char].availability == "Limited 5*"
                    and char_cons is not None
                    and char_cons > 0
                ):
                    whale_comp = True
                    if char_cons > CONS_LIMIT:
                        giga_whale = True
                if char in user.owned and user.owned[char].weapon in sig_weaps:
                    f2p_comp = False
                if "sustain" in CHARS_INFO[char].role:
                    sustain_count += 1

            if moc_mode:
                side_chamber = Stage(chamber.stage, 2 if chamber.node == 1 else 1)
                if side_chamber not in user.chambers:
                    continue
                user_side_chamber = user.chambers[side_chamber]
                for char in user_side_chamber.characters:
                    char_cons = None
                    if user_side_chamber.char_cons:
                        char_cons = user_side_chamber.char_cons[char]
                    elif char in user.owned:
                        char_cons = user.owned[char].cons

                    if (
                        CHARS_INFO[char].availability == "Limited 5*"
                        and char_cons is not None
                        and char_cons > 0
                    ):
                        whale_comp = True
                        if char_cons > CONS_LIMIT:
                            giga_whale = True
                    if char in user.owned and user.owned[char].weapon in sig_weaps:
                        f2p_comp = False

            # >E2 clears should still be included to calculate
            # characters' average score for all eidolons
            if (
                (WHALE_ONLY and (giga_whale or not whale_comp))
                or (F2P_ONLY and (not f2p_comp or whale_comp))
                or user_chamber.is_hard_mode
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

                    char_con = None
                    if chambers == one_stage:
                        if user_chamber.char_cons:
                            char_con = user_chamber.char_cons[comp_char]
                        elif comp_char in user.owned:
                            char_con = user.owned[comp_char].cons

                    if char_con is not None:
                        app[char].cons_freq[char_con].app_flat += 1
                        if sustain_count <= 1:
                            app[char].cons_freq[char_con].round_list[
                                cur_chamber
                            ].append(user_round)
                        app[char].cons_avg += char_con

                    if giga_whale:
                        continue

                    # to print the amount of players using a character,
                    # for char infographics
                    if chambers == one_stage:
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

                    if chambers != one_stage:
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
            char_item.app = round(char_item.app_flat / total, 2)
            char_item.app_exclude = round(char_item.app_flat_exclude / total, 2)
        else:
            char_item.app = 0.00
        if char_item.app_flat_exclude >= EXCLUDED_LIMIT:
            avg_round: list[float] = []
            std_dev_round: list[float] = []
            q1_round: list[float] = []
            uses_room: dict[int, int] = {}

            for room_num in range(1, 13):
                round_list = char_item.round_list[room_num]
                if room_num >= MOC_LOWER_LIMIT:
                    all_rounds[char][room_num] = {}
                    for i in range(41):
                        all_rounds[char][room_num][i] = 0
                if round_list:
                    if room_num >= MOC_LOWER_LIMIT:
                        for round_num_iter in round_list:
                            all_rounds[char][room_num][round_num_iter] += 1
                    uses_room[room_num] = len(round_list)
                    if len(round_list) > MIN_APP_LIMIT:
                        std_dev_round.append(stdev(round_list))
                        q1_round.append(
                            float(
                                calculate_percentile(round_list, 75 if pf_mode else 25),
                            ),
                        )
                        skewness = skew(round_list, axis=0, bias=True)
                        if abs(skewness) > SKEW_LIMIT:
                            avg_round.append(trim_mean(round_list, 0.25))
                        else:
                            avg_round.append(mean(round_list))
                    else:
                        std_dev_round.append(0)
                        q1_round.append(0)
                        avg_round.append(mean(round_list))

            is_count_cycles = True
            if not uses_room:
                is_count_cycles = False
            elif chambers == one_stage:
                char_item.sample_app_flat = sum(uses_room.values())
            for uses_room_num in uses_room.values():
                if uses_room_num < MIN_APP_LIMIT:
                    is_count_cycles = False
                    break

            if is_count_cycles:
                char_item.round = round(mean(avg_round), DEFAULT_ROUND)
                char_item.std_dev_round = round(mean(std_dev_round), DEFAULT_ROUND)
                char_item.q1_round = round(mean(q1_round), DEFAULT_ROUND)
            else:
                char_item.round = DEFAULT_VALUE
                char_item.q1_round = DEFAULT_VALUE
        else:
            char_item.round = DEFAULT_VALUE
            char_item.q1_round = DEFAULT_VALUE

        char_item.sample = len(user_chars[char])

        if chambers != one_stage:
            continue
        # Calculate constellations
        if char_item.app_flat_all > 0:
            char_item.cons_avg = round(char_item.cons_avg / char_item.app_flat_all, 2)
        for cons_freq in char_item.cons_freq.values():
            if cons_freq.app_flat > 0:
                cons_freq.app = round(
                    cons_freq.app_flat / char_item.app_flat_all * 100,
                    2,
                )
                avg_round = []
                for room_num in range(1, 13):
                    if cons_freq.round_list[room_num]:
                        if cons_freq.app_flat > SKEW_APP_LIMIT:
                            skewness = skew(
                                cons_freq.round_list[room_num],
                                axis=0,
                                bias=True,
                            )
                            if abs(skewness) > SKEW_LIMIT:
                                avg_round.append(
                                    trim_mean(cons_freq.round_list[room_num], 0.25),
                                )
                            else:
                                avg_round.append(mean(cons_freq.round_list[room_num]))
                        else:
                            avg_round.append(mean(cons_freq.round_list[room_num]))
                if avg_round:
                    cons_freq.round = round(mean(avg_round), DEFAULT_ROUND)
                else:
                    cons_freq.round = DEFAULT_VALUE
            else:
                cons_freq.app = 0.00
                cons_freq.round = DEFAULT_VALUE

        app_flat = char_item.owned / 100.0
        # Calculate weapons
        sorted_weapons = sorted(
            char_item.weap_freq.items(),
            key=lambda t: t[1].app_flat,
            reverse=True,
        )
        char_item.weap_freq = dict(sorted_weapons)
        for weap_freq in char_item.weap_freq.values():
            # If a gear appears >15 times, include it
            # Because there might be 1* gears
            # If it's for character infographic, include all gears
            if (
                weap_freq.app_flat > GEAR_APP_THRESHOLD
                or (weap_freq.app_flat / app_flat) > WEAP_APP_THRESHOLD
                or info_char
            ):
                weap_freq.app = round(weap_freq.app_flat / app_flat, 2)
                avg_round = []
                for room_num in range(1, 13):
                    if weap_freq.round_list[room_num]:
                        if weap_freq.app_flat > SKEW_APP_LIMIT:
                            skewness = skew(
                                weap_freq.round_list[room_num],
                                axis=0,
                                bias=True,
                            )
                            if abs(skewness) > SKEW_LIMIT:
                                avg_round.append(
                                    trim_mean(weap_freq.round_list[room_num], 0.25),
                                )
                            else:
                                avg_round.append(mean(weap_freq.round_list[room_num]))
                        else:
                            avg_round.append(mean(weap_freq.round_list[room_num]))
                if avg_round:
                    weap_freq.round = round(mean(avg_round), DEFAULT_ROUND)
                else:
                    weap_freq.round = DEFAULT_VALUE
            else:
                weap_freq.app = 0
                weap_freq.round = DEFAULT_VALUE

        # Remove flex artifacts
        if "Flex" in char_item.arti_freq:
            del char_item.arti_freq["Flex"]
        # Calculate artifacts
        sorted_arti = sorted(
            char_item.arti_freq.items(),
            key=lambda t: t[1].app_flat,
            reverse=True,
        )
        char_item.arti_freq = dict(sorted_arti)
        for arti, arti_freq in char_item.arti_freq.items():
            # If a gear appears >15 times, include it
            # Because there might be 1* gears
            # If it's for character infographic, include all gears
            if (
                arti_freq.app_flat > GEAR_APP_THRESHOLD or info_char
            ) and arti != "Flex":
                arti_freq.app = round(arti_freq.app_flat / app_flat, 2)
                avg_round = []
                for room_num in range(1, 13):
                    if arti_freq.round_list[room_num]:
                        if arti_freq.app_flat > SKEW_APP_LIMIT:
                            skewness = skew(
                                arti_freq.round_list[room_num],
                                axis=0,
                                bias=True,
                            )
                            if abs(skewness) > SKEW_LIMIT:
                                avg_round.append(
                                    trim_mean(arti_freq.round_list[room_num], 0.25),
                                )
                            else:
                                avg_round.append(mean(arti_freq.round_list[room_num]))
                        else:
                            avg_round.append(mean(arti_freq.round_list[room_num]))
                if avg_round:
                    arti_freq.round = round(mean(avg_round), DEFAULT_ROUND)
                else:
                    arti_freq.round = DEFAULT_VALUE
            else:
                arti_freq.app = 0
                arti_freq.round = DEFAULT_VALUE

        # Remove flex artifacts
        if "Flex" in char_item.planar_freq:
            del char_item.planar_freq["Flex"]
        # Calculate artifacts
        sorted_planars = sorted(
            char_item.planar_freq.items(),
            key=lambda t: t[1].app_flat,
            reverse=True,
        )
        char_item.planar_freq = dict(sorted_planars)
        for planar, planar_freq in char_item.planar_freq.items():
            # If a gear appears >15 times, include it
            # Because there might be 1* gears
            # If it's for character infographic, include all gears
            if (
                planar_freq.app_flat > GEAR_APP_THRESHOLD or info_char
            ) and planar != "Flex":
                planar_freq.app = round(planar_freq.app_flat / app_flat, 2)
                avg_round = []
                for room_num in range(1, 13):
                    if planar_freq.round_list[room_num]:
                        if planar_freq.app_flat > 1:
                            skewness = skew(
                                planar_freq.round_list[room_num],
                                axis=0,
                                bias=True,
                            )
                            if abs(skewness) > SKEW_LIMIT:
                                avg_round.append(
                                    trim_mean(planar_freq.round_list[room_num], 0.25),
                                )
                            else:
                                avg_round.append(mean(planar_freq.round_list[room_num]))
                        else:
                            avg_round.append(mean(planar_freq.round_list[room_num]))
                if avg_round:
                    planar_freq.round = round(mean(avg_round), DEFAULT_ROUND)
                else:
                    planar_freq.round = DEFAULT_VALUE
            else:
                planar_freq.app = 0
                planar_freq.round = DEFAULT_VALUE
    return app


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
        self.role = CHARS_INFO[char].role
        self.rarity = CHARS_INFO[char].availability
        self.weapons: dict[str, RoundApp] = {}
        self.weapons_round: dict[str, RoundApp] = {}
        self.artifacts: dict[str, RoundApp] = {}
        self.artifacts_round: dict[str, RoundApp] = {}
        self.planars: dict[str, RoundApp] = {}
        self.cons_usage = {i: dict[str, str]() for i in range(7)}
        self.rank: int


@profile
def usages(
    app: dict[str, CharApp],
    chambers: list[str],
) -> dict[str, CharUsageData]:
    """Calculate usage data for each character."""
    uses: dict[str, CharUsageData] = {}
    rates: list[float] = []

    for char, app_char in app.items():
        uses[char] = CharUsageData(app_char, char)
        rates.append(uses[char].app)

        for i in range(7):
            uses[char].cons_usage[i] = {"app": "-", "own": "-", "usage": "-"}

        if chambers != one_stage:
            continue

        weapons = list(app_char.weap_freq)
        for i in range(len(weapons)):
            uses[char].weapons[weapons[i]] = app_char.weap_freq[weapons[i]]

        artifacts = list(app_char.arti_freq)
        for i in range(len(artifacts)):
            uses[char].artifacts[artifacts[i]] = app_char.arti_freq[artifacts[i]]

        planars = list(app_char.planar_freq)
        for i in range(len(planars)):
            uses[char].planars[planars[i]] = app_char.planar_freq[planars[i]]

        for i in range(7):
            uses[char].cons_usage[i]["app"] = str(app_char.cons_freq[i].app)
            uses[char].cons_usage[i]["round"] = str(app_char.cons_freq[i].round)
    rates.sort(reverse=True)
    for char, use_char in uses.items():
        # if owns[char]["flat"] > 0:
        uses[char].rank = rates.index(use_char.app) + 1
    return uses
