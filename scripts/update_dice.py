import json
import os.path

from comp_rates_config import RECENT_PHASE

if os.path.exists("../data/raw_csvs_real/"):
    f = open("../data/raw_csvs_real/" + RECENT_PHASE + "_nous.json")
else:
    f = open("../data/raw_csvs/" + RECENT_PHASE + "_nous.json")
json_data = json.load(f)

dice_faces: set[str] = set()
dice_faces_dict = {
    "4076c4ccf19ca71dd8f31e313a9e9604": "IconRogueDlcDiceFaceI3",
    "2d74ffb5ffe4a607aecc90eba019e4a7": "IconRogueDlcDiceFaceI19",
    "927569cb77ff1d1f83f161b7daa6c800": "IconRogueDlcDiceFaceI1",
    "8c3be8be6ed8574cb256ede46b9fcb5f": "IconRogueDlcDiceFaceI48",
    "17dd0550fa4c1f59d57d7fbdf01f43ab": "IconRogueDlcDiceFaceI57",
    "e23e48c6b2f680def7af867bd0016e26": "IconRogueDlcDiceFaceI47",
    "7809aeae68e92730802bf96528412a92": "IconRogueDlcDiceFaceI38",
    "d4d6e9c442a4605402576d25cdef5256": "IconRogueDlcDiceFaceI25",
    "1612f8293df25a624186723d67fd9814": "IconRogueDlcDiceFaceI55",
    "75d71e35ac1a1a70c0e23f469a0f85b0": "IconRogueDlcDiceFaceI41",
    "8f2143a5685a5d5290f7e9730a27be70": "IconRogueDlcDiceFaceI45",
    "824e13071ddbf14538b6262a45459fbd": "IconRogueDlcDiceFaceI61",
    "a0b580b0164dea9b430d4aff913d47ed": "IconRogueDlcDiceFaceI2",
    "bfaaa223d6cbccca590061338d1db072": "IconRogueDlcDiceFaceI17",
    "c521b4c2f691c401b04a1efe7bf21c7a": "IconRogueDlcDiceFaceI59",
    "e2b68333ae7b177a47365e26ca3355b1": "IconRogueDlcDiceFaceI14",
    "7e436f51501ef7fb8de8d050360062dd": "IconRogueDlcDiceFaceI22",
    "4b4e0dd89f802e267710ab7fdf34f048": "IconRogueDlcDiceFaceI39",
    "b4af114804b8b29ffd27549473a8419b": "IconRogueDlcDiceFaceI21",
    "1859bb7d089a61684a297ca13bd8bc58": "IconRogueDlcDiceFaceI20",
    "c5428312a88fe038f25d4f00628e79d4": "IconRogueDlcDiceFaceI43",
    "bc24dfbeb7a64cd22c7b636e51ccc4db": "IconRogueDlcDiceFaceI28",
    "bd94bd7b47c21b8d8e0aa1de6319258f": "IconRogueDlcDiceFaceI33",
    "49ee3871183320f3390d7d33ff9ac3c6": "IconRogueDlcDiceFaceI62",
    "9ecaacd073f2fdac49fe9924359ae262": "IconRogueDlcDiceFaceI8",
    "5da32f55c0e0cd90fc6f54a6ab014935": "IconRogueDlcDiceFaceI30",
    "3a4bf0aeb128658470d64b27311df9b4": "IconRogueDlcDiceFaceI16",
    "7efabf0990b44ab63122645a66a2e003": "IconRogueDlcDiceFaceI60",
    "23b3539882166114dac1e4f8bc5bd40b": "IconRogueDlcDiceFaceI46",
    "eb0f53217d7c6b6d1fedb67430a2bce3": "IconRogueDlcDiceFaceI26",
    "8493c6ee996ff631ccd790b4158db219": "IconRogueDlcDiceFaceI11",
    "c4c35ee8946c7ef84d3adaf3c25d3cc6": "IconRogueDlcDiceFaceI12",
    "a90722aa29175fc83ba823d7bd5ba9af": "IconRogueDlcDiceFaceI44",
    "3f7e5f30fb37b3a3b7c95b6eb042ce93": "IconRogueDlcDiceFaceI7",
    "4f524d11c12e430db47f68f8126c8f76": "IconRogueDlcDiceFaceI5",
    "e36a32ba7af1886aeffc45c6cb8e0885": "IconRogueDlcDiceFaceI34",
    "c20bf8246d8686d3302863425a81a94a": "IconRogueDlcDiceFaceI29",
    "38b797f2845c3e7c8a622fe05afe8069": "IconRogueDlcDiceFaceI56",
    "e04588c0da45bb3ff51489eef10faa61": "IconRogueDlcDiceFaceI50",
    "218330fa60bb0d4e4bfc2e86f1230e69": "IconRogueDlcDiceFaceI42",
    "c5a4837fa898ecf0c83af28d9f598c8d": "IconRogueDlcDiceFaceI32",
    "572fe56e8d55c442a2a5a68fd7834457": "IconRogueDlcDiceFaceI53",
    "c833bfc8cdfd28d12c88d9a5b9a4c28b": "IconRogueDlcDiceFaceI37",
    "741ec763bf04448657a9a358bddb7f05": "IconRogueDlcDiceFaceI27",
    "1529bae43e1149be24426f13f67e4c02": "IconRogueDlcDiceFaceI4",
    "89b4b798edf86ff66b369d872aab5bb3": "IconRogueDlcDiceFaceI54",
    "6fc9230a43d575c6a5110360a65cc626": "IconRogueDlcDiceFaceI9",
    "3e9004fe45a0988d162bb34f0f82947a": "IconRogueDlcDiceFaceI24",
    "75317810b69f77b887274ce6554eee0d": "IconRogueDlcDiceFaceI58",
    "ac4cea890bfff8e56d6bdd4a646f69c0": "IconRogueDlcDiceFaceI52",
    "12621af77d1494fbc34f1989ffa7217d": "IconRogueDlcDiceFaceI10",
    "f99f29910d81c47425420a79e9b9e1b1": "IconRogueDlcDiceFaceI35",
    "c815a86d1ec79561d534489e5059bc44": "IconRogueDlcDiceFaceI6",
    "ac261e61efa49b6f4e401b15b0af6fca": "IconRogueDlcDiceFaceI15",
    "1098d12248664b23239a0e83a9162b2c": "IconRogueDlcDiceFaceI49",
    "9ce60577a279df29efb73ae8187286d5": "IconRogueDlcDiceFaceI23",
    "5250a4a969982b8b0c6c01248d670c28": "IconRogueDlcDiceFaceI13",
    "bbbb44b20d9e6a383d905856c11f34c3": "IconRogueDlcDiceFaceI31",
    "71a49443ecd9c8f1e23e7d7d97a67c9b": "IconRogueDlcDiceFaceI36",
    "512bf1946ba18cb5d07e9c437996ac6d": "IconRogueDlcDiceFaceI51",
}

for uid in json_data:
    for row in json_data[uid]:
        for dice_face in row["dice_face"]:
            dice_faces.add(dice_face)

# print(dice_faces)
# exit()

out_dices = {}
with open("../data/nous_dice.json") as char_file:
    DICES = json.load(char_file)
for dice in DICES:
    for dice_face in dice_faces:
        if DICES[dice]["shortIcon"] == dice_faces_dict[dice_face[:-2]] and DICES[dice][
            "rarity"
        ] == int(dice_face[-1:]):
            out_dices[dice_face] = DICES[dice]
            break

with open("../data/nous_dice_hoyolab.json", "w") as out_file:
    out_file.write(json.dumps(out_dices, indent=4))
exit()
