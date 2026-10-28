"""
Pass a reorg fixture's ``minReorgDepth`` to the client.

Registered after ``single_test_client``, whose ``environment`` fixture this
module extends: pytest prefers the most recently registered plugin, so a
definition in the simulator's conftest would be shadowed.
"""

import pytest

from execution_testing.fixtures import BlockchainEngineReorgFixture

MAX_REORG_DEPTH_VARIABLE = "HIVE_ENGINE_MAX_REORG_DEPTH"
"""Client variable carrying the reorg depth the client must serve."""


@pytest.fixture(scope="function")
def environment(
    environment: dict, fixture: BlockchainEngineReorgFixture
) -> dict:
    """Extend the client environment with the fixture's reorg-depth cap."""
    if fixture.min_reorg_depth is None:
        return environment
    return {
        **environment,
        MAX_REORG_DEPTH_VARIABLE: str(int(fixture.min_reorg_depth)),
    }
