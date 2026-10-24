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
DATASET_TOTAL = 21786

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
    any_version: int = 0

    @property
    def endpoint_total(self) -> int:
        return self.gained + self.removed + self.persisted


@dataclass
class VersionSelection:
    pairs: Dict[str, Tuple[str, str]]
    total: int = 0
    same_version: int = 0
    invalid: int = 0

    @property
    def dataset_total(self) -> int:
        return DATASET_TOTAL


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

            selection.pairs[row["libID"]] = (oldest, newest)

    if len(selection.pairs) != DATASET_TOTAL:
        raise ValueError(f"dataset size mismatch: {len(selection.pairs)} != {DATASET_TOTAL}")

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

        counts.any_version = sum(1 for lib_id in versions if present.get(lib_id))
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
            "endpoint_total", "endpoint_total_pct",
            "any_version", "any_version_pct",
        ])

        for feature, _ in FEATURES:
            counts = results[feature]
            writer.writerow([
                feature,
                counts.gained, percentage(counts.gained, dataset_total),
                counts.removed, percentage(counts.removed, dataset_total),
                counts.persisted, percentage(counts.persisted, dataset_total),
                counts.endpoint_total, percentage(counts.endpoint_total, dataset_total),
                counts.any_version, percentage(counts.any_version, dataset_total),
            ])

        writer.writerow([])
        writer.writerow(["notes"])
        writer.writerow(["metric", "value", "explanation"])
        writer.writerow([
            "dataset_total_libraries",
            dataset_total,
            "All percentages use this denominator.",
        ])
        writer.writerow([
            "percentage_definition",
            f"count / {dataset_total}",
            "Cell percentage = cell count / dataset size.",
        ])
        writer.writerow([
            "single_version_libraries",
            selection.same_version,
            "Libraries with oldest == newest are counted as persisted when the feature is present.",
        ])
        writer.writerow([
            "excluded_invalid_versions",
            selection.invalid,
            "Excluded because oldest/newest was missing or invalid.",
        ])
        writer.writerow([
            "absent_both_omissions",
            "",
            "Libraries with the feature absent in both endpoints are omitted from the cell counts.",
        ])
        writer.writerow([
            "endpoint_total_definition",
            "gained + removed + persisted",
            "Feature present in at least one endpoint (oldest or newest).",
        ])
        writer.writerow([
            "any_version_definition",
            "feature present in any version",
            "Also includes libraries with the feature only in non-endpoint versions.",
        ])


def write_markdown(results: Dict[str, TransitionCounts], selection: VersionSelection) -> None:
    dataset_total = selection.dataset_total
    print("| feature | gained (absent->present) | removed (present->absent) | persisted (present->present) | endpoint total | any version |")
    print("|---|---:|---:|---:|---:|---:|")

    for feature, _ in FEATURES:
        counts = results[feature]
        print(
            f"| {feature} "
            f"| {count_with_percentage(counts.gained, dataset_total)} "
            f"| {count_with_percentage(counts.removed, dataset_total)} "
            f"| {count_with_percentage(counts.persisted, dataset_total)} "
            f"| {count_with_percentage(counts.endpoint_total, dataset_total)} "
            f"| {count_with_percentage(counts.any_version, dataset_total)} |"
        )

    print()
    print("### Notes")
    print(f"- Dataset: {dataset_total} distinct libraries. Percentages are cell count / {dataset_total}.")
    print(f"- {selection.same_version} libraries have only one version (oldest == newest); when the feature is present, they count as persisted.")
    print(f"- {selection.invalid} source rows with missing or invalid versions were excluded.")
    print("- Libraries with the feature absent in both endpoints are omitted from the cell counts.")
    print("- `endpoint total` = gained + removed + persisted; `any version` also includes middle-only libraries.")


def main() -> None:
    selection = read_version_selection()
    results = count_transitions(selection.pairs)
    write_csv(results, selection)
    write_markdown(results, selection)


if __name__ == "__main__":
    main()
