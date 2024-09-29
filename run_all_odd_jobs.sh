#!/bin/bash

find jobs -name "job-*.sh" | while read -r script; do
    index=$(echo "$script" | grep -o -E '[0-9]+')
    
    if (( index % 2 == 1 )); then
        echo "Executing: $script"
        ./"$script"
    fi
done
