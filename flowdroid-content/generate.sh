#!/usr/bin/env bash
set -e

[[ ! -f $1 || -z $2 ]] && echo "Usage: $0 <input csv> <header number>" && exit 1

get_column() {
#$1 = input file
#$2 = column number
    cut -d',' -f"$2" "$1" | sed 's/ //g'
}

get_column_l() {
#$1 = input line
#$2 = column number
    echo "$1" | cut -d',' -f"$2" | sed 's/ //g'
}


input_file="$1"
column_number="$2"
output_dir="./output"
output_file="$output_dir/$(get_column header "$column_number").csv"
rm -f "$output_file"

while read line; do
    libid=$(cut -d',' -f1 <<< "$line" | sed 's/ //g')
    version=$(cut -d',' -f2 <<< "$line" | sed 's/ //g')
    result=$(cut -d',' -f"$column_number" <<< "$line" | sed 's/ //g')
    if [[ $result == '+' ]]; then
        echo "$libid,$version" >> $output_file
    fi
done<$input_file
