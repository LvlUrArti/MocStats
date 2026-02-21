#!/bin/bash

set -e # Stop on error

cd scripts

python comp_rates.py -w &
python comp_rates.py -f &
python comp_rates.py -a
python move.py

cd ../mihomo
python stats.py
cd ../scripts
python move.py
