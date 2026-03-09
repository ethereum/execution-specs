"""Tests related to json infrastructure."""

from typing import Dict

from .hardfork import TestHardfork

FORKS: Dict[str, TestHardfork] = {
    fork.json_test_name: fork for fork in TestHardfork.discover()
}
