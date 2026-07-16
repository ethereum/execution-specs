"""
Tests for SSZ static-vector generation + a reusable round-trip harness.

Shows a vector "comes about" as a thin reflection loop: for each model x mode
the engine already yields value / serialized / root, so the case is those three
and nothing here knows any SSZ encoding.
"""

from typing import Annotated, List, Type

from execution_testing.base_types import Address, Bytes, Hash
from execution_testing.base_types.ssz import (
    SszContainer,
    SszModel,
    Uint64,
    Uint256,
    byte_list,
    decode,
    encode,
    hash_tree_root,
    ssz_list,
)
from execution_testing.base_types.ssz_vectors import (
    case_files,
    generate_cases,
    make_case,
)

MAX_TX = 2**20
MAX_BYTES_PER_TX = 2**30
MAX_WITHDRAWALS = 16


class Withdrawal(SszModel):
    """A withdrawal container."""

    index: Uint64
    validator_index: Uint64
    address: Address
    amount: Uint64


class Payload(SszModel):
    """A container with a byte-list, a capped list, and a nested list."""

    parent_hash: Hash
    base_fee_per_gas: Uint256
    extra_data: Annotated[Bytes, byte_list(32)]
    transactions: Annotated[
        List[Bytes], ssz_list(byte_list(MAX_BYTES_PER_TX), MAX_TX)
    ]
    withdrawals: Annotated[
        List[Withdrawal], ssz_list(SszContainer(Withdrawal), MAX_WITHDRAWALS)
    ]


def assert_roundtrip(model: SszModel) -> None:
    """Reusable harness: encode -> decode reconstructs the SSZ value."""
    restored = decode(type(model), encode(model))
    assert encode(restored) == encode(model)
    assert hash_tree_root(restored) == hash_tree_root(model)


def test_case_triple_is_consistent() -> None:
    """A case's serialized/root match the engine, and the value round-trips."""
    w = Withdrawal(
        index=7,
        validator_index=42,
        address=Address(b"\x11" * 20),
        amount=32_000_000_000,
    )
    case = make_case(w)
    assert case.serialized == encode(w)
    assert case.root == hash_tree_root(w)
    assert case.value["amount"] == "0x773594000"
    assert_roundtrip(w)


def test_generate_cases_covers_models_and_modes() -> None:
    """Every model x mode is emitted: ZERO once, others count times."""
    models: List[Type[SszModel]] = [Withdrawal, Payload]
    cases = list(generate_cases(models, count=3))
    names = {name for name, _mode, _i, _c in cases}
    assert names == {"Withdrawal", "Payload"}
    zero = [c for c in cases if c[1] == "zero"]
    rand = [c for c in cases if c[1] == "random"]
    assert len(zero) == 2  # one per model
    assert len(rand) == 2 * 3  # count per model

    # Every generated case is internally consistent and round-trips its bytes.
    for _name, _mode, _i, case in cases:
        assert len(case.root) == 32
        model_cls = Withdrawal if _name == "Withdrawal" else Payload
        assert encode(decode(model_cls, case.serialized)) == case.serialized


def test_deterministic() -> None:
    """Generation is deterministic across runs (seeded per case)."""
    a = [c.root for *_h, c in generate_cases([Payload], count=2)]
    b = [c.root for *_h, c in generate_cases([Payload], count=2)]
    assert a == b


def test_case_files_layout() -> None:
    """A case serializes to the consensus value/serialized/roots files."""
    w = Withdrawal(
        index=1,
        validator_index=2,
        address=Address(b"\x00" * 20),
        amount=3,
    )
    files = case_files(make_case(w))
    assert set(files) == {"value.yaml", "serialized.ssz", "roots.yaml"}
    assert files["serialized.ssz"] == encode(w)
    assert b"root: '0x" in files["roots.yaml"]
