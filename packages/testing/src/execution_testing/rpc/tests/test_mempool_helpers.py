"""Test the type-agnostic transaction lookups of `EthRPC`."""

from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from execution_testing.base_types import Hash
from execution_testing.rpc import EthRPC


def response_mock(result: Any) -> MagicMock:
    """Return a mock of a successful JSON-RPC HTTP response."""
    response = MagicMock()
    response.json.return_value = {"jsonrpc": "2.0", "id": 1, "result": result}
    return response


@pytest.mark.parametrize(
    "result,known",
    [
        pytest.param(None, False, id="unknown"),
        # A frame transaction the response model cannot parse.
        pytest.param({"type": "0x6", "frames": []}, True, id="unparsable"),
    ],
)
def test_transaction_known(result: Any, known: bool) -> None:
    """A lookup only checks the client's answer for `null`."""
    rpc = EthRPC("http://localhost:8545")
    with patch.object(rpc.session, "post", return_value=response_mock(result)):
        assert rpc.transaction_known(Hash(1)) is known


def test_wait_for_receipts_polls_until_all_are_included() -> None:
    """Receipts are polled until every one is found, in input order."""
    rpc = EthRPC("http://localhost:8545", poll_interval=0)
    first, second = Hash(1), Hash(2)
    polls = [[None, {"id": 2}], [{"id": 1}]]
    with (
        patch.object(
            rpc, "get_transaction_receipts", side_effect=polls
        ) as get_receipts,
        patch.object(rpc, "pending_transactions_handler") as handler,
    ):
        receipts = rpc.wait_for_receipts([first, second])
    assert receipts == [{"id": 1}, {"id": 2}]
    assert [c.args[0] for c in get_receipts.call_args_list] == [
        [first, second],
        [first],
    ]
    assert handler.call_count == 1


def test_wait_for_receipts_times_out() -> None:
    """A transaction never included raises after the wait timeout."""
    rpc = EthRPC(
        "http://localhost:8545", transaction_wait_timeout=0, poll_interval=0
    )
    with (
        patch.object(rpc, "get_transaction_receipts", return_value=[None]),
        patch("time.time", side_effect=[0, 1]),
        pytest.raises(Exception, match="not included in a block"),
    ):
        rpc.wait_for_receipts([Hash(1)])
