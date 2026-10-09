"""Tests for the reorg consumer's handling of a failed head RPC lookup."""

from unittest.mock import MagicMock

import pytest

from execution_testing.client_clis import TransitionTool
from execution_testing.fixtures.reorg import (
    BlockchainEngineReorgFixture,
    ForkchoiceUpdatedStep,
    Outcome,
)
from execution_testing.forks import Cancun
from execution_testing.rpc.rpc_types import JSONRPCError
from execution_testing.specs.reorg import ReorgBlock, ReorgTest
from execution_testing.test_types import Alloc

from ..simulators.helpers.exceptions import LoggedError
from ..simulators.helpers.timing import TimingData
from ..simulators.simulator_logic.test_via_reorg import StepRunner


def runner(
    default_t8n: TransitionTool, eth: MagicMock, engine: MagicMock
) -> StepRunner:
    """A `StepRunner` for a single-block fixture, with stubbed RPC."""
    test = ReorgTest(
        fork=Cancun,
        pre=Alloc(),
        blocks=[ReorgBlock(label="a1")],
        steps=[],
    )
    fixture = test.generate(
        t8n=default_t8n, fixture_format=BlockchainEngineReorgFixture
    ).fixture
    assert isinstance(fixture, BlockchainEngineReorgFixture)
    return StepRunner(fixture, eth, engine, TimingData("test"), 0.0)


def test_head_moved_fails_on_rpc_error(default_t8n: TransitionTool) -> None:
    """
    A `headMoved` check must fail its step when the `latest` lookup errors,
    not be satisfied by it (PR3556-R0020).
    """
    eth = MagicMock()
    eth.get_block_by_number.side_effect = JSONRPCError(-32603, "boom")
    engine = MagicMock()
    step_runner = runner(default_t8n, eth, engine)
    response = MagicMock()
    response.payload_status.status.value = "SYNCING"
    response.payload_status.latest_valid_hash = None
    response.payload_status.validation_error = None
    response.payload_id = None
    engine.forkchoice_updated.return_value = response
    step = ForkchoiceUpdatedStep(
        head="a1",
        version=3,
        expect=[
            Outcome(
                id="syncing",
                status="SYNCING",
                latest_valid_hash="null",
                head_moved=False,
            )
        ],
    )
    with pytest.raises(LoggedError, match="-32603"):
        step_runner.forkchoice_updated("fcu", step, 0)
