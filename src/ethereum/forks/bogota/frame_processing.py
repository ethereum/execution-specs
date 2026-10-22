"""
Frame transaction processing.

The block-level flow for [EIP-8141] frame transactions, separate from
the regular flow in `fork.py` from admission onwards: a frame
transaction has no single top-level call to dispatch — it executes a
list of frames — and no upfront sender payment: the consumption of
the transaction's nonce set and the collection of its maximum cost
are effects of the `APPROVE` instruction, during execution.

[EIP-8141]: https://eips.ethereum.org/EIPS/eip-8141
"""

from typing import Tuple

from ethereum_rlp import rlp
from ethereum_types.bytes import Bytes
from ethereum_types.numeric import U256, Uint

from ethereum.merkle_patricia_trie import trie_set
from ethereum.state import Address

from . import vm
from .blocks import (
    FrameReceipt,
    FrameTransactionReceipt,
    Receipt,
    encode_receipt,
)
from .exceptions import InsufficientMaxFeeError
from .fork_types import ExecutionGas, StateGas
from .keyed_nonces import check_nonce_set
from .state_tracker import (
    TransactionState,
    create_ether,
    get_account,
    incorporate_tx_into_block,
)
from .transactions import encode_transaction, get_transaction_hash
from .transactions.frame_transaction import (
    FrameTransaction,
    validate_frame_transaction,
)
from .vm.frame_interpreter import process_frames
from .vm.gas import (
    calculate_blob_gas_price,
    calculate_total_blob_gas,
    check_block_gas_capacity,
    settle_frame_transaction_gas,
)


def check_frame_transaction(
    block_env: vm.BlockEnvironment,
    block_output: vm.BlockOutput,
    tx: FrameTransaction,
    index: Uint,
) -> vm.TransactionEnvironment:
    """
    Admit a raw frame transaction and build its execution environment.

    Statically validate the transaction and check that it is includable
    in the block, in that order, so that a transaction invalid in
    several ways reports the earliest failure.

    Unlike the regular flow, the sender needs no recovery — it is an
    explicit field, authenticated by the signature entries during
    static validation — and no balance or EOA check: payment is
    collected from the payer during execution, when a frame `APPROVE`s
    it.

    Parameters
    ----------
    block_env :
        The block scoped environment.
    block_output :
        The block output for the current block.
    tx :
        The frame transaction.
    index :
        The index of the current transaction.

    Returns
    -------
    tx_env :
        The environment for executing the transaction.

    Raises
    ------
    InvalidBlock :
        If the transaction is not includable.
    InvalidSignatureError :
        If a signature entry is cryptographically invalid.
    InvalidFrameError :
        If the frames or signature entries violate a structural
        constraint.
    TransactionGasLimitExceededError :
        If the derived gas limit exceeds the maximum allowed for a
        transaction.
    GasUsedExceedsLimitError :
        If the gas used by the transaction exceeds the block's gas limit.
    NonceMismatchError :
        If a nonce key the transaction selects does not hold the
        transaction's nonce sequence.
    InsufficientMaxFeeError :
        If the maximum fee does not cover the transaction's worst-case
        base fee charge.
    BlobGasLimitExceededError :
        If the blob gas used by the transaction exceeds the block's blob gas
        limit.

    """
    validation = validate_frame_transaction(tx)
    tx_state = TransactionState(parent=block_env.state)

    # The frames' total gas budget in each dimension. The execution
    # total becomes the grant the frames draw from; frame transactions
    # declare their state gas budgets explicitly per frame, so the
    # reservoir model of the regular flow does not apply and the
    # reservoir is empty.
    execution_gas_grant = Uint(0)
    state_reservation = Uint(0)
    for frame in tx.frames:
        execution_gas_grant += Uint(frame.gas_limits.execution)
        state_reservation += Uint(frame.gas_limits.state)

    # Explicit budgets make the block reservations exact per
    # dimension; the execution reservation carries the calldata floor,
    # which binds the execution dimension.
    execution_reservation = max(
        Uint(validation.intrinsic.execution) + execution_gas_grant,
        Uint(validation.intrinsic.calldata_floor),
    )

    check_block_gas_capacity(
        block_env,
        block_output,
        execution_reservation,
        state_reservation,
        calculate_total_blob_gas(tx),
    )

    sender_account = get_account(tx_state, tx.sender)

    max_cost, effective_gas_price = calculate_frame_transaction_fees(
        tx, validation.max_gas, block_env
    )

    check_nonce_set(tx_state, tx)

    return vm.TransactionEnvironment(
        origin=tx.sender,
        gas_limit=validation.max_gas,
        effective_gas_price=effective_gas_price,
        execution_gas_grant=ExecutionGas(execution_gas_grant),
        state_gas_reservoir=StateGas(Uint(0)),
        calldata_floor=validation.intrinsic.calldata_floor,
        access_list_addresses=set(),
        access_list_storage_keys=set(),
        accounts_with_paid_writes={tx.sender},
        state=tx_state,
        blob_versioned_hashes=tx.blob_versioned_hashes,
        authorizations=(),
        index_in_block=index,
        tx_hash=get_transaction_hash(encode_transaction(tx)),
        top_level_context=None,
        frame_context=vm.FrameContext(
            tx=tx,
            signature_hash=validation.signature_hash,
            resolved_signers=validation.resolved_signers,
            legacy_nonce=sender_account.nonce,
            standard_gas_limit=validation.standard_gas_limit,
            max_cost=max_cost,
            current_frame_index=Uint(0),
            frame_receipts=[],
            payer=None,
            sender_approved=False,
            state_gas_left=StateGas(Uint(0)),
            outstanding_charge_owners={},
        ),
    )


def calculate_frame_transaction_fees(
    tx: FrameTransaction,
    max_gas: Uint,
    block_env: vm.BlockEnvironment,
) -> Tuple[Uint, Uint]:
    """
    Check a frame transaction's fee budget against the block's base fees
    and derive what the payer escrows.

    The `max_fee` budget covers the execution, state, and blob gas
    together. It must cover the worst case at the block's base fees,
    `max_gas` at the base fee plus the blob gas at the blob base fee, or
    an `InsufficientMaxFeeError` is raised. The payer escrows that worst
    case plus the largest tip the rest of the budget allows.

    Return the escrow, `max_cost`, and the price per gas that `GASPRICE`
    reports: the base fee plus the tip per gas, capped by what the rest of
    the budget can pay for every unit of `max_gas`. The payer pays at
    least this price per unit of gas used, since unused gas can back a
    larger tip at settlement.
    """
    blob_fee = Uint(calculate_total_blob_gas(tx)) * calculate_blob_gas_price(
        block_env.excess_blob_gas
    )
    required_max_fee = max_gas * block_env.base_fee_per_gas + blob_fee
    if tx.fees.max_fee < required_max_fee:
        raise InsufficientMaxFeeError(
            f"max fee {tx.fees.max_fee} below the required {required_max_fee}"
        )

    budget_left = tx.fees.max_fee - required_max_fee
    max_priority_fee = min(
        tx.fees.max_priority_fee_per_gas * max_gas, budget_left
    )
    max_cost = required_max_fee + max_priority_fee
    gas_price = block_env.base_fee_per_gas + max_priority_fee // max_gas
    return max_cost, gas_price


def disburse_frame_gas_fees(
    block_env: vm.BlockEnvironment,
    tx_env: vm.TransactionEnvironment,
    gas_used: Uint,
) -> None:
    """
    Refund the payer's unspent escrow and pay the priority fee.

    At `APPROVE` the payer escrowed the transaction's `max_cost`. The
    gas used at the base fee, plus the blob gas at the blob base fee, is
    burned. The coinbase receives the priority fee per gas on the gas
    used, capped by what the escrow holds after the burn, and the payer
    gets back the rest.
    """
    frame_context = tx_env.frame_context
    assert frame_context is not None
    # `process_frames` invalidates the transaction unless a frame
    # approved payment.
    payer = frame_context.payer
    assert payer is not None

    tx = frame_context.tx
    blob_fee = Uint(calculate_total_blob_gas(tx)) * calculate_blob_gas_price(
        block_env.excess_blob_gas
    )
    base_fee_paid = gas_used * block_env.base_fee_per_gas + blob_fee
    priority_fee_paid = min(
        tx.fees.max_priority_fee_per_gas * gas_used,
        frame_context.max_cost - base_fee_paid,
    )
    payer_refund = frame_context.max_cost - base_fee_paid - priority_fee_paid

    create_ether(tx_env.state, payer, U256(payer_refund))
    create_ether(tx_env.state, block_env.coinbase, U256(priority_fee_paid))


def make_frame_receipt(
    tx: FrameTransaction,
    payer: Address,
    cumulative_gas_used: Uint,
    frame_receipts: Tuple[FrameReceipt, ...],
) -> Bytes | Receipt:
    """
    Make the receipt for a frame transaction that was executed.

    Unlike a regular receipt there is no transaction-level status and
    no bloom filter: outcomes are reported per frame, and the frames'
    logs reach the block's log bloom through the block accumulator.
    """
    receipt = FrameTransactionReceipt(
        cumulative_gas_used=cumulative_gas_used,
        payer=payer,
        frame_receipts=frame_receipts,
    )

    return encode_receipt(tx, receipt)


def process_frame_transaction(
    block_env: vm.BlockEnvironment,
    block_output: vm.BlockOutput,
    tx: FrameTransaction,
    index: Uint,
) -> None:
    """
    Execute a frame transaction against the provided environment.

    Admit the transaction, execute its frames in order, settle the gas,
    disburse the fees, and write the frame transaction receipt.
    """
    tx_env = check_frame_transaction(block_env, block_output, tx, index)

    tx_output = process_frames(block_env, tx_env)

    frame_context = tx_env.frame_context
    assert frame_context is not None
    # `process_frames` invalidates the transaction unless a frame
    # approved payment.
    payer = frame_context.payer
    assert payer is not None

    tx_unused_gas = Uint(tx_output.gas_left) + Uint(tx_output.state_gas_left)
    settlement = settle_frame_transaction_gas(
        frame_context.standard_gas_limit,
        tx_env.calldata_floor,
        tx_unused_gas,
        tx_output.refund_counter,
        StateGas(Uint(tx_output.state_gas_used)),
    )

    disburse_frame_gas_fees(block_env, tx_env, settlement.gas_used)

    block_output.block_gas_used += settlement.execution_gas_used
    block_output.block_state_gas_used += settlement.state_gas_used
    block_output.blob_gas_used += calculate_total_blob_gas(tx)

    block_output.cumulative_gas_used += settlement.gas_used
    receipt = make_frame_receipt(
        tx,
        payer,
        block_output.cumulative_gas_used,
        tuple(frame_context.frame_receipts),
    )

    receipt_key = rlp.encode(Uint(index))
    block_output.receipt_keys += (receipt_key,)

    trie_set(
        block_output.receipts_trie,
        receipt_key,
        receipt,
    )

    block_output.block_logs += tx_output.logs

    incorporate_tx_into_block(
        tx_env.state, block_env.block_access_list_builder
    )
