"""Helpers to load tests from JSON files."""

from .fixtures import ALL_FIXTURE_TYPES, Fixture, FixturesFile, FixtureTestItem
from .load_blockchain_tests import BlockchainTestFixture
from .load_state_tests import StateTestFixture
from .load_vm_tests import VmTestFixture

ALL_FIXTURE_TYPES.append(BlockchainTestFixture)
ALL_FIXTURE_TYPES.append(StateTestFixture)
ALL_FIXTURE_TYPES.append(VmTestFixture)

__all__ = ["ALL_FIXTURE_TYPES", "Fixture", "FixturesFile", "FixtureTestItem"]
