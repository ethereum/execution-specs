#!/usr/bin/env python3
"""
BAL test runner - executes all BAL tests using pytest.
"""

import sys
from pathlib import Path

import pytest


def main():
    """Run all BAL tests with pytest."""
    test_dir = Path(__file__).parent
    
    # Essential BAL test files
    test_files = [
        "test_bal_completeness.py",
        "test_bal_fixes.py",
    ]
    
    # Build full paths
    test_paths = []
    for test_file in test_files:
        test_path = test_dir / test_file
        if test_path.exists():
            test_paths.append(str(test_path))
    
    if not test_paths:
        print("No BAL test files found")
        return 1
    
    print(f"Running BAL tests: {[Path(f).name for f in test_paths]}")
    
    # Run tests with verbose output and proper pytest args
    pytest_args = [
        "-v",  # Verbose output
        "--tb=short",  # Short traceback format
        "-x",  # Stop on first failure
        "--confcutdir=tests/osaka",  # Use local conftest only
    ] + test_paths
    
    return pytest.main(pytest_args)


if __name__ == "__main__":
    sys.exit(main())