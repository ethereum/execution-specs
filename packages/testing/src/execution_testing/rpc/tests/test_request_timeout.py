"""Test the HTTP request timeout behavior of `BaseRPC` clients."""

from unittest.mock import MagicMock, patch

import requests

from execution_testing.rpc import EthRPC, RPCCall
from execution_testing.rpc.rpc import DEFAULT_REQUEST_TIMEOUT


def response_mock() -> MagicMock:
    """Return a mock of a successful JSON-RPC HTTP response."""
    response = MagicMock()
    response.json.return_value = {
        "jsonrpc": "2.0",
        "id": 1,
        "result": "0x0",
    }
    return response


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
    with patch.object(
        rpc.session,
        "post",
        side_effect=[
            requests.ReadTimeout("read timed out"),
            response_mock(),
        ],
    ) as post:
        rpc.post_request(request=RPCCall(method="blockNumber"))
    assert post.call_count == 2


def test_batch_request_default_timeout_is_applied() -> None:
    """Batch requests carry the default timeout as well."""
    response = MagicMock()
    response.json.return_value = [
        {"jsonrpc": "2.0", "id": 1, "result": "0x0"},
    ]
    rpc = EthRPC("http://localhost:8545")
    with patch.object(rpc.session, "post", return_value=response) as post:
        rpc.post_batch_request(calls=[RPCCall(method="blockNumber")])
    assert post.call_args.kwargs["timeout"] == DEFAULT_REQUEST_TIMEOUT
