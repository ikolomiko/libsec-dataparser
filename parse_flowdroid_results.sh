#!/usr/bin/env bash

set -e

libs_dir="$HOME/LibSec/libsec-results/flowdroid-2023-10-10"
output_file="./input/15_Uses_sensitive_data.csv"

[[ ! -d "$libs_dir" ]] && echo "invalid libs_dir" && exit 1
rm -f "$output_file"

total=$(\ls $libs_dir | wc -l)
i=1
for libid in $(\ls $libs_dir); do
    printf "Checking item $i/$total     \r"
    ((++i))
    for version in $(\ls $libs_dir/$libid); do
        logfile="$libs_dir/$libid/$version/flowdroid-log.txt"
        [[ ! -f "$logfile" ]] && continue

        lastline=$(tail -1 "$logfile")
        grep Found <<< "$lastline" &>/dev/null || continue
        count=$(awk '{print $2}' <<< $lastline)
        if (( $count >= 1 )); then
            echo "$libid,$version" >> "$output_file"
        fi
    done
    echo ""
done