"""
Tests for SSZ static-vector generation (consensus-specs-style suites).

Every generated case must be internally consistent with the engine (the
ground truth for bytes/roots), round-trip losslessly, and match pinned
known-answer values; the suites and mode semantics mirror consensus-specs'
ssz_static generator.
"""

import random
from pathlib import Path
from typing import Annotated, List

import pytest
import yaml

from execution_testing.base_types import Address, Bytes, Hash
from execution_testing.base_types.ssz import (
    SSZForkSchema,
    SSZModel,
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


class Withdrawal(SSZModel):
    """A withdrawal container."""

    index: Uint64
    validator_index: Uint64
    address: Address
    amount: Uint64


class Payload(SSZModel):
    """A container with a byte-list, a capped list, and a nested list."""

    parent_hash: Hash
    base_fee_per_gas: Uint256
    extra_data: Annotated[Bytes, byte_list(32)]
    transactions: Annotated[
        List[Annotated[Bytes, byte_list(MAX_BYTES_PER_TX)]],
        ssz_list(MAX_TX),
    ]
    withdrawals: Annotated[List[Withdrawal], ssz_list(MAX_WITHDRAWALS)]


class ForkedPayload(SSZModel):
    """A fork-scoped model, for the generator's fork axis."""

    parent_hash: Hash
    block_number: Uint64
    withdrawals: (
        Annotated[List[Withdrawal], ssz_list(MAX_WITHDRAWALS)] | None
    ) = None

    __ssz_schema__ = SSZForkSchema(
        base_fork="Paris",
        base=("parent_hash", "block_number"),
        appended={"Shanghai": ("withdrawals",)},
    )


def assert_roundtrip(model: SSZModel) -> None:
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


CONTENT_MODES = [
    ("zero", RandomizationMode.mode_zero, 0, b"\x00"),
    ("max", RandomizationMode.mode_max, 2**256 - 1, b"\xff"),
]


@pytest.mark.parametrize(
    "mode,fee,fill",
    [pytest.param(m, v, b, id=name) for name, m, v, b in CONTENT_MODES],
)
def test_content_modes_pin_values_not_lengths(
    mode: RandomizationMode, fee: int, fill: bytes
) -> None:
    """zero/max pin scalar CONTENT; collections stay short (1 byte)."""
    rng = random.Random(0)
    model = random_model(rng, Payload, mode)
    assert int(model.base_fee_per_gas) == fee
    assert bytes(model.parent_hash) == fill * 32
    # consensus semantics: byte-lists get ONE fill byte, not emptiness
    assert bytes(model.extra_data) == fill


COUNT_MODES = [
    ("nil", RandomizationMode.mode_nil_count, 0),
    ("one", RandomizationMode.mode_one_count, 1),
    ("lengthy", RandomizationMode.mode_max_count, 10),
]


@pytest.mark.parametrize(
    "mode,length",
    [pytest.param(m, n, id=name) for name, m, n in COUNT_MODES],
)
def test_count_modes_pin_lengths(mode: RandomizationMode, length: int) -> None:
    """nil/one/lengthy pin list LENGTHS (up to the generator cap of 10)."""
    rng = random.Random(0)
    model = random_model(rng, Payload, mode)
    assert len(model.transactions) == length
    assert len(model.withdrawals) == length


def test_generate_cases_covers_models_and_suites() -> None:
    """Every model x suite is emitted with the planned case counts."""
    cases = list(generate_cases([Withdrawal, Payload], count=2))
    names = {name for name, _fork, _suite, _i, _c in cases}
    assert names == {"Withdrawal", "Payload"}
    # 4 changing suites x 2 cases + 3 deterministic suites x 1 = 11 each
    assert len(cases) == 2 * 11

    # Every generated case is internally consistent and round-trips.
    for name, _fork, _suite, _i, case in cases:
        assert len(case.root) == 32
        model_cls = Withdrawal if name == "Withdrawal" else Payload
        assert encode(decode(model_cls, case.serialized)) == case.serialized


def test_value_yaml_matches_serialized() -> None:
    """
    The written value.yaml re-encodes to the written serialized.ssz.

    This is the contract an ssz_static consumer relies on: value,
    serialized bytes, and root must all describe the same object.
    """
    for _n, _f, _s, _i, case in generate_cases([Withdrawal], count=2):
        files = case_files(case)
        value = yaml.safe_load(files["value.yaml"])
        rebuilt = Withdrawal.model_validate(value)
        assert encode(rebuilt) == files["serialized.ssz"]
        root = yaml.safe_load(files["roots.yaml"])["root"]
        assert hash_tree_root(rebuilt).hex() == root.removeprefix("0x")


def test_deterministic() -> None:
    """Generation is deterministic across runs."""
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


@pytest.mark.parametrize("name", list(Payload.model_fields))
def test_random_value_covers_field_spec(name: str) -> None:
    """random_value handles every SSZType the test containers use."""
    rng = random.Random(1)
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
    # Hex strings must be single-quoted (a bare 0x... reads back as int).
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


def test_fork_scoped_vectors(tmp_path: Path) -> None:
    """(model, fork) entries emit per-fork projections under fork dirs."""
    written = write_vectors(
        [(ForkedPayload, "Paris"), (ForkedPayload, "Shanghai")],
        tmp_path,
        count=1,
    )
    assert written == 2 * 7  # all 7 suites x 1 case, per fork entry
    paris_zero = tmp_path / "ForkedPayload" / "Paris" / "ssz_zero" / "case_0"
    raw = (paris_zero / "serialized.ssz").read_bytes()
    restored = decode(ForkedPayload, raw, fork="Paris")
    assert restored.withdrawals is None  # beyond-fork field absent
    shanghai_zero = (
        tmp_path / "ForkedPayload" / "Shanghai" / "ssz_zero" / "case_0"
    )
    assert (shanghai_zero / "roots.yaml").is_file()


def test_duplicate_vector_targets_rejected(tmp_path: Path) -> None:
    """Two distinct same-named models cannot share an output directory."""

    def make_dup() -> type:
        class Withdrawal(SSZModel):  # same __name__, different class
            a: Uint64

        return Withdrawal

    with pytest.raises(ValueError, match="share vector output"):
        write_vectors([Withdrawal, make_dup()], tmp_path, count=1)
