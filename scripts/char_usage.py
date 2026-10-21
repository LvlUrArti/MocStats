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
    TRIM_PROPORTION,
    WHALE_ONLY,
    include_dual_sustain,
    moc_mode,
    one_stage,
    pf_mode,
    sig_weaps,
)
from composition import Stage
from numpy import percentile
from scipy.stats import skew, trim_mean

if TYPE_CHECKING:
    from collections.abc import Callable

    from composition import Composition
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
TRIM_PERCENT = TRIM_PROPORTION * 100


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


def robust_round_mean(round_list: list[int], *, can_trim: bool) -> float:
    """Mean of rounds, using the trimmed mean when the data is skewed."""
    if can_trim and abs(skew(round_list)) > SKEW_LIMIT:
        q1, q3 = percentile(round_list, [TRIM_PERCENT, 100 - TRIM_PERCENT])
        if q1 != q3:
            return trim_mean(round_list, TRIM_PROPORTION)
    return mean(round_list)


def check_whale(
    chamber: Composition,
    user: PlayerPhase,
    *,
    whale_comp: bool,
    giga_whale: bool,
    f2p_comp: bool,
) -> tuple[bool, bool, bool]:
    """Detect whale/f2p/giga-whale status from a chamber's composition."""
    for char in chamber.characters:
        char_cons: int | None = None
        if chamber.char_cons:
            char_cons = chamber.char_cons[char]
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
    return whale_comp, giga_whale, f2p_comp


def gear_round(freq: RoundApp) -> float:
    """Average cycle count, trimmed when the data is skewed."""
    avg_round = [
        robust_round_mean(
            freq.round_list[room_num],
            can_trim=freq.app_flat > SKEW_APP_LIMIT,
        )
        for room_num in range(1, 13)
        if freq.round_list[room_num]
    ]
    return round(mean(avg_round), DEFAULT_ROUND) if avg_round else DEFAULT_VALUE


def calc_gear_rates(
    gear_freq: dict[str, RoundApp],
    app_flat: float,
    *,
    info_char: bool,
    extra_include: Callable[[RoundApp], bool] = lambda _f: False,
) -> dict[str, RoundApp]:
    """Sort gear frequency by usage and populate appearance/round rates."""
    gear_freq = {
        gear: freq
        for gear, freq in sorted(
            gear_freq.items(),
            key=lambda t: t[1].app_flat,
            reverse=True,
        )
        if gear != "Flex"
    }
    for freq in gear_freq.values():
        if freq.app_flat > GEAR_APP_THRESHOLD or extra_include(freq) or info_char:
            freq.app = round(freq.app_flat / app_flat, 2)
            freq.round = gear_round(freq)
        else:
            freq.app = 0
            freq.round = DEFAULT_VALUE
    return gear_freq


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
            cur_chamber = chamber.stage
            if str(chamber) not in chambers or not user_chamber.valid_clear:
                continue

            whale_comp, giga_whale, f2p_comp = check_whale(
                user_chamber,
                user,
                whale_comp=False,
                giga_whale=False,
                f2p_comp=True,
            )
            sustain_count = sum(
                1
                for char in user_chamber.characters
                if "sustain" in CHARS_INFO[char].role
            )
            check_sustain_count = sustain_count <= 1 or include_dual_sustain

            if moc_mode:
                side_chamber = Stage(chamber.stage, 2 if chamber.node == 1 else 1)
                if side_chamber not in user.chambers:
                    continue
                user_side_chamber = user.chambers[side_chamber]
                whale_comp, giga_whale, f2p_comp = check_whale(
                    user_side_chamber,
                    user,
                    whale_comp=whale_comp,
                    giga_whale=giga_whale,
                    f2p_comp=f2p_comp,
                )

            all_uids.add(user.player)

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
                        if check_sustain_count:
                            app[char].cons_freq[char_con].round_list[
                                cur_chamber
                            ].append(user_round)
                        app[char].cons_avg += char_con

                    if giga_whale:
                        continue

                    if chambers == one_stage:
                        user_chars[char].add(user.player)

                    app[char].app_flat += 1

                    if (
                        whale_comp == WHALE_ONLY
                        and (not F2P_ONLY or f2p_comp)
                        and check_sustain_count
                    ):
                        app[char].app_flat_exclude += 1
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
                        if not whale_comp and check_sustain_count:
                            app[char].weap_freq[user_char.weapon].round_list[
                                cur_chamber
                            ].append(user_round)

                    if user_char.artifacts != "":
                        if user_char.artifacts not in app[char].arti_freq:
                            app[char].arti_freq[user_char.artifacts] = RoundApp()
                        app[char].arti_freq[user_char.artifacts].app_flat += 1
                        if not whale_comp and check_sustain_count:
                            app[char].arti_freq[user_char.artifacts].round_list[
                                cur_chamber
                            ].append(user_round)

                    if user_char.planars != "":
                        if user_char.planars not in app[char].planar_freq:
                            app[char].planar_freq[user_char.planars] = RoundApp()
                        app[char].planar_freq[user_char.planars].app_flat += 1
                        if not whale_comp and check_sustain_count:
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
                    enough_samples = len(round_list) > MIN_APP_LIMIT
                    std_dev_round.append(stdev(round_list) if enough_samples else 0)
                    avg_round.append(
                        robust_round_mean(round_list, can_trim=enough_samples),
                    )

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
            else:
                char_item.round = DEFAULT_VALUE
        else:
            char_item.round = DEFAULT_VALUE

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
                cons_freq.round = gear_round(cons_freq)
            else:
                cons_freq.app = 0.00
                cons_freq.round = DEFAULT_VALUE

        app_flat = char_item.owned / 100.0
        # Calculate weapons
        char_item.weap_freq = calc_gear_rates(
            char_item.weap_freq,
            app_flat,
            info_char=info_char,
            extra_include=lambda f, app_flat=app_flat: (
                f.app_flat / app_flat > WEAP_APP_THRESHOLD
            ),
        )
        # Calculate artifacts
        char_item.arti_freq = calc_gear_rates(
            char_item.arti_freq,
            app_flat,
            info_char=info_char,
        )
        # Calculate planars
        char_item.planar_freq = calc_gear_rates(
            char_item.planar_freq,
            app_flat,
            info_char=info_char,
        )
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

        uses[char].weapons = dict(app_char.weap_freq)
        uses[char].artifacts = dict(app_char.arti_freq)
        uses[char].planars = dict(app_char.planar_freq)

        for i in range(7):
            uses[char].cons_usage[i]["app"] = str(app_char.cons_freq[i].app)
            uses[char].cons_usage[i]["round"] = str(app_char.cons_freq[i].round)
    rates.sort(reverse=True)
    for char, use_char in uses.items():
        # if owns[char]["flat"] > 0:
        uses[char].rank = rates.index(use_char.app) + 1
    return uses
