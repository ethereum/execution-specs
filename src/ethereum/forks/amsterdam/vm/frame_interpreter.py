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

from ..blocks import FrameReceipt, Log
from ..exceptions import FrameTransactionExecutionError
from ..fork_types import ExecutionGas, StateGas
from ..state_tracker import (
    TransactionState,
    copy_tx_state,
    get_account,
    get_code,
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
    TransactionEnvironment,
    attempt_approval,
)
from .eoa_delegation import resolve_delegated_code_address
from .exceptions import ExceptionalHalt
from .gas import (
    GasCosts,
    GasMeter,
    charge_gas_from_meter,
    forfeit_remaining_gas,
    restore_state_gas,
    tx_state_gas_used,
)
from .interpreter import (
    TransactionOutput,
    charge_value_transfer_to_non_alive_account,
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
    warm journal that successful frames feed, and the quantities that
    settle the transaction once the last frame has run. When an
    atomic batch opens, a copy of the journal joins the batch's
    rollback point; unrolling the batch resumes from that copy —
    except the unused gas, which never rolls back.
    """

    warm_addresses: Set[Address]
    """
    Addresses left warm for later frames by successful frames.
    """

    warm_storage_keys: Set[Tuple[Address, Bytes32]]
    """
    Storage keys left warm for later frames by successful frames.
    """

    unused_gas: Uint
    """
    Gas the frames so far did not consume. Not available to later
    frames; it accumulates for settlement.
    """

    refund_counter: int
    """
    Refunds accrued by successful frames.
    """

    state_gas_used: int
    """
    Net state gas consumed by successful frames.
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
        unused_gas=journal.unused_gas,
        refund_counter=journal.refund_counter,
        state_gas_used=journal.state_gas_used,
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
    here.
    """

    first_frame_index: Uint
    """
    Index of the frame that opened the batch.
    """

    state_snapshot: TransactionState
    """
    Copy of the transaction state taken before the batch began.
    """

    payer: Optional[Address]
    """
    The context's payer before the batch began.
    """

    sender_approved: bool
    """
    The context's execution approval before the batch began.
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
    frame contributes to the transaction's settlement.
    """

    receipt: FrameReceipt
    """
    The frame's receipt entry.
    """

    gas_left: Uint
    """
    Gas the frame did not consume. Not available to later frames; it
    accumulates for settlement.
    """

    refund_counter: int
    """
    Refunds the frame accrued; zero unless the frame succeeded.
    """

    state_gas_used: int
    """
    Net state gas the frame consumed; zero unless the frame succeeded.
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
    journal.unused_gas += outcome.gas_left
    journal.refund_counter += outcome.refund_counter
    journal.state_gas_used += outcome.state_gas_used
    journal.accounts_to_delete |= outcome.accounts_to_delete


def unroll_atomic_batch(
    tx_env: TransactionEnvironment,
    batch: AtomicBatch,
    journal: FrameJournal,
) -> FrameJournal:
    """
    Unroll a failed atomic batch.

    The transaction state and the approval fields are restored to the
    condition immediately before the batch began, and the receipts of
    the executed batch frames keep their status and gas with their
    logs emptied. Return the batch's journal copy for the frame loop
    to continue from — carrying over the live journal's unused gas,
    because the gas the batch frames consumed remains charged.
    """
    frame_context = tx_env.frame_context
    assert frame_context is not None

    restore_tx_state(tx_env.state, batch.state_snapshot)
    frame_context.payer = batch.payer
    frame_context.sender_approved = batch.sender_approved

    receipts = frame_context.frame_receipts
    for index in range(int(batch.first_frame_index), len(receipts)):
        receipts[index] = replace(receipts[index], logs=())

    restored = batch.journal
    restored.unused_gas = journal.unused_gas
    return restored


def create_evm_from_frame(
    block_env: BlockEnvironment,
    tx_env: TransactionEnvironment,
    frame: Frame,
    resolved_target: Address,
    gas_meter: GasMeter,
    warm_addresses: Set[Address],
    warm_storage_keys: Set[Tuple[Address, Bytes32]],
) -> Evm:
    """
    Build a frame's top-level EVM.

    The frame starts warm with the coinbase, the precompiles, and the
    journal shared across frames — not its caller, and not its target:
    the target's warm or cold access is charged here, within the
    frame's own gas limit, as are the state gas for a value transfer
    reviving a dead account and the access for resolving an EIP-7702
    delegation. A charge exceeding the frame's gas raises instead of
    building the EVM, failing the frame.
    """
    ## Warm up the access sets
    accessed_addresses: Set[Address] = set(warm_addresses)
    accessed_addresses.add(block_env.coinbase)
    accessed_addresses.update(PRE_COMPILED_CONTRACTS.keys())
    accessed_storage_keys = set(warm_storage_keys)

    ## Resolve dispatch and charge its state-dependent costs
    if resolved_target in accessed_addresses:
        charge_gas_from_meter(gas_meter, GasCosts.WARM_ACCESS)
    else:
        charge_gas_from_meter(gas_meter, GasCosts.COLD_ACCOUNT_ACCESS)
        accessed_addresses.add(resolved_target)

    charge_value_transfer_to_non_alive_account(
        tx_env.state, gas_meter, resolved_target, frame.value
    )

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
    tx_env: TransactionEnvironment, frame: Frame
) -> FrameReceipt:
    """
    Execute the protocol default code of a `VERIFY` frame whose
    resolved target has no code. It consumes no gas.

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

    failure = FrameReceipt(
        status=FrameStatus.FAILURE, gas_used=Uint(0), logs=()
    )

    allowed_scope = frame.flags & APPROVE_SCOPE_MASK
    # The frame is not allowed to approve anything.
    if not allowed_scope:
        return failure

    if FrameFlag.APPROVE_EXECUTION in allowed_scope:
        signature_index = 0
    else:
        signature_index = 1

    # There is no signature entry at the authorizing index.
    if len(tx.signatures) <= signature_index:
        return failure
    signature = tx.signatures[signature_index]

    # Only a protocol-validated secp256k1 signature authorizes.
    if signature.scheme != FrameSignatureScheme.SECP256K1:
        return failure
    # The signature must cover the canonical signature hash.
    if len(signature.message) != 0:
        return failure
    # The signature must come from the frame's resolved target.
    if frame_context.resolved_signers[signature_index] != resolved_target:
        return failure

    if not attempt_approval(tx_env, allowed_scope):
        return failure

    return FrameReceipt(status=FrameStatus.SUCCESS, gas_used=Uint(0), logs=())


def execute_frame(
    block_env: BlockEnvironment,
    tx_env: TransactionEnvironment,
    frame: Frame,
    journal: FrameJournal,
) -> FrameOutcome:
    """
    Run a single frame as a top-level call and reduce its outcome.

    A `VERIFY` frame whose resolved target has no code runs the
    protocol default code instead of an EVM. As with an ordinary
    `CALL`, a caller that cannot cover the transferred value reverts
    the frame before it executes, consuming no gas.

    On success the frame's accesses are committed back to the
    journal's warm sets; a failed frame's accesses are discarded with
    its EVM, so nothing it touched stays warm.
    """
    frame_context = tx_env.frame_context
    assert frame_context is not None
    tx = frame_context.tx
    tx_state = tx_env.state
    resolved_target = resolve_frame_target(tx, frame)

    target_account = get_account(tx_state, resolved_target)
    if (
        frame.mode == FrameMode.VERIFY
        and target_account.code_hash == EMPTY_CODE_HASH
    ):
        return FrameOutcome(
            receipt=execute_default_verify_code(tx_env, frame),
            gas_left=Uint(frame.gas),
            refund_counter=0,
            state_gas_used=0,
            accounts_to_delete=set(),
        )

    if frame.value != U256(0):
        caller_balance = get_account(tx_state, tx_env.origin).balance
        if caller_balance < frame.value:
            return FrameOutcome(
                receipt=FrameReceipt(
                    status=FrameStatus.FAILURE, gas_used=Uint(0), logs=()
                ),
                gas_left=Uint(frame.gas),
                refund_counter=0,
                state_gas_used=0,
                accounts_to_delete=set(),
            )

    gas_meter = GasMeter(
        gas_left=ExecutionGas(Uint(frame.gas)),
        state_gas_left=StateGas(Uint(0)),
        state_gas_baseline=StateGas(Uint(0)),
    )

    try:
        evm = create_evm_from_frame(
            block_env,
            tx_env,
            frame,
            resolved_target,
            gas_meter,
            journal.warm_addresses,
            journal.warm_storage_keys,
        )
    except ExceptionalHalt:
        # The frame's entry charges exceeded its own gas limit.
        restore_state_gas(gas_meter)
        forfeit_remaining_gas(gas_meter)
        return FrameOutcome(
            receipt=FrameReceipt(
                status=FrameStatus.FAILURE,
                gas_used=Uint(frame.gas),
                logs=(),
            ),
            gas_left=Uint(0),
            refund_counter=0,
            state_gas_used=0,
            accounts_to_delete=set(),
        )

    process_call(evm)

    gas_used = Uint(frame.gas) - gas_meter.gas_left
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
        gas_left=gas_meter.gas_left,
        refund_counter=gas_meter.refund_counter,
        state_gas_used=tx_state_gas_used(gas_meter, StateGas(Uint(0))),
        accounts_to_delete=accounts_to_delete,
    )


def process_frames(
    block_env: BlockEnvironment,
    tx_env: TransactionEnvironment,
) -> TransactionOutput:
    """
    Execute the frames of a frame transaction in order.

    Each frame runs with a fresh gas meter holding its own gas limit;
    unused gas is not available to later frames and accumulates for
    settlement. Between frames the transient storage is discarded and
    the environment's origin is rebound to the caller of the frame
    about to run.

    A failing frame of an atomic batch unrolls the batch, and the
    remaining batch frames are skipped — their allotted gas counts as
    unused.

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
        unused_gas=Uint(0),
        refund_counter=0,
        state_gas_used=0,
        accounts_to_delete=set(),
    )

    open_batch: Optional[AtomicBatch] = None
    skip_batch = False

    for index, frame in enumerate(tx.frames):
        frame_context.current_frame_index = Uint(index)
        has_batch_flag = FrameFlag.ATOMIC_BATCH in frame.flags

        if has_batch_flag and open_batch is None:
            open_batch = AtomicBatch(
                first_frame_index=Uint(index),
                state_snapshot=copy_tx_state(tx_state),
                payer=frame_context.payer,
                sender_approved=frame_context.sender_approved,
                journal=copy_frame_journal(journal),
            )

        if skip_batch:
            # A frame of a failed atomic batch never executes; its
            # allotted gas counts as unused.
            frame_context.frame_receipts.append(
                FrameReceipt(
                    status=FrameStatus.SKIPPED, gas_used=Uint(0), logs=()
                )
            )
            journal.unused_gas += Uint(frame.gas)
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

        outcome = execute_frame(block_env, tx_env, frame, journal)
        receipt = outcome.receipt

        if (
            frame.mode == FrameMode.VERIFY
            and receipt.status == FrameStatus.FAILURE
        ):
            raise FrameTransactionExecutionError("VERIFY frame reverted")

        incorporate_frame_outcome(journal, outcome)
        frame_context.frame_receipts.append(receipt)

        terminates_batch = open_batch is not None and not has_batch_flag
        if receipt.status == FrameStatus.FAILURE and open_batch is not None:
            journal = unroll_atomic_batch(tx_env, open_batch, journal)
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

    return TransactionOutput(
        gas_left=ExecutionGas(journal.unused_gas),
        refund_counter=U256(journal.refund_counter),
        logs=logs,
        accounts_to_delete=journal.accounts_to_delete,
        error=None,
        return_data=Bytes(b""),
        state_gas_left=StateGas(Uint(0)),
        state_gas_used=journal.state_gas_used,
    )
