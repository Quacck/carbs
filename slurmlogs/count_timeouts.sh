#!/bin/bash

total_count_limit=0
total_count_optimal=0


for file in *; do
    if [ -f "$file" ]; then
        count=$(grep -o "Time limit reached" "$file" | wc -l)
        total_count_limit=$((total_count_limit + count))

        count_optimal=$(grep -o "Optimal solution found" "$file" | wc -l)
        total_count_optimal=$((total_count_optimal + count_optimal))
    fi
done

echo "$total_count_limit timemouts,  $total_count_optimal optimals"

