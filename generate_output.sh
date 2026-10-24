#!/usr/bin/env bash

[[ ! -f $1 ]] && echo "Usage: $0 <input csv file>" && exit 1

input_file="$1"
output_dir="./output"
output_file="$output_dir/$(basename $input_file)"

echo "libid,any-version,first-version,last-version,most-popular-if-applicable" > $output_file

for line in $(tail -n +2 versions-matrix.csv); do
    libid="$(cut -d',' -f1 <<< "$line")"
    oldest="$(cut -d',' -f2 <<< "$line")"
    newest="$(cut -d',' -f3 <<< "$line")"
    popular="$(cut -d',' -f4 <<< "$line")"
    
    query=$(grep "^$libid," $input_file)
    if [[ -z "$query" ]]; then
        echo "$libid,-,-,-,-" >> $output_file
        continue
    fi

    res_old="-"
    res_new="-"
    res_pop="-"
    for line in $query; do
        version="$(cut -d',' -f2 <<< "$line")"
        echo $libid + $version

        [[ $oldest == $version ]] && res_old="+"
        [[ $newest == $version ]] && res_new="+"
        [[ $popular == $version ]] && res_pop="+"
    done
    [[ $popular == "-" ]] && res_pop="no-popular"
    echo "$libid,+,$res_old,$res_new,$res_pop" >> $output_file
done
