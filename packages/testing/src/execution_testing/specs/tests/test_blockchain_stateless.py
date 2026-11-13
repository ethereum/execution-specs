"""Test which forks the filler builds stateless validation artifacts for."""

from unittest.mock import MagicMock, patch

import pytest

from execution_testing.base_types import Bytes
from execution_testing.forks import BPO_SCENARIOS, Amsterdam, Fork
from execution_testing.test_types import ExecutionWitness

from .. import blockchain_stateless
from ..blockchain_stateless import (
    StatelessBlockOptions,
    build_stateless_artifacts,
)

BPO_SCENARIO_FORKS = [
    scenario for scenarios in BPO_SCENARIOS.values() for scenario in scenarios
]


def build_empty_block(fork: Fork) -> MagicMock:
    """
    Build the stateless artifacts of an empty block at `fork`, and return the
    mock that stands in for the lookup of the fork's stateless code.
    """
    options = StatelessBlockOptions(
        skip_validation=False,
        witness_modifiers=(),
        stateless_input_bytes_modifier=None,
        expected_validation_success=None,
        expected_input_decode_failure=False,
    )
    with patch.object(blockchain_stateless, "spec_fork") as spec_fork:
        spec_fork.return_value.has_stateless = False
        artifacts = build_stateless_artifacts(
            options=options,
            fork=fork,
            execution_witness=ExecutionWitness(),
            block_rlp=Bytes(b""),
            block_access_list=None,
            requests_list=None,
            engine_payload_modifier=None,
            chain_id=1,
            block_valid=True,
            run_guest=True,
        )
    assert artifacts.stateless_input_bytes is None
    return spec_fork


@pytest.mark.parametrize("fork", BPO_SCENARIO_FORKS, ids=lambda f: f.name())
def test_bpo_scenario_fork_gets_no_stateless_input(fork: Fork) -> None:
    """
    Skip a BPO scenario fork, which the transition tool runs on its
    ancestor's spec with a blob schedule that the guest doesn't have.
    """
    build_empty_block(fork).assert_not_called()


def test_fork_with_its_own_spec_looks_up_its_stateless_code() -> None:
    """Look up the stateless code of a fork that runs on its own spec."""
    build_empty_block(Amsterdam).assert_called_once_with(Amsterdam)
