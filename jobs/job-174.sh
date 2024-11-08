#!/bin/bash
export GUROBI_HOME="/home/vincent.opitz/master-thesis/gurobi1103/linux64"
export LD_LIBRARY_PATH=$GUROBI_HOME/lib
export PATH=$GUROBI_HOME/bin:$PATH
export GRB_LICENSE_FILE="/home/vincent.opitz/master-thesis/gurobi1103/gurobi.lic"
python3 src/run.py --scheduling-policy carbon --carbon-trace DE-hourly-09-02-to-09-15 --task-trace evaluation_jobs --dynamic-power-draw --dynamic-power-draw-type constant-from-periodic-phases --dynamic-power-draw-phases "{'startup':[{'name': 'startup','duration': 300, 'power': 100}],'work':[{'name': 'high', 'power': 200, 'duration': 3600}, {'name': 'low', 'power': 100, 'duration': 1800}]}" --carbon-policy oracle --start-index 0 --w 48 --filename results/simulation/evaluation_jobs/carbon_constant-from-periodic-phases_1_300_100_48 --repeat
