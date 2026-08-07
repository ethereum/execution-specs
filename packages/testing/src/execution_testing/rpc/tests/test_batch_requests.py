"""Test the batch request chunking of `BaseRPC` clients."""

from typing import Any, Iterator
from unittest.mock import MagicMock, patch

import pytest

from execution_testing.base_types import Hash
from execution_testing.rpc import EthRPC, RPCCall


def echo_batch_response(*_args: Any, **kwargs: Any) -> MagicMock:
    """Return a mock batch response echoing each request id as its result."""
    response = MagicMock()
    response.json.return_value = [
        {"jsonrpc": "2.0", "id": request["id"], "result": hex(request["id"])}
        for request in kwargs["json"]
    ]
    return response


@pytest.fixture
def max_batch_size() -> int | None:
    """Batch size cap of the client under test; `None` uses the default."""
    return None


@pytest.fixture
def rpc(max_batch_size: int | None) -> EthRPC:
    """Return an `eth` RPC client pointed at a local endpoint."""
    return EthRPC("http://localhost:8545", max_batch_size=max_batch_size)


@pytest.fixture
def post(rpc: EthRPC) -> Iterator[MagicMock]:
    """Patch the client's HTTP POST to echo back every batched call."""
    with patch.object(
        rpc.session, "post", side_effect=echo_batch_response
    ) as post_mock:
        yield post_mock


@pytest.mark.parametrize("max_batch_size", [2])
def test_batch_request_is_chunked(rpc: EthRPC, post: MagicMock) -> None:
    """Calls beyond `max_batch_size` are split over several requests."""
    calls = [RPCCall(method="blockNumber") for _ in range(5)]
    responses = rpc.post_batch_request(calls=calls)
    chunk_sizes = [len(c.kwargs["json"]) for c in post.call_args_list]
    assert chunk_sizes == [2, 2, 1]
    assert [r.result for r in responses] == [hex(i) for i in range(1, 6)]


@pytest.mark.parametrize("max_batch_size", [5])
def test_batch_request_within_limit_is_a_single_request(
    rpc: EthRPC, post: MagicMock
) -> None:
    """A call list at the limit is sent as one request."""
    calls = [RPCCall(method="blockNumber") for _ in range(5)]
    rpc.post_batch_request(calls=calls)
    assert post.call_count == 1


def test_empty_batch_request_is_not_sent(rpc: EthRPC, post: MagicMock) -> None:
    """An empty call list short-circuits without an HTTP request."""
    assert rpc.post_batch_request(calls=[]) == []
    post.assert_not_called()


@pytest.mark.parametrize("max_batch_size", [2])
def test_chunked_receipts_keep_request_order(
    rpc: EthRPC, post: MagicMock
) -> None:
    """Chunked receipts are returned in the order of the input hashes."""
    hashes = [Hash(i) for i in range(1, 6)]
    receipts = rpc.get_transaction_receipts(hashes)
    assert post.call_count == 3
    assert receipts == [hex(i) for i in range(1, 6)]
