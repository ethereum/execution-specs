"""Test the stateless validation artifacts that the filler builds."""

from unittest.mock import MagicMock, patch

import pytest
from ethereum.stateless.types import deserialize_stateless_output

from execution_testing.base_types import Bytes, Hash
from execution_testing.fixtures.blockchain import (
    FixtureBlockBase,
    FixtureHeader,
)
from execution_testing.forks import BPO_SCENARIOS, Amsterdam, Fork
from execution_testing.test_types import Environment, ExecutionWitness
from execution_testing.test_types.block_access_list import BlockAccessList

from .. import blockchain_stateless
from ..blockchain_stateless import (
    StatelessBlockOptions,
    build_stateless_artifacts,
)

BPO_SCENARIO_FORKS = [
    scenario for scenarios in BPO_SCENARIOS.values() for scenario in scenarios
]


OPTIONS = StatelessBlockOptions(
    skip_validation=False,
    witness_modifiers=(),
    stateless_input_bytes_modifier=None,
    expected_validation_success=None,
    expected_input_decode_failure=False,
)


def build_empty_block(fork: Fork) -> MagicMock:
    """
    Build the stateless artifacts of an empty block at `fork`, and return the
    mock that stands in for the lookup of the fork's stateless code.
    """
    with patch.object(blockchain_stateless, "spec_fork") as spec_fork:
        spec_fork.return_value.has_stateless = False
        artifacts = build_stateless_artifacts(
            options=OPTIONS,
            fork=fork,
            execution_witness=ExecutionWitness(),
            block_rlp=lambda: Bytes(b""),
            block_access_list=None,
            requests_list=None,
            engine_payload_modifier=None,
            chain_id=1,
            block_valid=True,
            run_guest=True,
            transition_tool_validation=None,
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


def validation_without_the_guest(
    *, transition_tool_validation: bool | None, block_valid: bool
) -> bool:
    """
    Build the stateless artifacts of an empty Amsterdam block without running
    the guest, as in benchmark mode with an external transition tool, and
    return the validation result that the output reports.
    """
    header = FixtureHeader.genesis(
        Amsterdam, Environment().set_fork_requirements(Amsterdam), Hash(0)
    )
    block = FixtureBlockBase(
        header=header, txs=[], ommers=[], withdrawals=[]
    ).with_rlp(txs=[])
    artifacts = build_stateless_artifacts(
        options=OPTIONS,
        fork=Amsterdam,
        execution_witness=ExecutionWitness(),
        block_rlp=lambda: block.rlp,
        block_access_list=BlockAccessList(),
        requests_list=[],
        engine_payload_modifier=None,
        chain_id=1,
        block_valid=block_valid,
        run_guest=False,
        transition_tool_validation=transition_tool_validation,
    )
    assert artifacts.stateless_output_bytes is not None
    output = deserialize_stateless_output(artifacts.stateless_output_bytes)
    return output.successful_validation


def test_output_without_the_guest_reports_the_tool_success() -> None:
    """
    Report success when the transition tool says that its witness validates
    the block.
    """
    assert validation_without_the_guest(
        transition_tool_validation=True, block_valid=True
    )


def test_tool_that_does_not_validate_its_witness_fails() -> None:
    """
    Fail to build the artifacts when the transition tool doesn't say if its
    witness validates the block, since nothing else checks the witness.
    """
    with pytest.raises(Exception, match="without `successfulValidation`"):
        validation_without_the_guest(
            transition_tool_validation=None, block_valid=True
        )


def test_tool_rejecting_its_witness_fails_a_valid_block() -> None:
    """
    Fail to build the artifacts of a valid block when the transition tool
    says that its witness doesn't validate it.
    """
    with pytest.raises(AssertionError, match="returned False"):
        validation_without_the_guest(
            transition_tool_validation=False, block_valid=True
        )


def test_output_without_the_guest_reports_the_tool_rejection() -> None:
    """
    Write the rejection of the transition tool in the output of a block that
    is expected to be invalid.
    """
    assert not validation_without_the_guest(
        transition_tool_validation=False, block_valid=False
    )
