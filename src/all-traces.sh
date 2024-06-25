#!/bin/bash

declare -a traces=("test-trace") #("azure-100k" "mustang-trace-2015-100k" 

for trace_name in "${traces[@]}"; do
    echo $trace_name

    # Carbon Agnostic
    python3 src/run.py --scheduling-policy carbon --carbon-policy oracle -w 0x0 --task-trace $trace_name

    # Lowest Carbon Slot
    python3 src/run.py --scheduling-policy carbon --carbon-policy lowest -w 6x24 --task-trace $trace_name

    # Lowest Carbon Window
    python3 src/run.py --scheduling-policy carbon --carbon-policy waiting -w 6x24 --task-trace $trace_name

    # Carbon Saving per Waiting Time
    python3 src/run.py --scheduling-policy carbon --carbon-policy cst_average -w 6x24 --task-trace $trace_name

    # Ecovisor
    python3 src/run.py --scheduling-policy suspend-resume-threshold --carbon-policy oracle -w 6x24 --task-trace $trace_name

    # Wait AWhile
    python3 src/run.py --scheduling-policy suspend-resume --carbon-policy oracle -w 6x24 --task-trace $trace_name

    # Carbon Agnostic
    python3 src/run.py --scheduling-policy carbon --carbon-policy oracle -w 0x0 --task-trace $trace_name

    # Lowest Carbon Slot
    python3 src/run.py --scheduling-policy carbon --carbon-policy lowest -w 72 --task-trace $trace_name

    # Lowest Carbon Window
    python3 src/run.py --scheduling-policy carbon --carbon-policy waiting -w 72 --task-trace $trace_name

    # Carbon Saving per Waiting Time
    python3 src/run.py --scheduling-policy carbon --carbon-policy cst_average -w 72 --task-trace $trace_name

    # Ecovisor
    python3 src/run.py --scheduling-policy suspend-resume-threshold --carbon-policy oracle -w 72 --task-trace $trace_name

    # Wait AWhile
    python3 src/run.py --scheduling-policy suspend-resume --carbon-policy oracle -w 72 --task-trace $trace_name

done