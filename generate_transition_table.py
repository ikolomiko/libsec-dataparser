#!/usr/bin/env python3

import csv
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Set, Tuple

BASE_DIR = Path(__file__).resolve().parent
VERSIONS_MATRIX = BASE_DIR / "versions-matrix.csv"
INPUT_DIR = BASE_DIR / "input"
OUTPUT_FILE = BASE_DIR / "transition_table.csv"

FEATURES = [
    ("reflection", "01_Uses_reflection.csv"),
    ("installed package queries", "03_Read_installed_packages.csv"),
    ("sensitive data access", "15_Uses_sensitive_data.csv"),
    ("javascript usage", "02_Uses_javascript.csv"),
    ("classloader", "13_Uses_classloader.csv"),
]


@dataclass
class TransitionCounts:
    gained: int = 0
    removed: int = 0
    persisted: int = 0
    absent_both: int = 0

    @property
    def total(self) -> int:
        return self.gained + self.removed + self.persisted


@dataclass
class VersionSelection:
    pairs: Dict[str, Tuple[str, str]]
    total: int = 0
    same_version: int = 0
    invalid: int = 0

    @property
    def dataset_total(self) -> int:
        return self.total - self.invalid


def percentage(count: int, total: int) -> str:
    return f"{100 * count / total:.2f}%"


def count_with_percentage(count: int, total: int) -> str:
    return f"{count} ({percentage(count, total)})"


def read_version_selection() -> VersionSelection:
    selection = VersionSelection(pairs={})
    with VERSIONS_MATRIX.open(newline="") as file:
        for row in csv.DictReader(file):
            selection.total += 1
            oldest = row["oldest version"]
            newest = row["newest version"]

            if oldest in ("", "-") or newest in ("", "-"):
                selection.invalid += 1
                continue

            if oldest == newest:
                selection.same_version += 1
                continue

            selection.pairs[row["libID"]] = (oldest, newest)

    return selection


def read_presence(filename: str) -> Dict[str, Set[str]]:
    presence: Dict[str, Set[str]] = defaultdict(set)
    with (INPUT_DIR / filename).open(newline="") as file:
        for row in csv.reader(file):
            if len(row) < 2 or row[0] == "libid":
                continue
            presence[row[0]].add(row[1])

    return presence


def count_transitions(versions: Dict[str, Tuple[str, str]]) -> Dict[str, TransitionCounts]:
    results: Dict[str, TransitionCounts] = {}

    for feature, filename in FEATURES:
        present = read_presence(filename)
        counts = TransitionCounts()
        for lib_id, (oldest, newest) in versions.items():
            lib_versions = present.get(lib_id, set())
            old_present = oldest in lib_versions
            new_present = newest in lib_versions

            if old_present and new_present:
                counts.persisted += 1
            elif new_present:
                counts.gained += 1
            elif old_present:
                counts.removed += 1
            else:
                counts.absent_both += 1

        results[feature] = counts

    return results


def write_csv(results: Dict[str, TransitionCounts], selection: VersionSelection) -> None:
    dataset_total = selection.dataset_total
    with OUTPUT_FILE.open("w", newline="") as file:
        writer = csv.writer(file)
        writer.writerow([
            "feature",
            "gained", "gained_pct",
            "removed", "removed_pct",
            "persisted", "persisted_pct",
            "total", "total_pct",
        ])

        for feature, _ in FEATURES:
            counts = results[feature]
            writer.writerow([
                feature,
                counts.gained, percentage(counts.gained, dataset_total),
                counts.removed, percentage(counts.removed, dataset_total),
                counts.persisted, percentage(counts.persisted, dataset_total),
                counts.total, percentage(counts.total, dataset_total),
            ])

        writer.writerow([])
        writer.writerow(["notes"])
        writer.writerow(["metric", "value", "explanation"])
        writer.writerow([
            "dataset_total_libraries",
            dataset_total,
            "Distinct libraries in the analysis dataset; all percentages use this denominator.",
        ])
        writer.writerow([
            "percentage_definition",
            f"count / {dataset_total}",
            "Each cell percentage is the cell count divided by dataset_total_libraries.",
        ])
        writer.writerow([
            "versions_matrix_rows",
            selection.total,
            "Rows present in versions-matrix.csv.",
        ])
        writer.writerow([
            "excluded_invalid_versions",
            selection.invalid,
            "Rows with a missing or invalid oldest/newest version; not part of the dataset.",
        ])
        writer.writerow([
            "libraries_with_same_oldest_newest",
            selection.same_version,
            "Dataset libraries where oldest == newest; they count in the denominator but cannot contribute a transition.",
        ])
        writer.writerow([
            "libraries_with_distinct_oldest_newest",
            len(selection.pairs),
            "Dataset libraries with valid, distinct oldest/newest versions.",
        ])
        writer.writerow([
            "absent_both_omissions",
            "",
            "Libraries with a feature absent in both oldest and newest are omitted from that feature's three transition cells.",
        ])
        for feature, _ in FEATURES:
            writer.writerow([
                f"absent_both_{feature.replace(' ', '_')}",
                results[feature].absent_both,
                f"Dataset libraries with no {feature} in either endpoint.",
            ])


def write_markdown(results: Dict[str, TransitionCounts], selection: VersionSelection) -> None:
    dataset_total = selection.dataset_total
    print("| feature | gained (absent->present) | removed (present->absent) | persisted (present->present) | total |")
    print("|---|---:|---:|---:|---:|")

    for feature, _ in FEATURES:
        counts = results[feature]
        print(
            f"| {feature} "
            f"| {count_with_percentage(counts.gained, dataset_total)} "
            f"| {count_with_percentage(counts.removed, dataset_total)} "
            f"| {count_with_percentage(counts.persisted, dataset_total)} "
            f"| {count_with_percentage(counts.total, dataset_total)} |"
        )

    print()
    print("### Notes")
    print(f"- Dataset: {dataset_total} distinct libraries. Each percentage is the cell count divided by {dataset_total}.")
    print(f"- `versions-matrix.csv` has {selection.total} rows.")
    print(f"- {selection.invalid} rows were excluded because oldest/newest was missing or invalid; they are not part of the dataset.")
    print(f"- {selection.same_version} dataset libraries have oldest == newest. They are included in the {dataset_total} denominator but cannot contribute to gained, removed, or persisted.")
    print(f"- {len(selection.pairs)} dataset libraries have valid, distinct oldest/newest versions and can contribute to the transition cells.")
    print("- Libraries with the feature absent in both oldest and newest are omitted from that feature's three transition cells.")
    print("- Per-feature absent-in-both counts:")
    for feature, _ in FEATURES:
        print(f"  - {feature}: {results[feature].absent_both}")


def main() -> None:
    selection = read_version_selection()
    results = count_transitions(selection.pairs)
    write_csv(results, selection)
    write_markdown(results, selection)


if __name__ == "__main__":
    main()
