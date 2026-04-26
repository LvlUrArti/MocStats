"""Nohomo config."""

print_chart = False

# stats.py
comp_stats = []
check_char = True
check_char_name = "Yanqing"
check_stats: set[str] = set()

round_stats = {
    "char_lvl",
    "light_cone_lvl",
    "attack_lvl",
    "skill_lvl",
    "ultimate_lvl",
    "talent_lvl",
    "max_hp",
    "atk",
    "dfns",
    "speed",
}

skip_check_skew_stats = {
    "char_lvl",
    "light_cone_lvl",
    "attack_lvl",
    "skill_lvl",
    "ultimate_lvl",
    "talent_lvl",
    "energy_regen",
    "dmg_boost",
}
