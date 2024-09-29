#!/bin/bash

# update the cluster traces to include power information


long=$((45 * 60))
medium=$((30 * 60))
short=$((15 * 60))


work_types=("periodic-phases" "constant-from-periodic-phases")
work_phases=( \
    # balanced
    "[{'name': 'high', 'power': 200, 'duration': $medium}, {'name': 'low', 'power': 100, 'duration': $medium}]"\
    # long high
    "[{'name': 'high', 'power': 200, 'duration': $long}, {'name': 'low', 'power': 100, 'duration': $short}]"\
    # short high
    "[{'name': 'high', 'power': 200, 'duration': $short}, {'name': 'low', 'power': 100, 'duration': $long}]"\
)

startup_lengths=(0 30 60 120 180 240)
startup_power_levels=(100 200 300)
waiting_times=(
    4
    12
    24
    #48
)
scheduling_policies=(
    "carbon" \
    "suspend-resume" \
)

# as this is running on a cluster, we need to define the gurobi variables
export GUROBI_HOME="/home/vincent.opitz/master-thesis/gurobi1103/linux64"
export LD_LIBRARY_PATH=$GUROBI_HOME/lib
export PATH=$GUROBI_HOME/bin:$PATH
export GRB_LICENSE_FILE="/home/vincent.opitz/master-thesis/gurobi1103/gurobi.lic"

index=0

mkdir jobs

rm -r jobs/job-*

# now we use a bunch of nested loops to create the cross product between these scenarios
for scheduling_policy in "${scheduling_policies[@]}"; do 
    for work_type in "${work_types[@]}"; do
        for work_phase_index in "${!work_phases[@]}"; do
            for startup_length in "${startup_lengths[@]}"; do
                for startup_power_level in "${startup_power_levels[@]}"; do
                    for waiting_time in "${waiting_times[@]}"; do
                        ((index++))

                        work_phase=${work_phases[$work_phase_index]}

                        filename="results/simulation/evaluation/${scheduling_policy}_${work_type}_${work_phase_index}_${startup_length}_${startup_power_level}_${waiting_time}"
                        phases="{'startup':[{'name': 'startup','duration': $startup_length, 'power': 150}],'work':$work_phase}"

                        if [ ! -f "$filename" ]; then 

                            echo Creating $filename

                            # create a .sh script with the job for later submission
                            echo \#!/bin/bash > jobs/job-${index}.sh
                            echo 'export GUROBI_HOME="/home/vincent.opitz/master-thesis/gurobi1103/linux64"' >> jobs/job-${index}.sh
                            echo 'export LD_LIBRARY_PATH=$GUROBI_HOME/lib' >> jobs/job-${index}.sh
                            echo 'export PATH=$GUROBI_HOME/bin:$PATH' >> jobs/job-${index}.sh
                            echo 'export GRB_LICENSE_FILE="/home/vincent.opitz/master-thesis/gurobi1103/gurobi.lic"' >> jobs/job-${index}.sh
                            echo python3 src/run.py \
                                --scheduling-policy $scheduling_policy \
                                --task-trace single-job \
                                --dynamic-power-draw \
                                --dynamic-power-draw-type "$work_type" \
                                --dynamic-power-draw-phases \"$phases\" \
                                --carbon-policy oracle \
                                --start-index 8000 \
                                --w $waiting_time \
                                --filename $filename \
                                --repeat \
                                >> jobs/job-${index}.sh

                            chmod +x jobs/job-${index}.sh
                        else 
                            echo "Skipping $filename"
                        fi
                    done
                done
            done
        done
    done
done