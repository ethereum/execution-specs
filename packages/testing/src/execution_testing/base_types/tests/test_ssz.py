"""
Tests for SSZ support in base_types: containers declared once (base_types +
width ints) round-trip through SSZ and match hand-written remerkleable output,
covering every field kind (uint8/64/256, fixed vectors, capped byte-lists,
nested-container lists, bool, bitvector).
"""

from typing import Annotated, List

import pytest
from remerkleable.basic import boolean, uint8, uint64, uint256
from remerkleable.bitfields import Bitlist as RmkBitlist
from remerkleable.bitfields import Bitvector as RmkBitvector
from remerkleable.byte_arrays import ByteList, ByteVector
from remerkleable.complex import Container
from remerkleable.complex import List as RmkList
from remerkleable.complex import Vector as RmkVector
from remerkleable.progressive import ProgressiveContainer
from remerkleable.progressive import ProgressiveList as RmkProgressiveList

from execution_testing.base_types import Address, Bloom, Bytes, Hash
from execution_testing.base_types.ssz import (
    ProgressiveModel,
    SszModel,
    Uint8,
    Uint64,
    Uint256,
    bitlist,
    bitvector,
    byte_list,
    decode,
    describe_schema,
    encode,
    hash_tree_root,
    progressive_list,
    ssz_default,
    ssz_list,
    ssz_vector,
)

MAX_EXTRA = 32
MAX_BYTES_PER_TX = 2**30
MAX_TXS = 2**20
MAX_WITHDRAWALS = 16
CELLS = 128


class Withdrawal(SszModel):
    """A pydantic model declared to check the SSZ machinery."""

    index: Uint64
    validator_index: Uint64
    address: Address
    amount: Uint64


class ExecutionPayload(SszModel):
    """An Amsterdam-shaped payload exercising every field kind."""

    parent_hash: Hash
    fee_recipient: Address
    state_root: Hash
    logs_bloom: Bloom
    block_number: Uint64
    base_fee_per_gas: Uint256
    extra_data: Annotated[Bytes, byte_list(MAX_EXTRA)]
    transactions: Annotated[
        List[Annotated[Bytes, byte_list(MAX_BYTES_PER_TX)]],
        ssz_list(MAX_TXS),
    ]
    withdrawals: Annotated[List[Withdrawal], ssz_list(MAX_WITHDRAWALS)]


def _withdrawal() -> Withdrawal:
    return Withdrawal(
        index=7,
        validator_index=42,
        address=Address(b"\x11" * 20),
        amount=32_000_000_000,
    )


def assert_matches_reference(model: SszModel, ref: Container) -> None:
    """
    Compare the engine against a hand-written remerkleable twin.

    The twin is the ground truth: everything observable must agree -- the
    wire bytes, the hash_tree_root, the decode round-trip, and the default
    (zero) value of both types. The zero comparison pins the full schema
    and merkle shape, not just the one populated instance.
    """
    model_cls = type(model)
    ref_cls = type(ref)
    # populated instance: wire bytes + merkle root
    assert encode(model) == ref.encode_bytes()
    assert hash_tree_root(model) == bytes(ref.hash_tree_root())
    # decode round-trips losslessly
    restored = decode(model_cls, encode(model))
    assert encode(restored) == encode(model)
    assert hash_tree_root(restored) == hash_tree_root(model)
    # both sides agree on the zero value
    zero = ssz_default(model_cls)
    assert encode(zero) == ref_cls().encode_bytes()
    assert hash_tree_root(zero) == bytes(ref_cls().hash_tree_root())


def test_scalar_container_is_byte_identical_to_remerkleable() -> None:
    """The generated encoding equals a hand-written remerkleable container."""

    class Ref(Container):
        index: uint64
        validator_index: uint64
        address: ByteVector[20]
        amount: uint64

    ref = Ref(
        index=7,
        validator_index=42,
        address=b"\x11" * 20,
        amount=32_000_000_000,
    )
    assert_matches_reference(_withdrawal(), ref)


def test_full_payload_round_trips() -> None:
    """A container with every field kind round-trips pydantic<->SSZ."""
    payload = ExecutionPayload(
        parent_hash=Hash(b"\xaa" * 32),
        fee_recipient=Address(b"\xbb" * 20),
        state_root=Hash(b"\xcc" * 32),
        logs_bloom=Bloom(b"\x00" * 256),
        block_number=21_000_000,
        base_fee_per_gas=10**18,
        extra_data=Bytes(b"\xde\xad"),
        transactions=[Bytes(b"\x02\xf8"), Bytes(b"\x03" * 5)],
        withdrawals=[_withdrawal()],
    )
    restored = decode(ExecutionPayload, encode(payload))
    assert restored.parent_hash == payload.parent_hash
    assert int(restored.base_fee_per_gas) == 10**18
    assert [bytes(t) for t in restored.transactions] == [
        b"\x02\xf8",
        b"\x03" * 5,
    ]
    assert int(restored.withdrawals[0].amount) == 32_000_000_000
    assert len(hash_tree_root(payload)) == 32


def test_full_payload_byte_identical_to_remerkleable() -> None:
    """The rich payload encodes identically to a hand-written container."""

    class RefWithdrawal(Container):
        index: uint64
        validator_index: uint64
        address: ByteVector[20]
        amount: uint64

    class RefPayload(Container):
        parent_hash: ByteVector[32]
        fee_recipient: ByteVector[20]
        state_root: ByteVector[32]
        logs_bloom: ByteVector[256]
        block_number: uint64
        base_fee_per_gas: uint256
        extra_data: ByteList[MAX_EXTRA]
        transactions: RmkList[ByteList[MAX_BYTES_PER_TX], MAX_TXS]
        withdrawals: RmkList[RefWithdrawal, MAX_WITHDRAWALS]

    payload = ExecutionPayload(
        parent_hash=Hash(b"\xaa" * 32),
        fee_recipient=Address(b"\xbb" * 20),
        state_root=Hash(b"\xcc" * 32),
        logs_bloom=Bloom(b"\x00" * 256),
        block_number=21_000_000,
        base_fee_per_gas=10**18,
        extra_data=Bytes(b"\xde\xad"),
        transactions=[Bytes(b"\x02\xf8"), Bytes(b"\x03" * 5)],
        withdrawals=[_withdrawal()],
    )
    ref = RefPayload(
        parent_hash=b"\xaa" * 32,
        fee_recipient=b"\xbb" * 20,
        state_root=b"\xcc" * 32,
        logs_bloom=b"\x00" * 256,
        block_number=21_000_000,
        base_fee_per_gas=10**18,
        extra_data=b"\xde\xad",
        transactions=[b"\x02\xf8", b"\x03" * 5],
        withdrawals=[
            RefWithdrawal(
                index=7,
                validator_index=42,
                address=b"\x11" * 20,
                amount=32_000_000_000,
            )
        ],
    )
    assert_matches_reference(payload, ref)


def test_bool_and_bitvector_fields() -> None:
    """A boolean and a bit vector match their remerkleable equivalents."""

    class Status(SszModel):
        ok: bool
        columns: Annotated[List[bool], bitvector(CELLS)]

    bits = [i % 3 == 0 for i in range(CELLS)]
    value = Status(ok=True, columns=bits)

    class Ref(Container):
        ok: boolean
        columns: RmkBitvector[CELLS]

    ref = Ref(ok=True, columns=bits)
    assert_matches_reference(value, ref)
    restored = decode(Status, encode(value))
    assert restored.ok is True
    assert restored.columns == bits


def test_vector_and_bitlist() -> None:
    """Fixed Vector[uint64, N] and variable Bitlist[N] match remerkleable."""

    class Committee(SszModel):
        seats: Annotated[List[Uint64], ssz_vector(3)]
        flags: Annotated[List[bool], bitlist(8)]

    value = Committee(seats=[1, 2, 3], flags=[True, False, True])

    class Ref(Container):
        seats: RmkVector[uint64, 3]
        flags: RmkBitlist[8]

    ref = Ref(seats=[1, 2, 3], flags=[True, False, True])
    assert_matches_reference(value, ref)
    restored = decode(Committee, encode(value))
    assert [int(s) for s in restored.seats] == [1, 2, 3]
    assert restored.flags == [True, False, True]


def test_progressive_list_and_container() -> None:
    """Uncapped progressive list + progressive container match remerkleable."""

    class Prog(ProgressiveModel):
        a: Uint64
        b: Uint8
        items: Annotated[List[Uint64], progressive_list()]

    value = Prog(a=5, b=9, items=[10, 20, 30])

    class Ref(ProgressiveContainer(active_fields=[1, 1, 1])):  # type: ignore[misc]
        a: uint64
        b: uint8
        items: RmkProgressiveList[uint64]

    ref = Ref(a=5, b=9, items=[10, 20, 30])
    assert_matches_reference(value, ref)
    restored = decode(Prog, encode(value))
    assert [int(x) for x in restored.items] == [10, 20, 30]


def test_ssz_default_matches_remerkleable_zero() -> None:
    """ssz_default builds the SSZ zero value, like remerkleable's default."""
    zero = ssz_default(ExecutionPayload)
    assert int(zero.block_number) == 0
    assert zero.transactions == []
    assert zero.withdrawals == []
    assert bytes(zero.parent_hash) == b"\x00" * 32
    # zero encodes identically to a freshly-defaulted remerkleable container.
    assert encode(zero) == _zero_bytes()


def _zero_bytes() -> bytes:
    """The SSZ bytes of a default (zero) ExecutionPayload via remerkleable."""
    from execution_testing.base_types.ssz import build_ssz_type

    return build_ssz_type(ExecutionPayload)().encode_bytes()


def test_describe_schema_renders_every_field_kind() -> None:
    """describe_schema renders the resolved SSZ type of each field."""
    schema = describe_schema(ExecutionPayload)
    assert "block_number: uint64" in schema
    assert "base_fee_per_gas: uint256" in schema
    assert "parent_hash: ByteVector[32]" in schema
    assert f"extra_data: ByteList[{MAX_EXTRA}]" in schema
    assert (
        f"transactions: List[ByteList[{MAX_BYTES_PER_TX}], {MAX_TXS}]"
        in schema
    )
    assert f"withdrawals: List[Withdrawal, {MAX_WITHDRAWALS}]" in schema


def test_marker_type_mismatch_fails_at_import() -> None:
    """
    A cap marker on the wrong Python type raises when the model is defined.

    This is the guard against a silent mis-encode: the marker and the field's
    Python type must agree, and the check runs at class-definition time.
    """
    with pytest.raises(TypeError, match="ssz_vector requires a list"):

        class BadVector(SszModel):
            seats: Annotated[Uint64, ssz_vector(3)]  # not a list

    with pytest.raises(TypeError, match="byte_list requires a Bytes"):

        class BadByteList(SszModel):
            data: Annotated[Uint64, byte_list(8)]  # not Bytes

    with pytest.raises(TypeError, match="bit markers require a list"):

        class BadBits(SszModel):
            # non-bool element would silently truncate to truthiness on encode
            flags: Annotated[List[Uint64], bitlist(8)]


def test_progressive_active_fields_count_checked() -> None:
    """A mismatched __active_fields__ count raises at class definition."""
    with pytest.raises(TypeError, match="active"):

        class BadProg(ProgressiveModel):
            __active_fields__ = [1, 1]  # two active, three declared fields

            a: Uint64
            b: Uint64
            c: Uint64


def test_progressive_reserved_gap() -> None:
    """
    A reserved gap (0) matches a remerkleable container 1:1.

    active_fields=[1, 0, 1] declares two fields with a reserved middle slot;
    remerkleable requires the count of 1s to equal the declared field count.
    """

    class Prog(ProgressiveModel):
        __active_fields__ = [1, 0, 1]

        a: Uint64
        c: Uint64

    value = Prog(a=1, c=3)

    class Ref(ProgressiveContainer(active_fields=[1, 0, 1])):  # type: ignore[misc]
        a: uint64
        c: uint64

    ref = Ref(a=1, c=3)
    assert_matches_reference(value, ref)


def test_default_vector_of_container_has_independent_slots() -> None:
    """A defaulted Vector-of-container has independent (non-aliased) slots."""

    class Inner(SszModel):
        x: Uint64

    class Outer(SszModel):
        items: Annotated[List[Inner], ssz_vector(3)]

    zero = ssz_default(Outer)
    assert len(zero.items) == 3
    zero.items[0].x = Uint64(99)
    # Mutating one slot must not bleed into its siblings.
    assert int(zero.items[1].x) == 0
    assert int(zero.items[2].x) == 0
