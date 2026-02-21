"""Combine data from multiple CSV files."""

from csv import reader as csv_reader
from csv import writer as csv_writer

from comp_rates_config import RECENT_PHASE
from send2trash import send2trash

char_data: dict[str, dict[str, list[str]]] = {}
char_data_path = "../data/raw_csvs_real/" + RECENT_PHASE + "_char.csv"
enka_char_path = "../data/raw_csvs_real/" + RECENT_PHASE + "_build_char.csv"
print_data: list[list[str]] = []

print("Opening files...")
# with open("char_data.csv", 'r') as f:
with open(enka_char_path, encoding="UTF8") as f:
    reader = csv_reader(f, delimiter=",")
    print_data += [next(reader)]
    char_data_temp = list(reader)
with open(char_data_path) as f:
    reader = csv_reader(f, delimiter=",")
    headers = next(reader)
    char_data_temp += list(reader)
    for line in char_data_temp:
        if line[0] not in char_data:
            char_data[line[0]] = {}
        if line[2] not in char_data[line[0]]:
            char_data[line[0]][line[2]] = [
                line[3],
                line[4],
                line[5],
                line[6],
                line[7],
                line[8],
            ]
for uid, uid_char in char_data.items():
    for char in uid_char:
        print_data += [[uid, "", char] + uid_char[char]]

send2trash(char_data_path)
send2trash(enka_char_path)
with open(char_data_path, "w", newline="") as f:
    csv_writer = csv_writer(f)
    csv_writer.writerows(print_data)
