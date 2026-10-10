"""Tests for the reorg consumer's `headMoved` observation."""

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


@pytest.mark.parametrize(
    "latest,error",
    [
        ("genesis", None),
        ("a1", "matches none"),
        ("error", "-32603"),
        ("null", "returned no block"),
    ],
)
def test_head_moved_false_needs_an_observed_unmoved_head(
    default_t8n: TransitionTool, latest: str, error: str | None
) -> None:
    """
    ``headMoved=False`` passes only when ``latest`` is observed to be
    another block; a failed or empty lookup fails the step.
    """
    eth = MagicMock()
    engine = MagicMock()
    step_runner = runner(default_t8n, eth, engine)
    if latest == "error":
        eth.get_block_by_number.side_effect = JSONRPCError(-32603, "boom")
    elif latest == "null":
        eth.get_block_by_number.return_value = None
    else:
        eth.get_block_by_number.return_value = {
            "hash": step_runner.resolve(latest)
        }
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
    if error is None:
        step_runner.forkchoice_updated("fcu", step, 0)
        assert step_runner.matched[-1].endswith(":syncing")
    else:
        with pytest.raises(LoggedError, match=error):
            step_runner.forkchoice_updated("fcu", step, 0)
