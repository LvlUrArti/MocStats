#!/bin/bash

set -e # Stop on error

cd Comps

python comp_rates.py -w &
python comp_rates.py -f &
python comp_rates.py -a
python move.py

cd ../mihomo
python stats.py
cd ../Comps
python move.py
