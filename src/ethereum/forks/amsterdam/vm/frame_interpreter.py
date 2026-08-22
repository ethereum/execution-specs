"""
Execute the frames of an [EIP-8141] frame transaction.

Where a regular transaction describes a single top-level call, a frame
transaction describes a list of frames that `process_frames` executes
in order, each as its own top-level call with a fresh gas meter
holding the frame's gas limit. The frames share the transaction's
state, a `FrameJournal` of the effects accrued across frames, and
the approval context that the `APPROVE` instruction advances.

[EIP-8141]: https://eips.ethereum.org/EIPS/eip-8141
"""

from dataclasses import dataclass, replace
from typing import Optional, Set, Tuple, final

from ethereum_types.bytes import Bytes, Bytes32
from ethereum_types.numeric import U256, Uint

from ethereum.state import EMPTY_CODE_HASH, Address

from ..blocks import FrameReceipt, GasUsed, Log
from ..exceptions import FrameTransactionExecutionError
from ..fork_types import ExecutionGas, StateGas
from ..state_tracker import (
    TransactionState,
    copy_tx_state,
    get_account,
    get_code,
    is_account_alive,
    restore_tx_state,
)
from ..transactions.frame_transaction import (
    APPROVE_SCOPE_MASK,
    Frame,
    FrameFlag,
    FrameMode,
    FrameSignatureScheme,
    FrameStatus,
    resolve_frame_target,
)
from . import (
    FRAME_ENTRY_POINT,
    BlockEnvironment,
    Evm,
    FrameContext,
    TransactionEnvironment,
    attempt_approval,
    copy_frame_context,
    restore_frame_context,
)
from .eoa_delegation import resolve_delegated_code_address
from .exceptions import ExceptionalHalt
from .gas import (
    GasCosts,
    GasMeter,
    StateGasCosts,
    charge_frame_state_gas,
    charge_gas_from_meter,
)
from .interpreter import (
    TransactionOutput,
    process_call,
)
from .precompiled_contracts.mapping import PRE_COMPILED_CONTRACTS
from .runtime import get_valid_jump_destinations


@final
@dataclass
class FrameJournal:
    """
    Effects accrued across the frames of a frame transaction.

    Each finished frame's contributions are incorporated here: the
    warm journal that successful frames feed, and the refunds and
    scheduled deletions that settle the transaction once the last
    frame has run. Everything gas-shaped settles from the frame
    receipts instead. When an atomic batch opens, a copy of the
    journal joins the batch's rollback point; unrolling the batch
    resumes from that copy.
    """

    warm_addresses: Set[Address]
    """
    Addresses left warm for later frames by successful frames.
    """

    warm_storage_keys: Set[Tuple[Address, Bytes32]]
    """
    Storage keys left warm for later frames by successful frames.
    """

    refund_counter: int
    """
    Refunds accrued by successful frames.
    """

    accounts_to_delete: Set[Address]
    """
    Accounts scheduled for deletion by successful frames.
    """


def copy_frame_journal(journal: FrameJournal) -> FrameJournal:
    """
    Return an independent copy of the journal, safe to keep as a
    rollback point while the original continues to accrue.
    """
    return FrameJournal(
        warm_addresses=set(journal.warm_addresses),
        warm_storage_keys=set(journal.warm_storage_keys),
        refund_counter=journal.refund_counter,
        accounts_to_delete=set(journal.accounts_to_delete),
    )


@final
@dataclass
class AtomicBatch:
    """
    Rollback point captured when an atomic batch opens.

    A frame carrying the atomic batch flag opens a batch that runs up
    to and including the next frame without the flag. When a batch
    frame fails, `unroll_atomic_batch` restores everything captured
    here: one snapshot per rollback domain — the transaction state,
    the frame context, and the frame journal.
    """

    first_frame_index: Uint
    """
    Index of the frame that opened the batch.
    """

    state_snapshot: TransactionState
    """
    Copy of the transaction state taken before the batch began.
    """

    context_snapshot: FrameContext
    """
    Copy of the frame context taken before the batch began: the
    approval fields, the receipts of the pre-batch frames — restoring
    them undoes the refills the batch's frames applied to pre-batch
    state charges — and the outstanding-charge ownership map.
    """

    journal: FrameJournal
    """
    Copy of the frame journal taken before the batch began.
    """


@final
@dataclass
class FrameOutcome:
    """
    Reduced outcome of a single frame.

    A finished frame's EVM is read once and immediately reduced to
    this record: the consensus receipt entry, plus the quantities the
    frame contributes to the transaction's settlement that the
    receipt does not carry. Everything gas-shaped is derived from the
    receipt: the frame's unused gas, in either dimension, is its
    budget less its receipt's usage.
    """

    receipt: FrameReceipt
    """
    The frame's receipt entry.
    """

    refund_counter: int
    """
    Refunds the frame accrued; zero unless the frame succeeded.
    """

    accounts_to_delete: Set[Address]
    """
    Accounts the frame scheduled for deletion; empty unless the frame
    succeeded.
    """


def incorporate_frame_outcome(
    journal: FrameJournal, outcome: FrameOutcome
) -> None:
    """
    Incorporate a finished frame's settlement quantities into the
    journal.

    The frame's warm accesses are not carried on the outcome:
    `execute_frame` commits them into the journal only when the frame
    succeeds.
    """
    journal.refund_counter += outcome.refund_counter
    journal.accounts_to_delete |= outcome.accounts_to_delete


def unroll_atomic_batch(
    tx_env: TransactionEnvironment,
    batch: AtomicBatch,
) -> FrameJournal:
    """
    Unroll a failed atomic batch.

    The transaction state and the frame context are restored to the
    condition immediately before the batch began — undoing, with the
    batch's state changes, the refills its frames applied to pre-batch
    receipts — and the receipts of the executed batch frames are
    re-appended keeping their status and execution gas, with their
    logs emptied and their state gas zeroed. Return the batch's
    journal copy for the frame loop to continue from; the gas the
    batch frames consumed remains charged, since their receipts keep
    it.
    """
    frame_context = tx_env.frame_context
    assert frame_context is not None

    # Static validity bans approval scopes on batch frames, so the
    # unroll can never move the approval context.
    assert frame_context.payer == batch.context_snapshot.payer
    assert (
        frame_context.sender_approved == batch.context_snapshot.sender_approved
    )

    executed_batch_receipts = frame_context.frame_receipts[
        int(batch.first_frame_index) :
    ]

    restore_tx_state(tx_env.state, batch.state_snapshot)
    restore_frame_context(tx_env, batch.context_snapshot)

    for receipt in executed_batch_receipts:
        frame_context.frame_receipts.append(
            replace(
                receipt,
                gas_used=replace(receipt.gas_used, state=Uint(0)),
                logs=(),
            )
        )

    return batch.journal


def create_evm_from_frame(
    block_env: BlockEnvironment,
    tx_env: TransactionEnvironment,
    frame: Frame,
    resolved_target: Address,
    gas_meter: GasMeter,
    accessed_addresses: Set[Address],
    accessed_storage_keys: Set[Tuple[Address, Bytes32]],
) -> Evm:
    """
    Build a frame's top-level EVM.

    The access sets arrive from `execute_frame`, which seeded them
    from the journal shared across frames and charged the resolved
    target's warm or cold access into them at frame entry. Charged
    here are the frame's remaining entry costs: the access for
    resolving an EIP-7702 delegation, from the frame's own execution
    gas budget, and the state gas for a value transfer reviving a
    dead account — after the caller's balance check and before the
    frame's code executes. A charge exceeding either budget raises
    instead of building the EVM, failing the frame.
    """
    frame_context = tx_env.frame_context
    assert frame_context is not None

    if frame.value > U256(0) and not is_account_alive(
        tx_env.state, resolved_target
    ):
        charge_frame_state_gas(frame_context, StateGasCosts.NEW_ACCOUNT)

    code_address, disable_precompiles = resolve_delegated_code_address(
        tx_env.state, gas_meter, accessed_addresses, resolved_target
    )

    code = get_code(
        tx_env.state,
        get_account(tx_env.state, code_address).code_hash,
    )

    ## Build the frame
    return Evm(
        # Context
        block_env=block_env,
        tx_env=tx_env,
        parent_evm=None,
        depth=Uint(0),
        # Call Parameters
        caller=tx_env.origin,
        current_target=resolved_target,
        value=frame.value,
        call_data=frame.data,
        should_transfer_value=True,
        is_static=frame.mode == FrameMode.VERIFY,
        disable_precompiles=disable_precompiles,
        # Code
        code_address=code_address,
        code=code,
        valid_jump_destinations=get_valid_jump_destinations(code),
        # Machine State
        gas_meter=gas_meter,
        pc=Uint(0),
        stack=[],
        memory=bytearray(),
        return_data=b"",
        # Accrued Effects
        logs=(),
        accounts_to_delete=set(),
        accessed_addresses=accessed_addresses,
        accessed_storage_keys=accessed_storage_keys,
        # Outcome
        running=True,
        output=b"",
        error=None,
    )


def execute_default_verify_code(
    tx_env: TransactionEnvironment,
    frame: Frame,
) -> FrameStatus:
    """
    Execute the protocol default code of a `VERIFY` frame whose
    resolved target has no code, returning the frame's status.

    The default code draws no execution gas of its own: the frame's
    only execution charge is the resolved target's access, taken by
    `execute_frame` at frame entry. It can consume state gas through
    `APPROVE`, when incrementing the nonce creates the sender
    account; a pool that cannot cover that charge raises, halting the
    frame exceptionally.

    The default code approves the scope allowed by the frame's flags,
    provided the transaction carries an authorizing secp256k1
    signature entry over the canonical signature hash whose resolved
    signer is the frame's resolved target: the entry at index 0 for
    frames allowed to approve execution, or at index 1 for
    payment-only frames. Anything else reverts the frame — which, for
    a `VERIFY` frame, invalidates the transaction.
    """
    frame_context = tx_env.frame_context
    assert frame_context is not None
    tx = frame_context.tx
    resolved_target = resolve_frame_target(tx, frame)

    allowed_scope = frame.flags & APPROVE_SCOPE_MASK
    # The frame is not allowed to approve anything.
    if not allowed_scope:
        return FrameStatus.FAILURE

    if FrameFlag.APPROVE_EXECUTION in allowed_scope:
        signature_index = 0
    else:
        signature_index = 1

    # There is no signature entry at the authorizing index.
    if len(tx.signatures) <= signature_index:
        return FrameStatus.FAILURE
    signature = tx.signatures[signature_index]

    # Only a protocol-validated secp256k1 signature authorizes.
    if signature.scheme != FrameSignatureScheme.SECP256K1:
        return FrameStatus.FAILURE
    # The signature must cover the canonical signature hash.
    if len(signature.message) != 0:
        return FrameStatus.FAILURE
    # The signature must come from the frame's resolved target.
    if frame_context.resolved_signers[signature_index] != resolved_target:
        return FrameStatus.FAILURE

    if not attempt_approval(tx_env, allowed_scope):
        return FrameStatus.FAILURE

    return FrameStatus.SUCCESS


def execute_frame(
    block_env: BlockEnvironment,
    tx_env: TransactionEnvironment,
    frame: Frame,
    journal: FrameJournal,
) -> FrameOutcome:
    """
    Run a single frame as a top-level call and reduce its outcome.

    Every frame is charged its resolved target's warm or cold access
    at frame entry, from its own execution gas budget, before
    anything else: resolving the target's code is how the protocol
    dispatches the frame. A `VERIFY` frame whose resolved target has
    no code then runs the protocol default code instead of an EVM,
    unless that target is a precompile, which dispatches in every
    mode. As with an ordinary `CALL`, a caller that cannot cover the
    transferred value reverts the frame, consuming the gas charged so
    far.

    The frame's receipt reports its usage of both gas dimensions at
    frame exit: the execution gas its meter consumed — the whole
    budget when the frame halted exceptionally — and its state budget
    less the remaining pool. A failing frame's state gas, the
    frame-entry charge included, rolls back to the checkpoint taken
    here at frame entry, so its receipt reports zero state gas.

    On success the frame's accesses are committed back to the
    journal's warm sets — the resolved target included, which is what
    keeps a payer warm for later frames — and a failed frame's
    accesses are discarded, so nothing it touched stays warm.
    """
    frame_context = tx_env.frame_context
    assert frame_context is not None
    tx = frame_context.tx
    tx_state = tx_env.state
    resolved_target = resolve_frame_target(tx, frame)

    # Checkpoint at frame entry, before any charge: a failing frame's
    # state gas restores to here, and any edits it made to earlier
    # receipts are undone with it.
    entry_snapshot = copy_frame_context(tx_env)
    state_budget = Uint(frame.gas_limits.state)
    execution_budget = Uint(frame.gas_limits.execution)

    gas_meter = GasMeter(
        gas_left=ExecutionGas(execution_budget),
        reservoir=None,
    )

    ## Warm up the frame's access sets
    accessed_addresses: Set[Address] = set(journal.warm_addresses)
    accessed_addresses.add(block_env.coinbase)
    accessed_addresses.update(PRE_COMPILED_CONTRACTS.keys())
    accessed_storage_keys = set(journal.warm_storage_keys)

    ## Charge the resolved target's access
    try:
        if resolved_target in accessed_addresses:
            charge_gas_from_meter(gas_meter, GasCosts.WARM_ACCESS)
        else:
            charge_gas_from_meter(gas_meter, GasCosts.COLD_ACCOUNT_ACCESS)
            accessed_addresses.add(resolved_target)
    except ExceptionalHalt:
        # The target's access exceeded the frame's execution budget:
        # the frame halts exceptionally, consuming the budget whole.
        # Nothing else has been charged, so there is nothing to
        # restore.
        return FrameOutcome(
            receipt=FrameReceipt(
                status=FrameStatus.FAILURE,
                gas_used=GasUsed(execution=execution_budget, state=Uint(0)),
                logs=(),
            ),
            refund_counter=0,
            accounts_to_delete=set(),
        )

    target_account = get_account(tx_state, resolved_target)
    if (
        frame.mode == FrameMode.VERIFY
        and resolved_target not in PRE_COMPILED_CONTRACTS
        and target_account.code_hash == EMPTY_CODE_HASH
    ):
        try:
            status = execute_default_verify_code(tx_env, frame)
        except ExceptionalHalt:
            # `APPROVE` could not cover the sender-creation state
            # charge: the frame halts exceptionally with no approval
            # effects, consuming its execution budget.
            restore_frame_context(tx_env, entry_snapshot)
            return FrameOutcome(
                receipt=FrameReceipt(
                    status=FrameStatus.FAILURE,
                    gas_used=GasUsed(
                        execution=execution_budget,
                        state=Uint(0),
                    ),
                    logs=(),
                ),
                refund_counter=0,
                accounts_to_delete=set(),
            )
        if status == FrameStatus.SUCCESS:
            journal.warm_addresses.update(accessed_addresses)
        return FrameOutcome(
            receipt=FrameReceipt(
                status=status,
                gas_used=GasUsed(
                    execution=execution_budget - Uint(gas_meter.gas_left),
                    state=state_budget - Uint(frame_context.state_gas_left),
                ),
                logs=(),
            ),
            refund_counter=0,
            accounts_to_delete=set(),
        )

    if frame.value != U256(0):
        caller_balance = get_account(tx_state, tx_env.origin).balance
        if caller_balance < frame.value:
            return FrameOutcome(
                receipt=FrameReceipt(
                    status=FrameStatus.FAILURE,
                    gas_used=GasUsed(
                        execution=execution_budget - Uint(gas_meter.gas_left),
                        state=Uint(0),
                    ),
                    logs=(),
                ),
                refund_counter=0,
                accounts_to_delete=set(),
            )

    try:
        evm = create_evm_from_frame(
            block_env,
            tx_env,
            frame,
            resolved_target,
            gas_meter,
            accessed_addresses,
            accessed_storage_keys,
        )
    except ExceptionalHalt:
        # The frame's entry charges exceeded its own budgets: the
        # frame halts exceptionally, consuming its execution budget.
        restore_frame_context(tx_env, entry_snapshot)
        return FrameOutcome(
            receipt=FrameReceipt(
                status=FrameStatus.FAILURE,
                gas_used=GasUsed(
                    execution=execution_budget,
                    state=Uint(0),
                ),
                logs=(),
            ),
            refund_counter=0,
            accounts_to_delete=set(),
        )

    process_call(evm)

    if evm.error is not None:
        # The frame failed: `process_call` rolled its state gas back
        # to the call, and this restore extends the rollback over the
        # frame-entry charge.
        restore_frame_context(tx_env, entry_snapshot)

    gas_used = GasUsed(
        execution=execution_budget - Uint(gas_meter.gas_left),
        state=state_budget - Uint(frame_context.state_gas_left),
    )
    if evm.error is None:
        journal.warm_addresses.update(evm.accessed_addresses)
        journal.warm_storage_keys.update(evm.accessed_storage_keys)
        receipt = FrameReceipt(
            status=FrameStatus.SUCCESS, gas_used=gas_used, logs=evm.logs
        )
        accounts_to_delete = set(evm.accounts_to_delete)
    else:
        receipt = FrameReceipt(
            status=FrameStatus.FAILURE, gas_used=gas_used, logs=()
        )
        accounts_to_delete = set()

    return FrameOutcome(
        receipt=receipt,
        refund_counter=gas_meter.refund_counter,
        accounts_to_delete=accounts_to_delete,
    )


def process_frames(
    block_env: BlockEnvironment,
    tx_env: TransactionEnvironment,
) -> TransactionOutput:
    """
    Execute the frames of a frame transaction in order.

    Each frame runs against fresh gas pools holding its declared
    budgets: a gas meter for the execution dimension and the frame
    context's state gas pool for the state dimension. Unused gas is
    not available to later frames. Between frames the transient
    storage is discarded and the environment's origin is rebound to
    the caller of the frame about to run.

    A failing frame of an atomic batch unrolls the batch, and the
    remaining batch frames are skipped.

    Both gas dimensions settle from the final receipts: each frame's
    unused gas is its budget less its receipt's usage, so gas a
    rollback or a later frame's refill removed from a receipt counts
    as unused without further accounting.

    Unlike `process_top_level`, this flow can invalidate the whole
    transaction: a `VERIFY` frame reverting, a `SENDER` frame before
    execution approval, or no frame having approved payment by the end
    raises `FrameTransactionExecutionError`.
    """
    frame_context = tx_env.frame_context
    assert frame_context is not None
    assert tx_env.top_level_context is None

    tx = frame_context.tx
    tx_state = tx_env.state

    journal = FrameJournal(
        warm_addresses={tx.sender},
        warm_storage_keys=set(),
        refund_counter=0,
        accounts_to_delete=set(),
    )

    open_batch: Optional[AtomicBatch] = None
    skip_batch = False

    for index, frame in enumerate(tx.frames):
        frame_context.current_frame_index = Uint(index)
        has_batch_flag = FrameFlag.ATOMIC_BATCH in frame.flags

        if has_batch_flag and open_batch is None:
            context_snapshot = copy_frame_context(tx_env)
            assert context_snapshot is not None
            open_batch = AtomicBatch(
                first_frame_index=Uint(index),
                state_snapshot=copy_tx_state(tx_state),
                context_snapshot=context_snapshot,
                journal=copy_frame_journal(journal),
            )

        if skip_batch:
            # A frame of a failed atomic batch never executes; its
            # zero-usage receipt makes its allotted gas — in both
            # dimensions — count as unused.
            frame_context.frame_receipts.append(
                FrameReceipt(
                    status=FrameStatus.SKIPPED,
                    gas_used=GasUsed(execution=Uint(0), state=Uint(0)),
                    logs=(),
                )
            )
            if not has_batch_flag:
                open_batch = None
                skip_batch = False
            continue

        if (
            frame.mode == FrameMode.SENDER
            and not frame_context.sender_approved
        ):
            raise FrameTransactionExecutionError(
                "SENDER frame before execution approval"
            )

        # Transient storage is discarded between frames.
        tx_state.transient_storage.clear()

        # The ORIGIN opcode returns the frame's caller at every call
        # depth.
        if frame.mode == FrameMode.SENDER:
            tx_env.origin = tx.sender
        else:
            tx_env.origin = FRAME_ENTRY_POINT

        # Seed the frame's state gas pool from its declared budget.
        frame_context.state_gas_left = StateGas(Uint(frame.gas_limits.state))

        outcome = execute_frame(block_env, tx_env, frame, journal)
        receipt = outcome.receipt

        if (
            frame.mode == FrameMode.VERIFY
            and receipt.status == FrameStatus.FAILURE
        ):
            raise FrameTransactionExecutionError("VERIFY frame failed")

        incorporate_frame_outcome(journal, outcome)
        frame_context.frame_receipts.append(receipt)

        terminates_batch = open_batch is not None and not has_batch_flag
        if receipt.status == FrameStatus.FAILURE and open_batch is not None:
            journal = unroll_atomic_batch(tx_env, open_batch)
            if terminates_batch:
                open_batch = None
            else:
                skip_batch = True
        elif terminates_batch:
            open_batch = None

    if frame_context.payer is None:
        raise FrameTransactionExecutionError("no frame approved gas payment")

    logs: Tuple[Log, ...] = ()
    for receipt in frame_context.frame_receipts:
        logs += receipt.logs

    # Settle both dimensions from the final receipts; every frame has
    # exactly one.
    unused_execution_gas = Uint(0)
    unused_state_gas = Uint(0)
    state_gas_used = Uint(0)
    for frame, receipt in zip(
        tx.frames, frame_context.frame_receipts, strict=True
    ):
        unused_execution_gas += (
            Uint(frame.gas_limits.execution) - receipt.gas_used.execution
        )
        unused_state_gas += (
            Uint(frame.gas_limits.state) - receipt.gas_used.state
        )
        state_gas_used += receipt.gas_used.state

    return TransactionOutput(
        gas_left=ExecutionGas(unused_execution_gas),
        refund_counter=U256(journal.refund_counter),
        logs=logs,
        accounts_to_delete=journal.accounts_to_delete,
        error=None,
        return_data=Bytes(b""),
        state_gas_left=StateGas(unused_state_gas),
        state_gas_used=int(state_gas_used),
    )
