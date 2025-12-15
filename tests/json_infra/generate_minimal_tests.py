"""
Generate a minimal set of json_infra tests that maintain full code coverage.

This script runs all json_infra tests with coverage tracking, then uses the
minimize-tests tool to compute the smallest subset of tests that cover all
the same lines.

Usage:
    python generate_minimal_tests.py [--output FILE]

The minimal test list is written to minimal_tests.txt by default, which can
then be used with pytest's --tests-file option.
"""

import argparse
import subprocess
import sys
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(
        description="Generate minimal test set for json_infra tests"
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path(__file__).parent / "minimal_tests.txt",
        help="Output file for minimal test list (default: minimal_tests.txt)",
    )
    parser.add_argument(
        "--coverage-file",
        type=Path,
        default=Path.cwd() / ".coverage",
        help="Coverage data file (default: .coverage)",
    )
    args = parser.parse_args()

    print("=" * 70)
    print("Step 1: Running all json_infra tests with coverage tracking...")
    print("=" * 70)

    # Run all json_infra tests with coverage and test context tracking
    pytest_cmd = [
        "pytest",
        "-m", "not slow",
        "-n", "auto",
        "--maxprocesses", "6",
        "--dist=loadfile",
        "--cov=ethereum",
        "--cov-context=test",
        "--cov-report=",  # No report output
        "--basetemp=.pytest_cache/tmp",
        "tests/json_infra",
    ]

    print(f"Running: {' '.join(pytest_cmd)}")
    result = subprocess.run(pytest_cmd, check=False)

    if result.returncode != 0:
        print("\nWarning: Some tests failed, but continuing with coverage analysis...")

    if not args.coverage_file.exists():
        print(f"\nError: Coverage file not found: {args.coverage_file}")
        print("Make sure pytest-cov generated the coverage data.")
        return 1

    print("\n" + "=" * 70)
    print("Step 2: Computing minimal test set with minimize-tests...")
    print("=" * 70)

    # Run minimize-tests to generate minimal set
    minimize_cmd = ["minimize-tests", str(args.coverage_file)]

    print(f"Running: {' '.join(minimize_cmd)}")

    with open(args.output, "w") as output_file:
        result = subprocess.run(
            minimize_cmd,
            stdout=output_file,
            stderr=sys.stderr,
            check=True,
        )

    print(f"\n✓ Minimal test list written to: {args.output}")

    # Count the tests
    with open(args.output) as f:
        test_count = sum(1 for line in f if line.strip())

    print(f"✓ Minimal test set contains {test_count} tests")

    print("\n" + "=" * 70)
    print("Next steps:")
    print("=" * 70)
    print(f"1. Review the minimal test list: {args.output}")
    print("2. Run minimal tests:")
    print(f"   pytest --tests-file={args.output} tests/json_infra")
    print("3. Verify coverage is maintained:")
    print(f"   pytest --tests-file={args.output} --cov=ethereum --cov-report=term tests/json_infra")
    print("4. Commit the minimal test list to version control")

    return 0


if __name__ == "__main__":
    sys.exit(main())
