"""Tests for the reorg consumer's `sendRawTransaction` step."""

from typing import List
from unittest.mock import MagicMock, patch

import pytest

from execution_testing.base_types import Bytes
from execution_testing.client_clis import TransitionTool
from execution_testing.fixtures.reorg import (
    BlockchainEngineReorgFixture,
    SendRawTransactionStep,
    TxRef,
)
from execution_testing.forks import Cancun
from execution_testing.rpc import EthRPC
from execution_testing.specs.reorg import ReorgBlock, ReorgTest
from execution_testing.test_types import Alloc

from ..simulators.helpers.exceptions import LoggedError
from ..simulators.helpers.timing import TimingData
from ..simulators.simulator_logic.test_via_reorg import StepRunner


@pytest.mark.parametrize(
    "expect,passes", [(["rejected"], True), (["accepted"], False)]
)
def test_send_raw_transaction_reports_a_client_rejection(
    default_t8n: TransitionTool, expect: List[str], passes: bool
) -> None:
    """A JSON-RPC error from the client is the `rejected` result."""
    test = ReorgTest(
        fork=Cancun, pre=Alloc(), blocks=[ReorgBlock(label="a1")], steps=[]
    )
    fixture = test.generate(
        t8n=default_t8n, fixture_format=BlockchainEngineReorgFixture
    ).fixture
    assert isinstance(fixture, BlockchainEngineReorgFixture)
    eth = EthRPC("http://localhost:8545")
    step_runner = StepRunner(
        fixture, eth, MagicMock(), TimingData("test"), 0.0
    )
    step_runner.tx_rlp = MagicMock(return_value=Bytes(b"\x01"))  # type: ignore[method-assign]
    reply = MagicMock()
    reply.json.return_value = {
        "jsonrpc": "2.0",
        "id": 1,
        "error": {"code": -32000, "message": "already known"},
    }
    step = SendRawTransactionStep(tx=TxRef(block="a1"), expect=expect)
    with patch.object(eth.session, "post", return_value=reply):
        if passes:
            step_runner.send_raw_transaction("send", step)
            assert step_runner.matched[-1] == "send:rejected"
        else:
            with pytest.raises(LoggedError, match="rejected .-32000"):
                step_runner.send_raw_transaction("send", step)
