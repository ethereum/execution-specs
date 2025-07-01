#!/usr/bin/env python3
"""
BAL test runner - executes all BAL tests in proper order.
"""

import sys
import pytest
from pathlib import Path


def main():
    """Run all BAL tests."""
    test_dir = Path(__file__).parent
    
    # Test files in execution order
    test_files = [
        "test_bal_core.py",
        "test_bal_ssz.py", 
        "test_bal_integration.py",
        "test_block_access_list.py",
    ]
    
    # Optional mainnet tests
    optional_files = [
        "test_eip7928_mainnet_data.py",
        "test_eip7928_state_integration.py",
    ]
    
    # Check which files exist
    existing_files = []
    for test_file in test_files:
        if (test_dir / test_file).exists():
            existing_files.append(str(test_dir / test_file))
    
    for test_file in optional_files:
        if (test_dir / test_file).exists():
            existing_files.append(str(test_dir / test_file))
    
    if not existing_files:
        print("No BAL test files found")
        return 1
    
    print(f"Running BAL tests: {[Path(f).name for f in existing_files]}")
    
    # Run tests with verbose output
    return pytest.main(["-v"] + existing_files)


if __name__ == "__main__":
    sys.exit(main())