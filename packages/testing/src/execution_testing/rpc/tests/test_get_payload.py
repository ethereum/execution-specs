"""Tests for `EngineRPC.get_payload`'s per-version response shape."""

from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from execution_testing.base_types import Bytes
from execution_testing.rpc import EngineRPC


def json_rpc_response(result: Any) -> MagicMock:
    """A mock HTTP response wrapping `result` as a JSON-RPC 2.0 reply."""
    response = MagicMock()
    response.json.return_value = {"jsonrpc": "2.0", "id": 1, "result": result}
    return response


EXECUTION_PAYLOAD = {
    "parentHash": "0x" + "00" * 32,
    "feeRecipient": "0x" + "00" * 20,
    "stateRoot": "0x" + "00" * 32,
    "receiptsRoot": "0x" + "00" * 32,
    "logsBloom": "0x" + "00" * 256,
    "prevRandao": "0x" + "00" * 32,
    "blockNumber": "0x1",
    "gasLimit": "0x5208",
    "gasUsed": "0x0",
    "timestamp": "0x0",
    "extraData": "0x",
    "baseFeePerGas": "0x1",
    "blockHash": "0x" + "11" * 32,
    "transactions": [],
}


@pytest.fixture
def engine() -> EngineRPC:
    """An Engine RPC client pointed at a local endpoint."""
    return EngineRPC("http://localhost:8551")


def test_get_payload_v1_accepts_bare_execution_payload(
    engine: EngineRPC,
) -> None:
    """
    A conforming V1 result (the execution payload itself, not wrapped in
    `executionPayload`) parses (PR3556-R0022).
    """
    with patch.object(
        engine.session,
        "post",
        return_value=json_rpc_response(EXECUTION_PAYLOAD),
    ):
        response = engine.get_payload(Bytes(b"\x00" * 8), version=1)
    assert (
        str(response.execution_payload.block_hash)
        == EXECUTION_PAYLOAD["blockHash"]
    )


def test_get_payload_v2_requires_the_wrapper(engine: EngineRPC) -> None:
    """V2 and later keep the `executionPayload` wrapper, unaffected."""
    with patch.object(
        engine.session,
        "post",
        return_value=json_rpc_response(
            {"executionPayload": EXECUTION_PAYLOAD, "blockValue": "0x0"}
        ),
    ):
        response = engine.get_payload(Bytes(b"\x00" * 8), version=2)
    assert (
        str(response.execution_payload.block_hash)
        == EXECUTION_PAYLOAD["blockHash"]
    )
