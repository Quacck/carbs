#!/bin/bash
export GUROBI_HOME="/home/vincent.opitz/master-thesis/gurobi1103/linux64"
export LD_LIBRARY_PATH=$GUROBI_HOME/lib
export PATH=$GUROBI_HOME/bin:$PATH
export GRB_LICENSE_FILE="/home/vincent.opitz/master-thesis/gurobi1103/gurobi.lic"
python3 src/run.py --scheduling-policy suspend-resume --task-trace single-job --dynamic-power-draw --dynamic-power-draw-type periodic-phases --dynamic-power-draw-phases "{'startup':[{'name': 'startup','duration': 120, 'power': 150}],'work':[{'name': 'high', 'power': 200, 'duration': 2700}, {'name': 'low', 'power': 100, 'duration': 900}]}" --carbon-policy oracle --start-index 8000 --w 12 --filename results/simulation/evaluation/suspend-resume_periodic-phases_1_120_100_12 --repeat
