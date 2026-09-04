#!/usr/bin/env python3
"""
Write the .meta directory of a fixture subset.

Given the .meta directory of a full execution-spec-tests release, keep only
the index entries whose fixture files live under the given format directories
(e.g. blockchain_tests_engine) and write the result, with recomputed
test_count, fixture_formats and forks, to the output .meta directory. The
other files of the source .meta directory are copied along unchanged, except
the HTML reports. root_hash is cleared: it covers the whole release and no
longer describes the subset.

Standard library only, so that this runs in any Python base image.
"""

import argparse
import json
import shutil
import sys
from pathlib import Path

REPORT_FILES = {"report_consume.html", "report_fill.html"}


def main() -> int:
    """Filter the index and copy the remaining metadata files."""
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("src_meta", type=Path, help="source .meta directory")
    parser.add_argument("dst_meta", type=Path, help="output .meta directory")
    parser.add_argument(
        "--format-dir",
        action="append",
        required=True,
        dest="format_dirs",
        metavar="DIR",
        help="fixture directory to keep, e.g. blockchain_tests_engine "
        "(repeatable)",
    )
    args = parser.parse_args()
    keep = set(args.format_dirs)

    index = json.loads((args.src_meta / "index.json").read_text())
    total = len(index["test_cases"])
    cases = [
        case
        for case in index["test_cases"]
        if Path(case["json_path"]).parts[0] in keep
    ]
    if not cases:
        print(f"error: no test cases under {sorted(keep)}", file=sys.stderr)
        return 1

    forks = {case["fork"] for case in cases if case.get("fork")}
    index["test_cases"] = cases
    index["test_count"] = len(cases)
    index["fixture_formats"] = sorted({case["format"] for case in cases})
    index["forks"] = [
        fork for fork in index.get("forks") or [] if fork in forks
    ]
    index["root_hash"] = None

    args.dst_meta.mkdir(parents=True, exist_ok=True)
    for entry in args.src_meta.iterdir():
        if entry.name == "index.json" or entry.name in REPORT_FILES:
            continue
        if entry.is_dir():
            shutil.copytree(
                entry, args.dst_meta / entry.name, dirs_exist_ok=True
            )
        else:
            shutil.copy2(entry, args.dst_meta / entry.name)
    (args.dst_meta / "index.json").write_text(json.dumps(index) + "\n")

    print(
        f"kept {len(cases)} of {total} test cases under {sorted(keep)}; "
        f"formats {index['fixture_formats']}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
