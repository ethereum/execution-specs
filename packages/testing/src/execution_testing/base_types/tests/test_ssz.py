"""
Tests for SSZ support in base_types: containers declared once (base_types +
width ints) round-trip through SSZ and match hand-written remerkleable output,
covering every field kind (uint8/64/256, fixed vectors, capped byte-lists,
nested-container lists, bool, bitvector).
"""

from typing import Annotated, List

from remerkleable.basic import boolean, uint64, uint256
from remerkleable.bitfields import Bitvector as RmkBitvector
from remerkleable.byte_arrays import ByteList, ByteVector
from remerkleable.complex import Container
from remerkleable.complex import List as RmkList

from execution_testing.base_types import Address, Bloom, Bytes, Hash
from execution_testing.base_types.ssz import (
    SszContainer,
    SszModel,
    Uint64,
    Uint256,
    bitvector,
    byte_list,
    decode,
    encode,
    hash_tree_root,
    ssz_list,
)

MAX_EXTRA = 32
MAX_BYTES_PER_TX = 2**30
MAX_TXS = 2**20
MAX_WITHDRAWALS = 16
CELLS = 128


class Withdrawal(SszModel):
    """Declared once, in base_types terms."""

    index: Uint64
    validator_index: Uint64
    address: Address
    amount: Uint64


class ExecutionPayload(SszModel):
    """A rich Amsterdam-shaped payload exercising every field kind."""

    parent_hash: Hash
    fee_recipient: Address
    state_root: Hash
    logs_bloom: Bloom
    block_number: Uint64
    base_fee_per_gas: Uint256
    extra_data: Annotated[Bytes, byte_list(MAX_EXTRA)]
    transactions: Annotated[
        List[Bytes], ssz_list(byte_list(MAX_BYTES_PER_TX), MAX_TXS)
    ]
    withdrawals: Annotated[
        List[Withdrawal], ssz_list(SszContainer(Withdrawal), MAX_WITHDRAWALS)
    ]


def _withdrawal() -> Withdrawal:
    return Withdrawal(
        index=7,
        validator_index=42,
        address=Address(b"\x11" * 20),
        amount=32_000_000_000,
    )


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
    assert encode(_withdrawal()) == ref.encode_bytes()
    assert hash_tree_root(_withdrawal()) == bytes(ref.hash_tree_root())


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
    assert encode(payload) == ref.encode_bytes()
    assert hash_tree_root(payload) == bytes(ref.hash_tree_root())


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
    assert encode(value) == ref.encode_bytes()
    restored = decode(Status, encode(value))
    assert restored.ok is True
    assert restored.columns == bits
