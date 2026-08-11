"""
Tests for SSZ support in base_types.
"""

from typing import Annotated, Callable, List, Optional, Tuple

import pytest
from pydantic import ValidationError
from remerkleable.basic import boolean, uint8, uint64, uint256
from remerkleable.bitfields import Bitlist as RmkBitlist
from remerkleable.bitfields import Bitvector as RmkBitvector
from remerkleable.byte_arrays import ByteList, ByteVector
from remerkleable.complex import Container
from remerkleable.complex import List as RmkList
from remerkleable.complex import Vector as RmkVector
from remerkleable.progressive import (
    ProgressiveBitlist as RmkProgressiveBitlist,
)
from remerkleable.progressive import ProgressiveContainer
from remerkleable.progressive import ProgressiveList as RmkProgressiveList

from execution_testing.base_types import Address, Bloom, Bytes, Hash
from execution_testing.base_types.ssz import (
    ProgressiveModel,
    SSZForkSchema,
    SSZModel,
    SSZUint,
    Uint8,
    Uint16,
    Uint32,
    Uint64,
    Uint128,
    Uint256,
    bitlist,
    bitvector,
    build_ssz_type,
    byte_list,
    decode,
    describe_schema,
    encode,
    hash_tree_root,
    progressive_bitlist,
    progressive_list,
    spec_of,
    ssz_default,
    ssz_exclude,
    ssz_fields,
    ssz_list,
    ssz_vector,
)

MAX_EXTRA = 32
MAX_BYTES_PER_TX = 2**30
MAX_TXS = 2**20
MAX_WITHDRAWALS = 16
CELLS = 128
BITS = [i % 3 == 0 for i in range(CELLS)]


class Withdrawal(SSZModel):
    """A pydantic model declared to check the SSZ machinery."""

    index: Uint64
    validator_index: Uint64
    address: Address
    amount: Uint64


class ExecutionPayload(SSZModel):
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


class Status(SSZModel):
    """A boolean and a fixed bit vector."""

    ok: bool
    columns: Annotated[List[bool], bitvector(CELLS)]


class Committee(SSZModel):
    """A fixed Vector[uint64, N] and a variable Bitlist[N]."""

    seats: Annotated[List[Uint64], ssz_vector(3)]
    flags: Annotated[List[bool], bitlist(8)]


class Ballot(SSZModel):
    """An uncapped progressive bit list."""

    votes: Annotated[List[bool], progressive_bitlist()]


class Prog(ProgressiveModel):
    """EIP-7916 progressive container with a progressive list."""

    a: Uint64
    b: Uint8
    items: Annotated[List[Uint64], progressive_list()]


class GapProg(ProgressiveModel):
    """Two fields around a reserved (0) middle slot."""

    __active_fields__ = [1, 0, 1]

    a: Uint64
    c: Uint64


class MixedProg(ProgressiveModel):
    """A progressive container carrying a JSON-only (excluded) field."""

    a: Uint64
    note: Annotated[str, ssz_exclude()] = "json-only"
    c: Uint64


class ForkedPayload(SSZModel):
    """One model for every fork."""

    parent_hash: Hash
    blob_gas_used: Uint64 | None = None
    block_number: Uint64
    transactions: Annotated[  # JSON order differs from SSZ.
        List[Annotated[Bytes, byte_list(MAX_BYTES_PER_TX)]],
        ssz_list(MAX_TXS),
    ]
    withdrawals: (
        Annotated[List[Withdrawal], ssz_list(MAX_WITHDRAWALS)] | None
    ) = None

    __ssz_schema__ = SSZForkSchema(
        base_fork="Paris",
        base=("parent_hash", "block_number", "transactions"),
        appended={
            "Shanghai": ("withdrawals",),
            "Cancun": ("blob_gas_used",),
        },
    )


class Mixed(SSZModel):
    """An SSZ container carrying a JSON-only (excluded) field."""

    a: Uint64
    note: Annotated[str, ssz_exclude()] = "json-only"


class RefWithdrawal(Container):
    """Hand-written twin of Withdrawal."""

    index: uint64
    validator_index: uint64
    address: ByteVector[20]
    amount: uint64


class RefPayload(Container):
    """Hand-written twin of ExecutionPayload."""

    parent_hash: ByteVector[32]
    fee_recipient: ByteVector[20]
    state_root: ByteVector[32]
    logs_bloom: ByteVector[256]
    block_number: uint64
    base_fee_per_gas: uint256
    extra_data: ByteList[MAX_EXTRA]
    transactions: RmkList[ByteList[MAX_BYTES_PER_TX], MAX_TXS]
    withdrawals: RmkList[RefWithdrawal, MAX_WITHDRAWALS]


class RefStatus(Container):
    """Hand-written twin of Status."""

    ok: boolean
    columns: RmkBitvector[CELLS]


class RefCommittee(Container):
    """Hand-written twin of Committee."""

    seats: RmkVector[uint64, 3]
    flags: RmkBitlist[8]


class RefBallot(Container):
    """Hand-written twin of Ballot."""

    votes: RmkProgressiveBitlist


class RefProg(ProgressiveContainer(active_fields=[1, 1, 1])):  # type: ignore[misc]
    """Hand-written twin of Prog."""

    a: uint64
    b: uint8
    items: RmkProgressiveList[uint64]


class RefGapProg(ProgressiveContainer(active_fields=[1, 0, 1])):  # type: ignore[misc]
    """Hand-written twin of GapProg."""

    a: uint64
    c: uint64


class RefMixedProg(ProgressiveContainer(active_fields=[1, 1])):  # type: ignore[misc]
    """Hand-written twin of MixedProg: the excluded field takes no slot."""

    a: uint64
    c: uint64


class RefForkedParis(Container):
    """Hand-written twin of ForkedPayload at Paris."""

    parent_hash: ByteVector[32]
    block_number: uint64
    transactions: RmkList[ByteList[MAX_BYTES_PER_TX], MAX_TXS]


class RefForkedShanghai(Container):
    """Hand-written twin of ForkedPayload at Shanghai."""

    parent_hash: ByteVector[32]
    block_number: uint64
    transactions: RmkList[ByteList[MAX_BYTES_PER_TX], MAX_TXS]
    withdrawals: RmkList[RefWithdrawal, MAX_WITHDRAWALS]


class RefMixed(Container):  # the excluded field simply does not exist
    """Hand-written twin of Mixed (no excluded field)."""

    a: uint64


def _withdrawal() -> Withdrawal:
    return Withdrawal(
        index=7,
        validator_index=42,
        address=Address(b"\x11" * 20),
        amount=32_000_000_000,
    )


def _ref_withdrawal() -> Container:
    return RefWithdrawal(
        index=7,
        validator_index=42,
        address=b"\x11" * 20,
        amount=32_000_000_000,
    )


def _payload() -> ExecutionPayload:
    return ExecutionPayload(
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


def _ref_payload() -> Container:
    return RefPayload(
        parent_hash=b"\xaa" * 32,
        fee_recipient=b"\xbb" * 20,
        state_root=b"\xcc" * 32,
        logs_bloom=b"\x00" * 256,
        block_number=21_000_000,
        base_fee_per_gas=10**18,
        extra_data=b"\xde\xad",
        transactions=[b"\x02\xf8", b"\x03" * 5],
        withdrawals=[_ref_withdrawal()],
    )


def _paris_payload() -> ForkedPayload:
    return ForkedPayload(
        parent_hash=Hash(b"\xaa" * 32),
        block_number=100,
        transactions=[Bytes(b"\x02\xf8")],
    )


def _shanghai_payload() -> ForkedPayload:
    return ForkedPayload(
        parent_hash=Hash(b"\xaa" * 32),
        block_number=100,
        transactions=[Bytes(b"\x02\xf8")],
        withdrawals=[_withdrawal()],
    )


def assert_matches_reference(
    model: SSZModel, ref: Container, fork: Optional[str] = None
) -> None:
    """
    Compare the engine against a hand-written remerkleable twin.

    The twin is the ground truth: everything observable must
    """
    model_cls = type(model)
    ref_cls = type(ref)
    raw = encode(model, fork)
    # populated instance: wire bytes + merkle root
    assert raw == ref.encode_bytes()
    assert hash_tree_root(model, fork) == bytes(ref.hash_tree_root())
    # decode round-trips losslessly, back to an equal pydantic model
    restored = decode(model_cls, raw, fork)
    assert encode(restored, fork) == raw
    assert restored == model
    # both sides agree on the zero value
    zero = ssz_default(model_cls, fork)
    assert encode(zero, fork) == ref_cls().encode_bytes()
    assert hash_tree_root(zero, fork) == bytes(ref_cls().hash_tree_root())


TWIN_CASES: List[
    Tuple[
        str,
        Callable[[], SSZModel],
        Callable[[], Container],
        Optional[str],
    ]
] = [
    ("withdrawal", _withdrawal, _ref_withdrawal, None),
    ("payload", _payload, _ref_payload, None),
    (
        "bool-bitvector",
        lambda: Status(ok=True, columns=BITS),
        lambda: RefStatus(ok=True, columns=BITS),
        None,
    ),
    (
        "vector-bitlist",
        lambda: Committee(seats=[1, 2, 3], flags=[True, False, True]),
        lambda: RefCommittee(seats=[1, 2, 3], flags=[True, False, True]),
        None,
    ),
    (
        "progressive-bitlist",
        lambda: Ballot(votes=[True, False, True, True]),
        lambda: RefBallot(votes=[True, False, True, True]),
        None,
    ),
    (
        "progressive",
        lambda: Prog(a=5, b=9, items=[10, 20, 30]),
        lambda: RefProg(a=5, b=9, items=[10, 20, 30]),
        None,
    ),
    (
        "progressive-gap",
        lambda: GapProg(a=1, c=3),
        lambda: RefGapProg(a=1, c=3),
        None,
    ),
    (
        "progressive-excluded",
        lambda: MixedProg(a=1, c=3),
        lambda: RefMixedProg(a=1, c=3),
        None,
    ),
    (
        # default-valued excluded field: decode restores the default, so
        # the harness's restored == model leg holds; the non-default case
        # is covered by test_excluded_field_is_json_only.
        "excluded-field",
        lambda: Mixed(a=7),
        lambda: RefMixed(a=7),
        None,
    ),
    (
        "forked-paris",
        _paris_payload,
        lambda: RefForkedParis(
            parent_hash=b"\xaa" * 32,
            block_number=100,
            transactions=[b"\x02\xf8"],
        ),
        "Paris",
    ),
    (
        "forked-shanghai",
        _shanghai_payload,
        lambda: RefForkedShanghai(
            parent_hash=b"\xaa" * 32,
            block_number=100,
            transactions=[b"\x02\xf8"],
            withdrawals=[_ref_withdrawal()],
        ),
        "Shanghai",
    ),
]


@pytest.mark.parametrize(
    "make_model,make_ref,fork",
    [pytest.param(m, r, f, id=name) for name, m, r, f in TWIN_CASES],
)
def test_matches_remerkleable_reference(
    make_model: Callable[[], SSZModel],
    make_ref: Callable[[], Container],
    fork: Optional[str],
) -> None:
    """Every model kind is byte-identical to its hand-written twin."""
    assert_matches_reference(make_model(), make_ref(), fork)


def test_full_payload_round_trips() -> None:
    """A container with every field kind round-trips pydantic<->SSZ."""
    payload = _payload()
    restored = decode(ExecutionPayload, encode(payload))
    assert restored.parent_hash == payload.parent_hash
    assert int(restored.base_fee_per_gas) == 10**18
    assert [bytes(t) for t in restored.transactions] == [
        b"\x02\xf8",
        b"\x03" * 5,
    ]
    assert int(restored.withdrawals[0].amount) == 32_000_000_000
    assert len(hash_tree_root(payload)) == 32


def test_ssz_default_matches_remerkleable_zero() -> None:
    """ssz_default builds the SSZ zero value, like remerkleable's default."""
    zero = ssz_default(ExecutionPayload)
    assert int(zero.block_number) == 0
    assert zero.transactions == []
    assert zero.withdrawals == []
    assert bytes(zero.parent_hash) == b"\x00" * 32
    # zero encodes identically to a freshly-defaulted remerkleable container
    assert encode(zero) == build_ssz_type(ExecutionPayload)().encode_bytes()


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
    # progressive kinds render their consensus-style names
    assert "items: ProgressiveList[uint64]" in describe_schema(Prog)
    assert "votes: ProgressiveBitlist" in describe_schema(Ballot)


def test_default_vector_of_container_has_independent_slots() -> None:
    """A defaulted Vector-of-container has independent (non-aliased) slots."""

    class Inner(SSZModel):
        x: Uint64

    class Outer(SSZModel):
        items: Annotated[List[Inner], ssz_vector(3)]

    zero = ssz_default(Outer)
    assert len(zero.items) == 3
    zero.items[0].x = Uint64(99)
    # Mutating one slot must not bleed into its siblings.
    assert int(zero.items[1].x) == 0
    assert int(zero.items[2].x) == 0


def test_forked_model_json_omission_unchanged() -> None:
    """The JSON leg keeps today's exclude_none single-model behavior."""
    dumped = _shanghai_payload().model_dump(
        mode="json", by_alias=True, exclude_none=True
    )
    assert "withdrawals" in dumped
    assert "blobGasUsed" not in dumped  # pre-Cancun: key simply absent


def test_forked_model_decode_fills_none() -> None:
    """Decoding an older fork's bytes restores the one model with None."""
    shanghai = _shanghai_payload()
    raw = encode(shanghai, fork="Shanghai")
    restored = decode(ForkedPayload, raw, fork="Shanghai")
    assert restored == shanghai
    assert restored.blob_gas_used is None  # beyond-fork field stays None
    assert restored.withdrawals is not None


def test_fork_scoped_nested_in_complete_model_raises() -> None:
    """
    A COMPLETE model cannot carry a fork-scoped one.

    Without a fork at the outer encode there is nothing to propagate to
    the nested container, so the encode must refuse rather than pick a
    schema silently. (Fork-scoped outer models propagate their fork; see
    test_fork_propagates_to_nested_containers.)
    """

    class Wrapper(SSZModel):
        payload: ForkedPayload

    wrapper = Wrapper(payload=_shanghai_payload())
    with pytest.raises(TypeError, match="fork-scoped"):
        encode(wrapper)


def test_fork_propagates_to_nested_containers() -> None:
    """
    One fork projects the whole value tree (envelope contains payload).

    This is the general #793 shape: fork-evolving containers nest other
    fork-evolving containers, and everything inside one message is at
    the same chain fork. The outer fork= selects every nested projection.
    """

    class Envelope(SSZModel):
        payload: ForkedPayload
        blob_count: Uint64 | None = None  # Shanghai-era envelope field

        __ssz_schema__ = SSZForkSchema(
            base_fork="Paris",
            base=("payload",),
            appended={"Shanghai": ("blob_count",)},
        )

    class RefEnvelopeShanghai(Container):
        payload: RefForkedShanghai
        blob_count: uint64

    envelope = Envelope(payload=_shanghai_payload(), blob_count=3)
    ref = RefEnvelopeShanghai(
        payload=RefForkedShanghai(
            parent_hash=b"\xaa" * 32,
            block_number=100,
            transactions=[b"\x02\xf8"],
            withdrawals=[_ref_withdrawal()],
        ),
        blob_count=3,
    )
    assert_matches_reference(envelope, ref, fork="Shanghai")
    # decode restores both levels, beyond-fork fields None at each level
    restored = decode(Envelope, encode(envelope, "Shanghai"), fork="Shanghai")
    assert restored.payload.blob_gas_used is None
    # a nested payload that does not fit the propagated fork still raises
    paris_inside = Envelope(payload=_paris_payload(), blob_count=1)
    with pytest.raises(TypeError, match="missing=\\['withdrawals'\\]"):
        encode(paris_inside, fork="Shanghai")


def test_forked_model_describe_schema_per_fork() -> None:
    """describe_schema renders each fork's projection in SSZ order."""
    paris = describe_schema(ForkedPayload, fork="Paris")
    cancun = describe_schema(ForkedPayload, fork="Cancun")
    assert "blob_gas_used" not in paris
    assert cancun.splitlines()[-1].strip() == "blob_gas_used: uint64"
    # SSZ order comes from the schema tuples, not the class body: the
    # model declares blob_gas_used second, but it encodes LAST.
    assert cancun.splitlines()[1].strip() == "parent_hash: ByteVector[32]"


def _bad_vector_marker_on_scalar() -> None:
    class Bad(SSZModel):
        seats: Annotated[Uint64, ssz_vector(3)]  # not a list


def _bad_byte_list_on_int() -> None:
    class Bad(SSZModel):
        data: Annotated[Uint64, byte_list(8)]  # not Bytes


def _bad_bit_marker_on_ints() -> None:
    class Bad(SSZModel):
        flags: Annotated[List[Uint64], bitlist(8)]  # not list[bool]


def _bad_raw_ssz_type_marker() -> None:
    class Bad(SSZModel):
        x: Annotated[Uint64, SSZUint(32)]  # raw SSZType, not a helper


def _bad_unmapped_str() -> None:
    class Bad(SSZModel):
        s: str  # no SSZ mapping and not excluded


def _bad_bare_bytes() -> None:
    class Bad(SSZModel):
        data: Bytes  # variable bytes need a byte_list cap


def _bad_bare_list() -> None:
    class Bad(SSZModel):
        items: List[Uint64]  # lists need a cap/length marker


def _bad_multi_arm_union() -> None:
    class Bad(SSZModel):
        x: Uint64 | Uint8 | None = None  # only T | None supported


def _bad_optional_without_schema() -> None:
    class Bad(SSZModel):
        a: Uint64
        b: Uint64 | None = None  # optional but no schema


def _bad_schema_field_typo() -> None:
    class Bad(SSZModel):
        a: Uint64
        b: Uint64 | None = None

        __ssz_schema__ = SSZForkSchema(
            base_fork="Paris",
            base=("a",),
            appended={"Shanghai": ("typo",)},
        )


def _bad_required_appended() -> None:
    class Bad(SSZModel):
        a: Uint64
        b: Uint64  # appended but not optional

        __ssz_schema__ = SSZForkSchema(
            base_fork="Paris",
            base=("a",),
            appended={"Shanghai": ("b",)},
        )


def _bad_optional_base() -> None:
    class Bad(SSZModel):
        a: Uint64
        b: Uint64 | None = None  # optional but declared in base

        __ssz_schema__ = SSZForkSchema(
            base_fork="Paris",
            base=("a", "b"),
            appended={},
        )


def _bad_appended_no_default() -> None:
    class Bad(SSZModel):
        a: Uint64
        b: Uint64 | None  # optional type but NO None default

        __ssz_schema__ = SSZForkSchema(
            base_fork="Paris",
            base=("a",),
            appended={"Shanghai": ("b",)},
        )


def _bad_duplicate_schema_names() -> None:
    class Bad(SSZModel):
        a: Uint64
        b: Uint64 | None = None

        __ssz_schema__ = SSZForkSchema(
            base_fork="Paris",
            base=("a", "a"),
            appended={"Shanghai": ("b",)},
        )


def _bad_required_excluded() -> None:
    class Bad(SSZModel):
        a: Uint64
        note: Annotated[str, ssz_exclude()]  # excluded but required


def _bad_progressive_with_schema() -> None:
    class Bad(ProgressiveModel):
        a: Uint64

        __ssz_schema__ = SSZForkSchema(
            base_fork="Paris", base=("a",), appended={}
        )


def _bad_progressive_with_optional() -> None:
    class Bad(ProgressiveModel):
        a: Uint64
        b: Uint64 | None = None


def _bad_progressive_active_count() -> None:
    class Bad(ProgressiveModel):
        __active_fields__ = [1, 1]  # two active, three declared fields

        a: Uint64
        b: Uint64
        c: Uint64


def _bad_progressive_active_counts_excluded() -> None:
    # An excluded field takes no slot, so the third 1 has no field to
    # fill it: caught here rather than inside remerkleable at first
    # build_ssz_type.
    class Bad(ProgressiveModel):
        __active_fields__ = [1, 1, 1]  # three active, two SSZ fields

        a: Uint64
        note: Annotated[str, ssz_exclude()] = "json-only"
        c: Uint64


BAD_DECLARATIONS: List[Tuple[str, Callable[[], None], str]] = [
    ("vector-on-scalar", _bad_vector_marker_on_scalar, "requires a list"),
    ("byte-list-on-int", _bad_byte_list_on_int, "byte_list requires"),
    ("bits-on-ints", _bad_bit_marker_on_ints, "list\\[bool\\]"),
    ("raw-marker", _bad_raw_ssz_type_marker, "unsupported Annotated"),
    ("unmapped-str", _bad_unmapped_str, "no SSZ type"),
    ("bare-bytes", _bad_bare_bytes, "no SSZ type"),
    ("bare-list", _bad_bare_list, "no SSZ type"),
    ("multi-arm-union", _bad_multi_arm_union, "only T \\| None"),
    ("optional-no-schema", _bad_optional_without_schema, "no __ssz_schema__"),
    ("schema-typo", _bad_schema_field_typo, "does not match the model"),
    ("required-appended", _bad_required_appended, "must be T \\| None"),
    ("optional-base", _bad_optional_base, "optional base"),
    ("appended-no-default", _bad_appended_no_default, "default to None"),
    ("dup-schema-names", _bad_duplicate_schema_names, "more than once"),
    ("required-excluded", _bad_required_excluded, "no default"),
    ("progressive-schema", _bad_progressive_with_schema, "not supported"),
    ("progressive-optional", _bad_progressive_with_optional, "not supported"),
    ("progressive-count", _bad_progressive_active_count, "active"),
    (
        "progressive-count-excluded",
        _bad_progressive_active_counts_excluded,
        "3 active entries but the container declares 2 SSZ fields",
    ),
]


@pytest.mark.parametrize(
    "define,match",
    [pytest.param(fn, match, id=name) for name, fn, match in BAD_DECLARATIONS],
)
def test_bad_declaration_fails_at_import(
    define: Callable[[], None], match: str
) -> None:
    """Every mis-declared container fails at class definition, named."""
    with pytest.raises(TypeError, match=match):
        define()


STRICTNESS: List[Tuple[str, Optional[str], str]] = [
    ("bare-encode", None, "fork-scoped"),
    ("older-fork", "Paris", "unexpected=\\['withdrawals'\\]"),
    ("newer-fork", "Cancun", "missing=\\['blob_gas_used'\\]"),
    ("unknown-fork", "Osaka", "unknown fork"),
]


@pytest.mark.parametrize(
    "fork,match",
    [pytest.param(f, m, id=name) for name, f, m in STRICTNESS],
)
def test_forked_model_strictness(fork: Optional[str], match: str) -> None:
    """A Shanghai payload only encodes under the Shanghai schema."""
    with pytest.raises(TypeError, match=match):
        encode(_shanghai_payload(), fork=fork)


NOT_FORK_SCOPED: List[Tuple[str, Callable[[], object]]] = [
    ("encode", lambda: encode(_withdrawal(), fork="Paris")),
    ("decode", lambda: decode(Withdrawal, b"", fork="Paris")),
    ("describe", lambda: describe_schema(Withdrawal, fork="Paris")),
    ("default", lambda: ssz_default(Withdrawal, "Paris")),
    ("fields", lambda: ssz_fields(Withdrawal, "Paris")),
]


@pytest.mark.parametrize(
    "call",
    [pytest.param(c, id=name) for name, c in NOT_FORK_SCOPED],
)
def test_fork_on_complete_model_raises(call: Callable[[], object]) -> None:
    """Passing fork= to a non-fork-scoped model raises on every path."""
    with pytest.raises(TypeError, match="is not fork-scoped"):
        call()


def test_ssz_default_per_fork() -> None:
    """ssz_default(fork) zeroes that fork's fields, leaves the rest None."""
    zero = ssz_default(ForkedPayload, "Shanghai")
    assert zero.withdrawals == []
    assert zero.blob_gas_used is None  # beyond Shanghai: absent, not zero
    assert encode(zero, "Shanghai") == RefForkedShanghai().encode_bytes()
    with pytest.raises(TypeError, match="fork-scoped"):
        ssz_default(ForkedPayload)  # bare default: must name the fork


@pytest.mark.parametrize("mutation", ["truncate", "extend"])
def test_decode_of_malformed_bytes_raises(mutation: str) -> None:
    """Truncated or oversized SSZ data raises, never mis-decodes."""
    raw = encode(_withdrawal())
    data = raw[:-1] if mutation == "truncate" else raw + b"\x00"
    with pytest.raises(ValueError):
        decode(Withdrawal, data)


def test_decode_under_wrong_fork_does_not_silently_succeed() -> None:
    """Shanghai bytes decoded as Cancun raise (schema sizes differ)."""
    raw = encode(_shanghai_payload(), fork="Shanghai")
    with pytest.raises(Exception):  # noqa: B017 - remerkleable's error
        decode(ForkedPayload, raw, fork="Cancun")


def test_build_ssz_type_cache_identity() -> None:
    """One cache entry per (class, fork); distinct classes never share."""
    assert build_ssz_type(Withdrawal) is build_ssz_type(Withdrawal, None)
    assert build_ssz_type(ForkedPayload, "Paris") is build_ssz_type(
        ForkedPayload, "Paris"
    )
    assert build_ssz_type(ForkedPayload, "Paris") is not build_ssz_type(
        ForkedPayload, "Shanghai"
    )

    def make_dup() -> type:
        class Dup(SSZModel):
            a: Uint64

        return Dup

    first, second = make_dup(), make_dup()
    assert first is not second
    assert build_ssz_type(first) is not build_ssz_type(second)


UINT_WIDTHS = [
    (Uint8, 8),
    (Uint16, 16),
    (Uint32, 32),
    (Uint64, 64),
    (Uint128, 128),
    (Uint256, 256),
]


@pytest.mark.parametrize(
    "uint_cls,bits",
    [pytest.param(c, b, id=c.__name__) for c, b in UINT_WIDTHS],
)
def test_uint_width_checked_at_construction(uint_cls: type, bits: int) -> None:
    """A wrong-width value fails when built, not at first encode."""
    assert int(uint_cls((1 << bits) - 1)) == (1 << bits) - 1
    with pytest.raises(ValueError, match="out of range"):
        uint_cls(1 << bits)
    with pytest.raises(ValueError, match="out of range"):
        uint_cls(-1)


def test_uint_width_checked_at_model_parse() -> None:
    """Pydantic parsing of an overflowing value fails loudly."""
    with pytest.raises(ValidationError):
        Withdrawal(
            index=1,
            validator_index=2,
            address=Address(b"\x00" * 20),
            amount=1 << 64,  # one past uint64
        )


def test_excluded_field_is_json_only() -> None:
    """ssz_exclude()d fields exist in JSON but are invisible to SSZ."""
    value = Mixed(a=7, note="kept in JSON")
    assert "note" in value.model_dump(mode="json")
    assert ssz_fields(Mixed) == ("a",)
    # decode cannot see the field; it comes back as the default
    restored = decode(Mixed, encode(value))
    assert int(restored.a) == 7
    assert restored.note == "json-only"


def test_excluded_field_on_fork_scoped_model() -> None:
    """Exclusion composes with __ssz_schema__ (schema skips the field)."""

    class ForkedMixed(SSZModel):
        a: Uint64
        b: Uint64 | None = None
        note: Annotated[str, ssz_exclude()] = "aux"

        __ssz_schema__ = SSZForkSchema(
            base_fork="One",
            base=("a",),
            appended={"Two": ("b",)},
        )

    value = ForkedMixed(a=1, note="ride-along")
    assert ssz_fields(ForkedMixed, "One") == ("a",)
    restored = decode(ForkedMixed, encode(value, "One"), "One")
    assert restored.b is None
    assert restored.note == "aux"


def test_excluded_field_takes_no_active_slot() -> None:
    """An excluded field is absent from the active-field bitvector."""
    assert ssz_fields(MixedProg) == ("a", "c")

    class GapMixedProg(ProgressiveModel):
        __active_fields__ = [1, 0, 1]  # two active, two SSZ fields

        a: Uint64
        note: Annotated[str, ssz_exclude()] = "json-only"
        c: Uint64

    assert ssz_fields(GapMixedProg) == ("a", "c")
    assert hash_tree_root(GapMixedProg(a=1, c=3)) == hash_tree_root(
        GapProg(a=1, c=3)
    )


def test_exclusion_is_inherited() -> None:
    """A subclass keeps the base's excluded fields excluded."""

    class MixedChild(Mixed):
        b: Uint64

    assert ssz_fields(MixedChild) == ("a", "b")


def test_spec_of_rejects_excluded_field() -> None:
    """spec_of refuses excluded fields instead of resolving the type."""
    with pytest.raises(TypeError, match="SSZ-excluded"):
        spec_of(Mixed, "note")


def test_single_fork_schema_works_end_to_end() -> None:
    """A schema with no appended forks is valid and encodable."""

    class OnlyFork(SSZModel):
        a: Uint64

        __ssz_schema__ = SSZForkSchema(
            base_fork="Only", base=("a",), appended={}
        )

    value = OnlyFork(a=5)
    assert ssz_fields(OnlyFork, "Only") == ("a",)
    assert decode(OnlyFork, encode(value, "Only"), "Only") == value
