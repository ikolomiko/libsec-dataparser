#!/usr/bin/env bash

input_folder="./output"
output_file="./final_table.csv"

header="analysis,any-version,first-version,last-version,most-popular-version"
echo $header > $output_file

for file in $(ls $input_folder/*); do
    analysis_name="$(basename $file | cut -d'.' -f1)"
    line_count=$(wc -l $file | awk '{print $1}')

    any_count=$(cut -d',' -f2 $file | grep '+' | wc -l)
    first_count=$(cut -d',' -f3 $file | grep '+' | wc -l)
    last_count=$(cut -d',' -f4 $file | grep '+' | wc -l)
    popular_count=$(cut -d',' -f5 $file | grep '+' | wc -l)
    no_popular_count=$(cut -d',' -f4 versions-matrix.csv | grep '^-$' | wc -l)

    perc_any="$(echo "scale=4; 100*$any_count/$line_count" | bc)"
    perc_first="$(echo "scale=4; 100*$first_count/$line_count" | bc)"
    perc_last="$(echo "scale=4; 100*$last_count/$line_count" | bc)"
    perc_pop="$(echo "scale=4; 100*$popular_count/($line_count - $no_popular_count)" | bc)"
    
    echo "${analysis_name},${perc_any}%,${perc_first}%,${perc_last}%,${perc_pop}%" >> $output_file
done