"""Tests for `assertState`'s canonical-identity check in the reorg consumer."""

from typing import Any, Dict

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


class FakeEthRPC:
    """Stub `EthRPC` returning a fixed, wrong block hash."""

    def __init__(self, block_hash: Hash) -> None:
        """Store the hash `eth_getBlockByNumber` will report."""
        self.block_hash = block_hash

    def get_block_by_number(self, _number: Any) -> Dict[str, Any]:
        """Return a block whose hash never matches the fixture's block."""
        return {"hash": self.block_hash}


def test_assert_state_rejects_noncanonical_block(
    default_t8n: TransitionTool,
) -> None:
    """
    `assertState.at` fails clearly when the block at that height is not
    the labeled block: e.g. it was superseded by a sibling reorg.
    """
    test = ReorgTest(
        fork=Cancun,
        pre=Alloc(),
        blocks=[ReorgBlock(label="a1")],
        steps=[],
    )
    result = test.generate(
        t8n=default_t8n, fixture_format=BlockchainEngineReorgFixture
    )
    fixture = result.fixture
    assert isinstance(fixture, BlockchainEngineReorgFixture)

    runner = StepRunner(
        fixture,
        FakeEthRPC(Hash(0xDEAD)),  # type: ignore[arg-type]
        None,  # type: ignore[arg-type]
        TimingData("test"),
        1.0,
    )
    with pytest.raises(LoggedError, match="not canonical"):
        runner.assert_state(
            "assertState", AssertStateStep(at="a1", accounts={})
        )
