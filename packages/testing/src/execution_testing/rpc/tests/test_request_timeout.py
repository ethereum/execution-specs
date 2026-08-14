"""Test the HTTP request timeout and retry behavior of `BaseRPC` clients."""

from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import pytest
import requests

from execution_testing.base_types import Hash
from execution_testing.cli.pytest_commands.plugins.execute.rpc.chain_builder_eth_rpc import (  # noqa: E501
    ChainBuilderEthRPC,
)
from execution_testing.forks import Cancun
from execution_testing.rpc import (
    DEFAULT_REQUEST_TIMEOUT,
    EthRPC,
    LiveBlock,
    RPCCall,
    SendTransactionExceptionError,
)
from execution_testing.rpc.rpc_types import PayloadStatusEnum


def response_mock(
    json_value: dict[str, Any] | list[dict[str, Any]] | None = None,
) -> MagicMock:
    """Return a mock of a successful JSON-RPC HTTP response."""
    if json_value is None:
        json_value = {"jsonrpc": "2.0", "id": 1, "result": "0x0"}
    response = MagicMock()
    response.json.return_value = json_value
    return response


def duplicate_error_response() -> MagicMock:
    """Return a mock duplicate-transaction JSON-RPC error response."""
    return response_mock(
        {
            "jsonrpc": "2.0",
            "id": 1,
            "error": {"code": -32000, "message": "already known"},
        }
    )


def transaction_mock(index: int = 0) -> Any:
    """Return a mock signed transaction for send tests."""
    transaction: Any = MagicMock()
    transaction.hash = Hash(index + 1)
    transaction.rlp.return_value = bytes([index + 1])
    transaction.metadata_string.return_value = f"tx-{index}"
    return transaction


def test_default_timeout_is_applied() -> None:
    """Requests carry the default timeout when none is given."""
    rpc = EthRPC("http://localhost:8545")
    with patch.object(
        rpc.session, "post", return_value=response_mock()
    ) as post:
        rpc.post_request(request=RPCCall(method="blockNumber"))
    assert post.call_args.kwargs["timeout"] == DEFAULT_REQUEST_TIMEOUT


def test_per_request_timeout_overrides_default() -> None:
    """An explicit per-request timeout takes precedence."""
    rpc = EthRPC("http://localhost:8545")
    with patch.object(
        rpc.session, "post", return_value=response_mock()
    ) as post:
        rpc.post_request(request=RPCCall(method="blockNumber"), timeout=7)
    assert post.call_args.kwargs["timeout"] == 7


def test_constructor_timeout_overrides_default() -> None:
    """A timeout given at construction replaces the default."""
    rpc = EthRPC("http://localhost:8545", request_timeout=5.0)
    with patch.object(
        rpc.session, "post", return_value=response_mock()
    ) as post:
        rpc.post_request(request=RPCCall(method="blockNumber"))
    assert post.call_args.kwargs["timeout"] == 5.0


def test_constructor_timeout_none_disables_timeout() -> None:
    """`request_timeout=None` restores unbounded requests."""
    rpc = EthRPC("http://localhost:8545", request_timeout=None)
    with patch.object(
        rpc.session, "post", return_value=response_mock()
    ) as post:
        rpc.post_request(request=RPCCall(method="blockNumber"))
    assert post.call_args.kwargs["timeout"] is None


def test_read_timeout_is_retried() -> None:
    """A read timeout is retried on a fresh request."""
    rpc = EthRPC("http://localhost:8545")
    with (
        patch("time.sleep"),
        patch.object(
            rpc.session,
            "post",
            side_effect=[
                requests.ReadTimeout("read timed out"),
                response_mock(),
            ],
        ) as post,
    ):
        rpc.post_request(request=RPCCall(method="blockNumber"))
    assert post.call_count == 2


def test_batch_request_default_timeout_is_applied() -> None:
    """Batch requests carry the default timeout as well."""
    rpc = EthRPC("http://localhost:8545")
    batch_response = response_mock(
        [{"jsonrpc": "2.0", "id": 1, "result": "0x0"}]
    )
    with patch.object(
        rpc.session, "post", return_value=batch_response
    ) as post:
        rpc.post_batch_request(calls=[RPCCall(method="blockNumber")])
    assert post.call_args.kwargs["timeout"] == DEFAULT_REQUEST_TIMEOUT


def test_chain_builder_accepts_request_timeout(tmp_path: Path) -> None:
    """`ChainBuilderEthRPC` forwards `request_timeout` to the base client."""
    engine_rpc: Any = MagicMock()
    engine_rpc.forkchoice_updated.return_value.payload_status.status = (
        PayloadStatusEnum.VALID
    )
    head_block = LiveBlock.model_validate(
        {
            "number": "0x0",
            "timestamp": "0x0",
            "hash": f"0x{'00' * 32}",
            "stateRoot": f"0x{'00' * 32}",
            "gasLimit": "0x1c9c380",
            "miner": f"0x{'00' * 20}",
        }
    )
    with patch.object(
        ChainBuilderEthRPC, "get_block_by_number", return_value=head_block
    ):
        rpc = ChainBuilderEthRPC(
            rpc_endpoint="http://localhost:8545",
            fork=Cancun,
            engine_rpc=engine_rpc,
            session_temp_folder=tmp_path,
            get_payload_wait_time=1,
            request_timeout=5.0,
        )
    assert rpc.request_timeout == 5.0


def test_resent_transaction_duplicate_error_is_success() -> None:
    """A re-sent transaction answered "already known" counts as sent."""
    rpc = EthRPC("http://localhost:8545")
    transaction = transaction_mock()
    with (
        patch("time.sleep"),
        patch.object(
            rpc.session,
            "post",
            side_effect=[
                requests.ReadTimeout("read timed out"),
                duplicate_error_response(),
            ],
        ) as post,
        patch.object(
            EthRPC, "get_transaction_by_hash", return_value=MagicMock()
        ) as get_transaction,
    ):
        result = rpc.send_transaction(transaction)
    assert result == transaction.hash
    assert post.call_count == 2
    get_transaction.assert_called_once_with(transaction.hash)


def test_send_transaction_error_raises_when_transaction_unknown() -> None:
    """A send error for a transaction the client does not know raises."""
    rpc = EthRPC("http://localhost:8545")
    transaction = transaction_mock()
    with (
        patch.object(
            rpc.session, "post", return_value=duplicate_error_response()
        ),
        patch.object(EthRPC, "get_transaction_by_hash", return_value=None),
        pytest.raises(SendTransactionExceptionError),
    ):
        rpc.send_transaction(transaction)


def test_send_transactions_recover_duplicate_batch_items() -> None:
    """Duplicate errors in a re-sent batch count as sent per item."""
    rpc = EthRPC("http://localhost:8545")
    transactions = [transaction_mock(0), transaction_mock(1)]
    batch_response = response_mock(
        [
            {
                "jsonrpc": "2.0",
                "id": "tx-0",
                "error": {"code": -32000, "message": "already known"},
            },
            {
                "jsonrpc": "2.0",
                "id": "tx-1",
                "result": f"{transactions[1].hash}",
            },
        ]
    )
    with (
        patch.object(rpc.session, "post", return_value=batch_response),
        patch.object(
            EthRPC, "get_transaction_by_hash", return_value=MagicMock()
        ) as get_transaction,
    ):
        results = rpc.send_transactions(transactions)
    assert results == [tx.hash for tx in transactions]
    get_transaction.assert_called_once_with(transactions[0].hash)
