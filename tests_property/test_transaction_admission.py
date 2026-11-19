"""
Which transactions a block admits, each rule pinned on both sides.

A random transaction goes into a block built to fit it exactly: the sender
holds the framework's minimum balance at the transaction's nonce, the base
fees equal the transaction's caps, and the block has just enough of each
kind of gas left. That transaction must be admitted. Each case then makes
the smallest change that breaks one rule, or moves to the last value a rule
still allows.
"""

from dataclasses import dataclass, replace
from typing import Any, Callable, Dict, Sequence

import pytest
from ethereum_types.bytes import Bytes, Bytes0
from ethereum_types.numeric import U64, U256, Uint
from execution_testing import Hash, Transaction, TransactionType
from execution_testing.forks import Fork
from execution_testing.test_types.balance_expectations import (
    effective_gas_price,
)
from hypothesis import assume, given
from hypothesis import strategies as st

import ethereum.exceptions
from ethereum.crypto.hash import keccak256
from ethereum.state import EMPTY_CODE_HASH, Account, Address
from ethereum.state_mpt import State
from ethereum_spec_tools.forks import Hardfork

from .forks import requires
from .spec_api import spec_transaction, zeroed
from .strategies import (
    MAX_U64,
    MAX_U256,
    VERSIONED_HASH,
    framework_tx_fields,
    intrinsic_execution_gas,
    ints,
    minimum_gas_limit,
    signed,
)

# The block state tracker that `check_transaction` reads arrives with
# EIP-7928, together with the checks gathered into one admission function.
pytestmark = requires(lambda fork: fork.header_bal_hash_required())

# EIP-7702: code that delegates the account to `address`.
DELEGATION_PREFIX = b"\xef\x01\x00"
# Any other code makes the sender a contract (EIP-3607).
CONTRACT_CODE = b"\x60\x00"

BLOB_GAS_BOUND = 1 << 30
FEE_MARKET_TYPES = [
    TransactionType.BASE_FEE,
    TransactionType.BLOB_TRANSACTION,
    TransactionType.SET_CODE,
]
GAS_PRICE_TYPES = [TransactionType.LEGACY, TransactionType.ACCESS_LIST]


@dataclass(frozen=True)
class Block:
    """The sender's account and the block a transaction is admitted to."""

    sender_nonce: int
    sender_balance: int
    sender_code: bytes
    base_fee: int
    excess_blob_gas: int
    execution_gas_left: int
    state_gas_left: int
    blob_gas_left: int


def largest_excess_priced_within(fork: Fork, fee_cap: int) -> int:
    """Return the largest excess blob gas whose price `fee_cap` covers."""
    price = fork.blob_gas_price_calculator()
    low, high = 0, BLOB_GAS_BOUND
    while low < high:
        middle = (low + high + 1) // 2
        if price(excess_blob_gas=middle) <= fee_cap:
            low = middle
        else:
            high = middle - 1
    return low


def exact_fit(fork: Fork, tx: Transaction) -> Block:
    """Return the block that admits `tx` with nothing to spare."""
    blob_gas = len(tx.blob_versioned_hashes or []) * fork.blob_gas_per_blob()
    tx_gas_cap = fork.transaction_gas_limit_cap()
    assert tx_gas_cap is not None
    return Block(
        sender_nonce=int(tx.nonce),
        sender_balance=tx.signer_minimum_balance(fork=fork),
        sender_code=b"",
        base_fee=int(tx.max_fee_per_gas or tx.gas_price or 0),
        excess_blob_gas=largest_excess_priced_within(
            fork, int(tx.max_fee_per_blob_gas or 0)
        ),
        # EIP-7825 caps the execution gas one transaction can use.
        execution_gas_left=min(int(tx.gas_limit), tx_gas_cap),
        state_gas_left=int(tx.gas_limit),
        blob_gas_left=blob_gas,
    )


def admit(
    spec: Hardfork,
    fork: Fork,
    tx: Transaction,
    block: Block,
    change_spec_tx: Callable[[Any], Any] = lambda tx: tx,
) -> Any:
    """
    Run the spec's admission check for `tx` in `block`, and return the
    environment it builds for execution.
    """
    vm = spec.module("vm")
    tracker = spec.module("state_tracker")
    bal = spec.module("block_access_lists")
    transactions = spec.module("transactions")

    block_state = tracker.BlockState(pre_state=State())
    code_hash = keccak256(block.sender_code) if block.sender_code else None
    assert tx.sender is not None
    block_state.account_writes[Address(tx.sender)] = Account(
        nonce=Uint(block.sender_nonce),
        balance=U256(block.sender_balance),
        code_hash=code_hash or EMPTY_CODE_HASH,
    )
    if code_hash is not None:
        block_state.code_writes[code_hash] = Bytes(block.sender_code)

    block_gas_limit = max(block.execution_gas_left, block.state_gas_left)
    max_blob_gas = fork.max_blobs_per_block() * fork.blob_gas_per_blob()
    block_env = zeroed(
        vm.BlockEnvironment,
        state=block_state,
        block_gas_limit=Uint(block_gas_limit),
        base_fee_per_gas=Uint(block.base_fee),
        excess_blob_gas=U64(block.excess_blob_gas),
        block_access_list_builder=bal.BlockAccessListBuilder(),
    )
    block_output = vm.BlockOutput(
        block_gas_used=Uint(block_gas_limit - block.execution_gas_left),
        block_state_gas_used=Uint(block_gas_limit - block.state_gas_left),
        blob_gas_used=U64(max(max_blob_gas - block.blob_gas_left, 0)),
    )
    spec_tx = change_spec_tx(spec_transaction(transactions, tx))
    return spec.module("fork").check_transaction(
        block_env, block_output, spec_tx, Uint(0)
    )


@dataclass(frozen=True)
class Case:
    """One change from the exact fit, and what the spec must make of it."""

    types: Sequence[int]
    """The transaction types the rule applies to."""
    rejected_with: str | None
    """The exception the spec raises, or None when it still admits."""
    tx: Callable[..., Dict[str, Any]] = lambda f, **_: f
    """
    Change the transaction's fields `f` before the block is fitted to it,
    given by keyword along with the `fork`.
    """
    block: Callable[[Block], Block] = lambda block: block
    """Change the block after it is fitted to the transaction."""
    spec_tx: Callable[[Any], Any] = lambda tx: tx
    """Change the spec's transaction, for a shape the framework can't build."""


ALL_TYPES = list(TransactionType)
CREATING_TYPES = [*GAS_PRICE_TYPES, TransactionType.BASE_FEE]
CASES: Dict[str, Case] = {
    "nonce_below_the_account": Case(
        ALL_TYPES,
        "NonceMismatchError",
        block=lambda b: replace(b, sender_nonce=b.sender_nonce + 1),
    ),
    "nonce_above_the_account": Case(
        ALL_TYPES,
        "NonceMismatchError",
        block=lambda b: replace(b, sender_nonce=b.sender_nonce - 1),
    ),
    # EIP-2681: the nonce stays below 2**64 - 1.
    "nonce_at_the_last_valid": Case(
        ALL_TYPES, None, tx=lambda f, **_: {**f, "nonce": MAX_U64 - 1}
    ),
    "nonce_at_the_limit": Case(
        ALL_TYPES,
        "NonceOverflowError",
        tx=lambda f, **_: {**f, "nonce": MAX_U64},
    ),
    "balance_one_short": Case(
        ALL_TYPES,
        "InsufficientBalanceError",
        block=lambda b: replace(b, sender_balance=b.sender_balance - 1),
    ),
    "sender_delegated": Case(
        ALL_TYPES,
        None,
        block=lambda b: replace(
            b, sender_code=DELEGATION_PREFIX + b"\x01" * 20
        ),
    ),
    "sender_is_a_contract": Case(
        ALL_TYPES,
        "InvalidSenderError",
        block=lambda b: replace(b, sender_code=CONTRACT_CODE),
    ),
    "sender_delegation_one_byte_short": Case(
        ALL_TYPES,
        "InvalidSenderError",
        block=lambda b: replace(
            b, sender_code=DELEGATION_PREFIX + b"\x01" * 19
        ),
    ),
    "sender_delegation_one_byte_long": Case(
        ALL_TYPES,
        "InvalidSenderError",
        block=lambda b: replace(
            b, sender_code=DELEGATION_PREFIX + b"\x01" * 21
        ),
    ),
    "sender_delegation_of_another_version": Case(
        ALL_TYPES,
        "InvalidSenderError",
        block=lambda b: replace(b, sender_code=b"\xef\x01\x01" + b"\x01" * 20),
    ),
    "max_fee_below_the_base_fee": Case(
        FEE_MARKET_TYPES,
        "InsufficientMaxFeePerGasError",
        block=lambda b: replace(b, base_fee=b.base_fee + 1),
    ),
    "gas_price_below_the_base_fee": Case(
        GAS_PRICE_TYPES,
        "InsufficientMaxFeePerGasError",
        block=lambda b: replace(b, base_fee=b.base_fee + 1),
    ),
    "priority_fee_at_the_max_fee": Case(
        FEE_MARKET_TYPES,
        None,
        tx=lambda f, **_: {
            **f,
            "max_priority_fee_per_gas": f["max_fee_per_gas"],
        },
    ),
    "priority_fee_above_the_max_fee": Case(
        FEE_MARKET_TYPES,
        "PriorityFeeGreaterThanMaxFeeError",
        tx=lambda f, **_: {
            **f,
            "max_priority_fee_per_gas": f["max_fee_per_gas"] + 1,
        },
    ),
    "execution_gas_one_short": Case(
        ALL_TYPES,
        "GasUsedExceedsLimitError",
        block=lambda b: replace(
            b, execution_gas_left=b.execution_gas_left - 1
        ),
    ),
    "state_gas_one_short": Case(
        ALL_TYPES,
        "GasUsedExceedsLimitError",
        block=lambda b: replace(b, state_gas_left=b.state_gas_left - 1),
    ),
    "init_code_at_the_limit": Case(
        CREATING_TYPES,
        None,
        tx=lambda f, fork: {
            **f,
            "to": None,
            "data": b"\x00" * fork.max_initcode_size(),
        },
    ),
    "init_code_one_too_large": Case(
        CREATING_TYPES,
        "InitCodeTooLargeError",
        tx=lambda f, fork: {
            **f,
            "to": None,
            "data": b"\x00" * (fork.max_initcode_size() + 1),
        },
    ),
    "blob_fee_cap_below_the_price": Case(
        [TransactionType.BLOB_TRANSACTION],
        "InsufficientMaxFeePerBlobGasError",
        block=lambda b: replace(b, excess_blob_gas=b.excess_blob_gas + 1),
    ),
    "blob_gas_one_short": Case(
        [TransactionType.BLOB_TRANSACTION],
        "BlobGasLimitExceededError",
        block=lambda b: replace(b, blob_gas_left=b.blob_gas_left - 1),
    ),
    "no_blobs": Case(
        [TransactionType.BLOB_TRANSACTION],
        "NoBlobDataError",
        tx=lambda f, **_: {**f, "blob_versioned_hashes": []},
    ),
    "one_blob_too_many": Case(
        [TransactionType.BLOB_TRANSACTION],
        "BlobCountExceededError",
        tx=lambda f, fork: {
            **f,
            "blob_versioned_hashes": [VERSIONED_HASH]
            * (fork.max_blobs_per_tx() + 1),
        },
    ),
    "blob_hash_with_another_version": Case(
        [TransactionType.BLOB_TRANSACTION],
        "InvalidBlobVersionedHashError",
        tx=lambda f, **_: {
            **f,
            "blob_versioned_hashes": [Hash(b"\x02" + b"\x00" * 31)],
        },
    ),
    # Blob and set-code transactions type `to` as an address, so no encoding
    # can carry a creation; these two build one on the spec's object.
    "blob_transaction_creates": Case(
        [TransactionType.BLOB_TRANSACTION],
        "TransactionTypeContractCreationError",
        spec_tx=lambda tx: replace(tx, to=Bytes0(b"")),
    ),
    "set_code_transaction_creates": Case(
        [TransactionType.SET_CODE],
        "TransactionTypeContractCreationError",
        spec_tx=lambda tx: replace(tx, to=Bytes0(b"")),
    ),
    "no_authorizations": Case(
        [TransactionType.SET_CODE],
        "EmptyAuthorizationListError",
        tx=lambda f, **_: {**f, "authorization_list": []},
    ),
}


def exception_named(spec: Hardfork, name: str) -> type:
    """Return a fork's exception class, or a shared one like InvalidBlock."""
    fork_exceptions = spec.module("exceptions")
    if hasattr(fork_exceptions, name):
        return getattr(fork_exceptions, name)
    return getattr(ethereum.exceptions, name)


def fitted(fork: Fork, fields: Dict[str, Any], spare_gas: int) -> Transaction:
    """
    Return the transaction with `fields`, signed, with `spare_gas` above the
    least gas limit it needs.
    """
    minimum = minimum_gas_limit(fork, signed(fields))
    return signed({**fields, "gas_limit": minimum + spare_gas})


def spare_gas_near(fork: Fork) -> st.SearchStrategy[int]:
    """
    Return gas above a transaction's least limit: a little, or enough to
    put the limit on either side of the per-transaction execution cap.
    """
    cap = fork.transaction_gas_limit_cap()
    if cap is None:
        return ints(1 << 20)
    return st.one_of(
        ints(1 << 20), st.integers(cap - (1 << 20), cap + (1 << 20))
    )


def check_environment(
    fork: Fork, tx: Transaction, base_fee: int, env: Any
) -> None:
    """
    Check what admission hands to execution: the price per gas, and the
    gas left after the intrinsic cost, split at the EIP-7825 cap.
    """
    assert int(env.effective_gas_price) == effective_gas_price(tx, base_fee)
    cap = fork.transaction_gas_limit_cap()
    assert cap is not None
    intrinsic = intrinsic_execution_gas(fork, tx)
    grant = int(env.execution_gas_grant)
    assert grant == min(tx.gas_limit, cap) - intrinsic
    assert grant + int(env.state_gas_reservoir) == tx.gas_limit - intrinsic


@pytest.mark.parametrize("case_name", sorted(CASES))
@given(data=st.data())
def test_admission_rule_boundary(
    spec: Hardfork,
    fork: Fork,
    case_name: str,
    data: st.DataObject,
) -> None:
    """
    A transaction in a block built to fit it is admitted, and the case's
    change either keeps it admitted or makes the spec reject it with the
    case's exception.
    """
    case = CASES[case_name]
    spare_gas = data.draw(spare_gas_near(fork))
    types = [ty for ty in case.types if ty in fork.tx_types()]
    if not types:
        pytest.skip(f"{fork.name()} has no transaction type to change")
    fields = data.draw(framework_tx_fields(fork, types=types))
    # The framework's minimum balance reads a zero fee cap as unset.
    for fee_cap in ("gas_price", "max_fee_per_gas", "max_fee_per_blob_gas"):
        if fee_cap in fields:
            fields[fee_cap] = max(fields[fee_cap], 1)

    exact = fitted(fork, fields, spare_gas)
    assume(exact.gas_limit <= (fork.transaction_total_gas_limit_cap() or 0))
    block = exact_fit(fork, exact)
    # The balance field is 256 bits wide, so a transaction can cost more
    # than any sender holds.
    if block.sender_balance > MAX_U256:
        with pytest.raises(exception_named(spec, "InsufficientBalanceError")):
            admit(spec, fork, exact, replace(block, sender_balance=MAX_U256))
        return
    base_fee = data.draw(ints(block.base_fee))
    env = admit(spec, fork, exact, replace(block, base_fee=base_fee))
    check_environment(fork, exact, base_fee, env)

    changed = fitted(fork, case.tx(f=dict(fields), fork=fork), spare_gas)
    changed_block = case.block(exact_fit(fork, changed))
    assume(changed_block.sender_nonce >= 0)
    assume(changed_block.sender_balance <= MAX_U256)
    if case.rejected_with is None:
        admit(spec, fork, changed, changed_block, case.spec_tx)
    else:
        with pytest.raises(exception_named(spec, case.rejected_with)):
            admit(spec, fork, changed, changed_block, case.spec_tx)
