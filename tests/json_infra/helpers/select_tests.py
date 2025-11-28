"""
Targeted test selection based on changed files.

This module reads a list of changed files and determines which fork
folders have been modified, then provides functions to generate targeted
pytest commands.
"""

from pathlib import Path
from typing import List

from .. import TestHardfork

FORK_MAPPING = {
    fork.short_name: fork.json_test_name for fork in TestHardfork.discover()
}


def extract_affected_forks(
    repo_root: Path, files_path: str, optimized: bool
) -> List[str]:
    """
    Extract fork names from changed file paths read from disk.

    Args:
        repo_root: Root directory of the repository config.
        files_path: Path to file containing changed file paths
        (one per line)
        optimized: If optimized tests are being run.

    Returns:
        List of fork json_test_names that have been affected

    """
    all_forks = [fork.json_test_name for fork in TestHardfork.discover()]
    # Read changed files from disk
    changed_files_file = Path(files_path)
    if not changed_files_file.exists():
        print(f"File list file {files_path} does not exist or is empty!!")
        return all_forks

    with open(changed_files_file, "r") as f:
        changed_files = [line.strip() for line in f if line.strip()]

    # Extract affected forks
    affected_forks = set()

    for file_path_str in changed_files:
        if not file_path_str or file_path_str.startswith("#"):
            # Skip empty lines and comments
            continue

        try:
            # Normalize the path
            file_path = Path(file_path_str)

            # Convert absolute paths to relative
            if file_path.is_absolute():
                try:
                    file_path = file_path.relative_to(repo_root)
                except ValueError:
                    # Path is outside repo, skip it
                    continue

        except (TypeError, ValueError, OSError):
            # Skip invalid paths
            continue

        if file_path.is_relative_to("tests/json_infra/"):
            # Run all forks if something changes in the test
            # framework
            return all_forks
        if file_path.is_relative_to("src/ethereum_spec_tools/evm_tools"):
            # Run all forks if something changes in the evm
            # tools
            return all_forks
        if optimized and file_path.is_relative_to("src/ethereum_optimized"):
            # Run all forks if something changes in the optimized tools and
            # while running optimized environment.
            return all_forks
        if file_path.is_relative_to("src/ethereum/"):
            parts = Path(file_path).parts
            if len(parts) < 4 or parts[2] != "forks":
                # Run all tests if something changes in the
                # non fork-specific part of src/ethereum
                return all_forks

            # Run tests for specific forks
            fork_short_name = parts[3]
            fork_json_name = FORK_MAPPING.get(fork_short_name)
            if fork_json_name:
                affected_forks.add(fork_json_name)

    return list(affected_forks)
