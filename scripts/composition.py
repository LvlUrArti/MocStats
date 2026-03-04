"""An object that stores information about a particular composition."""

from __future__ import annotations

from dataclasses import dataclass
from typing import NamedTuple

from comp_rates_config import (
    CHARS_BY_NAME,
    DOT_LIST,
    DOT_SUPPORT_LIST,
    DPS_APPEND_LIST,
    DPS_LIST,
    FUA_LIST,
    HARMONY_LIST,
    HEALER_LIST,
    PRESERVATION_LIST,
    SUB_DPS_APPEND_LIST,
    SUB_DPS_LIST,
    SUPER_BREAK_LIST,
)


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
    is_hard_mode: bool | None

    def __post_init__(self) -> None:
        """Composition constructor."""
        self.player = str(self.player)
        self.char_structs(self.comp_chars, self.comp_chars_cons)

    def char_structs(self, comp_chars: list[str], comp_chars_cons: list[int]) -> None:
        """Character structure creator."""
        """
        Makes a presence dict that maps character names to bools, and
        a list (alphabetically ordered) of the character names.
        """
        self.char_presence: dict[str, bool] = {}
        self.char_cons: dict[str, int] = {}
        fives: list[str] = []
        self.dps: list[str] = []
        self.subdps: list[str] = []
        self.anemo: list[str] = []
        self.healer: list[str] = []
        self.dot: list[str] = []
        self.fua: list[str] = []
        self.super_break: list[str] = []
        len_element = {
            "Ice": 0,
            "Wind": 0,
            "Fire": 0,
            "Imaginary": 0,
            "Quantum": 0,
            "Lightning": 0,
            "Physical": 0,
        }
        if comp_chars_cons:
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
            if CHARS_BY_NAME[character].availability in ["Limited 5*", "5*"]:
                fives.append(character)

            if character in DPS_LIST:
                self.dps.insert(0, character)
            elif character in DPS_APPEND_LIST:
                self.dps.append(character)
            elif character in SUB_DPS_LIST:
                self.subdps.insert(0, character)
            elif character in SUB_DPS_APPEND_LIST:
                self.subdps.append(character)
            elif character in DOT_SUPPORT_LIST:
                self.anemo.insert(0, character)
            elif character in HARMONY_LIST:
                self.anemo.append(character)
            elif character in HEALER_LIST:
                self.healer.insert(0, character)
            elif character in PRESERVATION_LIST:
                self.healer.append(character)

            if character in DOT_LIST:
                self.dot.append(character)
            if character in FUA_LIST:
                self.fua.append(character)
            if character in SUPER_BREAK_LIST:
                self.super_break.append(character)

            if CHARS_BY_NAME[character].element == "Ice":
                len_element["Ice"] += 1
            if CHARS_BY_NAME[character].element == "Wind":
                len_element["Wind"] += 1
            if CHARS_BY_NAME[character].element == "Fire":
                len_element["Fire"] += 1
            if CHARS_BY_NAME[character].element == "Imaginary":
                len_element["Imaginary"] += 1
            if CHARS_BY_NAME[character].element == "Quantum":
                len_element["Quantum"] += 1
            if CHARS_BY_NAME[character].element == "Thunder":
                len_element["Lightning"] += 1
            if CHARS_BY_NAME[character].element == "Physical":
                len_element["Physical"] += 1

        if (not self.dps and not self.subdps) and "Lingsha" in self.healer:
            self.dps.insert(0, "Lingsha")

        self.fivecount = len(fives)
        self.characters = self.dps + self.subdps + self.anemo + self.healer

        if (
            "Acheron" in self.dps or "Kafka" in self.dps
        ) and "Black Swan" in self.subdps:
            self.subdps.remove("Black Swan")
            self.anemo.insert(0, "Black Swan")

        """Name structure creator.
        """
        self.comp_name = "-"
        self.alt_comp_name = "-"
        self.dual_comp_name = "-"

        if self.comp_name == "-":
            if len(self.dot) >= 1:
                if len(self.dot) > 2:
                    self.alt_comp_name = self.characters[0] + " Triple DoT"
                elif len(self.dot) > 1:
                    self.alt_comp_name = self.characters[0] + " Dual DoT"
            elif len(self.fua) > 1:
                self.alt_comp_name = self.characters[0] + " Follow-Up"

            # if self.comp_name == "-":
            archetype = ""
            if len(self.healer) == 0:
                archetype = " No Sustain"
                self.alt_comp_name = self.characters[0] + " No Sustain"
            elif len(self.super_break) >= 1:
                archetype = " Super Break"
            elif len(self.dps) + len(self.subdps) > 1:
                if (
                    len(self.dps) + len(self.subdps) > 2
                    and "Follow-Up" not in self.alt_comp_name
                ):
                    archetype = " Triple Carry"
                else:
                    archetype = " Dual Carry"
                self.dual_comp_name = self.characters[1] + archetype
            elif len(self.healer) > 1:
                archetype = " Dual Sustain"
            elif len(self.anemo) > 0:
                archetype = " Hypercarry"

            if self.dps or self.subdps or self.anemo:
                self.comp_name = self.characters[0] + archetype
            else:
                self.comp_name = "Full Sustain"

    def contains_chars(self, chars: list[str]) -> bool:
        """Return a bool whether this comp contains all the chars in included list."""
        return all(self.char_presence[char] for char in chars)
