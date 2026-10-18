"""Tests for the reorg consumer's `assertLogs` block-identity check."""

from typing import List
from unittest.mock import MagicMock

import pytest

from execution_testing.client_clis import TransitionTool
from execution_testing.fixtures.reorg import (
    AssertLogsStep,
    BlockchainEngineReorgFixture,
)
from execution_testing.forks import Cancun
from execution_testing.specs.reorg import ReorgBlock, ReorgTest
from execution_testing.test_types import Alloc

from ..simulators.helpers.exceptions import LoggedError
from ..simulators.helpers.timing import TimingData
from ..simulators.simulator_logic.test_via_reorg import (
    BoundPayload,
    StepRunner,
)


@pytest.mark.parametrize(
    "returned,expected,passes",
    [
        (["a2", "a1"], ["a1", "a2"], True),
        (["a1", "a1"], ["a1"], False),
        (["a1"], ["a1", "a1"], False),
        (["a2"], ["a1"], False),
    ],
    ids=["any_order", "extra_log", "missing_log", "wrong_block"],
)
def test_assert_logs_counts_logs_per_block(
    default_t8n: TransitionTool,
    returned: List[str],
    expected: List[str],
    passes: bool,
) -> None:
    """`assertLogs` wants exactly one log per listed block, in any order."""
    test = ReorgTest(
        fork=Cancun,
        pre=Alloc(),
        blocks=[ReorgBlock(label="a1"), ReorgBlock(label="a2")],
        steps=[],
    )
    fixture = test.generate(
        t8n=default_t8n, fixture_format=BlockchainEngineReorgFixture
    ).fixture
    assert isinstance(fixture, BlockchainEngineReorgFixture)
    eth = MagicMock()
    eth.post_request.return_value.result_or_raise.return_value = [
        {"blockHash": str(fixture.resolve(label))} for label in returned
    ]
    step_runner = StepRunner(
        fixture, eth, MagicMock(), TimingData("test"), 0.0
    )
    step = AssertLogsStep(blocks=expected)
    if passes:
        step_runner.assert_logs("logs", step)
    else:
        with pytest.raises(LoggedError, match="eth_getLogs returned"):
            step_runner.assert_logs("logs", step)


def test_assert_logs_accepts_a_hash_bound_to_two_labels(
    default_t8n: TransitionTool,
) -> None:
    """
    A label whose hash was later rebound to a second label must still match
    `assertLogs` (PR3556-R0021): the reverse `labels_by_hash` lookup only
    keeps the latest bind, but both labels identify the same block.
    """
    test = ReorgTest(
        fork=Cancun, pre=Alloc(), blocks=[ReorgBlock(label="a1")], steps=[]
    )
    fixture = test.generate(
        t8n=default_t8n, fixture_format=BlockchainEngineReorgFixture
    ).fixture
    assert isinstance(fixture, BlockchainEngineReorgFixture)
    eth = MagicMock()
    step_runner = StepRunner(
        fixture, eth, MagicMock(), TimingData("test"), 0.0
    )
    payload = fixture.blocks["a1"].payload.params[0]
    step_runner.bound["p"] = BoundPayload(
        payload=payload,
        versioned_hashes=[],
        parent_beacon_block_root=None,
        execution_requests=None,
        label_parent="genesis",
    )
    step_runner.labels_by_hash[payload.block_hash] = "q"  # a later bind
    eth.post_request.return_value.result_or_raise.return_value = [
        {"blockHash": str(payload.block_hash)}
    ]
    step_runner.assert_logs("logs", AssertLogsStep(blocks=["p"]))
