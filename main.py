from library import MultiRepoLibrary, Library
from packaging.version import parse, Version
import os
from metadata import LibMetadata
import json
from sys import stderr
import csv, dataclasses

FIELDS = ["libID", "oldest version", "newest version", "most popular version (if applicable)"]

def parse_version(lib: MultiRepoLibrary) -> Version:
    try:
        return parse(lib.version)
    except:
        return parse("0.0.0")

def oldest_version(all_versions: list[MultiRepoLibrary]) -> str:
    if not all_versions:
        return "-"
    
    return min(all_versions, key=parse_version).version

def newest_version(all_versions: list[MultiRepoLibrary]) -> str:
    if not all_versions:
        return "-"
    
    return max(all_versions, key=parse_version).version

def most_popular_version(all_versions: list[MultiRepoLibrary]) -> str:
    if not all_versions:
        return "-"
    result = max(all_versions, key=lambda x: x.usages)
    if result.usages == 0:
        return "-"
    else:
        return result.version
    
def row(id: str, oldest: str, newest: str, popular: str) -> dict[str, str]:
    return {
        FIELDS[0]: id,
        FIELDS[1]: oldest,
        FIELDS[2]: newest,
        FIELDS[3]: popular
    }

def read_metadata(metadata_dir: str) -> dict[str, str]:
    id = "?"
    oldest = "?"
    newest = "?"
    popular = "?"

    try:
        if metadata_dir[-1] != "/":
            metadata_dir += "/"

        metadata: LibMetadata | None = None
        with open(metadata_dir + "metadata.json", "r") as file:
            data = json.loads(file.read())
            metadata = LibMetadata(data)

        id = metadata.id
        all_versions: list[MultiRepoLibrary] = []
        for repo in metadata.repos:
            for v in repo.versions:
                if v.downloaded:
                    l = MultiRepoLibrary(metadata, repo, v)
                    all_versions.append(l)

        oldest = oldest_version(all_versions)
        newest = newest_version(all_versions)
        popular = most_popular_version(all_versions)
    except Exception as e:
        print("error at " + metadata_dir, file=stderr)
        print(e)
        exit(2)
    finally:
        return row(id, oldest, newest, popular)

def create_versions_matrix() -> None:
    root_dir = os.path.expanduser("~/LibSec/libsec-results/libdata/")
    subdirs = next(os.walk(root_dir))[1]
    subdirs.sort()
    
    output_name = "versions-matrix.csv"
    output = open(output_name, "w")
    writer = csv.DictWriter(output, fieldnames=FIELDS)
    writer.writeheader()

    for i, subdir in enumerate(subdirs):
        print(f"{i+1}/{len(subdirs)} is running")
        results = read_metadata(root_dir + subdir)
        writer.writerow(results)

    output.close()

@dataclasses.dataclass
class LibVersions:
    id: str
    oldest_ver: str
    newest_ver: str
    popular_ver: str

def generate_output(input_filename: str, versions_matrix: list[LibVersions]) -> None:
    
    pass

def main() -> None:
    # create_versions_matrix()

    pass


if __name__ == '__main__':
    main()
