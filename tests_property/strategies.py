"""
Strategies for spec base types and framework transactions, weighted toward
boundary values.

Uniform random integers almost never land on the values where EVM
semantics change (zero, one, word boundaries, type maxima), so every
numeric strategy here mixes explicit boundary sampling with the full
range.
"""

from dataclasses import replace
from typing import Any, Callable, Dict, List, Sequence

from ethereum_types.bytes import Bytes, Bytes20
from ethereum_types.numeric import U64, U256, Uint
from execution_testing import (
    EOA,
    AuthorizationTuple,
    Hash,
    RecipientType,
    Transaction,
    TransactionType,
)
from execution_testing.base_types import AccessList
from execution_testing.forks import Fork
from hypothesis import strategies as st
from hypothesis import target

from ethereum.state import Address

# EIP-4844: a versioned hash starts with the KZG version byte.
# SEC 2, section 2.4.1: the order of secp256k1's group, which bounds a
# private key and a signature's `r` and `s`.
SECP256K1N = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141
VERSIONED_HASH = Hash(b"\x01" + b"\x00" * 31)

MAX_U64 = int(U64.MAX_VALUE)
MAX_U256 = int(U256.MAX_VALUE)

private_keys = st.integers(min_value=1, max_value=SECP256K1N - 1)


def _boundaries(bits: int) -> List[int]:
    values = {0, 1, 2, (1 << bits) - 1, (1 << bits) - 2}
    for exp in (7, 8, 15, 16, 31, 32, 63, 64, 127, 128, 255):
        if exp < bits:
            values.update({1 << exp, (1 << exp) - 1, (1 << exp) + 1})
    return sorted(values)


def ints(max_value: int) -> st.SearchStrategy[int]:
    """Return ints up to `max_value`, weighted toward boundaries."""
    boundaries = [b for b in _boundaries(256) if b <= max_value]
    return st.one_of(
        st.sampled_from(boundaries + [max_value]),
        st.integers(min_value=0, max_value=max_value),
    )


def u256s() -> st.SearchStrategy[U256]:
    """Return 256-bit unsigned integers, weighted toward boundaries."""
    return ints(MAX_U256).map(U256)


def u64s() -> st.SearchStrategy[U64]:
    """Return 64-bit unsigned integers, weighted toward boundaries."""
    return ints(MAX_U64).map(U64)


def uints(max_value: int = MAX_U64) -> st.SearchStrategy[Uint]:
    """Return `Uint`s up to `max_value`, weighted toward boundaries."""
    return ints(max_value).map(Uint)


def addresses() -> st.SearchStrategy[Address]:
    """Return random addresses."""
    return st.binary(min_size=20, max_size=20).map(
        lambda b: Address(Bytes20(b))
    )


def bytes_data(
    min_size: int = 0, max_size: int = 256
) -> st.SearchStrategy[Bytes]:
    """
    Return byte strings with sizes weighted toward 32-byte word
    boundaries, where memory expansion and calldata pricing change, and
    toward the 55 and 56 bytes where RLP moves to a long string prefix.
    """
    hotspot_sizes = sorted(
        {0, 1, 31, 32, 33, 55, 56, 63, 64, 65}
        & set(range(min_size, max_size + 1))
    )
    return st.one_of(
        st.sampled_from(hotspot_sizes).flatmap(
            lambda n: st.binary(min_size=n, max_size=n)
        ),
        st.binary(min_size=min_size, max_size=max_size),
    ).map(Bytes)


def framework_tx(ty: int, **fields: Any) -> Transaction:
    """
    Return a framework transaction of type `ty`, with one blob or one
    authorization where the type needs it, unless `fields` sets them.
    """
    defaults: Dict[str, Any] = {"gas_limit": 21_000}
    if ty == TransactionType.BLOB_TRANSACTION:
        defaults["blob_versioned_hashes"] = [VERSIONED_HASH]
    elif ty == TransactionType.SET_CODE:
        unsigned = AuthorizationTuple(address=0xCC, v=0, r=0, s=0)
        defaults["authorization_list"] = [unsigned]
    return Transaction(ty=ty, **{**defaults, **fields})


@st.composite
def framework_tx_fields(
    draw: st.DrawFn, fork: Fork, types: Sequence[int] | None = None
) -> Dict[str, Any]:
    """
    Return the fields of a random transaction of one of `types`, or of any
    type `fork` allows, with its type as `ty` and its signing key as
    `secret_key`, that pass the spec's validation apart from gas.
    """
    ty = draw(st.sampled_from(types or fork.tx_types()))
    key = draw(private_keys)
    sender = EOA(key=key)
    recipients: List[Any] = [draw(addresses()), sender]
    if ty in fork.contract_creating_tx_types():
        recipients.append(None)
    fields: Dict[str, Any] = {
        "ty": ty,
        "secret_key": key,
        "to": draw(st.sampled_from(recipients)),
        # EIP-2681: the highest nonce is invalid.
        "nonce": draw(ints(MAX_U64 - 1)),
        "gas_limit": draw(ints(MAX_U64)),
        "value": draw(ints(MAX_U256)),
        "data": draw(bytes_data()),
        "chain_id": draw(st.one_of(st.just(MAX_U64), st.integers(1, MAX_U64))),
    }
    if ty == TransactionType.LEGACY:
        fields["protected"] = fork.supports_protected_txs() and draw(
            st.booleans()
        )
    if ty in (TransactionType.LEGACY, TransactionType.ACCESS_LIST):
        fields["gas_price"] = draw(ints(MAX_U64))
    else:
        fee_cap = draw(ints(MAX_U64))
        fields["max_fee_per_gas"] = fee_cap
        fields["max_priority_fee_per_gas"] = draw(ints(fee_cap))
    if ty != TransactionType.LEGACY:
        fields["access_list"] = draw(access_lists())
    if ty == TransactionType.BLOB_TRANSACTION:
        fields["max_fee_per_blob_gas"] = draw(ints(MAX_U64))
        blob_count = draw(st.integers(1, fork.max_blobs_per_tx()))
        fields["blob_versioned_hashes"] = [VERSIONED_HASH] * blob_count
    if ty == TransactionType.SET_CODE:
        authorization = st.builds(
            AuthorizationTuple,
            chain_id=ints(MAX_U64),
            address=addresses(),
            nonce=ints(MAX_U64),
            secret_key=private_keys,
        )
        fields["authorization_list"] = draw(
            st.lists(authorization, min_size=1, max_size=4)
        )
    return fields


def signed(fields: Dict[str, Any]) -> Transaction:
    """Return the framework transaction with `fields`, signed."""
    return framework_tx(**fields).with_signature_and_sender()


def framework_txs(
    fork: Fork, types: Sequence[int] | None = None
) -> st.SearchStrategy[Transaction]:
    """
    Return signed framework transactions of one of `types`, or of every
    type `fork` allows, with random fields that still pass the spec's
    validation apart from gas.
    """
    return framework_tx_fields(fork, types).map(signed)


def minimum_gas_limit(fork: Fork, tx: Transaction) -> int:
    """Return the least gas limit the framework says `tx` needs."""
    return _intrinsic_cost(fork, tx, deducted_before_execution=False)


def intrinsic_execution_gas(fork: Fork, tx: Transaction) -> int:
    """Return the execution gas the framework says `tx` pays up front."""
    return _intrinsic_cost(fork, tx, deducted_before_execution=True)


def _intrinsic_cost(
    fork: Fork, tx: Transaction, *, deducted_before_execution: bool
) -> int:
    return fork.transaction_intrinsic_cost_calculator()(
        calldata=tx.data,
        contract_creation=tx.to is None,
        access_list=tx.access_list,
        authorization_list_or_count=tx.authorization_list,
        sends_value=tx.value > 0,
        recipient_type=(
            RecipientType.SELF
            if tx.to == tx.sender
            else RecipientType.CONTRACT
        ),
        return_cost_deducted_prior_execution=deducted_before_execution,
    )


def access_lists() -> st.SearchStrategy[List[AccessList]]:
    """Return short framework access lists."""
    entries = st.tuples(
        addresses().map(bytes),
        st.lists(st.binary(min_size=32, max_size=32), max_size=3),
    )
    return st.lists(
        entries.map(
            lambda entry: AccessList(address=entry[0], storage_keys=entry[1])
        ),
        max_size=3,
    )


def past(bound: int, offset: int) -> U256:
    """Return the value `offset` past `bound`, within 256 bits."""
    return U256(min(bound + offset, MAX_U256))


def highest_s(fork: Fork) -> int:
    """Return the largest `s` a fork accepts."""
    # EIP-2 keeps `s` in the lower half of the curve order.
    return SECP256K1N // 2 if fork.is_eip_enabled(2) else SECP256K1N - 1


# Each break returns `item`, a signed transaction or authorization, with one
# signature value at its bound plus `offset`. The `offset` and the `fork` come
# by keyword.
SIGNATURE_BREAKS: Dict[str, Callable[..., Any]] = {
    "r_zero": lambda item, **_: replace(item, r=U256(0)),
    "r_past_the_curve_order": lambda item, offset, **_: replace(
        item, r=past(SECP256K1N, offset)
    ),
    "s_zero": lambda item, **_: replace(item, s=U256(0)),
    "s_past_its_bound": lambda item, fork, offset: replace(
        item, s=past(highest_s(fork) + 1, offset)
    ),
    "y_parity_past_one": lambda item, offset, **_: replace(
        item, y_parity=past(2, offset)
    ),
}


def aim_at(value: int, edge: int, label: str) -> None:
    """
    Score `value` by how close it lands to `edge`, so Hypothesis spends
    more examples on both sides of a rule's boundary.

    Hypothesis's `target()` keeps the examples that score highest on a
    label and mutates them further.
    """
    target(-abs(value - edge), label=label)
