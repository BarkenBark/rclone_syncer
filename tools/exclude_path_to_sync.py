#!/usr/bin/env python3

import argparse
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parents[1]
sys.path.append(str(SCRIPT_DIR))
from util.barktools import user_yes_no

RCLONE_IGNORE_FILENAME = ".barksync_ignore"


def main(*paths: Path):
    paths = tuple([p.resolve() for p in paths])
    paths = tuple([p for p in paths if p.is_dir()])

    print("Will exclude the following directories from syncing:")
    for p in paths:
        print("-", p)
    if not user_yes_no("Okay?"):
        sys.exit(0)

    for p in paths:
        rclone_ignore_path = p / RCLONE_IGNORE_FILENAME
        with open(rclone_ignore_path, "w") as f:
            f.write("\n")

    print(f"Succesfully added {RCLONE_IGNORE_FILENAME} to the specified paths.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "paths",
        nargs="*",
        type=Path,
        default=[Path.cwd()],
        help="Paths to exclude from syncing.",
    )
    args = parser.parse_args()
    main(*args.paths)
