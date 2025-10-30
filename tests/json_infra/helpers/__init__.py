"""Helpers to load tests from JSON files."""

import json
from functools import lru_cache
from typing import Dict


@lru_cache(maxsize=100)
def load_json_file(test_file: str) -> Dict:
    """
    Load and cache a JSON fixture file.

    Uses LRU (Least Recently Used) cache to avoid re-reading the same
    JSON files multiple times during test execution. This is especially
    important when running tests in parallel, as multiple test cases
    from the same file would otherwise cause redundant file I/O.

    The cache is bounded to 100 files, which provides a good balance
    between memory usage and performance. When the cache is full, the
    least recently accessed file will be evicted.

    Args:
        test_file: Path to the JSON fixture file

    Returns:
        Parsed JSON data as a dictionary

    """
    with open(test_file, "r") as fp:
        return json.load(fp)
