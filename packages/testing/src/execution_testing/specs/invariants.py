"""
Chain invariants checked on every valid block while filling.

Enabled with `fill --invariant-checks`. A violation is emitted as an
`InvariantViolationWarning`; CI turns that warning into an error.
"""

import warnings
from collections import Counter
from dataclasses import dataclass, replace
from typing import (
    TYPE_CHECKING,
    Dict,
    List,
    Optional,
    Sequence,
    Set,
    Tuple,
    Type,
)

from execution_testing.base_types import Account, Wei
from execution_testing.test_types.balance_expectations import transaction_key
from execution_testing.test_types.block_access_list import BalAccountChange
from execution_testing.vm import Op

if TYPE_CHECKING:
    from ..base_types import Address
    from ..client_clis.cli_types import Result
    from ..evm_tools.t8n.evm_trace.bal_witness import BalWitness, SlotAccess
    from ..forks.base_fork import BaseFork
    from ..test_types import Alloc, Environment, Transaction
    from ..test_types.balance_expectations import PostStateContext
    from ..test_types.block_access_list import BlockAccessList
    from .blockchain import BuiltBlock


class InvariantViolationWarning(UserWarning):
    """Warning category for chain invariant violations found during fill."""


@dataclass(frozen=True)
class InvariantViolation:
    """A single violated invariant, with a human-readable breakdown."""

    invariant: str
    message: str


def _accepted_txs(
    txs: Sequence["Transaction"], result: "Result"
) -> List["Transaction"]:
    rejected_indices = {
        int(rejected.index) for rejected in result.rejected_transactions
    }
    return [
        tx for index, tx in enumerate(txs) if index not in rejected_indices
    ]


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

    @classmethod
    def of_built_block(cls, block: "BuiltBlock") -> "BlockTotals":
        """Return the totals of a block a blockchain test built."""
        header = block.header
        blob_gas_price = 0
        if header.excess_blob_gas is not None:
            blob_gas_price = block.fork.blob_gas_price_calculator()(
                excess_blob_gas=int(header.excess_blob_gas)
            )
        # EIP-4895 withdrawal amounts are in gwei.
        withdrawn = sum(int(w.amount) for w in block.withdrawals or [])
        return cls(
            gas_limit=int(header.gas_limit),
            gas_used=block.block_gas_used(),
            receipts_gas_used=block.cumulative_gas_used(),
            base_fee_per_gas=int(header.base_fee_per_gas or 0),
            blob_gas_used=int(header.blob_gas_used or 0),
            blob_gas_price=blob_gas_price,
            issued=block.fork.get_reward() + withdrawn * Wei("1 gwei"),
        )

    @classmethod
    def of_state_test(
        cls,
        *,
        fork: Type["BaseFork"],
        tx: "Transaction",
        env: "Environment",
        result: "Result",
        context: "PostStateContext",
    ) -> "BlockTotals":
        """
        Return the totals of a state test's transaction, priced as its
        post-state is. A state test pays no reward and no withdrawals.
        """
        totals = cls(
            gas_limit=int(env.gas_limit),
            gas_used=int(result.gas_used),
            receipts_gas_used=0,
            base_fee_per_gas=0,
            blob_gas_used=0,
            blob_gas_price=0,
            issued=0,
        )
        if tx.error is not None:
            return totals
        receipt_gas = result.receipts[-1].cumulative_gas_used
        assert receipt_gas is not None, "receipt has no cumulative gas used"
        blob_gas_used = 0
        if tx.blob_versioned_hashes:
            blob_count = len(tx.blob_versioned_hashes)
            blob_gas_used = fork.blob_gas_per_blob() * blob_count
        landing = context.landing(transaction_key(tx))
        return replace(
            totals,
            receipts_gas_used=int(receipt_gas),
            base_fee_per_gas=landing.base_fee_per_gas(),
            blob_gas_used=blob_gas_used,
            blob_gas_price=landing.blob_gas_price() or 0,
        )


def _may_have_run_selfdestruct(result: "Result") -> bool:
    """
    Return whether SELFDESTRUCT may have run in the block.

    A transition tool without opcode counts cannot rule it out.
    """
    if result.opcode_count is None:
        return True
    return result.opcode_count.root.get(Op.SELFDESTRUCT, 0) > 0


def check_ether_conservation(
    fork: Type["BaseFork"],
    pre_alloc: "Alloc",
    post_alloc: "Alloc",
    result: "Result",
    totals: BlockTotals,
) -> List[InvariantViolation]:
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
        return []
    return [
        InvariantViolation(
            invariant="ether_conservation",
            message=(
                f"balance delta {delta} != expected {expected} "
                f"(issued={totals.issued}, "
                f"base_fee_burn={base_fee_burn}, "
                f"blob_fee_burn={blob_fee_burn}, "
                f"unexplained={delta - expected})"
            ),
        )
    ]


def check_gas_accounting(
    fork: Type["BaseFork"], result: "Result", totals: BlockTotals
) -> List[InvariantViolation]:
    """
    Check the header's gas used against the gas limit and the receipts.

    The last receipt's cumulative gas equals the header's unless the fork
    keeps refunds in the header or meters several gas dimensions. A refund
    is at most `1 / max_refund_quotient` of a transaction's gas, so with
    refunds kept the header is at most `q / (q - 1)` of the receipts. With
    several dimensions the header is the largest one, and each receipt is
    at most the sum of its dimensions, so the header is at least the
    receipts over their count.
    """
    violations: List[InvariantViolation] = []
    gas_used = totals.gas_used

    if gas_used > totals.gas_limit:
        violations.append(
            InvariantViolation(
                invariant="gas_used_within_limit",
                message=(
                    f"block gas_used {gas_used} exceeds "
                    f"gas_limit {totals.gas_limit}"
                ),
            )
        )

    previous = 0
    for index, receipt in enumerate(result.receipts):
        cumulative = receipt.cumulative_gas_used
        if cumulative is None or int(cumulative) <= previous:
            violations.append(
                InvariantViolation(
                    invariant="receipt_gas_monotonicity",
                    message=(
                        f"receipt {index} cumulative gas {cumulative} "
                        f"<= previous {previous}"
                    ),
                )
            )
            continue
        previous = int(cumulative)

    receipts_gas = totals.receipts_gas_used
    dimensions = fork.block_gas_dimensions()
    lowest = (receipts_gas + dimensions - 1) // dimensions
    highest = receipts_gas
    if fork.block_gas_used_includes_refunds():
        quotient = fork.max_refund_quotient()
        highest = receipts_gas * quotient // (quotient - 1)
    if not lowest <= gas_used <= highest:
        violations.append(
            InvariantViolation(
                invariant="receipt_gas_totals",
                message=(
                    f"block gas_used {gas_used} outside [{lowest}, "
                    f"{highest}] for receipts totaling {receipts_gas}"
                ),
            )
        )
    return violations


def check_nonce_monotonicity(
    fork: Type["BaseFork"],
    pre_alloc: "Alloc",
    post_alloc: "Alloc",
    txs: Sequence["Transaction"],
    result: "Result",
) -> List[InvariantViolation]:
    """
    Check that nonces never decrease and senders advance per transaction.

    Before EIP-6780, SELFDESTRUCT can delete an account that a later
    transfer re-creates at nonce 0, so a block that ran it skips the
    decrease check. From EIP-6780 on it deletes only accounts created in
    the same transaction, which never lowers a nonce.
    """
    violations: List[InvariantViolation] = []

    def nonce_of(alloc: "Alloc", address: "Address") -> int | None:
        account = alloc.root.get(address)
        if account is None:
            return None
        return int(account.nonce)

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
                violations.append(
                    InvariantViolation(
                        invariant="nonce_never_decreases",
                        message=(
                            f"nonce of {address} decreased "
                            f"{pre_nonce} -> {post_nonce}"
                        ),
                    )
                )

    accepted = Counter(
        tx.sender for tx in _accepted_txs(txs, result) if tx.sender is not None
    )
    for sender, count in accepted.items():
        pre_nonce = nonce_of(pre_alloc, sender) or 0
        post_nonce = nonce_of(post_alloc, sender)
        if post_nonce is not None and post_nonce < pre_nonce + count:
            violations.append(
                InvariantViolation(
                    invariant="sender_nonce_advances",
                    message=(
                        f"sender {sender} nonce {pre_nonce} -> "
                        f"{post_nonce} after {count} accepted "
                        "transactions"
                    ),
                )
            )
    return violations


def _check_changes(
    address: "Address",
    field: str,
    pre_value: object,
    post_value: object,
    recorded: Sequence[object],
) -> List[InvariantViolation]:
    """Check one field's recorded post-values against its pre and post."""
    if not recorded:
        if pre_value == post_value:
            return []
        return [
            InvariantViolation(
                invariant="bal_state_diff",
                message=f"{address} {field} changed but the BAL has no entry",
            )
        ]
    violations = []
    if recorded[-1] != post_value:
        violations.append(
            InvariantViolation(
                invariant="bal_state_diff",
                message=(
                    f"{address} {field} last BAL value {recorded[-1]!r} "
                    f"!= post-state {post_value!r}"
                ),
            )
        )
    previous = pre_value
    for value in recorded:
        if value == previous:
            violations.append(
                InvariantViolation(
                    invariant="bal_state_diff",
                    message=(
                        f"{address} {field} BAL records a no-op change "
                        f"to {value!r}"
                    ),
                )
            )
        previous = value
    return violations


def check_bal_against_state_diff(
    pre_alloc: "Alloc",
    post_alloc: "Alloc",
    block_access_list: Optional["BlockAccessList"],
) -> List[InvariantViolation]:
    """
    Check the block access list against the block's pre/post state diff.

    Every changed balance, nonce, code or storage value has an entry, the
    entry at the last index equals the post-state, and no entry repeats
    the value before it. Storage is skipped for an account that starts
    with storage but no code and no nonce and ends with none: deleting it
    wipes the storage, which the BAL has no way to record.
    """
    if block_access_list is None:
        return []
    entries = {entry.address: entry for entry in block_access_list.root}
    violations: List[InvariantViolation] = []
    addresses = pre_alloc.root.keys() | post_alloc.root.keys() | entries.keys()
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
            for slot in (
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
            violations += _check_changes(
                address, field, pre_value, post_value, recorded
            )
    return violations


def check_bal_access_witness(
    witness: Optional["BalWitness"],
    block_access_list: Optional["BlockAccessList"],
) -> List[InvariantViolation]:
    """
    Check the BAL's storage slots against the slots execution accessed.

    The witness comes from the trace stream, not from the state tracker
    that builds the BAL, so a slot the tracker dropped or invented shows
    up here. Only the EELS transition tool produces a witness.
    """
    if witness is None or block_access_list is None:
        return []
    listed: Set["SlotAccess"] = set()
    for entry in block_access_list.root:
        address = int.from_bytes(entry.address, "big")
        listed |= {(address, int(slot.slot)) for slot in entry.storage_changes}
        listed |= {(address, int(read)) for read in entry.storage_reads}

    # The trace shows a storage op start and end but not the access itself,
    # so the BAL must hold every slot an SLOAD or SSTORE completed on, and
    # only slots one started on: `ended <= BAL <= started`.
    violations: List[InvariantViolation] = []
    for problem, slots in (
        ("accessed but absent from the BAL", witness.ended - listed),
        ("in the BAL but never accessed", listed - witness.started),
    ):
        if not slots:
            continue
        sample = ", ".join(
            f"{address:#042x}:{slot:#x}" for address, slot in sorted(slots)[:3]
        )
        violations.append(
            InvariantViolation(
                invariant="bal_access_witness",
                message=f"{problem} ({len(slots)}): {sample}",
            )
        )
    return violations


def check_block_invariants(
    *,
    fork: Type["BaseFork"],
    pre_alloc: "Alloc",
    post_alloc: "Alloc",
    result: "Result",
    txs: Sequence["Transaction"],
    totals: BlockTotals,
    block_access_list: Optional["BlockAccessList"] = None,
    bal_witness: Optional["BalWitness"] = None,
    block_number: int | None = None,
    block_access_list_only: bool = False,
) -> None:
    """
    Run every block-level invariant check and warn on any violation.

    With `block_access_list_only`, only the checks of the block access
    list run: the blockchain form of a state test, whose state form
    checked the rest.

    The warning names the block when the test has more than one, since
    `-W error` turns the first violation into the test's failure.
    """
    violations = [
        *check_bal_against_state_diff(
            pre_alloc, post_alloc, block_access_list
        ),
        *check_bal_access_witness(bal_witness, block_access_list),
    ]
    if not block_access_list_only:
        violations = [
            *check_ether_conservation(
                fork, pre_alloc, post_alloc, result, totals
            ),
            *check_gas_accounting(fork, result, totals),
            *check_nonce_monotonicity(
                fork, pre_alloc, post_alloc, txs, result
            ),
            *violations,
        ]
    # One warning per block, since `-W error` raises on the first warning.
    if violations:
        where = "" if block_number is None else f"block {block_number}: "
        warnings.warn(
            "\n".join(
                f"{where}[{v.invariant}] {v.message}" for v in violations
            ),
            InvariantViolationWarning,
            stacklevel=3,
        )
