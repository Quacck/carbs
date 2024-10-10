#!/bin/bash

echo "gap" > gap_values.txt

for file in *; do
    if [ -f "$file" ]; then
        grep "Best objective" "$file" | while read -r line; do
            field=$(echo "$line" | awk -v FS=" " -v OFS="$separator" "{print \$8}")
            echo "$field" >> gap_values.txt
        done
    fi
done
