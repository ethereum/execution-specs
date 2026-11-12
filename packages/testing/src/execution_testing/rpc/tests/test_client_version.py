"""Test the `engine_getClientVersionV1` method of `EngineRPC`."""

from typing import Any
from unittest.mock import MagicMock, patch

import pytest
from pydantic import ValidationError

from execution_testing.base_types import Bytes
from execution_testing.rpc import ClientVersionV1, EngineRPC

CALLER = ClientVersionV1(
    code="ET",
    name="execution-testing",
    version="1.0.0",
    commit=Bytes(bytes(4)),
)


def response_mock(json_value: dict[str, Any]) -> MagicMock:
    """Return a mock of a successful JSON-RPC HTTP response."""
    response = MagicMock()
    response.json.return_value = json_value
    return response


def test_get_client_version_request() -> None:
    """The caller's version is sent as the only parameter, signed by JWT."""
    rpc = EngineRPC("http://localhost:8551")
    response = response_mock({"jsonrpc": "2.0", "id": 1, "result": []})
    with patch.object(rpc.session, "post", return_value=response) as post:
        rpc.get_client_version(CALLER)
    payload = post.call_args.kwargs["json"]
    assert payload["method"] == "engine_getClientVersionV1"
    assert payload["params"] == [
        {
            "code": "ET",
            "name": "execution-testing",
            "version": "1.0.0",
            "commit": "0x00000000",
        }
    ]
    authorization = post.call_args.kwargs["headers"]["Authorization"]
    assert authorization.startswith("Bearer ")


def test_get_client_version_response() -> None:
    """Every client version in the response is returned, in order."""
    rpc = EngineRPC("http://localhost:8551")
    result = [
        {
            "code": "GE",
            "name": "go-ethereum",
            "version": "1.16.0",
            "commit": "0xfa4ff922",
        },
        {
            "code": "NM",
            "name": "Nethermind",
            "version": "1.33.0",
            "commit": "0x0102abcd",
        },
    ]
    response = response_mock({"jsonrpc": "2.0", "id": 1, "result": result})
    with patch.object(rpc.session, "post", return_value=response):
        client_versions = rpc.get_client_version(CALLER)
    assert [str(v) for v in client_versions] == [
        "go-ethereum 1.16.0 (GE, 0xfa4ff922)",
        "Nethermind 1.33.0 (NM, 0x0102abcd)",
    ]


@pytest.mark.parametrize(
    "result",
    [None, {"code": "GE"}, [{"code": "GE"}]],
    ids=["null", "object", "incomplete_entry"],
)
def test_get_client_version_malformed_response(result: Any) -> None:
    """A response that is not a list of client versions is rejected."""
    rpc = EngineRPC("http://localhost:8551")
    response = response_mock({"jsonrpc": "2.0", "id": 1, "result": result})
    with (
        patch.object(rpc.session, "post", return_value=response),
        pytest.raises(ValidationError),
    ):
        rpc.get_client_version(CALLER)
