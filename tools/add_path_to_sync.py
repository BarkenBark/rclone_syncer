#!/usr/bin/env python3

import argparse
import difflib
import json
import socket
import subprocess
import sys
from collections import OrderedDict
from pathlib import Path
from typing import List

from exclude_path_to_sync import RCLONE_IGNORE_FILENAME

SCRIPT_DIR = Path(__file__).resolve().parents[1]
sys.path.append(str(SCRIPT_DIR))

REMOTE_TOP_DIRECTORY_NAME = f"{socket.gethostname()}_backup"
PATHS_TO_SYNC_JSON_PATH = SCRIPT_DIR / "cfg/paths_to_sync.json"
JSON_PRETTY_FORMAT_KWARGS = {"indent": 4, "separators": (",", ": ")}


# Wrapper class for `OrderedDict` which lets us consider entries in the list of paths to
# sync as equal only w.r.t. the "local_path" field.
class PathToSync(OrderedDict):
    def __eq__(self, __o: object) -> bool:
        if not isinstance(__o, PathToSync):
            return NotImplemented
        return self["local_path"] == __o["local_path"]

    def __ne__(self, __o: object) -> bool:
        return not self == __o


def main(
    *paths: Path,
    excludes: List[str] = [],
    dry_run: bool = False,
    unexclude: bool = False,
):
    paths = tuple([p.resolve() for p in paths])

    # Print what's going to happen and have user confirm.
    print(
        (
            f"\nWill {'(not) ' if dry_run else ''}add the following paths to "
            f"{PATHS_TO_SYNC_JSON_PATH}:"
        )
    )
    for p in paths:
        print("-", p)

    if excludes:
        print("Using the following exclusion patterns:")
        for exclude_pattern in excludes:
            print("-", exclude_pattern)
    else:
        print("Using no exclusion patterns.")

    # Load existing paths to sync.
    with open(PATHS_TO_SYNC_JSON_PATH, "r") as f:
        paths_to_sync: List[PathToSync] = json.load(f, object_pairs_hook=PathToSync)
        paths_to_sync_str_before = json.dumps(
            paths_to_sync,
            **JSON_PRETTY_FORMAT_KWARGS,  # type: ignore
        )

    # Add new paths to sync. Update existing paths to sync with new remote paths and
    # exclusion filters.
    for p in paths:
        local_path = str(p)
        if p.is_file():
            remote_path = REMOTE_TOP_DIRECTORY_NAME + str(p.parent)
        elif p.is_dir():
            remote_path = REMOTE_TOP_DIRECTORY_NAME + str(p)
        else:
            continue

        path_to_sync = PathToSync(
            local_path=local_path,
            remote_path=remote_path,
        )

        if excludes:
            path_to_sync["excludes"] = excludes
        paths_to_sync = [p_ for p_ in paths_to_sync if p_ != path_to_sync]
        paths_to_sync.append(path_to_sync)

    # Get resulting diff.
    paths_to_sync_str_after = json.dumps(
        paths_to_sync,
        **JSON_PRETTY_FORMAT_KWARGS,  # type: ignore
    )
    diff = difflib.unified_diff(
        paths_to_sync_str_before.splitlines(),
        paths_to_sync_str_after.splitlines(),
        fromfile="before",
        tofile="after",
        lineterm="",
    )

    if dry_run:
        print(
            (
                "\nThe following changes would have been made to "
                f"{PATHS_TO_SYNC_JSON_PATH}:"
            )
        )
        for line in diff:
            print(line)
        sys.exit(0)

    # Write to the list of paths to sync.
    with open(PATHS_TO_SYNC_JSON_PATH, "w") as f:
        json.dump(paths_to_sync, f, **JSON_PRETTY_FORMAT_KWARGS)  # type: ignore

    # Remove rclone ignore files if present.
    unlinked_files: List[Path] = []
    if unexclude:
        for path_to_sync in paths_to_sync:
            rclone_ignore_path = (
                Path(path_to_sync["local_path"]) / RCLONE_IGNORE_FILENAME
            )
            if rclone_ignore_path.is_file():
                rclone_ignore_path.unlink()
                unlinked_files.append(rclone_ignore_path)

    # Print resulting changes made.
    if diff:
        print(f"\nThe following changes were made to {PATHS_TO_SYNC_JSON_PATH}:")
        for line in diff:
            print(line)
    else:
        print(f"\nNo changes made to {PATHS_TO_SYNC_JSON_PATH}.")

    if unlinked_files:
        print(
            f"\nThe following directories had their {RCLONE_IGNORE_FILENAME} removed:"
        )
        for unlinked_file in unlinked_files:
            print(unlinked_file)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "paths",
        nargs="*",
        type=Path,
        default=[Path.cwd()],
        help="Paths to start syncing.",
    )
    parser.add_argument(
        "--exclude",
        type=str,
        default=[],
        action="append",
        help=(
            "Exclusion filter to add for rclone sync. Multiple instances can be passed."
            "Applies to all paths passed to this script. See rclone documentation for "
            "pattern explanation."
        ),
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Do not write to the file, only print the contents that would be written.",
    )
    parser.add_argument(
        "--unexclude",
        action="store_true",
        help=f"Remove {RCLONE_IGNORE_FILENAME} for paths which have it.",
    )
    parser.add_argument(
        "--sync",
        action="store_true",
        help="Run sync script after updating paths to sync.",
    )
    args = parser.parse_args()

    main(
        *args.paths,
        excludes=args.exclude,
        dry_run=args.dry_run,
        unexclude=args.unexclude,
    )
    if args.sync:
        subprocess.run([SCRIPT_DIR / "sync_paths.sh"])
