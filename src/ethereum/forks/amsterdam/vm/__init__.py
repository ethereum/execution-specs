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
from typing import List, Optional, Set, Tuple

from ethereum_types.bytes import Bytes, Bytes0, Bytes32
from ethereum_types.numeric import U64, U256, Uint

from ethereum.crypto.hash import Hash32
from ethereum.exceptions import EthereumException
from ethereum.state import Address

from ..block_access_lists import BlockAccessList, BlockAccessListBuilder
from ..blocks import Log, Receipt, Withdrawal
from ..fork_types import Authorization, VersionedHash
from ..state_tracker import BlockState, TransactionState
from ..transactions import LegacyTransaction
from ..trie import Trie

__all__ = ("Environment", "Evm", "Message")


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


@dataclass
class TransactionEnvironment:
    """
    Items that are used by contract creation or message call.
    """

    origin: Address
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
    state_gas_used: Uint = Uint(0)
    state_gas_refund: Uint = Uint(0)
    state_gas_refund_pending: Uint = Uint(0)


def credit_state_gas_refund(evm: Evm, amount: Uint) -> None:
    """
    Credit an inline state gas refund to `evm.state_gas_left`.

    Clamp the applied portion to this frame's `state_gas_used` — the
    matching charge may sit in an ancestor sharing storage via
    CALLCODE/DELEGATECALL.  Track it in `state_gas_refund` so
    `incorporate_child_on_error` can undo the inflation, and defer the
    unapplied remainder in `state_gas_refund_pending` for propagation
    on success.

    Parameters
    ----------
    evm :
        The frame crediting the refund.
    amount :
        The refund amount to credit.

    """
    applied = min(amount, evm.state_gas_used)
    evm.state_gas_left += applied
    evm.state_gas_used -= applied
    evm.state_gas_refund += applied
    evm.state_gas_refund_pending += amount - applied


def incorporate_child_on_success(evm: Evm, child_evm: Evm) -> None:
    """
    Incorporate the state of a successful `child_evm` into the parent `evm`.

    Propagate `state_gas_refund` (inline credits the child applied) so
    an ancestor revert can undo the inflation, and apply
    `state_gas_refund_pending` (the unapplied remainder) to the parent
    via `credit_state_gas_refund`; any leftover propagates further up.

    Parameters
    ----------
    evm :
        The parent `EVM`.
    child_evm :
        The child evm to incorporate.

    """
    evm.gas_left += child_evm.gas_left
    evm.state_gas_left += child_evm.state_gas_left
    evm.logs += child_evm.logs
    evm.refund_counter += child_evm.refund_counter
    evm.accounts_to_delete.update(child_evm.accounts_to_delete)
    evm.accessed_addresses.update(child_evm.accessed_addresses)
    evm.accessed_storage_keys.update(child_evm.accessed_storage_keys)
    evm.regular_gas_used += child_evm.regular_gas_used
    evm.state_gas_used += child_evm.state_gas_used
    evm.state_gas_refund += child_evm.state_gas_refund
    credit_state_gas_refund(evm, child_evm.state_gas_refund_pending)


def incorporate_child_on_error(
    evm: Evm,
    child_evm: Evm,
) -> None:
    """
    Incorporate the state of an unsuccessful `child_evm` into the parent `evm`.

    On failure (revert or exceptional halt) state changes are rolled back,
    so no state was actually grown.  All state gas, both reservoir and any
    that spilled into `gas_left`, is restored to the parent's reservoir and
    the child's `state_gas_used` is not accumulated.

    Inline state-gas refunds (SSTORE 0 to x to 0, CREATE silent failure)
    credited by the child inflated its `state_gas_left`; subtract
    `state_gas_refund` from the amount returned to the parent's
    reservoir so the inflation does not leak across the error boundary.
    `state_gas_refund_pending` is discarded with the child frame.

    Parameters
    ----------
    evm :
        The parent `EVM`.
    child_evm :
        The child evm to incorporate.

    """
    evm.gas_left += child_evm.gas_left
    evm.state_gas_left += (
        child_evm.state_gas_used
        + child_evm.state_gas_left
        - child_evm.state_gas_refund
    )
    evm.regular_gas_used += child_evm.regular_gas_used
