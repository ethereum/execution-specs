"""
Tests for the SSZ behavior of the engine execution payload fixture.
"""

from typing import Any, Dict, Optional, Tuple, Type

import pytest
from pydantic import ValidationError
from remerkleable.basic import uint64, uint256
from remerkleable.byte_arrays import ByteList, ByteVector
from remerkleable.complex import Container
from remerkleable.complex import List as RmkList

from execution_testing.base_types import (
    Address,
    Bloom,
    Bytes,
    Hash,
    HeaderNonce,
    ssz,
    to_json,
)
from execution_testing.base_types.ssz import (
    SSZForkSchema,
    Uint64,
    Uint256,
)
from execution_testing.forks import (
    BPO1,
    Amsterdam,
    BPO2ToAmsterdamAtTime15k,
    Cancun,
    Fork,
    London,
    Osaka,
    Paris,
    Prague,
    Shanghai,
    ShanghaiToCancunAtTime15k,
    ssz_schema_fork_key,
)
from execution_testing.test_types import Withdrawal

from ..blockchain import (
    MAX_BLOCK_ACCESS_LIST_BYTES,
    MAX_BYTES_PER_TRANSACTION,
    MAX_EXTRA_DATA_BYTES,
    MAX_TRANSACTIONS_PER_PAYLOAD,
    MAX_WITHDRAWALS_PER_PAYLOAD,
    FixtureEngineNewPayload,
    FixtureExecutionPayload,
    FixtureExecutionPayloadModifier,
    FixtureHeader,
    ForkScopedSSZModel,
)

BASE_FIELDS = (
    "parent_hash",
    "fee_recipient",
    "state_root",
    "receipts_root",
    "logs_bloom",
    "prev_randao",
    "number",
    "gas_limit",
    "gas_used",
    "timestamp",
    "extra_data",
    "base_fee_per_gas",
    "block_hash",
    "transactions",
)


class RefWithdrawal(Container):
    """Hand-written twin of Withdrawal."""

    index: uint64
    validator_index: uint64
    address: ByteVector[20]
    amount: uint64


class RefPayloadParis(Container):
    """Hand-written twin of FixtureExecutionPayload at Paris."""

    parent_hash: ByteVector[32]
    fee_recipient: ByteVector[20]
    state_root: ByteVector[32]
    receipts_root: ByteVector[32]
    logs_bloom: ByteVector[256]
    prev_randao: ByteVector[32]
    block_number: uint64
    gas_limit: uint64
    gas_used: uint64
    timestamp: uint64
    extra_data: ByteList[MAX_EXTRA_DATA_BYTES]
    base_fee_per_gas: uint256
    block_hash: ByteVector[32]
    transactions: RmkList[
        ByteList[MAX_BYTES_PER_TRANSACTION],
        MAX_TRANSACTIONS_PER_PAYLOAD,
    ]


class RefPayloadShanghai(Container):
    """Hand-written twin of FixtureExecutionPayload at Shanghai."""

    parent_hash: ByteVector[32]
    fee_recipient: ByteVector[20]
    state_root: ByteVector[32]
    receipts_root: ByteVector[32]
    logs_bloom: ByteVector[256]
    prev_randao: ByteVector[32]
    block_number: uint64
    gas_limit: uint64
    gas_used: uint64
    timestamp: uint64
    extra_data: ByteList[MAX_EXTRA_DATA_BYTES]
    base_fee_per_gas: uint256
    block_hash: ByteVector[32]
    transactions: RmkList[
        ByteList[MAX_BYTES_PER_TRANSACTION],
        MAX_TRANSACTIONS_PER_PAYLOAD,
    ]
    withdrawals: RmkList[RefWithdrawal, MAX_WITHDRAWALS_PER_PAYLOAD]


class RefPayloadCancun(Container):
    """Hand-written twin of FixtureExecutionPayload at Cancun."""

    parent_hash: ByteVector[32]
    fee_recipient: ByteVector[20]
    state_root: ByteVector[32]
    receipts_root: ByteVector[32]
    logs_bloom: ByteVector[256]
    prev_randao: ByteVector[32]
    block_number: uint64
    gas_limit: uint64
    gas_used: uint64
    timestamp: uint64
    extra_data: ByteList[MAX_EXTRA_DATA_BYTES]
    base_fee_per_gas: uint256
    block_hash: ByteVector[32]
    transactions: RmkList[
        ByteList[MAX_BYTES_PER_TRANSACTION],
        MAX_TRANSACTIONS_PER_PAYLOAD,
    ]
    withdrawals: RmkList[RefWithdrawal, MAX_WITHDRAWALS_PER_PAYLOAD]
    blob_gas_used: uint64
    excess_blob_gas: uint64


class RefPayloadAmsterdam(Container):
    """Hand-written twin of FixtureExecutionPayload at Amsterdam."""

    parent_hash: ByteVector[32]
    fee_recipient: ByteVector[20]
    state_root: ByteVector[32]
    receipts_root: ByteVector[32]
    logs_bloom: ByteVector[256]
    prev_randao: ByteVector[32]
    block_number: uint64
    gas_limit: uint64
    gas_used: uint64
    timestamp: uint64
    extra_data: ByteList[MAX_EXTRA_DATA_BYTES]
    base_fee_per_gas: uint256
    block_hash: ByteVector[32]
    transactions: RmkList[
        ByteList[MAX_BYTES_PER_TRANSACTION],
        MAX_TRANSACTIONS_PER_PAYLOAD,
    ]
    withdrawals: RmkList[RefWithdrawal, MAX_WITHDRAWALS_PER_PAYLOAD]
    blob_gas_used: uint64
    excess_blob_gas: uint64
    block_access_list: ByteList[MAX_BLOCK_ACCESS_LIST_BYTES]
    slot_number: uint64


REF_PAYLOAD_CLASSES: Dict[str, Type[Container]] = {
    "Paris": RefPayloadParis,
    "Shanghai": RefPayloadShanghai,
    "Cancun": RefPayloadCancun,
    "Amsterdam": RefPayloadAmsterdam,
}

FORK_BY_KEY: Dict[str, Fork] = {
    "Paris": Paris,
    "Shanghai": Shanghai,
    "Cancun": Cancun,
    "Amsterdam": Amsterdam,
}


def _withdrawal(i: int) -> Withdrawal:
    """Build a distinctive withdrawal for index ``i``."""
    return Withdrawal(
        index=i,
        validator_index=i + 1,
        address=Address(bytes([0x11 + i]) * 20),
        amount=32_000_000_000 + i,
    )


def _ref_withdrawal(withdrawal: Withdrawal) -> Container:
    """Build the remerkleable twin of ``withdrawal``."""
    return RefWithdrawal(
        index=int(withdrawal.index),
        validator_index=int(withdrawal.validator_index),
        address=bytes(withdrawal.address),
        amount=int(withdrawal.amount),
    )


def _payload_kwargs(fork_key: str) -> Dict[str, Any]:
    """Build constructor kwargs populated to exactly ``fork_key``."""
    kwargs: Dict[str, Any] = dict(
        parent_hash=Hash(b"\xaa" * 32),
        fee_recipient=Address(b"\xbb" * 20),
        state_root=Hash(b"\xcc" * 32),
        receipts_root=Hash(b"\xdd" * 32),
        logs_bloom=Bloom(b"\x00" * 256),
        number=1,
        gas_limit=30_000_000,
        gas_used=21_000,
        timestamp=1_700_000_000,
        extra_data=Bytes(b"\xde\xad"),
        prev_randao=Hash(b"\xee" * 32),
        base_fee_per_gas=10**18,
        block_hash=Hash(b"\xff" * 32),
        transactions=[Bytes(b"\x02\xf8"), Bytes(b"\x03" * 5)],
    )
    if fork_key in ("Shanghai", "Cancun", "Amsterdam"):
        kwargs["withdrawals"] = [_withdrawal(0), _withdrawal(1)]
    if fork_key in ("Cancun", "Amsterdam"):
        kwargs["blob_gas_used"] = 131_072
        kwargs["excess_blob_gas"] = 262_144
    if fork_key == "Amsterdam":
        kwargs["block_access_list"] = Bytes(b"\xc0")
        kwargs["slot_number"] = 12
    return kwargs


def _payload(fork_key: str) -> FixtureExecutionPayload:
    """Build a payload populated to exactly ``fork_key``'s fields."""
    return FixtureExecutionPayload(**_payload_kwargs(fork_key))


def _ref_payload(payload: FixtureExecutionPayload, fork_key: str) -> Container:
    """Build the remerkleable twin of ``payload`` at ``fork_key``."""
    kwargs: Dict[str, Any] = dict(
        parent_hash=bytes(payload.parent_hash),
        fee_recipient=bytes(payload.fee_recipient),
        state_root=bytes(payload.state_root),
        receipts_root=bytes(payload.receipts_root),
        logs_bloom=bytes(payload.logs_bloom),
        prev_randao=bytes(payload.prev_randao),
        block_number=int(payload.number),
        gas_limit=int(payload.gas_limit),
        gas_used=int(payload.gas_used),
        timestamp=int(payload.timestamp),
        extra_data=bytes(payload.extra_data),
        base_fee_per_gas=int(payload.base_fee_per_gas),
        block_hash=bytes(payload.block_hash),
        transactions=[bytes(tx) for tx in payload.transactions],
    )
    if fork_key in ("Shanghai", "Cancun", "Amsterdam"):
        assert payload.withdrawals is not None
        kwargs["withdrawals"] = [
            _ref_withdrawal(w) for w in payload.withdrawals
        ]
    if fork_key in ("Cancun", "Amsterdam"):
        kwargs["blob_gas_used"] = int(payload.blob_gas_used or 0)
        kwargs["excess_blob_gas"] = int(payload.excess_blob_gas or 0)
    if fork_key == "Amsterdam":
        kwargs["block_access_list"] = bytes(payload.block_access_list or b"")
        kwargs["slot_number"] = int(payload.slot_number or 0)
    return REF_PAYLOAD_CLASSES[fork_key](**kwargs)


def assert_matches_reference(
    model: ssz.SSZModel, ref: Container, fork_key: Optional[str] = None
) -> None:
    """
    Compare the engine against a hand-written remerkleable twin.

    The twin is the ground truth: wire bytes, merkle root, decode
    round-trip, and the zero value must all agree.
    """
    fork = FORK_BY_KEY[fork_key] if fork_key is not None else None
    model_cls = type(model)
    ref_cls = type(ref)
    raw = ssz.encode(model, fork)
    assert raw == ref.encode_bytes()
    assert ssz.hash_tree_root(model, fork) == bytes(ref.hash_tree_root())
    restored = ssz.decode(model_cls, raw, fork)
    assert ssz.encode(restored, fork) == raw
    assert restored == model
    zero = ssz.ssz_default(model_cls, fork)
    assert ssz.encode(zero, fork) == ref_cls().encode_bytes()
    assert ssz.hash_tree_root(zero, fork) == bytes(ref_cls().hash_tree_root())


def test_withdrawal_matches_reference() -> None:
    """The withdrawal container is byte-identical to its twin."""
    assert_matches_reference(_withdrawal(0), _ref_withdrawal(_withdrawal(0)))


def test_withdrawal_json_unchanged() -> None:
    """The withdrawal keeps its camelCase un-padded hex JSON shape."""
    withdrawal = Withdrawal(
        index=0,
        validator_index=1,
        address=0x1234,
        amount=2,
    )
    json_repr = {
        "index": "0x0",
        "validatorIndex": "0x1",
        "address": "0x0000000000000000000000000000000000001234",
        "amount": "0x2",
    }
    assert to_json(withdrawal) == json_repr
    assert Withdrawal(**json_repr) == withdrawal


def test_withdrawal_width_enforced() -> None:
    """A withdrawal amount beyond 64 bits fails validation."""
    with pytest.raises(ValidationError):
        Withdrawal(
            index=0,
            validator_index=0,
            address=Address(b"\x11" * 20),
            amount=2**64,
        )


@pytest.mark.parametrize(
    "fork_key", ["Paris", "Shanghai", "Cancun", "Amsterdam"]
)
def test_payload_matches_reference(fork_key: str) -> None:
    """Every fork's payload is byte-identical to its twin."""
    payload = _payload(fork_key)
    assert_matches_reference(
        payload, _ref_payload(payload, fork_key), fork_key
    )


@pytest.mark.parametrize(
    "fork_key,expected",
    [
        pytest.param("Paris", BASE_FIELDS, id="Paris"),
        pytest.param("Shanghai", (*BASE_FIELDS, "withdrawals"), id="Shanghai"),
        pytest.param(
            "Cancun",
            (
                *BASE_FIELDS,
                "withdrawals",
                "blob_gas_used",
                "excess_blob_gas",
            ),
            id="Cancun",
        ),
        pytest.param(
            "Amsterdam",
            (
                *BASE_FIELDS,
                "withdrawals",
                "blob_gas_used",
                "excess_blob_gas",
                "block_access_list",
                "slot_number",
            ),
            id="Amsterdam",
        ),
    ],
)
def test_payload_ssz_field_order(
    fork_key: str, expected: Tuple[str, ...]
) -> None:
    """The canonical wire order is pinned per fork."""
    assert (
        ssz.ssz_fields(FixtureExecutionPayload, FORK_BY_KEY[fork_key])
        == expected
    )


@pytest.mark.parametrize(
    "fork,expected_key",
    [
        pytest.param(Paris, Paris, id="Paris"),
        pytest.param(Shanghai, Shanghai, id="Shanghai"),
        pytest.param(Cancun, Cancun, id="Cancun"),
        pytest.param(Prague, Cancun, id="Prague"),
        pytest.param(Osaka, Cancun, id="Osaka"),
        pytest.param(BPO1, Cancun, id="BPO1"),
        pytest.param(Amsterdam, Amsterdam, id="Amsterdam"),
        pytest.param(
            ShanghaiToCancunAtTime15k,
            Cancun,
            id="ShanghaiToCancunAtTime15k",
        ),
        pytest.param(
            BPO2ToAmsterdamAtTime15k,
            Amsterdam,
            id="BPO2ToAmsterdamAtTime15k",
        ),
    ],
)
def test_fork_key_resolution(fork: Fork, expected_key: Fork) -> None:
    """Payload-neutral forks resolve to the nearest earlier key."""
    assert FixtureExecutionPayload.ssz_fork_key(fork) == expected_key


def test_fork_key_resolution_pre_base_raises() -> None:
    """A fork older than the schema's base fork is rejected."""
    with pytest.raises(ValueError, match="predates"):
        FixtureExecutionPayload.ssz_fork_key(London)


def test_payload_ssz_methods_accept_fork_classes() -> None:
    """The mixin's SSZ methods take Fork classes, not key strings."""
    payload = _payload("Cancun")
    wire = payload.ssz_encode(Prague)
    assert bytes(wire) == ssz.encode(payload, Cancun)
    assert FixtureExecutionPayload.ssz_decode(bytes(wire), Prague) == payload
    amsterdam_payload = _payload("Amsterdam")
    root = amsterdam_payload.ssz_hash_tree_root(Amsterdam)
    assert isinstance(root, Hash)
    assert len(root) == 32
    assert bytes(root) == ssz.hash_tree_root(amsterdam_payload, Amsterdam)


def test_payload_json_unchanged() -> None:
    """The payload keeps its camelCase un-padded hex JSON shape."""
    payload = _payload("Amsterdam")
    json_repr = {
        "parentHash": "0x" + "aa" * 32,
        "feeRecipient": "0x" + "bb" * 20,
        "stateRoot": "0x" + "cc" * 32,
        "receiptsRoot": "0x" + "dd" * 32,
        "logsBloom": "0x" + "00" * 256,
        "blockNumber": "0x1",
        "gasLimit": "0x1c9c380",
        "gasUsed": "0x5208",
        "timestamp": "0x6553f100",
        "extraData": "0xdead",
        "prevRandao": "0x" + "ee" * 32,
        "baseFeePerGas": "0xde0b6b3a7640000",
        "blobGasUsed": "0x20000",
        "excessBlobGas": "0x40000",
        "blockHash": "0x" + "ff" * 32,
        "transactions": ["0x02f8", "0x0303030303"],
        "withdrawals": [
            {
                "index": "0x0",
                "validatorIndex": "0x1",
                "address": "0x" + "11" * 20,
                "amount": "0x773594000",
            },
            {
                "index": "0x1",
                "validatorIndex": "0x2",
                "address": "0x" + "12" * 20,
                "amount": "0x773594001",
            },
        ],
        "blockAccessList": "0xc0",
        "slotNumber": "0xc",
    }
    assert to_json(payload) == json_repr
    assert FixtureExecutionPayload(**json_repr) == payload
    cancun_json = to_json(_payload("Cancun"))
    assert "blockAccessList" not in cancun_json
    assert "slotNumber" not in cancun_json


def test_payload_uint_width_enforced() -> None:
    """A payload gas limit beyond 64 bits fails validation."""
    kwargs = _payload_kwargs("Paris")
    kwargs["gas_limit"] = 2**64
    with pytest.raises(ValidationError):
        FixtureExecutionPayload(**kwargs)


def _amsterdam_header() -> FixtureHeader:
    """Build a fully-populated Amsterdam header."""
    return FixtureHeader(
        parent_hash=Hash(0),
        ommers_hash=Hash(1),
        fee_recipient=Address(2),
        state_root=Hash(3),
        transactions_trie=Hash(4),
        receipts_root=Hash(5),
        logs_bloom=Bloom(6),
        difficulty=7,
        number=1,
        gas_limit=9,
        gas_used=10,
        timestamp=11,
        extra_data=Bytes([12]),
        prev_randao=Hash(13),
        nonce=HeaderNonce(14),
        base_fee_per_gas=15,
        withdrawals_root=Hash(16),
        blob_gas_used=17,
        excess_blob_gas=18,
        parent_beacon_block_root=19,
        requests_hash=20,
        block_access_list_hash=Hash(21),
        slot_number=22,
    )


def test_from_fixture_header_round_trip() -> None:
    """A payload built through the fill pipeline SSZ round-trips."""
    new_payload = FixtureEngineNewPayload.from_fixture_header(
        fork=Amsterdam,
        header=_amsterdam_header(),
        transactions=[],
        withdrawals=[],
        requests=[],
        block_access_list=Bytes(b"\xc0"),
    )
    payload = new_payload.params[0]
    assert isinstance(payload.number, Uint64)
    assert isinstance(payload.base_fee_per_gas, Uint256)
    wire = payload.ssz_encode(Amsterdam)
    restored = FixtureExecutionPayload.ssz_decode(bytes(wire), Amsterdam)
    assert restored == payload
    ref = _ref_payload(payload, "Amsterdam")
    assert bytes(payload.ssz_hash_tree_root(Amsterdam)) == bytes(
        ref.hash_tree_root()
    )


def test_encode_wrong_fork_refuses_to_drop_data() -> None:
    """Encoding at a fork that does not fit the populated fields fails."""
    with pytest.raises(TypeError, match="unexpected"):
        ssz.encode(_payload("Amsterdam"), Cancun)
    with pytest.raises(TypeError, match="missing"):
        ssz.encode(_payload("Cancun"), Amsterdam)


def test_decode_older_fork_leaves_future_fields_none() -> None:
    """Decoding Paris wire bytes leaves post-Paris fields as None."""
    wire = ssz.encode(_payload("Paris"), Paris)
    restored = ssz.decode(FixtureExecutionPayload, wire, Paris)
    assert restored.withdrawals is None
    assert restored.blob_gas_used is None
    assert restored.excess_blob_gas is None
    assert restored.block_access_list is None
    assert restored.slot_number is None


def test_modifier_removed_fields_encode_at_earlier_fork() -> None:
    """REMOVE_FIELD strips the Amsterdam tail so Cancun encoding fits."""
    modifier = FixtureExecutionPayloadModifier(
        block_access_list=FixtureExecutionPayloadModifier.REMOVE_FIELD,
        slot_number=FixtureExecutionPayloadModifier.REMOVE_FIELD,
    )
    result = modifier.apply(_payload("Amsterdam"))
    cancun_payload = _payload("Cancun")
    assert ssz.encode(result, Cancun) == ssz.encode(cancun_payload, Cancun)
    with pytest.raises(TypeError, match="missing"):
        ssz.encode(result, Amsterdam)


def test_mixin_without_schema_raises() -> None:
    """A mixin subclass without a schema cannot resolve fork keys."""

    class NoSchema(ForkScopedSSZModel):
        """A fork-scoped mixin subclass missing its schema."""

    with pytest.raises(TypeError, match="does not declare"):
        NoSchema.ssz_fork_key(Paris)


def test_unknown_schema_fork_key_raises() -> None:
    """A schema key that is not a fork name is rejected."""
    schema = SSZForkSchema(base_fork="NotAFork", base=(), appended={})
    with pytest.raises(ValueError, match="not a fork class"):
        ssz_schema_fork_key(schema, Paris)


def test_describe_schema_amsterdam() -> None:
    """The Amsterdam schema description ends with the new fields."""
    description = ssz.describe_schema(FixtureExecutionPayload, Amsterdam)
    assert "Amsterdam" in description
    assert "block_access_list" in description
    assert "slot_number" in description
    assert description.index("block_access_list") < description.index(
        "slot_number"
    )
