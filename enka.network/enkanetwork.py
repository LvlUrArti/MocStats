"""Collects character data from Enka Network."""

import _thread
import asyncio
import traceback
from os import stat as os_stat

import enka  # type: ignore[reportMissingTypeStubs]
from enka_config import (
    char_filename,
    csv,
    filename,
    json,
    relics_data,
    trailblazer_ids,
    uids,
)

print(len(uids))


def jprint(obj: dict[str, str]) -> None:
    """Create a formatted string of the Python JSON object."""
    text = json.dumps(obj, sort_keys=True, indent=4)
    print(text)


def input_thread(input_list: list[bool]) -> None:
    """Input thread."""
    input()
    input_list.append(True)


def empty_file(path: str) -> bool:
    """Check if file is empty."""
    return os_stat(path).st_size == 0


async def main() -> None:
    """Compile character builds."""
    async with enka.HSRClient(enka.hsr.Language.ENGLISH) as client:
        is_update = input("Update assets? (y/n) ")
        if is_update == "y":
            await client.update_assets()

        # TODO: Automate header keys, follow ZZZ example
        header = [
            "uid",
            "player_level",
            "character",
            "char_level",
            "path",
            "light_cone",
            "light_cone_level",
            "attack_lvl",
            "skill_lvl",
            "ultimate_lvl",
            "talent_lvl",
            "HP",
            "ATK",
            "DEF",
            "SPD",
            "CRIT Rate",
            "CRIT DMG",
            "DMG Boost",
            "Outgoing Healing Boost",
            "Energy Regeneration Rate",
            "Effect RES",
            "Effect Hit Rate",
            "Break Effect",
            "SPD sub",
            "HP sub",
            "ATK sub",
            "DEF sub",
            "CRIT Rate sub",
            "CRIT DMG sub",
            "Effect RES sub",
            "Effect Hit Rate sub",
            "Break Effect sub",
            "Body",
            "Feet",
            "Sphere",
            "Rope",
            "relic",
            "ornament",
        ]

        writer = csv.writer(open(filename, "a", encoding="UTF8", newline=""))
        if empty_file(filename):
            writer.writerow(header)

        header = [
            "uid",
            "phase",
            "name",
            "level",
            "cons",
            "weapon",
            "element",
            "artifacts",
            "relics",
        ]

        writer_chars = csv.writer(
            open(char_filename, "a", encoding="UTF8", newline=""),
        )
        if empty_file(char_filename):
            writer_chars.writerow(header)

        input_list: list[bool] = []
        _thread.start_new_thread(input_thread, (input_list,))
        uid_iter = -1
        while not input_list and uid_iter < len(uids):
            uid_iter += 1
            uid = uids[uid_iter]

            i: int = -1
            while i < 5:
                i += 1
                if i == 5:
                    print("error")
                try:
                    print(f"{uid_iter + 1} / {len(uids)} : {uid}, {i}")
                    data = await client.fetch_showcase(uid)
                    for character in data.characters:
                        element_name = character.element.name.capitalize()
                        line: list[str | int | float | None] = []
                        line_chars: list[str | int | float | None] = []
                        line.append(uid)
                        line_chars.append(uid)
                        line_chars.append("2.2b")
                        line.append(data.player.level)
                        if str(character.id) in trailblazer_ids:
                            if "March 7th" in character.name:
                                line.append("March 7th")
                                line_chars.append("March 7th")
                            else:
                                line.append("Trailblazer")
                                line_chars.append("Trailblazer")
                        else:
                            line.append(character.name)
                            line_chars.append(character.name)
                        line.append(character.level)
                        line_chars.append(character.level)
                        line_chars.append(character.eidolons_unlocked)
                        line.append(element_name)
                        if character.light_cone is not None:
                            line.append(character.light_cone.name)
                            line_chars.append(character.light_cone.name)
                            line.append(character.light_cone.level)
                        else:
                            line.append("")
                            line_chars.append("")
                            line.append("")
                        line_chars.append(element_name)

                        line.extend(
                            skill.level
                            for skill in character.traces
                            if skill.type == 2 and skill.max_level > 1
                        )

                        desired_stats = {
                            "HP": 0.00,
                            "ATK": 0.00,
                            "DEF": 0.00,
                            "SPD": 0.00,
                            "CRIT Rate": 0.00,
                            "CRIT DMG": 0.00,
                            str(element_name) + " DMG Boost": 0.00,
                            "Outgoing Healing Boost": 0.00,
                            "Energy Regeneration Rate": 0.00,
                            "Effect RES": 0.00,
                            "Effect Hit Rate": 0.00,
                            "Break Effect": 0.00,
                        }

                        for stat in character.stats.values():
                            if stat.name in desired_stats:
                                if stat.type == "BaseSpeed":
                                    continue
                                if stat.is_percentage:
                                    if stat.name == "Energy Regeneration Rate":
                                        desired_stats[stat.name] = (
                                            stat.value - 1
                                        ) * 100
                                    else:
                                        desired_stats[stat.name] = stat.value * 100
                                else:
                                    desired_stats[stat.name] = stat.value

                        line.extend(round(stat, 3) for stat in desired_stats.values())

                        mainstats = {
                            "HEAD": "",
                            "HAND": "",
                            "BODY": "",
                            "FOOT": "",
                            "NECK": "",
                            "OBJECT": "",
                        }
                        substats = {
                            "Flat HP": 0.00,
                            "Flat ATK": 0.00,
                            "Flat DEF": 0.00,
                            "Flat SPD": 0.00,
                            "HP": 0.00,
                            "ATK": 0.00,
                            "DEF": 0.00,
                            "CRIT Rate": 0.00,
                            "CRIT DMG": 0.00,
                            "Effect RES": 0.00,
                            "Effect Hit Rate": 0.00,
                            "Break Effect": 0.00,
                        }
                        artifacts: dict[str, int] = {}
                        ornaments: dict[str, int] = {}
                        for relic in character.relics:
                            mainstats[relics_data[str(relic.id)]["type"]] = (
                                relic.main_stat.name
                            )
                            if relics_data[str(relic.id)]["type"] in ["OBJECT", "NECK"]:
                                if relic.set_name not in ornaments:
                                    ornaments[relic.set_name] = 1
                                else:
                                    ornaments[relic.set_name] += 1
                            elif relic.set_name not in artifacts:
                                artifacts[relic.set_name] = 1
                            else:
                                artifacts[relic.set_name] += 1
                            for stat in relic.sub_stats:
                                if stat.is_percentage:
                                    substats[stat.name] += stat.value * 100
                                else:
                                    substats["Flat " + stat.name] += stat.value

                        line.extend(
                            round(substats[stat_key], 3)
                            for stat_key in list(substats.keys())[3:]
                        )

                        line.extend(
                            mainstats[stat_key]
                            for stat_key in list(mainstats.keys())[2:]
                        )

                        char_set = None
                        for arti_set, arti_count in artifacts.items():
                            if arti_count in {2, 4}:
                                if char_set is not None:
                                    if arti_set < char_set:
                                        char_set = arti_set + ", " + char_set
                                    else:
                                        char_set += ", " + arti_set
                                else:
                                    char_set = arti_set
                            elif arti_count == 3:
                                char_set = arti_set + ", Flex"
                        if len(artifacts) > 2:
                            if char_set is not None:
                                char_set += ", Flex"
                            else:
                                char_set = "Flex"
                        line.append(char_set)
                        line_chars.append(char_set)

                        char_set = None
                        for set_name, set_value in ornaments.items():
                            if set_value == 2:
                                char_set = set_name
                        line.append(char_set)
                        line_chars.append(char_set)

                        writer.writerow(line)
                        writer_chars.writerow(line_chars)
                    break
                except enka.errors.PlayerDoesNotExistError:
                    print("Player does not exist.")
                    break
                except enka.errors.APIRequestTimeoutError:
                    print("timeout")
                    await asyncio.sleep(1)
                except enka.errors.GameMaintenanceError:
                    print("Game is in maintenance.")
                    await asyncio.sleep(1)
                except asyncio.exceptions.TimeoutError:
                    print("timeout")
                    await asyncio.sleep(1)
                except AttributeError:
                    print(f"{uid}: {traceback.format_exc()}")
                    await asyncio.sleep(1)
                except Exception as e:
                    if str(e) == "[429] Too Many Requests":
                        print("[429] Too Many Requests")
                        await asyncio.sleep(3)
                    elif "Cannot connect" in str(e):
                        print("Cannot connect")
                        i = 0
                        await asyncio.sleep(1)
                    elif str(e) == "User not found.":
                        print("User not found.")
                        break
                    else:
                        print(f"{uid}: {traceback.format_exc()}")
                        break

        print("\nFinished")

        # if len(error_uids):
        # 	print('Error with UIDs:')
        # 	for i in error_uids:
        # 		print(i)


asyncio.run(main())
