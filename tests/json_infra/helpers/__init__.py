"""Helpers to load tests from JSON files."""

from typing import List, Type

from .fixtures import Fixture
from .load_blockchain_tests import BlockchainTestFixture
from .load_state_tests import StateTestFixture

ALL_FIXTURE_TYPES: List[Type[Fixture]] = [
    BlockchainTestFixture,
    StateTestFixture,
]

__all__ = ["ALL_FIXTURE_TYPES", "Fixture"]
