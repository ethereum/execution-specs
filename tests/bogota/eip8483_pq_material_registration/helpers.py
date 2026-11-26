"""Helpers shared by the EIP-8483 tests."""

from typing import Dict, Sequence, Tuple, Type, TypeVar

import pytest
from execution_testing import (
    Address,
    Alloc,
    Bytecode,
    FeeSystemContractRequest,
    Op,
    PQBuilderRegistrationRequest,
    PQRegistrationRequest,
    Storage,
)
from execution_testing.base_types import FixedSizeBytes

PQRequestClass = (
    Type[PQRegistrationRequest] | Type[PQBuilderRegistrationRequest]
)
"""Either request class, both of which build requests from a proof."""

FixedBytes = TypeVar("FixedBytes", bound=FixedSizeBytes)

with_both_registrations = pytest.mark.parametrize(
    "request_class",
    [
        pytest.param(PQRegistrationRequest, id="validator"),
        pytest.param(PQBuilderRegistrationRequest, id="builder"),
    ],
)
"""Parametrize a test with the validator and the builder request classes."""


def record_storage(
    record: FeeSystemContractRequest, queue_index: int
) -> Dict[int, int]:
    """
    Return the slots the predeploy writes for `record` at `queue_index`: the
    source address, then the public key and `pq_data` in 32-byte words, the
    last one padded with zeros. The signature that follows them in the
    calldata is never stored.
    """
    serialized = bytes(record)
    source, data = serialized[:20], serialized[20:]
    words = data.ljust(32 * (record.slots_per_request - 1), b"\0")
    assert len(words) == 32 * (record.slots_per_request - 1)
    values = [int.from_bytes(source, "big")] + [
        int.from_bytes(words[i : i + 32], "big")
        for i in range(0, len(words), 32)
    ]
    return dict(zip(record.record_slots(queue_index, 1), values, strict=True))


def queue_storage(
    records: Sequence[FeeSystemContractRequest], *, head: int = 0
) -> Dict[int, int]:
    """
    Return the storage of a queue whose items from `head` on are `records`,
    leaving out the slots that hold zero.
    """
    request_class = type(records[0])
    storage = {
        request_class.queue_head_slot: head,
        request_class.queue_tail_slot: head + len(records),
    }
    for index, record in enumerate(records, start=head):
        storage |= record_storage(record, index)
    return {slot: value for slot, value in storage.items() if value != 0}


def call_results_relay(
    pre: Alloc,
    calls: Sequence[Tuple[Address, bytes, int, bool]],
) -> Tuple[Address, bytes, Storage]:
    """
    Deploy a relay that makes each `(address, calldata, value, succeeds)`
    call in order, reading the calldata from its own, and stores whether it
    succeeded. Return the relay, the transaction data that drives it and its
    expected storage. The result slots start at a canary value, so a call
    expected to fail must have run and stored zero.
    """
    storage = Storage()
    code = Bytecode()
    offset = 0
    for address, calldata, value, succeeds in calls:
        code += Op.CALLDATACOPY(0, offset, len(calldata)) + Op.SSTORE(
            storage.store_next(int(succeeds)),
            Op.CALL(Op.GAS, address, value, 0, len(calldata), 0, 0),
        )
        offset += len(calldata)
    relay = pre.deploy_contract(
        code,
        balance=sum(value for _, _, value, _ in calls),
        storage=storage.canary(),
    )
    data = b"".join(calldata for _, calldata, _, _ in calls)
    return relay, data, storage


def flip_byte(data: FixedBytes, index: int) -> FixedBytes:
    """Return `data` with the lowest bit of the byte at `index` flipped."""
    flipped = bytearray(data)
    flipped[index] ^= 0x01
    return type(data)(bytes(flipped))


def deploy_fee_getter(
    pre: Alloc, predeploy: Address, expected_fee: int
) -> tuple[Address, Storage]:
    """
    Deploy a contract that queries the predeploy's fee and stores whether the
    query succeeded and the fee it returned.
    """
    storage = Storage()
    code = Op.SSTORE(
        storage.store_next(1, "query_success"),
        Op.CALL(Op.GAS, predeploy, 0, 0, 0, 0, 32),
    ) + Op.SSTORE(storage.store_next(expected_fee, "fee"), Op.MLOAD(0))
    return pre.deploy_contract(code, storage=storage.canary()), storage
