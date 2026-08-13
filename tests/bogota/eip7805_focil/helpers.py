"""Shared helpers for Amsterdam EIP-7805 FOCIL tests."""

from typing import NamedTuple

from execution_testing import (
    EOA,
    Alloc,
    Fork,
    Transaction,
)


class TransactionWithOrigin(NamedTuple):
    """Transaction plus whether it appeared in any inclusion list."""

    tx: Transaction
    is_inclusion_list_tx: bool


class IncludedBlockTx(NamedTuple):
    """Description of a transaction already included in the block body."""

    actual_gas_used: int
    nonce: int = 0
    is_inclusion_list_tx: bool = False
    sender_label: str | None = None
    sender_balance: int = 10**18


class PendingInclusionListTx(NamedTuple):
    """Description of an IL transaction omitted from the block body."""

    actual_gas_used: int
    nonce: int = 0
    sender_label: str | None = None
    sender_balance: int = 10**18


# EIP-7928 caps a block's access list at `block_gas_limit //
# GAS_BLOCK_ACCESS_LIST_ITEM` items (2000 gas per item on Amsterdam). These
# scenarios size the block gas limit to the transactions alone, which on the
# current Amsterdam leaves no budget for the block's own access list: the
# system-contract predeploys touched every block (beacon roots, history, the
# EIP-7002/7251 request contracts and the EIP-8282 builder deposit/exit pair)
# plus the senders, recipients and coinbase come to ~30 items against a limit
# of ~22, and every fixture fails to fill with
# `BlockAccessListGasLimitExceededError`.
#
# Raising the limit alone would change what the scenarios assert, because the
# gas a pending IL transaction is allowed is derived from
# `block_gas_limit - gas_used_by_included_txs`. So `build_block` raises the
# limit and spends exactly the same amount on a ballast transaction, leaving
# `remaining_gas` — and therefore every "fits" / "does not fit" boundary —
# byte-for-byte what it was.
# Gas to add. Realised as a whole number of empty transfers so the amount is
# always representable on the fork's calldata-cost lattice (a flat target like
# 64_000 is not, once EIP-7623's floor makes marginal calldata cost non-linear).


def bal_gas_headroom(fork: Fork) -> int:
    """Gas added to a block's limit to leave room for its own access list."""
    empty_transfer_gas = fork.transaction_intrinsic_cost_calculator()()
    bal_gas_headroom_target = (
        fork.empty_block_bal_item_count()
        * fork.gas_costs().BLOCK_ACCESS_LIST_ITEM
    )
    count = -(-bal_gas_headroom_target // empty_transfer_gas)
    return count * empty_transfer_gas


class BuiltBlock(NamedTuple):
    """
    Concrete block data plus the derived gas headroom.

    We simulate having received a block that contains a bunch of `block_txs`.
    We also simulate that we have access to every committee member's
    inclusion lists and we already flattened all of these IL txs into one list
    we call `inclusion_list_txs`. If a member of this list was included in a
    block it will exists both in `block_txs` and in `inclusion_list_txs`.
    If a member of `inclusion_list_txs` is not in `block_txs` then for an
    accepted block this means that one of the IL tx validity checks failed.

    A block is invalid when it has enough `remaining_gas` so that it could
    have included a valid member of `inclusion_list_txs` in `block_txs` but did
    not.

    The validity checks for any member of `inclusion_list_txs` are:
    1. Sender `nonce` is correct
    2. Sender `balance` could have afforded the tx

    `effective_gas_limit` is the gas limit the block must actually declare:
    the caller's `block_gas_limit` plus `BAL_GAS_HEADROOM`. Pass it to
    `Environment(gas_limit=...)` instead of the raw value.

    These helpers only describe the block body, the flattened IL view, and
    the gas headroom for a scenario. The actual satisfaction check is done by
    the Amsterdam fork logic after block execution, when it re-validates any
    missing IL transactions against the block's post-state.

    """

    block_txs: list[Transaction]
    inclusion_list_txs: list[Transaction]
    remaining_gas: int
    effective_gas_limit: int


def _resolve_sender(
    pre: Alloc,
    *,
    senders_by_label: dict[str, EOA],
    sender_label: str | None,
    sender_balance: int,
) -> EOA:
    """
    Return a fresh sender or reuse one selected by label.

    This is a helper function for `build_block()`.

    """
    if sender_label is None:
        return pre.fund_eoa(amount=sender_balance)
    if sender_label not in senders_by_label:
        senders_by_label[sender_label] = pre.fund_eoa(amount=sender_balance)
    return senders_by_label[sender_label]


def generate_custom_tx(
    pre: Alloc,
    *,
    fork: Fork,
    actual_gas_used: int,
    is_inclusion_list_tx: bool,
    nonce: int = 0,
    sender: EOA | None = None,
) -> TransactionWithOrigin:
    """Create a plain transfer tx with a specific intrinsic gas usage."""
    if sender is None:
        sender = pre.fund_eoa(amount=10**18)
    recipient = pre.fund_eoa()
    calldata = _build_calldata_for_intrinsic_gas_used(
        fork=fork,
        actual_gas_used=actual_gas_used,
    )
    tx = Transaction(
        sender=sender,
        nonce=nonce,
        to=recipient,
        gas_limit=actual_gas_used,
        data=calldata,
    )
    return TransactionWithOrigin(
        tx=tx, is_inclusion_list_tx=is_inclusion_list_tx
    )


def _build_calldata_for_intrinsic_gas_used(
    *, fork: Fork, actual_gas_used: int
) -> bytes:
    """
    Build calldata for a plain transfer with exactly this intrinsic gas.

    This is a helper function for `generate_custom_tx()`.
    """
    intrinsic_cost_calculator = fork.transaction_intrinsic_cost_calculator()
    empty_transfer_gas = intrinsic_cost_calculator()
    if actual_gas_used < empty_transfer_gas:
        raise ValueError(
            f"actual gas used must be >= empty transfer intrinsic gas: "
            f"{actual_gas_used} < {empty_transfer_gas}"
        )

    additional_gas = actual_gas_used - empty_transfer_gas
    if additional_gas == 0:
        return b""

    zero_byte_cost = (
        intrinsic_cost_calculator(calldata=b"\x00") - empty_transfer_gas
    )
    nonzero_byte_cost = (
        intrinsic_cost_calculator(calldata=b"\x01") - empty_transfer_gas
    )
    for nonzero_byte_count in range(additional_gas // nonzero_byte_cost + 1):
        remaining_gas = additional_gas - (
            nonzero_byte_count * nonzero_byte_cost
        )
        if remaining_gas % zero_byte_cost == 0:
            zero_byte_count = remaining_gas // zero_byte_cost
            return (b"\x01" * nonzero_byte_count) + (b"\x00" * zero_byte_count)

    raise ValueError(
        "requested actual gas used is not representable with calldata "
        f"costs for this fork: {actual_gas_used}"
    )


def flatten_inclusion_list_txs(
    txs_with_origins: list[TransactionWithOrigin],
) -> list[Transaction]:
    """
    Return the flattened EL view of transactions that appeared in any IL.

    These tests do not model distinct committee-member inclusion lists.
    Instead, they pass the execution layer the single flattened list of
    transactions that appeared in any inclusion list, because that is the
    only membership information the EL consumes here.
    """
    return [
        tx_with_origin.tx
        for tx_with_origin in txs_with_origins
        if tx_with_origin.is_inclusion_list_tx
    ]


def build_block(
    pre: Alloc,
    *,
    fork: Fork,
    block_gas_limit: int,
    included_block_tx_specs: tuple[IncludedBlockTx, ...],
    pending_inclusion_list_tx_specs: tuple[PendingInclusionListTx, ...],
) -> BuiltBlock:
    """Build block-body txs, flattened IL txs, and remaining gas."""
    senders_by_label: dict[str, EOA] = {}
    included_block_txs = [
        generate_custom_tx(
            pre,
            fork=fork,
            actual_gas_used=tx_spec.actual_gas_used,
            nonce=tx_spec.nonce,
            is_inclusion_list_tx=tx_spec.is_inclusion_list_tx,
            sender=_resolve_sender(
                pre,
                senders_by_label=senders_by_label,
                sender_label=tx_spec.sender_label,
                sender_balance=tx_spec.sender_balance,
            ),
        )
        for tx_spec in included_block_tx_specs
    ]
    pending_inclusion_list_txs = [
        generate_custom_tx(
            pre,
            fork=fork,
            actual_gas_used=tx_spec.actual_gas_used,
            nonce=tx_spec.nonce,
            is_inclusion_list_tx=True,
            sender=_resolve_sender(
                pre,
                senders_by_label=senders_by_label,
                sender_label=tx_spec.sender_label,
                sender_balance=tx_spec.sender_balance,
            ),
        )
        for tx_spec in pending_inclusion_list_tx_specs
    ]
    gas_used_by_included_txs = sum(
        tx_spec.actual_gas_used for tx_spec in included_block_tx_specs
    )

    # Ballast: burns exactly the extra gas the raised limit adds, so
    # `remaining_gas` below is identical to what it was before the limit was
    # raised for the EIP-7928 access-list budget. It is a plain transfer from a
    # fresh sender and appears in no inclusion list, so it cannot affect which
    # IL transactions are appendable.
    empty_transfer_gas = fork.transaction_intrinsic_cost_calculator()()
    headroom = bal_gas_headroom(fork)
    ballast_txs = [
        generate_custom_tx(
            pre,
            fork=fork,
            actual_gas_used=empty_transfer_gas,
            is_inclusion_list_tx=False,
        ).tx
        for _ in range(headroom // empty_transfer_gas)
    ]

    return BuiltBlock(
        block_txs=ballast_txs
        + [tx_with_origin.tx for tx_with_origin in included_block_txs],
        inclusion_list_txs=flatten_inclusion_list_txs(
            included_block_txs + pending_inclusion_list_txs
        ),
        remaining_gas=block_gas_limit - gas_used_by_included_txs,
        effective_gas_limit=block_gas_limit + headroom,
    )
