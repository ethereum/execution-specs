"""
Properties of the signature values sender recovery accepts.

The framework signs each transaction, so a valid signature and the sender
it recovers are known apart from the spec. Each rule is then broken from
that signature, at the first value past its bound and beyond.
"""

from dataclasses import replace
from types import ModuleType
from typing import Any, Callable, Dict, Sequence

import pytest
from ethereum_types.bytes import Bytes
from ethereum_types.numeric import U64, U256
from execution_testing import Transaction, TransactionType
from execution_testing.forks import Fork
from hypothesis import given
from hypothesis import strategies as st

from ethereum.exceptions import InvalidSignatureError
from ethereum.state import Address

from .forks import requires
from .spec_api import (
    sender_of,
    spec_transaction,
)
from .strategies import (
    MAX_U256,
    SECP256K1N,
    SIGNATURE_BREAKS,
    addresses,
    bytes_data,
    framework_tx,
    framework_txs,
    highest_s,
    past,
    private_keys,
)

TYPED = [ty for ty in TransactionType if ty != TransactionType.LEGACY]
# EIP-155: a protected `v` is `35 + 2 * chain_id + parity`.
FIRST_PROTECTED_V = 35


# The signature breaks shared with authorizations, and two that only a
# legacy transaction's `v` can make.
BREAKS: Dict[str, Callable[..., Any]] = {
    **SIGNATURE_BREAKS,
    "v_below_the_protected_range": lambda tx, offset, **_: replace(
        tx, v=U256(FIRST_PROTECTED_V - 1 - offset % (FIRST_PROTECTED_V - 29))
    ),
    "chain_id_past_64_bits": lambda tx, offset, **_: replace(
        tx, v=past(FIRST_PROTECTED_V + 2 * 2**64, 2 * offset)
    ),
}
BREAK_TYPES: Dict[str, Sequence[int]] = {
    "y_parity_past_one": TYPED,
    "v_below_the_protected_range": [TransactionType.LEGACY],
    "chain_id_past_64_bits": [TransactionType.LEGACY],
}
# Each rule flips at its bound and nothing changes past it, so the first
# values past it and the top of the field are the offsets that matter. The
# first six also walk `v` through every value below the protected range.
OFFSETS = st.sampled_from([*range(FIRST_PROTECTED_V - 29), 2**64, MAX_U256])


def breakable(break_name: str) -> Any:
    """Return the break as a parameter for forks with a type it breaks."""
    types = BREAK_TYPES.get(break_name, list(TransactionType))
    has_a_type = requires(
        lambda fork: any(ty in fork.tx_types() for ty in types)
    )
    return pytest.param(break_name, marks=has_a_type)


@pytest.mark.parametrize("break_name", [breakable(b) for b in sorted(BREAKS)])
@given(data=st.data(), offset=OFFSETS)
def test_signature_values_past_their_bounds_are_rejected(
    fork: Fork,
    transactions: ModuleType,
    break_name: str,
    data: st.DataObject,
    offset: int,
) -> None:
    """
    A valid signature recovers the framework's sender, and the same
    transaction with one signature value at or past its bound is rejected.
    """
    types = BREAK_TYPES.get(break_name, list(TransactionType))
    types = [ty for ty in types if ty in fork.tx_types()]
    framework = data.draw(framework_txs(fork, types))
    tx = spec_transaction(transactions, framework)
    assert sender_of(transactions, tx) == framework.sender

    with pytest.raises(InvalidSignatureError):
        broken = BREAKS[break_name](tx, fork=fork, offset=offset)
        sender_of(transactions, broken)


@given(data=st.data())
def test_s_at_its_bound_is_accepted(
    fork: Fork, transactions: ModuleType, data: st.DataObject
) -> None:
    """
    A signature whose `s` is the largest the fork accepts recovers a
    sender, the accepting side of the `s_past_its_bound` break.
    """
    framework = data.draw(framework_txs(fork))
    tx = spec_transaction(transactions, framework)
    sender_of(transactions, replace(tx, s=U256(highest_s(fork))))


def signed_legacy_tx(key: int, data: Bytes, to: Address) -> Transaction:
    """Return a legacy call signed by `key`, without a chain id."""
    return framework_tx(
        TransactionType.LEGACY,
        protected=False,
        secret_key=key,
        data=data,
        to=to,
    ).with_signature_and_sender()


@given(key=private_keys, data=bytes_data(max_size=64), to=addresses())
def test_high_s_signatures_are_rejected_from_eip_2(
    fork: Fork, transactions: ModuleType, key: int, data: Bytes, to: Address
) -> None:
    """
    A malleable high-s signature recovers the same sender before EIP-2 and
    is rejected from EIP-2 on.
    """
    framework = signed_legacy_tx(key, data, to)
    tx = spec_transaction(transactions, framework)
    # Negating `s` and flipping the parity gives a second valid signature.
    flipped = replace(tx, v=U256(55) - tx.v, s=U256(SECP256K1N) - tx.s)
    if fork.is_eip_enabled(2):
        with pytest.raises(InvalidSignatureError):
            transactions.recover_sender(flipped)
    else:
        assert transactions.recover_sender(flipped) == framework.sender


@requires(lambda fork: fork.supports_protected_txs())
def test_replay_protected_signing_matches_the_worked_example(
    transactions: ModuleType,
) -> None:
    """The spec reproduces the signing hash and sender of EIP-155's example."""
    example: Any = Transaction(
        ty=TransactionType.LEGACY,
        nonce=9,
        gas_price=20 * 10**9,
        gas_limit=21000,
        to=b"\x35" * 20,
        value=10**18,
        v=37,
        r=18515461264373351373200002665853028612451056578545711640558177340181847433846,
        s=46948507304638947509940763649030358759909902576025900602547168820602576006531,
    )
    tx = spec_transaction(transactions, example)
    assert transactions.signing_hash_155(tx, U64(1)) == bytes.fromhex(
        "daf5a779ae972f972197303d7b574746c7ef83eadac0f2791ad23db92e4c8e53"
    )
    assert transactions.recover_sender(tx) == Address(
        bytes.fromhex("9d8a62f656a8d1615c1294fd71e9cfb3e4855a4f")
    )
