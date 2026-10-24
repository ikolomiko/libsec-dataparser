#!/usr/bin/env bash

set -euo pipefail

input_folder="./output"
flowdroid_folder="./flowdroid-content/output"
output_file="./final_table.csv"
versions_file="./versions-matrix.csv"
dataset_ids="$(mktemp)"
trap 'rm -f "$dataset_ids"' EXIT

tail -n +2 "$versions_file" | awk -F',' '$2 != "-" && $3 != "-" {print $1}' > "$dataset_ids"

dataset_total=21786
dataset_id_count=$(wc -l < "$dataset_ids")
if [[ "$dataset_id_count" -ne "$dataset_total" ]]; then
    echo "dataset size mismatch: $dataset_id_count != $dataset_total" >&2
    exit 1
fi

no_popular_count=$(awk -F',' 'NR==FNR{valid[$1]=1; next} ($1 in valid) && $4 == "-" {count++} END{print count+0}' "$dataset_ids" "$versions_file")
popular_total=$((dataset_total - no_popular_count))

header="analysis,any-version,first-version,last-version,most-popular-version"
echo "$header" > "$output_file"

for file in "$input_folder"/*; do
    analysis_name="$(basename "$file" | cut -d'.' -f1)"

    any_count=$(awk -F',' 'NR==FNR{valid[$1]=1; next} ($1 in valid) && $2 == "+" {count++} END{print count+0}' "$dataset_ids" "$file")
    first_count=$(awk -F',' 'NR==FNR{valid[$1]=1; next} ($1 in valid) && $3 == "+" {count++} END{print count+0}' "$dataset_ids" "$file")
    last_count=$(awk -F',' 'NR==FNR{valid[$1]=1; next} ($1 in valid) && $4 == "+" {count++} END{print count+0}' "$dataset_ids" "$file")
    popular_count=$(awk -F',' 'NR==FNR{valid[$1]=1; next} ($1 in valid) && $5 == "+" {count++} END{print count+0}' "$dataset_ids" "$file")

    perc_any=$(awk -v count="$any_count" -v total="$dataset_total" 'BEGIN { printf "%.4f", 100 * count / total }')
    perc_first=$(awk -v count="$first_count" -v total="$dataset_total" 'BEGIN { printf "%.4f", 100 * count / total }')
    perc_last=$(awk -v count="$last_count" -v total="$dataset_total" 'BEGIN { printf "%.4f", 100 * count / total }')
    perc_pop=$(awk -v count="$popular_count" -v total="$popular_total" 'BEGIN { printf "%.4f", 100 * count / total }')

    echo "${analysis_name},${perc_any}%,${perc_first}%,${perc_last}%,${perc_pop}%" >> "$output_file"
done

for file in "$flowdroid_folder/FILE_INFORMATION.csv"; do
    analysis_name="$(basename "$file" | cut -d'.' -f1)"

    any_count=$(awk -F',' 'NR==FNR{valid[$1]=1; next} ($1 in valid) && !seen[$1]++ {count++} END{print count+0}' "$dataset_ids" "$file")
    first_count=$(awk -F',' 'NR==FNR{if (NR>1 && $2 != "-" && $3 != "-") oldest[$1]=$2; next} ($1 in oldest) && $2 == oldest[$1] && !seen[$1]++ {count++} END{print count+0}' "$versions_file" "$file")
    last_count=$(awk -F',' 'NR==FNR{if (NR>1 && $2 != "-" && $3 != "-") newest[$1]=$3; next} ($1 in newest) && $2 == newest[$1] && !seen[$1]++ {count++} END{print count+0}' "$versions_file" "$file")
    popular_count=$(awk -F',' 'NR==FNR{if (NR>1 && $2 != "-" && $3 != "-") popular[$1]=$4; next} ($1 in popular) && popular[$1] != "-" && $2 == popular[$1] && !seen[$1]++ {count++} END{print count+0}' "$versions_file" "$file")

    perc_any=$(awk -v count="$any_count" -v total="$dataset_total" 'BEGIN { printf "%.4f", 100 * count / total }')
    perc_first=$(awk -v count="$first_count" -v total="$dataset_total" 'BEGIN { printf "%.4f", 100 * count / total }')
    perc_last=$(awk -v count="$last_count" -v total="$dataset_total" 'BEGIN { printf "%.4f", 100 * count / total }')
    perc_pop=$(awk -v count="$popular_count" -v total="$popular_total" 'BEGIN { printf "%.4f", 100 * count / total }')

    echo "${analysis_name},${perc_any}%,${perc_first}%,${perc_last}%,${perc_pop}%" >> "$output_file"
done
