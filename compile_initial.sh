#!/bin/bash

set -e # Stop on error
cd scripts
python combine_raw_chars.py
python csv_to_pickle.py &
python csv_to_pickle.py -pf &
python csv_to_pickle.py -aa &
python csv_to_pickle.py -as &
python hash.py
