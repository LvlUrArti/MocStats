"""Combine data from multiple CSV files."""

import csv
from os import path

from send2trash import send2trash

output: list[list[str]] = []
output_char: list[list[str]] = []

iteration = 0
while path.exists("output" + str(iteration + 1) + ".csv"):
    iteration += 1
uidlistchar = set[str]()
uidlist = set[str]()
uidcheck = set[int]()

for i in range(iteration):
    print(f"{i + 1} / {iteration}", end="")
    # with open("output" + str(i + 1) + ".csv", 'r', encoding='UTF8') as f:
    with open("output" + str(i + 1) + ".csv") as f:
        reader = csv.reader(f, delimiter=",")
        headers = next(reader)
        if i == 0:
            output += [headers]
            output_temp = list(reader)
            for j in output_temp:
                uidlistchar.add(j[0])
                output += [j]
        else:
            output_temp = list(reader)
            for j in output_temp:
                if j[0] not in uidlistchar:
                    output += [j]

    with open("output" + str(i + 1) + "_char.csv") as f:
        reader = csv.reader(f, delimiter=",")
        headers = next(reader)
        if i == 0:
            output_char += [headers]
            output_chartemp = list(reader)
            for j in output_chartemp:
                uidlist.add(j[0])
                output_char += [j]
        else:
            output_chartemp = list(reader)
            for j in output_chartemp:
                if j[0] not in uidlist:
                    output_char += [j]
                    uidcheck.add(int(j[0]))
    send2trash("output" + str(i + 1) + ".csv")
    send2trash("output" + str(i + 1) + "_char.csv")
    print("\r", end="")

with open("output1.csv", "w", newline="") as f:
    csv_writer = csv.writer(f)
    csv_writer.writerows(output)

with open("output1_char.csv", "w", newline="") as f:
    csv_writer = csv.writer(f)
    csv_writer.writerows(output_char)
