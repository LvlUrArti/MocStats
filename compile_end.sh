#!/bin/bash

set -e # Stop on error

cd scripts/compile_result

python combine_char.py
python combine_comp.py
python combine_comp.py -pf
python combine_comp.py -as
python combine_comp.py -aa

if [ -d "../../web_results" ]; then
	python copyfiles.py
	python copyfiles.py -pf
	python copyfiles.py -as
	python copyfiles.py -aa
fi
