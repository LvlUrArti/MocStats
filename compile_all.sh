#!/bin/bash

set -e # Stop on error

# Check for arguments, e.g. `sh compile_all.sh hello`
if [ -n "$1" ]; then
	cd Comps
else
	cd Comps
	python combine_raw_chars.py
	python csv_to_pickle.py &
	python csv_to_pickle.py -pf &
	python csv_to_pickle.py -aa &
	python csv_to_pickle.py -as &
	python hash.py
	cd hf_data
	python up_data.py -y
	python up_data.py -n
	cd ../
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
echo "AA"
python comp_rates.py -w -aa &
python comp_rates.py -f -aa &
python comp_rates.py -a -aa
echo ""
echo "Move AA"
python move.py -aa

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

echo ""
echo "AA stats"
cd ../mihomo
python stats.py -aa
cd ../Comps
python move.py -aa

python combine_char.py
python combine_comp.py
python combine_comp.py -pf
python combine_comp.py -as
python combine_comp.py -aa

if [ -d "../web_results" ]; then
	python copyfiles.py
	python copyfiles.py -pf
	python copyfiles.py -as
	python copyfiles.py -aa
fi
