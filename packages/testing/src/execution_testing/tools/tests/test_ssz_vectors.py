"""
Tests for SSZ static-vector generation (consensus-specs-style suites).

Every generated case must be internally consistent with the engine (the
ground truth for bytes/roots) and round-trip losslessly; the suites and
mode semantics mirror consensus-specs' ssz_static generator.
"""

import random
from pathlib import Path
from typing import Annotated, List, Type

from execution_testing.base_types import Address, Bytes, Hash
from execution_testing.base_types.ssz import (
    SszModel,
    Uint64,
    Uint256,
    byte_list,
    decode,
    encode,
    hash_tree_root,
    spec_of,
    ssz_list,
)
from execution_testing.tools.ssz_vectors import (
    RandomizationMode,
    case_files,
    deterministic_seed,
    generate_cases,
    make_case,
    random_model,
    random_value,
    suite_plan,
    write_vectors,
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
        List[Annotated[Bytes, byte_list(MAX_BYTES_PER_TX)]],
        ssz_list(MAX_TX),
    ]
    withdrawals: Annotated[List[Withdrawal], ssz_list(MAX_WITHDRAWALS)]


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


def test_suite_plan_mirrors_consensus() -> None:
    """The published CL suite names; changing modes get several cases."""
    plan = suite_plan(count=30)
    names = [name for name, *_rest in plan]
    assert names == [
        "ssz_random",
        "ssz_zero",
        "ssz_max",
        "ssz_nil",
        "ssz_one",
        "ssz_lengthy",
        "ssz_random_chaos",
    ]
    counts = {name: n for name, _m, _c, n in plan}
    # consensus-specs: cases_if_random if chaos or is_changing() else 1
    assert counts["ssz_random"] == 30
    assert counts["ssz_one"] == 30
    assert counts["ssz_lengthy"] == 30
    assert counts["ssz_random_chaos"] == 30
    assert counts["ssz_zero"] == 1
    assert counts["ssz_max"] == 1
    assert counts["ssz_nil"] == 1


def test_mode_semantics() -> None:
    """Consensus mode semantics: zero/max pin content, counts pin length."""
    rng = random.Random(0)
    zero = random_model(rng, Payload, RandomizationMode.mode_zero)
    assert int(zero.base_fee_per_gas) == 0
    assert bytes(zero.parent_hash) == b"\x00" * 32
    # zero keeps byte-lists SHORT (one zero byte), not empty.
    assert bytes(zero.extra_data) == b"\x00"

    saturated = random_model(rng, Payload, RandomizationMode.mode_max)
    assert int(saturated.base_fee_per_gas) == 2**256 - 1
    assert bytes(saturated.parent_hash) == b"\xff" * 32
    assert bytes(saturated.extra_data) == b"\xff"

    empty = random_model(rng, Payload, RandomizationMode.mode_nil_count)
    assert empty.transactions == []
    assert empty.withdrawals == []
    assert bytes(empty.extra_data) == b""

    one = random_model(rng, Payload, RandomizationMode.mode_one_count)
    assert len(one.transactions) == 1
    assert len(one.withdrawals) == 1

    lengthy = random_model(rng, Payload, RandomizationMode.mode_max_count)
    # Saturated up to the generator's list cap (10), not the huge SSZ limit.
    assert len(lengthy.transactions) == 10
    assert len(lengthy.withdrawals) == 10


def test_generate_cases_covers_models_and_suites() -> None:
    """Every model x suite is emitted with the planned case counts."""
    models: List[Type[SszModel]] = [Withdrawal, Payload]
    cases = list(generate_cases(models, count=2))
    names = {name for name, _suite, _i, _c in cases}
    assert names == {"Withdrawal", "Payload"}
    # 4 changing suites x 2 cases + 3 deterministic suites x 1 = 11 per model
    assert len(cases) == 2 * 11

    # Every generated case is internally consistent and round-trips.
    for name, _suite, _i, case in cases:
        assert len(case.root) == 32
        model_cls = Withdrawal if name == "Withdrawal" else Payload
        assert encode(decode(model_cls, case.serialized)) == case.serialized


def test_deterministic() -> None:
    """Generation is deterministic across runs (sha256-seeded per case)."""
    a = [c.root for *_h, c in generate_cases([Payload], count=2)]
    b = [c.root for *_h, c in generate_cases([Payload], count=2)]
    assert a == b
    assert deterministic_seed("a", "b", 0) == deterministic_seed("a", "b", 0)
    assert deterministic_seed("a", "b", 0) != deterministic_seed("a", "b", 1)


def test_chaos_redraws_modes() -> None:
    """Chaos re-draws the mode per node yet still builds valid values."""
    rng = random.Random(deterministic_seed("chaos-test"))
    for _ in range(5):
        model = random_model(
            rng, Payload, RandomizationMode.mode_random, chaos=True
        )
        assert_roundtrip(model)


def test_random_value_covers_every_field_spec() -> None:
    """random_value handles every SszType the test containers use."""
    rng = random.Random(1)
    for name in Payload.model_fields:
        value = random_value(
            rng, spec_of(Payload, name), RandomizationMode.mode_random
        )
        assert value is not None


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
    # Hex strings must be single-quoted (a bare 0x... reads back as an int).
    assert b"root: '0x" in files["roots.yaml"]
    assert b"amount: '0x3'" in files["value.yaml"]
    assert b"address: '0x" in files["value.yaml"]


def test_write_vectors_emits_consensus_tree(tmp_path: Path) -> None:
    """write_vectors lays out <Container>/<suite>/case_<n>/ triples."""
    written = write_vectors([Withdrawal], tmp_path, count=2)
    assert written == 11  # 4 changing x 2 + 3 deterministic x 1
    zero_case = tmp_path / "Withdrawal" / "ssz_zero" / "case_0"
    assert (zero_case / "value.yaml").is_file()
    assert (zero_case / "serialized.ssz").is_file()
    assert (zero_case / "roots.yaml").is_file()
    # The serialized bytes reload and re-encode identically via the engine.
    raw = (zero_case / "serialized.ssz").read_bytes()
    assert encode(decode(Withdrawal, raw)) == raw
    # Changing suites have every planned case on disk.
    random_dir = tmp_path / "Withdrawal" / "ssz_random"
    assert sorted(p.name for p in random_dir.iterdir()) == [
        "case_0",
        "case_1",
    ]
