#!/bin/bash

set -e # Stop on error

# Check for arguments, e.g. `sh compile_all.sh hello`
if [ -n "$1" ]; then
	cd scripts
else
	cd scripts
	python combine_raw_chars.py
	python csv_to_pickle.py -moc &
	python csv_to_pickle.py -pf &
	python csv_to_pickle.py -aa &
	python csv_to_pickle.py -as &
	python hash.py
	cd hf_data
	python up_data.py -y
	python up_data.py -n
	python generate_config.py
	cd ../
fi

echo ""
echo "MoC"
python comp_rates.py -w -moc &
python comp_rates.py -f -moc &
python comp_rates.py -a -moc

echo ""
echo "PF"
python comp_rates.py -w -pf &
python comp_rates.py -f -pf &
python comp_rates.py -a -pf

echo ""
echo "AS"
python comp_rates.py -w -as &
python comp_rates.py -f -as &
python comp_rates.py -a -as

echo ""
echo "AA"
python comp_rates.py -w -aa &
python comp_rates.py -f -aa &
python comp_rates.py -a -aa

cd ../mihomo
echo ""
echo "MoC stats"
python stats.py -moc

echo ""
echo "PF stats"
python stats.py -pf

echo ""
echo "AS stats"
python stats.py -as

echo ""
echo "AA stats"
python stats.py -aa

cd ../scripts/compile_result
python combine_char.py
python histograph.py
python combine_comp.py -moc
python combine_comp.py -pf
python combine_comp.py -as
python combine_comp.py -aa

if [ -d "../../results/web_results" ]; then
	python copyfiles.py -moc
	python copyfiles.py -pf
	python copyfiles.py -as
	python copyfiles.py -aa

	cd ../hf_data
	python up_results.py
fi
