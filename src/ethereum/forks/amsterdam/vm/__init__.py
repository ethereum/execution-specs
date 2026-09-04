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

from ethereum_types.bytes import Bytes, Bytes32
from ethereum_types.numeric import U64, U256, Uint

from ethereum.crypto.hash import Hash32, keccak256
from ethereum.exceptions import EthereumException
from ethereum.merkle_patricia_trie import Trie
from ethereum.state import Address
from ethereum.utils.byte import left_pad_zero_bytes

from ..block_access_lists import BlockAccessList, BlockAccessListBuilder
from ..blocks import Log, Receipt, Withdrawal
from ..fork_types import (
    Authorization,
    ExecutionGas,
    StateGas,
    VersionedHash,
)
from ..state_tracker import BlockState, TransactionState
from ..transactions import LegacyTransaction
from .gas import GasMeter

__all__ = ("Environment", "Evm")
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
@dataclass
class TransactionEnvironment:
    """
    Items that are used while processing a transaction.
    """

    origin: Address
    # For a creation, the address the contract deploys to.
    recipient: Address
    is_create: bool
    data: Bytes
    value: U256
    gas_limit: Uint
    effective_gas_price: Uint
    execution_gas_grant: ExecutionGas
    state_gas_reservoir: StateGas
    content_floor: Uint
    access_list_addresses: Set[Address]
    access_list_storage_keys: Set[Tuple[Address, Bytes32]]
    accounts_with_paid_writes: Set[Address]
    state: TransactionState
    blob_versioned_hashes: Tuple[VersionedHash, ...]
    authorizations: Tuple[Authorization, ...]
    index_in_block: Optional[Uint]
    tx_hash: Optional[Hash32]


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

    Parameters
    ----------
    evm :
        The parent `EVM`.
    child_evm :
        The child evm to incorporate.

    [spill]: ref:ethereum.forks.amsterdam.vm.gas.GasMeter.state_gas_spilled

    """
    child_meter = child_evm.gas_meter
    # Only the top frame commits state gas; a child never carries any.
    assert child_meter.state_gas_committed_spill == Uint(0)

    if child_evm.error:
        # A failed child arrives settled: rolled back to its baseline,
        # spill refilled, refunds discarded.
        assert child_meter.state_gas_spilled == Uint(0)
        assert child_meter.refund_counter == 0
        assert child_meter.state_gas_left == child_meter.state_gas_baseline

    # Gas returns to the parent regardless of the child's fate.
    # Note that upon failure, the child already arrives settled.
    gas_meter = evm.gas_meter
    gas_meter.gas_left += child_meter.gas_left
    gas_meter.state_gas_left += child_meter.state_gas_left
    gas_meter.state_gas_spilled += child_meter.state_gas_spilled
    gas_meter.refund_counter += child_meter.refund_counter

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
