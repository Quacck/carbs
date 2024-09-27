#!/bin/bash

# update the cluster traces to include power information


long=$((45 * 60))
medium=$((30 * 60))
short=$((15 * 60))


work_types=("periodic-phases" "constant-from-phased")
work_phases=( \
    # balanced
    "[{'name': 'high', 'power': 200, 'duration': $medium}, {'name': 'low', 'power': 100, 'duration': $medium}]"\
    # long high
    "[{'name': 'high', 'power': 200, 'duration': $long}, {'name': 'low', 'power': 100, 'duration': $short}]"\
    # short high
    "[{'name': 'high', 'power': 200, 'duration': $short}, {'name': 'low', 'power': 100, 'duration': $long}]"\
)

startup_lengths=(0 15 30 60 120 180 240)
startup_power_levels=(100 200 300)
waiting_times=(
    4
    12
    24
    #48
)
scheduling_policies=(
    #"carbon"\
    "suspend-resume"\
)


# now we use a bunch of nested loops to create the cross product between these scenarios
for scheduling_policy in "${scheduling_policies[@]}"; do 
    for work_type in "${work_types[@]}"; do
        for work_phase_index in "${!work_phases[@]}"; do
            for startup_length in "${startup_lengths[@]}"; do
                for startup_power_level in "${startup_power_levels[@]}"; do
                    for waiting_time in "${waiting_times[@]}"; do

                        work_phase=${work_phases[$work_phase_index]}

                        filename="results/simulation/evaluation/${scheduling_policy}_${work_type}_${work_phase_index}_${startup_length}_${startup_power_level}_${waiting_time}"
                        echo $filename

                        phases="{'startup':[{'name': 'startup','duration': $startup_length, 'power': 150}],'work':$work_phase}"

                        # if this takes too long, use squeue to parallelize this on cluster
                        python3 src/run.py \
                            --scheduling-policy $scheduling_policy \
                            --task-trace single-job \
                            --dynamic-power-draw \
                            --dynamic-power-draw-type "$work_type" \
                            --dynamic-power-draw-phases "$phases" \
                            --carbon-policy oracle \
                            --start-index 8000 \
                            --w $waiting_time \
                            --filename $filename \
                            --repeat
                    done
                done
            done
        done
    done
done