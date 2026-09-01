"""
Test the execute genesis header against the fill genesis header.

``execute``/``fill-stateful`` build the client genesis with
``build_genesis_header`` while ``fill`` uses ``FixtureHeader.genesis``;
both hand-populate fork-conditional header fields, so a fork that
extends the header must extend both. Feeding them equivalent inputs and
comparing the result catches one-sided drift.
"""

from typing import Any, Dict, List

import pytest

from execution_testing.base_types import to_json
from execution_testing.cli.pytest_commands.plugins.execute.rpc.hive import (
    build_genesis_header,
)
from execution_testing.fixtures.blockchain import FixtureHeader
from execution_testing.forks import (
    Fork,
    get_deployed_forks,
    get_development_forks,
)
from execution_testing.specs.blockchain import GENESIS_ENVIRONMENT_DEFAULTS
from execution_testing.test_types import Environment

# ``build_genesis_header`` pins these two values instead of taking them
# from the environment; mirror them so both builders receive equivalent
# inputs and any difference is a structural one.
EXECUTE_GENESIS_ENVIRONMENT: Dict[str, Any] = GENESIS_ENVIRONMENT_DEFAULTS | {
    "timestamp": 1,
    "difficulty": 0x20000,
}

FORKS: List[Fork] = get_deployed_forks() + get_development_forks()


@pytest.mark.parametrize("fork", FORKS, ids=lambda fork: fork.name())
def test_execute_genesis_matches_fill_genesis(fork: Fork) -> None:
    """The two genesis builders must produce identical headers."""
    pre_alloc, execute_genesis = build_genesis_header(fork)
    env = Environment(**EXECUTE_GENESIS_ENVIRONMENT).set_fork_requirements(
        fork
    )
    fill_genesis = FixtureHeader.genesis(fork, env, pre_alloc.state_root())
    assert to_json(execute_genesis) == to_json(fill_genesis)
    assert execute_genesis.block_hash == fill_genesis.block_hash
