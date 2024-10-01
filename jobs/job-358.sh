#!/bin/bash
export GUROBI_HOME="/home/vincent.opitz/master-thesis/gurobi1103/linux64"
export LD_LIBRARY_PATH=$GUROBI_HOME/lib
export PATH=$GUROBI_HOME/bin:$PATH
export GRB_LICENSE_FILE="/home/vincent.opitz/master-thesis/gurobi1103/gurobi.lic"
python3 src/run.py --scheduling-policy suspend-resume --task-trace different_lengths --dynamic-power-draw --dynamic-power-draw-type constant-from-periodic-phases --dynamic-power-draw-phases "{'startup':[{'name': 'startup','duration': 0, 'power': 150}],'work':[{'name': 'high', 'power': 200, 'duration': 1800}, {'name': 'low', 'power': 100, 'duration': 3600}]}" --carbon-policy oracle --start-index 7000 --w 12 --filename results/simulation/different_lengths/suspend-resume_constant-from-periodic-phases_2_0_200_12 --repeat
