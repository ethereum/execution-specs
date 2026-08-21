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

from dataclasses import dataclass, field, replace
from typing import Dict, List, Optional, Set, Tuple, final

from ethereum_types.bytes import Bytes, Bytes32
from ethereum_types.frozen import slotted_freezable
from ethereum_types.numeric import U64, U256, Uint

from ethereum.crypto.hash import Hash32, keccak256
from ethereum.exceptions import EthereumException
from ethereum.merkle_patricia_trie import Trie
from ethereum.state import Address
from ethereum.utils.byte import left_pad_zero_bytes

from ..block_access_lists import BlockAccessList, BlockAccessListBuilder
from ..blocks import FrameReceipt, Log, Receipt, Withdrawal
from ..fork_types import (
    Authorization,
    ExecutionGas,
    StateGas,
    VersionedHash,
)
from ..state_tracker import (
    BlockState,
    TransactionState,
    get_account,
    increment_nonce,
    is_account_alive,
    set_account_balance,
)
from ..transactions import LegacyTransaction
from ..transactions.frame_transaction import (
    APPROVE_SCOPE_MASK,
    FrameFlag,
    FrameTransaction,
    resolve_frame_target,
)
from .gas import GasMeter, StateGasCosts, charge_frame_state_gas

__all__ = ("Environment", "Evm")
TRANSFER_TOPIC = keccak256(b"Transfer(address,address,uint256)")
SYSTEM_ADDRESS = Address(
    bytes.fromhex("fffffffffffffffffffffffffffffffffffffffe")
)
FRAME_ENTRY_POINT = Address(
    bytes.fromhex("00000000000000000000000000000000000000aa")
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

    block_gas_used : `ExecutionGas`
        Execution gas used for executing all transactions. EIP-8037
        names this counter `block_execution_gas_used`.
    block_state_gas_used : `StateGas`
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

    block_gas_used: ExecutionGas = ExecutionGas(Uint(0))
    block_state_gas_used: StateGas = StateGas(Uint(0))
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
@slotted_freezable
@dataclass
class TopLevelContext:
    """
    The single top-level call or creation a non-frame transaction
    describes.

    Unlike `FrameContext`, this is a frozen one-shot descriptor:
    consumed once when the transaction's top-level frame is built;
    instructions never read it.
    """

    recipient: Address
    """
    The address the transaction calls; for a creation, the address the
    contract deploys to.
    """

    is_create: bool
    """
    Whether the transaction is a contract creation.
    """

    data: Bytes
    """
    The transaction's data payload: call data for a call, init code
    for a creation.
    """

    value: U256
    """
    The amount of ether (in wei) sent with the transaction.
    """


@final
@dataclass
class FrameContext:
    """
    Frame-transaction state, alive for the whole transaction and
    visible at every call depth through the transaction environment.

    The state gas dimension lives here rather than on the gas meters:
    each frame's pool is shared by every call depth within the frame,
    never forwarded or split like execution gas. While a frame
    executes only its pool moves; its attributed state gas is written
    once, at frame exit, into its receipt — the frame's budget less
    the remaining pool. A later frame's cross-frame refill lowers the
    owning frame's receipt entry in place. The pool, the receipts, and
    the outstanding-charge ownership map roll back with the
    transaction state, through the same snapshots
    (`copy_frame_context` / `restore_frame_context`) that already
    accompany every state snapshot.
    """

    tx: FrameTransaction
    """
    The frame transaction being executed.
    """

    signature_hash: Hash32
    """
    The transaction's canonical signature hash.
    """

    resolved_signers: Tuple[Optional[Address], ...]
    """
    The signer each signature entry resolved to; `None` for
    `ARBITRARY` entries, to which the protocol assigns no signer.
    """

    standard_gas_limit: Uint
    """
    Settlement anchor: the transaction's intrinsic cost plus the sum
    of the frames' gas budgets in both dimensions. The environment's
    `gas_limit` carries the inclusion-facing `max_gas` instead.
    """

    max_cost: Uint
    """
    The maximum cost of the transaction: `max_gas` priced at the fee
    cap, plus the blob fee. Collected from the payer when a frame
    approves payment.
    """

    current_frame_index: Uint
    """
    Index of the frame currently executing, advanced by the frame
    loop.
    """

    frame_receipts: List[FrameReceipt]
    """
    Receipts of the completed frames, growing as frames complete.

    Entries are not final until the transaction ends: a later frame's
    refill of a state charge lowers the owning frame's
    `gas_used.state`, and an atomic batch unroll zeroes the state gas
    and empties the logs of the unrolled frames' receipts.
    """

    payer: Optional[Address]
    """
    The account that approved paying for the transaction's gas, once
    one has.
    """

    sender_approved: bool
    """
    Whether the sender has approved future frames executing on its
    behalf.
    """

    state_gas_left: StateGas
    """
    State gas remaining in the executing frame's pool, seeded from the
    frame's declared state budget at frame entry. EVM call frames at
    every depth within the frame draw from it directly; a charge
    exceeding it halts the current call frame exceptionally.
    """

    outstanding_charge_owners: Dict[Tuple[Address, Bytes32], Uint]
    """
    For each storage slot whose creation charge is outstanding, the
    index of the frame that paid it. A refill of the slot lowers the
    owner frame's attributed state gas — the executing frame's pool
    when the owner is still executing, its receipt entry otherwise —
    and clears the entry either way.
    """


@final
@dataclass
class TransactionEnvironment:
    """
    Items that are used while processing a transaction.

    Fields shared by every transaction type, plus exactly one of the
    two type-specific contexts: `top_level_context` for a regular or
    system transaction, `frame_context` for a frame transaction.
    """

    origin: Address
    gas_limit: Uint
    effective_gas_price: Uint
    execution_gas_grant: ExecutionGas
    state_gas_reservoir: StateGas
    calldata_floor: Uint
    access_list_addresses: Set[Address]
    access_list_storage_keys: Set[Tuple[Address, Bytes32]]
    accounts_with_paid_writes: Set[Address]
    state: TransactionState
    blob_versioned_hashes: Tuple[VersionedHash, ...]
    authorizations: Tuple[Authorization, ...]
    index_in_block: Optional[Uint]
    tx_hash: Optional[Hash32]

    top_level_context: Optional[TopLevelContext]
    """
    Present iff the transaction describes a single top-level call or
    creation. Exactly one of this and `frame_context` is set; both
    flow entries assert it.
    """

    frame_context: Optional[FrameContext]
    """
    Present iff this is a frame transaction. The frame-only opcodes
    exceptionally halt when this is `None`.
    """


def copy_frame_context(
    tx_env: TransactionEnvironment,
) -> Optional[FrameContext]:
    """
    Copy a frame transaction's context, to be restored on failure.

    Paired with every transaction-state snapshot taken while a frame
    executes: `APPROVE`'s state-side effects (the sender's nonce
    increment and the payment escrow) are transaction-state writes
    that roll back with the state, so the context fields recording the
    approval must roll back in the same motion — as must the state gas
    pool, the receipts a cross-frame refill may have edited, and the
    outstanding-charge ownership map. Return `None` for other
    transaction types, whose environments carry no frame context.
    """
    frame_context = tx_env.frame_context
    if frame_context is None:
        return None
    return replace(
        frame_context,
        frame_receipts=list(frame_context.frame_receipts),
        outstanding_charge_owners=dict(
            frame_context.outstanding_charge_owners
        ),
    )


def restore_frame_context(
    tx_env: TransactionEnvironment,
    snapshot: Optional[FrameContext],
) -> None:
    """
    Restore the mutable fields of a frame transaction's context from a
    copy taken by `copy_frame_context`; a no-op for other transaction
    types.
    """
    if snapshot is None:
        return
    frame_context = tx_env.frame_context
    assert frame_context is not None
    frame_context.current_frame_index = snapshot.current_frame_index
    frame_context.frame_receipts = snapshot.frame_receipts
    frame_context.payer = snapshot.payer
    frame_context.sender_approved = snapshot.sender_approved
    frame_context.state_gas_left = snapshot.state_gas_left
    frame_context.outstanding_charge_owners = (
        snapshot.outstanding_charge_owners
    )


def attempt_approval(
    tx_env: TransactionEnvironment,
    scope: FrameFlag,
    accessed_addresses: Set[Address],
) -> bool:
    """
    Attempt an `APPROVE` of `scope` on behalf of the executing frame's
    resolved target, applying its effects on success.

    The scope must be non-empty and within the frame's allowed
    approval flags. Approving execution requires that execution is not
    already approved and that the frame's resolved target is the
    transaction's sender. Approving payment requires that no payer is
    set, that execution is approved (by this same scope or earlier),
    and that the resolved target can cover the transaction's maximum
    cost; it increments the sender's nonce and collects the maximum
    cost from the resolved target, which becomes the payer. Collecting
    the maximum cost warms the payer like any protocol-touched
    account, in the caller's active warm set so the warmth shares the
    approval's rollback fate; an execution-only approval touches no
    payer balance and warms nothing.

    When incrementing the nonce creates the sender account, the
    account creation is charged from the executing frame's state gas
    pool immediately before the increment. A pool that cannot cover
    the charge halts the current call frame exceptionally — the halt's
    rollback discards every approval effect, including an execution
    approval this same call already recorded.

    Return whether the approval was granted; a refusal reverts the
    requesting call frame, which is the frame itself only when the
    protocol default code is the caller.
    """
    frame_context = tx_env.frame_context
    assert frame_context is not None
    tx = frame_context.tx
    frame = tx.frames[int(frame_context.current_frame_index)]
    resolved_target = resolve_frame_target(tx, frame)

    allowed_scope = frame.flags & APPROVE_SCOPE_MASK
    # An empty scope, or one beyond the frame's allowed flags.
    if not scope or scope & ~allowed_scope:
        return False

    approves_execution = FrameFlag.APPROVE_EXECUTION in scope
    approves_payment = FrameFlag.APPROVE_PAYMENT in scope

    if approves_execution:
        # Execution is already approved.
        if frame_context.sender_approved:
            return False
        # Only the sender may approve execution on its own behalf.
        if resolved_target != tx.sender:
            return False

    if approves_payment:
        # Payment is already approved.
        if frame_context.payer is not None:
            return False
        # Payment approval requires execution approval first.
        if not (frame_context.sender_approved or approves_execution):
            return False
        payer_balance = get_account(tx_env.state, resolved_target).balance
        # The payer cannot cover the transaction's maximum cost.
        if Uint(payer_balance) < frame_context.max_cost:
            return False

    if approves_execution:
        frame_context.sender_approved = True
    if approves_payment:
        if not is_account_alive(tx_env.state, tx.sender):
            charge_frame_state_gas(frame_context, StateGasCosts.NEW_ACCOUNT)
        increment_nonce(tx_env.state, tx.sender)
        set_account_balance(
            tx_env.state,
            resolved_target,
            U256(Uint(payer_balance) - frame_context.max_cost),
        )
        frame_context.payer = resolved_target
        accessed_addresses.add(resolved_target)

    return True


@final
@dataclass
class Evm:
    """
    A single call frame: its parameters, gas meter, machine state, and
    accrued effects.

    A call spawns a child frame and each top-level call is a frame at
    depth zero, so one dataclass describes them all.
    """

    pc: Uint
    stack: List[U256]
    memory: bytearray
    # Init code for a creation; the resolved code for a call.
    code: Bytes
    gas_meter: GasMeter
    valid_jump_destinations: Set[Uint]
    logs: Tuple[Log, ...]
    running: bool

    # The call's parameters, fixed at frame creation.
    block_env: BlockEnvironment
    tx_env: TransactionEnvironment
    caller: Address
    current_target: Address
    value: U256
    call_data: Bytes
    code_address: Optional[Address]
    depth: Uint
    should_transfer_value: bool
    is_static: bool
    disable_precompiles: bool
    parent_evm: Optional["Evm"]

    output: Bytes
    accounts_to_delete: Set[Address]
    return_data: Bytes
    error: Optional[EthereumException]
    accessed_addresses: Set[Address]
    accessed_storage_keys: Set[Tuple[Address, Bytes32]]


def incorporate_child(evm: Evm, child_evm: Evm) -> None:
    """
    Incorporate the state of a returning `child_evm` into the parent
    `evm`.

    Gas flows back to the parent regardless of the child's fate. A
    failed child settles its own meter before returning -- its state
    gas rolled back to the baseline, its [spill] refilled, and its
    refunds discarded -- so absorbing the meter unconditionally
    reclaims exactly the gas the child gives back. Everything else the
    child accumulated -- logs, scheduled self-destructs, refunds, and
    warmed access sets -- survives only on success, dying with a
    failed child's reverted state.

    A call tree never mixes gas models: within a frame transaction no
    meter carries a reservoir -- state gas lives on the frame context,
    shared by every call depth, so none of it moves between meters
    here -- while in the single-gas-field model every meter carries
    one.

    Parameters
    ----------
    evm :
        The parent `EVM`.
    child_evm :
        The child evm to incorporate.

    [spill]: ref:ethereum.forks.amsterdam.vm.gas.StateGasReservoir.state_gas_spilled

    """  # noqa: E501
    child_meter = child_evm.gas_meter
    gas_meter = evm.gas_meter

    if child_evm.error:
        # A failed child arrives settled: refunds discarded.
        assert child_meter.refund_counter == 0

    # Execution gas returns to the parent regardless of the child's
    # fate. Note that upon failure, the child already arrives settled.
    gas_meter.gas_left += child_meter.gas_left
    gas_meter.refund_counter += child_meter.refund_counter

    child_reservoir = child_meter.reservoir
    if child_reservoir is None:
        assert gas_meter.reservoir is None
    else:
        parent_reservoir = gas_meter.reservoir
        assert parent_reservoir is not None

        # Only the top frame commits state gas; a child never carries
        # any.
        assert child_reservoir.state_gas_committed_spill == Uint(0)

        if child_evm.error:
            # A failed child arrives settled: rolled back to its
            # baseline, spill refilled.
            assert child_reservoir.state_gas_spilled == Uint(0)
            assert (
                child_reservoir.state_gas_left
                == child_reservoir.state_gas_baseline
            )

        parent_reservoir.state_gas_left += child_reservoir.state_gas_left
        parent_reservoir.state_gas_spilled += child_reservoir.state_gas_spilled

    # Everything else survives only on success.
    if not child_evm.error:
        evm.logs += child_evm.logs
        evm.accounts_to_delete.update(child_evm.accounts_to_delete)
        evm.accessed_addresses.update(child_evm.accessed_addresses)
        evm.accessed_storage_keys.update(child_evm.accessed_storage_keys)


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
