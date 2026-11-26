"""
Chain invariants checked on every valid block while filling.

Enabled with `fill --invariant-checks`. A violation is raised as an
`InvariantViolationError`, which fails the fill on the first one found.
"""

from collections import Counter
from dataclasses import dataclass
from typing import AbstractSet, Dict, Optional, Sequence, Set, Tuple

from execution_testing.base_types import Account, Address
from execution_testing.client_clis.cli_types import Result
from execution_testing.evm_tools.t8n.evm_trace.bal_witness import (
    BalWitness,
    SlotAccess,
)
from execution_testing.forks import Fork
from execution_testing.test_types import Alloc, Transaction
from execution_testing.test_types.block_access_list import (
    BalAccountChange,
    BlockAccessList,
)
from execution_testing.vm import Op


class InvariantViolationError(Exception):
    """A chain invariant a filled block broke."""

    def __init__(self, invariant: str, message: str) -> None:
        self.invariant = invariant
        self.message = message
        super().__init__(invariant, message)

    def __str__(self) -> str:
        """Name the invariant ahead of the message."""
        return f"[{self.invariant}] {self.message}"


def _accepted_txs(
    txs: Sequence[Transaction], result: Result
) -> list[Transaction]:
    rejected_indices = {
        int(rejected.index) for rejected in result.rejected_transactions
    }
    return [
        tx for index, tx in enumerate(txs) if index not in rejected_indices
    ]


def _keyed_nonce_uses(
    fork: Fork, txs: Sequence[Transaction], result: Result
) -> Counter[Tuple[Address, int]]:
    """
    Count the accepted transactions selecting each keyed nonce slot.

    A transaction with EIP-8250 nonce keys leaves its sender's account
    nonce alone and advances each key's sequence, held in a storage slot
    as `(account, slot)`. The protocol reads and writes that slot itself,
    with no `SLOAD` or `SSTORE`.
    """
    uses: Counter[Tuple[Address, int]] = Counter()
    for tx in _accepted_txs(txs, result):
        if tx.sender is not None and tx.nonce_keys:
            uses.update(fork.keyed_nonce_slots(tx.sender, tx.nonce_keys))
    return uses


@dataclass(frozen=True)
class BlockTotals:
    """The gas, prices and issuance of a block, as the framework built it."""

    gas_limit: int
    gas_used: int
    """The header's gas used."""
    receipts_gas_used: int
    """The last receipt's cumulative gas used."""
    base_fee_per_gas: int
    blob_gas_used: int
    blob_gas_price: int
    issued: int
    """The block reward plus the withdrawals, in wei."""


def _may_have_run_selfdestruct(result: Result) -> bool:
    """
    Return whether SELFDESTRUCT may have run in the block.

    A transition tool without opcode counts cannot rule it out.
    """
    if result.opcode_count is None:
        return True
    return result.opcode_count.root.get(Op.SELFDESTRUCT, 0) > 0


def check_ether_conservation(
    fork: Fork,
    pre_alloc: Alloc,
    post_alloc: Alloc,
    result: Result,
    totals: BlockTotals,
) -> None:
    """
    Check that total ether changes only by issuance minus the fee burn.

    Before EIP-8246, SELFDESTRUCT can also burn ether, so a block that ran
    it may only lose more ether than the fees explain, never gain any.
    """
    delta = sum(
        int(account.balance) for account in post_alloc.root.values() if account
    ) - sum(
        int(account.balance) for account in pre_alloc.root.values() if account
    )
    base_fee_burn = totals.base_fee_per_gas * totals.receipts_gas_used
    blob_fee_burn = totals.blob_gas_price * totals.blob_gas_used
    expected = totals.issued - base_fee_burn - blob_fee_burn
    may_burn = fork.selfdestruct_burns_balance() and (
        _may_have_run_selfdestruct(result)
    )
    if delta == expected or (may_burn and delta < expected):
        return
    raise InvariantViolationError(
        invariant="ether_conservation",
        message=(
            f"balance delta {delta} != expected {expected} "
            f"(issued={totals.issued}, "
            f"base_fee_burn={base_fee_burn}, "
            f"blob_fee_burn={blob_fee_burn}, "
            f"unexplained={delta - expected})"
        ),
    )


def check_gas_accounting(
    fork: Fork, result: Result, totals: BlockTotals
) -> None:
    """
    Check the header's gas used against the gas limit and the receipts.

    The last receipt's cumulative gas equals the header's unless the fork
    keeps refunds in the header or meters several gas dimensions. A refund
    is at most `1 / max_refund_quotient` of a transaction's gas, so with
    refunds kept the header is at most `q / (q - 1)` of the receipts. With
    several dimensions the header is the largest one, and each receipt is
    at most the sum of its dimensions, so the header is at least the
    receipts over their count. From EIP-8037 on, the header is therefore
    only bounded, not pinned: the transition tool reports no per-dimension
    totals to check it against.
    """
    gas_used = totals.gas_used

    if gas_used > totals.gas_limit:
        raise InvariantViolationError(
            invariant="gas_used_within_limit",
            message=(
                f"block gas_used {gas_used} exceeds "
                f"gas_limit {totals.gas_limit}"
            ),
        )

    previous = 0
    for index, receipt in enumerate(result.receipts):
        cumulative = receipt.cumulative_gas_used
        if cumulative is None:
            raise InvariantViolationError(
                invariant="receipt_gas_monotonicity",
                message=f"receipt {index} has no cumulative gas",
            )
        if int(cumulative) <= previous:
            raise InvariantViolationError(
                invariant="receipt_gas_monotonicity",
                message=(
                    f"receipt {index} cumulative gas {cumulative} "
                    f"<= previous {previous}"
                ),
            )
        previous = int(cumulative)

    receipts_gas = totals.receipts_gas_used
    dimensions = len(fork.block_gas_dimensions())
    lowest = (receipts_gas + dimensions - 1) // dimensions
    highest = receipts_gas
    if fork.block_gas_used_includes_refunds():
        quotient = fork.max_refund_quotient()
        highest = receipts_gas * quotient // (quotient - 1)
    if not lowest <= gas_used <= highest:
        raise InvariantViolationError(
            invariant="receipt_gas_totals",
            message=(
                f"block gas_used {gas_used} outside [{lowest}, "
                f"{highest}] for receipts totaling {receipts_gas}"
            ),
        )


def check_nonce_monotonicity(
    fork: Fork,
    pre_alloc: Alloc,
    post_alloc: Alloc,
    txs: Sequence[Transaction],
    result: Result,
) -> None:
    """
    Check that nonces never decrease and senders advance per transaction.

    Before EIP-6780, SELFDESTRUCT can delete an account that a later
    transfer re-creates at nonce 0, so a block that ran it skips the
    decrease check. From EIP-6780 on it deletes only accounts created in
    the same transaction, which never lowers a nonce.

    A transaction with EIP-8250 nonce keys advances each key's sequence
    instead of its sender's account nonce.
    """

    def nonce_of(alloc: Alloc, address: Address) -> int | None:
        account = alloc.root.get(address)
        if account is None:
            return None
        return int(account.nonce)

    def sequence_of(alloc: Alloc, address: Address, slot: int) -> int:
        account = alloc.root.get(address)
        if account is None or slot not in account.storage:
            return 0
        return int(account.storage[slot])

    may_delete = fork.selfdestruct_deletes_existing_accounts() and (
        _may_have_run_selfdestruct(result)
    )
    if not may_delete:
        for address in pre_alloc.root:
            pre_nonce = nonce_of(pre_alloc, address)
            post_nonce = nonce_of(post_alloc, address)
            if (
                pre_nonce is not None
                and post_nonce is not None
                and post_nonce < pre_nonce
            ):
                raise InvariantViolationError(
                    invariant="nonce_never_decreases",
                    message=(
                        f"nonce of {address} decreased "
                        f"{pre_nonce} -> {post_nonce}"
                    ),
                )

    accepted = Counter(
        tx.sender
        for tx in _accepted_txs(txs, result)
        if tx.sender is not None and not tx.nonce_keys
    )
    for sender, count in accepted.items():
        pre_nonce = nonce_of(pre_alloc, sender) or 0
        post_nonce = nonce_of(post_alloc, sender)
        if post_nonce is not None and post_nonce < pre_nonce + count:
            raise InvariantViolationError(
                invariant="sender_nonce_advances",
                message=(
                    f"sender {sender} nonce {pre_nonce} -> "
                    f"{post_nonce} after {count} accepted "
                    "transactions"
                ),
            )

    keyed = _keyed_nonce_uses(fork, txs, result)
    for (account, slot), count in keyed.items():
        pre_sequence = sequence_of(pre_alloc, account, slot)
        post_sequence = sequence_of(post_alloc, account, slot)
        if post_sequence < pre_sequence + count:
            raise InvariantViolationError(
                invariant="keyed_nonce_advances",
                message=(
                    f"keyed nonce at {account} slot {slot:#x} went "
                    f"{pre_sequence} -> {post_sequence} after {count} "
                    "accepted transactions"
                ),
            )


def _check_changes(
    address: Address,
    field: str,
    pre_value: object,
    post_value: object,
    recorded: Sequence[object],
) -> None:
    """Check one field's recorded post-values against its pre and post."""
    if not recorded:
        if pre_value == post_value:
            return
        raise InvariantViolationError(
            invariant="bal_state_diff",
            message=f"{address} {field} changed but the BAL has no entry",
        )
    if recorded[-1] != post_value:
        raise InvariantViolationError(
            invariant="bal_state_diff",
            message=(
                f"{address} {field} last BAL value {recorded[-1]!r} "
                f"!= post-state {post_value!r}"
            ),
        )
    previous = pre_value
    for value in recorded:
        if value == previous:
            raise InvariantViolationError(
                invariant="bal_state_diff",
                message=(
                    f"{address} {field} BAL records a no-op change "
                    f"to {value!r}"
                ),
            )
        previous = value


def check_bal_against_state_diff(
    pre_alloc: Alloc,
    post_alloc: Alloc,
    block_access_list: Optional[BlockAccessList],
) -> None:
    """
    Check the block access list against the block's pre/post state diff.

    Every changed balance, nonce, code or storage value has an entry, the
    entry at the last index equals the post-state, and no entry repeats
    the value before it. Storage is skipped for an account that starts
    with storage but no code and no nonce and ends with none: deleting it
    wipes the storage, which the BAL has no way to record.
    """
    if block_access_list is None:
        return
    entries = {entry.address: entry for entry in block_access_list.root}
    # Sorted so the same block always fails on the same violation: a set
    # of addresses iterates in a per-process hash order.
    addresses = sorted(
        pre_alloc.root.keys() | post_alloc.root.keys() | entries.keys()
    )
    for address in addresses:
        pre = pre_alloc.root.get(address) or Account()
        post = post_alloc.root.get(address) or Account()
        entry = entries.get(address) or BalAccountChange(address=address)

        # Each field maps to (pre value, post value, recorded post-values).
        fields: Dict[str, Tuple[object, object, Sequence[object]]] = {
            "balance": (
                int(pre.balance),
                int(post.balance),
                [int(c.post_balance) for c in entry.balance_changes],
            ),
            "nonce": (
                int(pre.nonce),
                int(post.nonce),
                [int(c.post_nonce) for c in entry.nonce_changes],
            ),
            "code": (
                bytes(pre.code),
                bytes(post.code),
                [bytes(c.new_code) for c in entry.code_changes],
            ),
        }
        pre_storage = {int(k): int(v) for k, v in pre.storage.root.items()}
        post_storage = {int(k): int(v) for k, v in post.storage.root.items()}
        recorded_storage = {
            int(slot.slot): [int(c.post_value) for c in slot.slot_changes]
            for slot in entry.storage_changes
        }
        wiped = (
            any(pre_storage.values())
            and not pre.code
            and pre.nonce == 0
            and not any(post_storage.values())
        )
        if not wiped:
            for slot in sorted(
                pre_storage.keys()
                | post_storage.keys()
                | recorded_storage.keys()
            ):
                fields[f"storage[{slot:#x}]"] = (
                    pre_storage.get(slot, 0),
                    post_storage.get(slot, 0),
                    recorded_storage.get(slot, []),
                )

        for field, (pre_value, post_value, recorded) in fields.items():
            _check_changes(address, field, pre_value, post_value, recorded)


def check_bal_access_witness(
    witness: Optional[BalWitness],
    block_access_list: Optional[BlockAccessList],
    protocol_accessed: AbstractSet[SlotAccess] = frozenset(),
) -> None:
    """
    Check the BAL's storage slots against the slots execution accessed.

    The witness comes from the trace stream, not from the state tracker
    that builds the BAL, so a slot the tracker dropped or invented shows
    up here. Only the EELS transition tool produces a witness.

    `protocol_accessed` holds the slots the protocol read or wrote itself.
    No instruction shows them in the trace, and the BAL must list each.
    """
    if witness is None or block_access_list is None:
        return
    started = witness.started | protocol_accessed
    ended = witness.ended | protocol_accessed
    listed: Set[SlotAccess] = set()
    for entry in block_access_list.root:
        address = int.from_bytes(entry.address, "big")
        listed |= {(address, int(slot.slot)) for slot in entry.storage_changes}
        listed |= {(address, int(read)) for read in entry.storage_reads}

    # The trace shows a storage op start and end but not the access itself,
    # so the BAL must hold every slot an SLOAD or SSTORE completed on, and
    # only slots one started on: `ended <= BAL <= started`.
    for problem, slots in (
        ("accessed but absent from the BAL", ended - listed),
        ("in the BAL but never accessed", listed - started),
    ):
        if not slots:
            continue
        sample = ", ".join(
            f"{address:#042x}:{slot:#x}" for address, slot in sorted(slots)[:3]
        )
        raise InvariantViolationError(
            invariant="bal_access_witness",
            message=f"{problem} ({len(slots)}): {sample}",
        )


def check_block_invariants(
    *,
    fork: Fork,
    pre_alloc: Alloc,
    post_alloc: Alloc,
    result: Result,
    txs: Sequence[Transaction],
    totals: BlockTotals,
    block_access_list: Optional[BlockAccessList] = None,
    bal_witness: Optional[BalWitness] = None,
    block_number: int | None = None,
    block_access_list_only: bool = False,
) -> None:
    """
    Run every block-level invariant check, raising on the first violation.

    With `block_access_list_only`, only the checks of the block access
    list run: the blockchain form of a state test, whose state form
    checked the rest.

    Given `block_number`, the raised violation carries it as a note.
    """
    try:
        if not block_access_list_only:
            check_ether_conservation(
                fork, pre_alloc, post_alloc, result, totals
            )
            check_gas_accounting(fork, result, totals)
            check_nonce_monotonicity(fork, pre_alloc, post_alloc, txs, result)
        check_bal_against_state_diff(pre_alloc, post_alloc, block_access_list)
        check_bal_access_witness(
            bal_witness,
            block_access_list,
            protocol_accessed={
                (int.from_bytes(account, "big"), slot)
                for account, slot in _keyed_nonce_uses(fork, txs, result)
            },
        )
    except InvariantViolationError as violation:
        if block_number is not None:
            violation.add_note(f"block {block_number}")
        raise
