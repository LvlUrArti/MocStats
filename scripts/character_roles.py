"""Central definitions for character roles and role-variant keys."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Final


@dataclass(frozen=True)
class RoleDef:
    """Metadata for a character role."""

    name: str
    display_name: str
    prefix: str
    special_role: str
    bucket: str


ROLE_DEFS: Final[dict[str, RoleDef]] = {
    "dps": RoleDef("dps", "DPS", "solo", "DPS", "dps"),
    "specialist": RoleDef("specialist", "Specialist", "supp", "S-DPS", "subdps"),
    "amplifier": RoleDef("amplifier", "Amplifier", "amp", "AMP", "amplifier"),
    "sustain": RoleDef("sustain", "Sustain", "sust", "SUST", "healer"),
}

PREFIX_TO_ROLE: Final[dict[str, str]] = {
    role_def.prefix: role_def.name for role_def in ROLE_DEFS.values()
}


def primary_role(roles: list[str]) -> str:
    """Return the primary role (the first role) of a character."""
    return roles[0]


def has_role_variants(roles: list[str]) -> bool:
    """Return whether a character has role-specific variant keys."""
    return len(roles) > 1


def iter_character_keys(
    base_key: str,
    roles: list[str],
) -> list[tuple[str, str | None]]:
    """Return a base key and its role variant keys as (key, role) pairs."""
    keys: list[tuple[str, str | None]] = [(base_key, None)]
    if has_role_variants(roles):
        keys.extend((f"{ROLE_DEFS[role].prefix}-{base_key}", role) for role in roles)
    return keys


def split_key(key: str) -> tuple[str | None, str]:
    """Split a variant key into its prefix and base key."""
    for prefix in PREFIX_TO_ROLE:
        marker = f"{prefix}-"
        if key.startswith(marker):
            return prefix, key[len(marker) :]
    return None, key


def is_prefixed(key: str) -> bool:
    """Return whether a key has a known role prefix."""
    prefix, _base = split_key(key)
    return prefix is not None


def role_for_key(key: str, roles: list[str]) -> str:
    """Return the role represented by a key."""
    prefix, _base = split_key(key)
    if prefix is not None:
        return PREFIX_TO_ROLE[prefix]
    return primary_role(roles)


def special_role_for_key(key: str, roles: list[str]) -> str:
    """Return the output 'special_role' label for a key."""
    prefix, _base = split_key(key)
    if prefix is not None:
        return ROLE_DEFS[PREFIX_TO_ROLE[prefix]].special_role
    return "ALL" if has_role_variants(roles) else ""


def usage_variant_roles(roles: list[str], *, is_sole_dps: bool) -> list[str]:
    """Return the role variants to count for one composition usage.

    A multi-role character counts as its DPS role when it is the only DPS,
    otherwise as its first non-DPS role.
    """
    if not has_role_variants(roles):
        return []
    if is_sole_dps and "dps" in roles:
        return ["dps"]
    return [role for role in roles if role != "dps"][:1]


def composition_bucket(roles: list[str]) -> str:
    """Return the composition bucket for a character's primary role."""
    return ROLE_DEFS[primary_role(roles)].bucket
