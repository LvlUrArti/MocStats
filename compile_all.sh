#!/bin/bash

set -e # Stop on error

# Check for arguments, e.g. `sh compile_all.sh hello`
if [ -n "$1" ]; then
  cd Comps
else
  cd Comps
  python combine_raw_chars.py
	python hash.py &
	python csv_to_pickle.py &
	python csv_to_pickle.py -pf &
	python csv_to_pickle.py -as
fi

echo ""
echo "MoC"
python comp_rates.py -w &
python comp_rates.py -f &
python comp_rates.py -a
echo ""
echo "Move MoC"
python move.py

echo ""
echo "PF"
python comp_rates.py -w -pf &
python comp_rates.py -f -pf &
python comp_rates.py -a -pf
echo ""
echo "Move PF"
python move.py -pf

echo ""
echo "AS"
python comp_rates.py -w -as &
python comp_rates.py -f -as &
python comp_rates.py -a -as
echo ""
echo "Move AS"
python move.py -as

echo ""
echo "MoC stats"
cd ../mihomo
python stats.py
cd ../Comps
python move.py

echo ""
echo "PF stats"
cd ../mihomo
python stats.py -pf
cd ../Comps
python move.py -pf

echo ""
echo "AS stats"
cd ../mihomo
python stats.py -as
cd ../Comps
python move.py -as

python combine_char.py
python combine_comp.py
python combine_comp.py -pf
python combine_comp.py -as

if [ -d "../web_results" ]; then
  python copyfiles.py
  python copyfiles.py -pf
  python copyfiles.py -as
fi
