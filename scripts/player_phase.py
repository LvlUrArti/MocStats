"""An object that stores information about a player on a phase."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from composition import Composition, Stage

# Set class constants in initialization
# Load the list of characters from their file
with open("../data/relic_affixes.json") as relic_file:
    articombinations: dict[str, list[str]] = json.load(relic_file)


@dataclass
class OwnedChars:
    """An object that stores information about owned characters."""

    level: int
    cons: int
    weapon: str
    element: str
    artifacts: str
    planars: str


class PlayerPhase:
    """An object that stores information about a player on a phase."""

    """Has:
    player: a string for this player.
    phase: a string for the phase.
    chambers: a string->composition dict for the comps they used.
    owned: a string->dict (character) dict for the characters they owned:
        None if they don't own the character.
    """

    def __init__(self, player: str) -> None:
        """Composition constructor."""
        """
        Takes in:
        A player, as a string
        A phase, as a string
        """
        self.player = player
        self.chambers: dict[Stage, Composition] = {}
        self.owned: dict[str, OwnedChars] = {}

    def add_character(
        self,
        name: str,
        char: OwnedChars,
    ) -> None:
        """Add in a character to the owned characters dict."""
        for arti_item in articombinations.values():
            articom: list[str] = []
            comarti: list[str] = []
            for artiset in arti_item:
                articom.append(artiset + ", ")
                comarti.append(", " + artiset)
            replaced = False
            arti_name = arti_item[0]
            for arti_replace in comarti:
                if arti_replace in char.artifacts:
                    char.artifacts = char.artifacts.replace(
                        arti_replace,
                        ", " + arti_name,
                    )
                    replaced = True
            if replaced:
                arti_name = arti_item[1]
            for arti_replace in articom:
                if arti_replace in char.artifacts:
                    char.artifacts = char.artifacts.replace(arti_replace, "")
                    char.artifacts = char.artifacts + ", " + arti_name

        if "Flex, " in char.artifacts:
            char.artifacts = char.artifacts.replace("Flex, ", "") + ", Flex"
        self.owned[name] = char

    def add_comp(self, composition: Composition) -> None:
        """Add a composition to the chambers dict."""
        if composition.player != self.player:
            return
        if composition.room in self.chambers:
            return
        self.chambers[composition.room] = composition

    def chars_owned(self, characters: list[str]) -> bool:
        """Take in an iter of char names. True if the player owned them all."""
        return all(self.owned[char] for char in characters)

    def chars_used(self, characters: list[str]) -> bool:
        """Take in an iter of char names. True if the player used them all."""
        if not self.chars_owned(characters):
            return False
        return all(self.char_used(char) for char in characters)

    def no_chars_owned(self, characters: list[str]) -> bool:
        """Take in an iter of character names. True if the player owns none of them."""
        return all(not self.owned[char] for char in characters)

    def no_chars_used(self, characters: list[str]) -> bool:
        """Take in an iter of character names. True if the player used none of them."""
        return all(not self.char_used(char) for char in characters)

    def char_used(self, character: str) -> bool:
        """Take in a character name. True if the player used them."""
        if not self.owned[character]:
            return False
        for chamber in self.chambers.values():
            if chamber.char_presence[character]:
                return True
        return False
