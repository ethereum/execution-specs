"""
Ethereum Virtual Machine (EVM).

.. contents:: Table of Contents
    :backlinks: none
    :local:

Introduction
------------

The abstract computer which runs the code stored in an
`.fork_types.Account`.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Set, Tuple, final

from ethereum_types.bytes import Bytes, Bytes0, Bytes32
from ethereum_types.numeric import U64, U256, Uint

from ethereum.crypto.hash import Hash32, keccak256
from ethereum.exceptions import EthereumException
from ethereum.merkle_patricia_trie import Trie
from ethereum.state import Address
from ethereum.utils.byte import left_pad_zero_bytes

from ..block_access_lists import BlockAccessList, BlockAccessListBuilder
from ..blocks import Log, Receipt, Withdrawal
from ..fork_types import Authorization, StateGas, VersionedHash
from ..state_tracker import (
    BlockState,
    TransactionState,
    get_account,
    increment_nonce,
    set_account_balance,
)
from ..transactions import (
    APPROVE_EXECUTION,
    APPROVE_PAYMENT,
    APPROVE_SCOPE_MASK,
    FrameTransaction,
    LegacyTransaction,
)

__all__ = ("Environment", "Evm", "Message")
TRANSFER_TOPIC = keccak256(b"Transfer(address,address,uint256)")
SYSTEM_ADDRESS = Address(
    bytes.fromhex("fffffffffffffffffffffffffffffffffffffffe")
)
CALL_SUCCESS = U256(1)


@final
@dataclass
class BlockEnvironment:
    """
    Items external to the virtual machine itself, provided by the environment.
    """

    chain_id: U64
    state: BlockState
    block_gas_limit: Uint
    block_hashes: List[Hash32]
    coinbase: Address
    number: Uint
    base_fee_per_gas: Uint
    time: U256
    prev_randao: Bytes32
    excess_blob_gas: U64
    parent_beacon_block_root: Hash32
    block_access_list_builder: BlockAccessListBuilder
    slot_number: U64


@final
@dataclass
class BlockOutput:
    """
    Output from applying the block body to the present state.

    Contains the following:

    block_gas_used : `ethereum.base_types.Uint`
        Gas used for executing all transactions.
    block_state_gas_used : `ethereum.base_types.Uint`
        State gas used for executing all transactions.
    cumulative_gas_used : `ethereum.base_types.Uint`
        Cumulative gas paid by users (post-refund, post-floor).
    transactions_trie : `ethereum.fork_types.Root`
        Trie of all the transactions in the block.
    receipts_trie : `ethereum.fork_types.Root`
        Trie root of all the receipts in the block.
    receipt_keys :
        Keys of all the receipts in the block.
    block_logs : `Bloom`
        Logs bloom of all the logs included in all the transactions of the
        block.
    withdrawals_trie : `ethereum.fork_types.Root`
        Trie root of all the withdrawals in the block.
    blob_gas_used : `ethereum.base_types.U64`
        Total blob gas used in the block.
    requests : `Bytes`
        Hash of all the requests in the block.
    block_access_list: `BlockAccessList`
        The block access list for the block.
    """

    block_gas_used: Uint = Uint(0)
    block_state_gas_used: Uint = Uint(0)
    cumulative_gas_used: Uint = Uint(0)
    transactions_trie: Trie[Bytes, Optional[Bytes | LegacyTransaction]] = (
        field(default_factory=lambda: Trie(secured=False, default=None))
    )
    receipts_trie: Trie[Bytes, Optional[Bytes | Receipt]] = field(
        default_factory=lambda: Trie(secured=False, default=None)
    )
    receipt_keys: Tuple[Bytes, ...] = field(default_factory=tuple)
    block_logs: Tuple[Log, ...] = field(default_factory=tuple)
    withdrawals_trie: Trie[Bytes, Optional[Bytes | Withdrawal]] = field(
        default_factory=lambda: Trie(secured=False, default=None)
    )
    blob_gas_used: U64 = U64(0)
    requests: List[Bytes] = field(default_factory=list)
    block_access_list: BlockAccessList = field(default_factory=list)


@final
@dataclass
class FrameApproval:
    """
    A pending approval granted by the `APPROVE` instruction.

    Approvals accumulate on the [`Evm`] like logs: they propagate to the
    parent call on success and are discarded when the granting call
    reverts. They are applied to the [`FrameTransactionContext`][ctx]
    once the frame completes successfully.

    [`Evm`]: ref:ethereum.forks.bogota.vm.Evm
    [ctx]: ref:ethereum.forks.bogota.vm.FrameTransactionContext
    """

    scope: Uint
    """
    The approval scope granted: a bitmask of [`APPROVE_PAYMENT`][pay]
    and [`APPROVE_EXECUTION`][exe].

    [pay]: ref:ethereum.forks.bogota.transactions.APPROVE_PAYMENT
    [exe]: ref:ethereum.forks.bogota.transactions.APPROVE_EXECUTION
    """

    approver: Address
    """
    The resolved target of the frame that granted the approval. Becomes
    the payer when the scope includes payment approval.
    """


@final
@dataclass
class FrameTransactionContext:
    """
    Transaction-scoped context of an executing frame transaction, as
    defined in [EIP-8141]. Shared by all frames of the transaction.

    [EIP-8141]: https://eips.ethereum.org/EIPS/eip-8141
    """

    tx: FrameTransaction
    """
    The frame transaction being executed.
    """

    sig_hash: Hash32
    """
    The canonical signature hash of the transaction.
    """

    max_cost: Uint
    """
    The maximum cost of the transaction, collected from the payer upon
    payment approval: the total gas limit priced at `max_fee_per_gas`
    plus the blob fees priced at `max_fee_per_blob_gas`.
    """

    sender_approved: bool = False
    """
    Whether a frame has approved execution on behalf of the sender.
    """

    payer: Optional[Address] = None
    """
    The account that approved payment and was charged the maximum
    transaction cost, or `None` while payment is unapproved.
    """

    current_frame_index: Uint = Uint(0)
    """
    The index of the currently executing frame.
    """

    frame_statuses: List[Uint] = field(default_factory=list)
    """
    Status codes of the frames executed so far.
    """


def apply_frame_approval(
    frame_context: FrameTransactionContext, approval: FrameApproval
) -> None:
    """
    Apply a committed approval to the frame transaction context.

    Parameters
    ----------
    frame_context :
        The context of the executing frame transaction.
    approval :
        The approval to apply.

    """
    if approval.scope & APPROVE_EXECUTION:
        frame_context.sender_approved = True
    if approval.scope & APPROVE_PAYMENT:
        frame_context.payer = approval.approver


def attempt_frame_approval(
    frame_context: FrameTransactionContext,
    scope: Uint,
    frame_flags: Uint,
    resolved_target: Address,
    sender_approved: bool,
    payer: Optional[Address],
    tx_state: TransactionState,
) -> Optional[FrameApproval]:
    """
    Validate and perform an `APPROVE` of `scope`, returning the granted
    approval or `None` when the request must revert the calling frame.

    On payment approval the sender's nonce is incremented and the
    maximum transaction cost is collected from the resolved target.
    These state changes are journaled by the calling EVM frame and roll
    back together with the returned approval if that frame later
    reverts.

    Parameters
    ----------
    frame_context :
        The context of the executing frame transaction.
    scope :
        The requested approval scope.
    frame_flags :
        The flags of the frame requesting approval; bits 0-1 hold the
        allowed approval scope.
    resolved_target :
        The resolved target of the frame requesting approval.
    sender_approved :
        Whether execution approval is in effect, including pending
        approvals of the calling frame.
    payer :
        The payment approver in effect, including pending approvals of
        the calling frame.
    tx_state :
        The transaction state.

    Returns
    -------
    approval : `Optional[FrameApproval]`
        The granted approval, or `None` if the request is not allowed.

    """
    tx_sender = frame_context.tx.sender
    allowed_scope = frame_flags & APPROVE_SCOPE_MASK
    if scope == 0 or int(scope) & ~int(allowed_scope) != 0:
        return None

    if scope & APPROVE_EXECUTION:
        if sender_approved:
            return None
        if resolved_target != tx_sender:
            return None

    if scope & APPROVE_PAYMENT:
        if payer is not None:
            return None
        approver_balance = get_account(tx_state, resolved_target).balance
        if Uint(approver_balance) < frame_context.max_cost:
            return None
        if not (sender_approved or scope & APPROVE_EXECUTION):
            return None
        increment_nonce(tx_state, tx_sender)
        set_account_balance(
            tx_state,
            resolved_target,
            U256(Uint(approver_balance) - frame_context.max_cost),
        )

    return FrameApproval(scope=scope, approver=resolved_target)


@final
@dataclass
class TransactionEnvironment:
    """
    Items that are used while processing a transaction.
    """

    origin: Address
    recipient: Bytes0 | Address
    value: U256
    gas_price: Uint
    gas: Uint
    state_gas_reservoir: Uint
    access_list_addresses: Set[Address]
    access_list_storage_keys: Set[Tuple[Address, Bytes32]]
    state: TransactionState
    blob_versioned_hashes: Tuple[VersionedHash, ...]
    authorizations: Tuple[Authorization, ...]
    index_in_block: Optional[Uint]
    tx_hash: Optional[Hash32]
    intrinsic_regular_gas: Uint
    intrinsic_state_gas: Uint
    frame_context: Optional[FrameTransactionContext] = None


@final
@dataclass
class Message:
    """
    Items that are used by contract creation or message call.
    """

    block_env: BlockEnvironment
    tx_env: TransactionEnvironment
    caller: Address
    target: Bytes0 | Address
    current_target: Address
    gas: Uint
    state_gas_reservoir: Uint
    value: U256
    data: Bytes
    code_address: Optional[Address]
    code: Bytes
    depth: Uint
    should_transfer_value: bool
    is_static: bool
    accessed_addresses: Set[Address]
    accessed_storage_keys: Set[Tuple[Address, Bytes32]]
    disable_precompiles: bool
    parent_evm: Optional["Evm"]


@final
@dataclass
class Evm:
    """The internal state of the virtual machine."""

    pc: Uint
    stack: List[U256]
    memory: bytearray
    code: Bytes
    gas_left: Uint
    state_gas_left: Uint
    valid_jump_destinations: Set[Uint]
    logs: Tuple[Log, ...]
    refund_counter: int
    running: bool
    message: Message
    output: Bytes
    accounts_to_delete: Set[Address]
    return_data: Bytes
    error: Optional[EthereumException]
    accessed_addresses: Set[Address]
    accessed_storage_keys: Set[Tuple[Address, Bytes32]]
    regular_gas_used: Uint = Uint(0)
    state_gas_spilled: Uint = Uint(0)
    approvals: Tuple[FrameApproval, ...] = ()


def pending_frame_approval_state(
    evm: Evm,
) -> Tuple[bool, Optional[Address]]:
    """
    Return the approval state visible to the given EVM frame.

    Combines the committed approvals of the
    [`FrameTransactionContext`][ctx] with the pending approvals
    journaled along the call chain of `evm`, so that an `APPROVE` in a
    child call is visible to later `APPROVE` checks in the same frame
    while still rolling back if an enclosing call reverts.

    Parameters
    ----------
    evm :
        The current EVM frame.

    Returns
    -------
    approval_state : `Tuple[bool, Optional[Address]]`
        Whether execution is approved, and the payment approver if any.

    [ctx]: ref:ethereum.forks.bogota.vm.FrameTransactionContext

    """
    frame_context = evm.message.tx_env.frame_context
    assert frame_context is not None
    sender_approved = frame_context.sender_approved
    payer = frame_context.payer

    lineage = []
    ancestor: Optional[Evm] = evm
    while ancestor is not None:
        lineage.append(ancestor)
        ancestor = ancestor.message.parent_evm

    for ancestor in reversed(lineage):
        for approval in ancestor.approvals:
            if approval.scope & APPROVE_EXECUTION:
                sender_approved = True
            if approval.scope & APPROVE_PAYMENT:
                payer = approval.approver

    return sender_approved, payer


def credit_state_gas_refund(evm: Evm, amount: StateGas) -> None:
    """
    Credit a state gas refund to the local frame, in LIFO order.

    State-gas charges draw from the reservoir first and from `gas_left`
    last, so refills credit the pool charged last first: `gas_left` up
    to `state_gas_spilled`, then the reservoir. This restores the
    exact pools the charge drew from, so the two never drift.

    Parameters
    ----------
    evm :
        The frame crediting the refund.
    amount :
        The refund amount to credit.

    """
    from_gas_left = min(amount, evm.state_gas_spilled)
    evm.gas_left += from_gas_left
    evm.state_gas_spilled -= from_gas_left
    evm.state_gas_left += amount - from_gas_left


def incorporate_child_on_success(evm: Evm, child_evm: Evm) -> None:
    """
    Incorporate the state of a successful `child_evm` into the parent `evm`.

    Parameters
    ----------
    evm :
        The parent `EVM`.
    child_evm :
        The child evm to incorporate.

    """
    evm.gas_left += child_evm.gas_left
    evm.state_gas_left += child_evm.state_gas_left
    evm.state_gas_spilled += child_evm.state_gas_spilled
    evm.logs += child_evm.logs
    evm.refund_counter += child_evm.refund_counter
    evm.accounts_to_delete.update(child_evm.accounts_to_delete)
    evm.accessed_addresses.update(child_evm.accessed_addresses)
    evm.accessed_storage_keys.update(child_evm.accessed_storage_keys)
    evm.regular_gas_used += child_evm.regular_gas_used
    evm.approvals += child_evm.approvals


def refill_frame_state_gas(evm: Evm) -> None:
    """
    Roll back the frame's state gas in LIFO order on revert or halt.

    The frame's state changes are undone, so the state gas it consumed
    is credited back to `gas_left` first and then to the reservoir,
    restoring the pools the charges drew from.

    Parameters
    ----------
    evm :
        The frame whose state gas is rolled back.

    """
    evm.gas_left += evm.state_gas_spilled
    evm.state_gas_left = evm.message.state_gas_reservoir
    evm.state_gas_spilled = Uint(0)


def frame_state_gas_used(evm: Evm) -> int:
    """
    Return the net state gas consumed by a finished frame.

    Equal to the reservoir drawn down ([`state_gas_reservoir`][sgr] at entry
    minus the reservoir now) plus [`state_gas_spilled`][sgs]. May be negative
    when refunds exceed charges.

    Parameters
    ----------
    evm :
        The finished frame.

    [sgr]: ref:ethereum.forks.bogota.vm.Message.state_gas_reservoir
    [sgs]: ref:ethereum.forks.bogota.vm.Evm.state_gas_spilled

    """
    return (
        int(evm.message.state_gas_reservoir)
        - int(evm.state_gas_left)
        + int(evm.state_gas_spilled)
    )


def incorporate_child_on_error(
    evm: Evm,
    child_evm: Evm,
) -> None:
    """
    Incorporate the state of an unsuccessful `child_evm` into the parent `evm`.

    The child rolls back its own state gas via `refill_frame_state_gas`
    before returning (on both reverts and exceptional halts), so its
    `gas_left` and reservoir already reflect the LIFO refill. The parent
    therefore only reabsorbs the child's `gas_left` and reservoir.

    Parameters
    ----------
    evm :
        The parent `EVM`.
    child_evm :
        The child evm to incorporate.

    """
    evm.gas_left += child_evm.gas_left
    evm.state_gas_left += child_evm.state_gas_left
    evm.regular_gas_used += child_evm.regular_gas_used


def emit_transfer_log(
    evm: Evm,
    sender: Address,
    recipient: Address,
    transfer_amount: U256,
) -> None:
    """
    Emit a LOG3 for all ETH transfers satisfying EIP-7708.

    Parameters
    ----------
    evm :
        The state of the ethereum virtual machine
    sender :
        The account address sending the transfer
    recipient :
        The account address receiving the transfer
    transfer_amount :
        The amount of ETH transacted

    """
    if transfer_amount == 0:
        return

    padded_sender = left_pad_zero_bytes(sender, 32)
    padded_recipient = left_pad_zero_bytes(recipient, 32)
    log_entry = Log(
        address=SYSTEM_ADDRESS,
        topics=(
            TRANSFER_TOPIC,
            Hash32(padded_sender),
            Hash32(padded_recipient),
        ),
        data=transfer_amount.to_be_bytes32(),
    )

    evm.logs = evm.logs + (log_entry,)
