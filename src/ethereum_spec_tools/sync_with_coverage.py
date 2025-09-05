#!/usr/bin/env python3
"""
Script that runs live coverage of execution-specs while syncing mainnet blocks,
and finds out blocks that hit code paths not covered by the baseline
(json_infra tests).

This script:
1. Generates a Baseline coverage by running json_infra tests if coverage.xml
doesn't exist
2. Converts coverage.xml to baseline_coverage.json if needed
3. Runs slipcover along with the sync tool

To be able to pause/run from a midpoint, `persist` needs to work.
If state is persisted as a part of the sync tool, the syncing (and coverage)
continues from that the last persisted state.
"""

import subprocess
import sys
import json
from pathlib import Path


def run_command(cmd, description):
    print(f"Running: {description}")
    print(f"Command: {' '.join(cmd) if isinstance(cmd, list) else cmd}")

    result = subprocess.run(
        cmd,
        shell=isinstance(cmd, str),
        check=True,
        text=True
    )
    print(f"✅ {description} completed successfully")
    return result


def check_file_exists(filepath):
    exists = Path(filepath).exists()
    status = "✅ Found" if exists else "❌ Missing"
    print(f"{status}: {filepath}")
    return exists


def main():
    print("Starting coverage collection workflow...")
    print("=" * 50)

    # Check baseline coverage
    print("\nStep 1: Checking for Baseline coverage (baseline_coverage.json)")
    if check_file_exists("baseline_coverage.json"):
        print("✅ Baseline coverage already exists, "
              "skipping baseline generation")
    else:
        # substep: check if coverage.xml exists in .tox directory
        print("\nStep 1a: Checking for coverage.xml")
        coverage_xml_path = ".tox/coverage.xml"
        if not check_file_exists(coverage_xml_path):
            print("\n🔧 Running tox to generate coverage.xml...")
            run_command(["tox", "-e", "json_infra"], "tox -e json_infra")

            # Verify coverage.xml was created
            if not check_file_exists(coverage_xml_path):
                print("❌ coverage.xml was not created by tox command")
                sys.exit(1)
        else:
            print("✅ coverage.xml already exists in .tox/, skipping tox")

        # substep: convert coverage.xml to baseline_coverage.json
        print("\nStep 1b: Converting coverage.xml to baseline_coverage.json")

        run_command(
            ["python", "src/ethereum_spec_tools/get_baseline_cov.py"],
            "Converting coverage.xml to baseline_coverage.json"
        )

        # Verify baseline_coverage.json was created
        if not check_file_exists("baseline_coverage.json"):
            print("❌ baseline_coverage.json was not created")
            sys.exit(1)

    # Run slipcover
    # TODO: run with persist when that works
    print("\nStep 2: Running slipcover with sync tool")
    slipcover_cmd = [
        "python", "-m", "slipcover",
        "--source", "src/ethereum/",
        "src/ethereum_spec_tools/sync_slipcover.py"
    ]

    print("\nStarting slipcover coverage collection...")

    try:
        result = subprocess.run(slipcover_cmd, text=True)

        if result.returncode == 0:
            print("\n✅ Slipcover completed successfully")
        elif result.returncode == 130:  # Ctrl+C
            print("\n⚠️  Slipcover interrupted by user (Ctrl+C)")
        else:
            print(f"\n❌ Slipcover exited with code {result.returncode}")

    except KeyboardInterrupt:
        print("\n⚠️  Process interrupted by user")

    # Check output files
    print("\nStep 3: Checking output files")
    if check_file_exists("coverage_diff.json"):
        try:
            with open("coverage_diff.json", 'r') as f:
                data = json.load(f)
                entries_count = len(data) if isinstance(data, list) else 0
                print(f"Contains {entries_count} coverage difference entries")
        except Exception as e:
            print(f"⚠️ Could not read coverage_diff.json: {e}")

    print("=" * 50)


if __name__ == "__main__":
    main()
