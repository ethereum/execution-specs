"""Tests for `assertState`'s canonical-identity check in the reorg consumer."""

from unittest.mock import MagicMock

import pytest

from execution_testing.base_types import Hash
from execution_testing.client_clis import TransitionTool
from execution_testing.fixtures.reorg import (
    AssertStateStep,
    BlockchainEngineReorgFixture,
)
from execution_testing.forks import Cancun
from execution_testing.specs.reorg import ReorgBlock, ReorgTest
from execution_testing.test_types import Alloc

from ..simulators.helpers.exceptions import LoggedError
from ..simulators.helpers.timing import TimingData
from ..simulators.simulator_logic.test_via_reorg import StepRunner


def test_assert_state_rejects_noncanonical_block(
    default_t8n: TransitionTool,
) -> None:
    """`assertState.at` fails when another block holds the label's height."""
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
    eth = MagicMock()
    eth.get_block_by_number.return_value = {"hash": Hash(0xDEAD)}
    runner = StepRunner(fixture, eth, MagicMock(), TimingData("test"), 1.0)
    with pytest.raises(LoggedError, match="expected a1"):
        runner.assert_state(
            "assertState", AssertStateStep(at="a1", accounts={})
        )
