"""
Tests for block access list sidecar delivery over the Engine API.

Amsterdam's `engine_newPayloadV5` carries the block access list inline;
Bogota's `engine_newPayloadV6` does not — the list travels separately,
delivered lists are stored by block hash (including before the fork
activates), a V6 payload reports SYNCING until its list arrives, and a
wrong list fails the block-hash check once the two are paired.
"""

from types import SimpleNamespace
from typing import Any, Dict, cast

import pytest
from ethereum_rlp import rlp
from ethereum_types.bytes import Bytes, Bytes32
from ethereum_types.numeric import U64, U256, Uint

from ethereum.crypto.hash import Hash32
from ethereum.exceptions import InvalidEngineParamsError
from ethereum.forks.amsterdam.execution_engine import (
    ExecutionEngine,
    ExecutionPayloadV5,
    PayloadStatus,
    new_payload_v6,
    notify_block_access_list_v1,
)
from ethereum.forks.amsterdam.fork_types import Bloom
from ethereum.state import Address, Root
from ethereum_spec_tools.engine_server.forks import FORKS, ForkSpec
from ethereum_spec_tools.engine_server.server import EngineBackend, RpcError

BLOCK_HASH = Hash32(b"\x11" * 32)
EMPTY_LIST = Bytes(rlp.encode([]))
FORK_TIMESTAMP = 15_000

_SPECS: Dict[str, ForkSpec] = {spec.name: spec for spec in FORKS}


def _engine() -> ExecutionEngine:
    """Minimal engine carrying only the sidecar store."""
    return cast(ExecutionEngine, SimpleNamespace(block_access_lists={}))


def _backend() -> EngineBackend:
    """
    A backend whose schedule transitions from Amsterdam to the Bogota
    pseudo-fork: the inline-list V5 wire before the boundary, the
    sidecar V6 wire after it.
    """
    return EngineBackend(
        engine=SimpleNamespace(),
        genesis_spec=_SPECS["Amsterdam"],
        schedule=[
            (_SPECS["Amsterdam"], 0),
            (_SPECS["Bogota"], FORK_TIMESTAMP),
        ],
    )


def _payload(block_hash: Hash32) -> ExecutionPayloadV5:
    """A structurally complete payload with placeholder values."""
    return ExecutionPayloadV5(
        parent_hash=Hash32(b"\x00" * 32),
        fee_recipient=Address(b"\x00" * 20),
        state_root=Root(b"\x00" * 32),
        receipts_root=Root(b"\x00" * 32),
        logs_bloom=Bloom(b"\x00" * 256),
        prev_randao=Bytes32(b"\x00" * 32),
        block_number=Uint(1),
        gas_limit=Uint(30_000_000),
        gas_used=Uint(0),
        timestamp=U256(FORK_TIMESTAMP),
        extra_data=Bytes(b""),
        base_fee_per_gas=Uint(7),
        block_hash=block_hash,
        transactions=(),
        withdrawals=(),
        blob_gas_used=U64(0),
        excess_blob_gas=U64(0),
        slot_number=U64(1),
    )


def _payload_json(
    timestamp: int,
    slot_number: bool = False,
    block_access_list: str | None = None,
) -> Dict[str, Any]:
    """A payload JSON object with placeholder values."""
    obj: Dict[str, Any] = {
        "parentHash": "0x" + "00" * 32,
        "feeRecipient": "0x" + "00" * 20,
        "stateRoot": "0x" + "00" * 32,
        "receiptsRoot": "0x" + "00" * 32,
        "logsBloom": "0x" + "00" * 256,
        "prevRandao": "0x" + "00" * 32,
        "blockNumber": "0x1",
        "gasLimit": "0x1c9c380",
        "gasUsed": "0x0",
        "timestamp": hex(timestamp),
        "extraData": "0x",
        "baseFeePerGas": "0x7",
        "blockHash": "0x" + "11" * 32,
        "transactions": [],
        "withdrawals": [],
        "blobGasUsed": "0x0",
        "excessBlobGas": "0x0",
    }
    if slot_number:
        obj["slotNumber"] = "0x1"
    if block_access_list is not None:
        obj["blockAccessList"] = block_access_list
    return obj


def _new_payload_params(payload_json: Dict[str, Any]) -> list:
    return [payload_json, [], "0x" + "00" * 32, []]


def test_undecodable_list_is_an_invalid_param() -> None:
    """A structurally undecodable list is rejected and not stored."""
    engine = _engine()
    with pytest.raises(InvalidEngineParamsError):
        notify_block_access_list_v1(engine, Bytes(b"\xff\x01"), BLOCK_HASH)
    assert BLOCK_HASH not in engine.block_access_lists


def test_delivered_list_is_stored_by_block_hash() -> None:
    """A well-formed list waits in the engine keyed by block hash."""
    engine = _engine()
    notify_block_access_list_v1(engine, EMPTY_LIST, BLOCK_HASH)
    assert engine.block_access_lists[BLOCK_HASH] == EMPTY_LIST


def test_payload_before_list_reports_syncing() -> None:
    """A payload whose list has not arrived cannot be validated."""
    status = new_payload_v6(
        _engine(), _payload(BLOCK_HASH), (), Root(b"\x00" * 32), ()
    )
    assert status.status == PayloadStatus.SYNCING


def test_wrong_list_fails_the_block_hash_check() -> None:
    """A delivered list that does not back the header is caught."""
    engine = _engine()
    notify_block_access_list_v1(engine, EMPTY_LIST, BLOCK_HASH)
    status = new_payload_v6(
        engine, _payload(BLOCK_HASH), (), Root(b"\x00" * 32), ()
    )
    assert status.status == PayloadStatus.INVALID
    assert status.validation_error == "invalid block hash"


def test_notify_stores_before_the_fork_activates() -> None:
    """
    A sidecar may arrive while the chain is still on the previous fork;
    the store is created on first delivery even for a pre-Amsterdam
    genesis engine.
    """
    backend = _backend()
    result = backend.handle(
        "engine_notifyBlockAccessListV1",
        ["0x" + EMPTY_LIST.hex(), "0x" + "11" * 32],
    )
    assert result is None
    assert backend.engine.block_access_lists[BLOCK_HASH] == EMPTY_LIST


def test_pre_fork_payload_is_not_gated_on_delivery() -> None:
    """
    Before the transition, `engine_newPayloadV5` carries its list
    inline and proceeds without any delivery — it fails on its
    placeholder block hash, never SYNCING.
    """
    backend = _backend()
    response = backend.handle(
        "engine_newPayloadV5",
        _new_payload_params(
            _payload_json(
                FORK_TIMESTAMP - 1,
                slot_number=True,
                block_access_list="0x" + EMPTY_LIST.hex(),
            )
        ),
    )
    assert response["status"] == "INVALID"
    assert response["validationError"] == "invalid block hash"


def test_post_fork_payload_syncs_until_delivery() -> None:
    """
    At the transition, the first Bogota payload reports SYNCING
    until its list is delivered, then proceeds to normal validation.
    """
    backend = _backend()
    params = _new_payload_params(
        _payload_json(FORK_TIMESTAMP, slot_number=True)
    )
    response = backend.handle("engine_newPayloadV6", params)
    assert response["status"] == "SYNCING"

    backend.handle(
        "engine_notifyBlockAccessListV1",
        ["0x" + EMPTY_LIST.hex(), "0x" + "11" * 32],
    )
    response = backend.handle("engine_newPayloadV6", params)
    assert response["status"] == "INVALID"
    assert response["validationError"] == "invalid block hash"


def test_post_fork_payload_rejects_an_embedded_list() -> None:
    """After the transition, the payload no longer carries the list."""
    backend = _backend()
    with pytest.raises(RpcError):
        backend.handle(
            "engine_newPayloadV6",
            _new_payload_params(
                _payload_json(
                    FORK_TIMESTAMP, slot_number=True, block_access_list="0x"
                )
            ),
        )
