"""An object that stores information about a particular composition."""

from __future__ import annotations

from dataclasses import dataclass
from typing import NamedTuple

from comp_rates_config import CHARS_INFO, aa_mode


class Stage(NamedTuple):
    """A stage in a phase."""

    stage: int
    node: int

    def __str__(self) -> str:
        """Stage string representation."""
        return f"{self.stage}-{self.node}"

    @classmethod
    def from_string(cls, stage_str: str) -> Stage:
        """Stage constructor."""
        room, node = stage_str.split("-")
        return cls(int(room), int(node))


@dataclass
class Composition:
    """An object that stores information about a particular composition."""

    """An object that stores information about a particular composition. Has:
    player: a string for the player who used this comp.
    room: a string in the form XX-X-X for the room this comp was used in.
    char_presence: a string --> boolean dict for chars in this comp.
    characters: a list of strings for the names of the chars in this comp.
    elements: a string --> int dict for the num of chars for each element.
    resonance: a string --> boolean dict for which resonances are active.

    Additional methods are:
    resonance_string: returns the resonances active as a string.
    on_res_chars: returns the list of characters activating the resonance.
    char_elemeent_list: returns the list of character's elements.
    """

    player: str  # UID as string
    room: Stage
    round_num: int
    star_num: int
    buff: str | None
    comp_chars: list[str]
    comp_chars_cons: list[int]
    is_hard_mode: bool | None  # Anomaly Arbitration plight mode

    def __post_init__(self) -> None:
        """Composition constructor."""
        self.player = str(self.player)

        self.valid_clear = False
        if (self.star_num == 3) or (
            aa_mode
            and (
                (2 < self.round_num <= 4 and self.star_num == 2)
                or (self.round_num > 4 and self.star_num == 1)
            )
        ):
            self.valid_clear = True

        self.char_structs(self.comp_chars, self.comp_chars_cons)

    def char_structs(self, comp_chars: list[str], comp_chars_cons: list[int]) -> None:
        """Character structure creator."""
        """
        Makes a presence dict that maps character names to bools, and
        a list (alphabetically ordered) of the character names.
        """
        self.char_presence: dict[str, bool] = {}
        self.char_cons: dict[str, int] | None = None
        fives: list[str] = []
        self.dps: list[str] = []
        self.subdps: list[str] = []
        self.amplifier: list[str] = []
        self.healer: list[str] = []
        if comp_chars_cons:
            self.char_cons = {}
            for char_iter in range(len(comp_chars)):
                self.char_cons[comp_chars[char_iter]] = comp_chars_cons[char_iter]
        comp_chars.sort()
        for iter_character in comp_chars:
            character = iter_character
            if character == "Topaz and Numby":
                character = "Topaz & Numby"
            if character == "March 7th":
                character = "Ice March 7th"
            self.char_presence[character] = True
            if CHARS_INFO[character].availability in ["Limited 5*", "5*"]:
                fives.append(character)

            if CHARS_INFO[character].role == ["dps"]:
                self.dps.insert(0, character)
            elif CHARS_INFO[character].role == ["dps", "specialist"]:
                self.dps.append(character)
            elif CHARS_INFO[character].role[0] == "specialist":
                self.subdps.append(character)
            elif CHARS_INFO[character].role[0] == "amplifier":
                self.amplifier.append(character)
            elif CHARS_INFO[character].role[0] == "sustain":
                self.healer.append(character)

        if not self.dps and not self.subdps:
            for char in ("Lingsha", "Welt"):
                for role in ("healer", "amplifier"):
                    if char in getattr(self, role):
                        getattr(self, role).remove(char)
                        self.dps.append(char)

        if not self.healer and "Welt" in self.amplifier:
            self.amplifier.remove("Welt")
            self.healer.append("Welt")

        self.fivecount = len(fives)
        self.characters = self.dps + self.subdps + self.amplifier + self.healer

        if (
            "Acheron" in self.dps or "Kafka" in self.dps
        ) and "Black Swan" in self.subdps:
            self.subdps.remove("Black Swan")
            self.amplifier.insert(0, "Black Swan")

        archetype = " Hypercarry"
        self.comp_name = self.characters[0] + archetype

    def contains_chars(self, chars: list[str]) -> bool:
        """Return a bool whether this comp contains all the chars in included list."""
        return all(self.char_presence[char] for char in chars)
