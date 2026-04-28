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

from ethereum.crypto.hash import Hash32, keccak256
from ethereum.exceptions import EthereumException
from ethereum.merkle_patricia_trie import Trie
from ethereum.state import Address
from ethereum.utils.byte import left_pad_zero_bytes

from ..block_access_lists import BlockAccessList, BlockAccessListBuilder
from ..blocks import Log, Receipt, Withdrawal
from ..fork_types import Authorization, VersionedHash
from ..state_tracker import BlockState, TransactionState
from ..transactions import LegacyTransaction

__all__ = ("Environment", "Evm", "Message")
TRANSFER_TOPIC = keccak256(b"Transfer(address,address,uint256)")
BURN_TOPIC = keccak256(b"Burn(address,uint256)")
SYSTEM_ADDRESS = Address(
    bytes.fromhex("fffffffffffffffffffffffffffffffffffffffe")
)
CALL_SUCCESS = U256(1)


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
    # The state-gas dimension of block accounting. Block-end check
    # enforces `max(block_gas_used, block_state_gas_used) <=
    # gas_limit`. Header `gas_used` reports the binding dimension.
    block_state_gas_used: Uint = Uint(0)
    # Running total of post-refund, post-floor tx gas. Used to
    # populate receipt `cumulative_gas_used` (per-tx delta of
    # consecutive receipts gives that tx's actual gas paid).
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
    # State-gas budget allocated to this tx. Seeds the depth-0
    # `Evm.state_gas_reservoir` and propagates via Message.
    state_gas_reservoir: Uint
    access_list_addresses: Set[Address]
    access_list_storage_keys: Set[Tuple[Address, Bytes32]]
    state: TransactionState
    blob_versioned_hashes: Tuple[VersionedHash, ...]
    authorizations: Tuple[Authorization, ...]
    index_in_block: Optional[Uint]
    tx_hash: Optional[Hash32]
    # Pre-validated intrinsic costs split by dimension. Immutable
    # post-validation; used for block-level 2D accounting.
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
    # State-gas budget handed to this frame. Initially set from
    # `tx_env.state_gas_reservoir` for the depth-0 frame; for child
    # frames, set by the caller's CALL/CREATE handoff (see
    # `generic_create` and `call`/etc. in instructions/system.py).
    # Seeds the child `Evm.state_gas_reservoir` in `process_message`.
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
    # Per-frame state-gas budget (the reservoir handed down from the
    # parent's `Message.state_gas_reservoir`). Drains at frame-end
    # only, never per-opcode.
    state_gas_reservoir: Uint
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
    # Per-tx running totals. Block-level 2D accounting needs the
    # regular and state portions separated; these counters get
    # composed up via `incorporate_child_on_success` and read at
    # tx-end by `process_transaction`.
    regular_gas_used: Uint = Uint(0)
    state_gas_used: Uint = Uint(0)


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
    evm.state_gas_reservoir += child_evm.state_gas_reservoir
    evm.logs += child_evm.logs
    evm.refund_counter += child_evm.refund_counter
    evm.accounts_to_delete.update(child_evm.accounts_to_delete)
    evm.accessed_addresses.update(child_evm.accessed_addresses)
    evm.accessed_storage_keys.update(child_evm.accessed_storage_keys)
    evm.regular_gas_used += child_evm.regular_gas_used
    evm.state_gas_used += child_evm.state_gas_used


def incorporate_child_on_error(
    evm: Evm,
    child_evm: Evm,
) -> None:
    """
    Incorporate the state of an unsuccessful `child_evm` into the parent `evm`.

    All state gas the child held is returned to the parent `state_gas_reservoir`.

    Parameters
    ----------
    evm :
        The parent `EVM`.
    child_evm :
        The child evm to incorporate.

    """
    # `restore_tx_state` already rolled the child's writes out of
    # `tx_state`, so the parent's frame-end diff won't see them and
    # the parent walks away as if the child call never happened from
    # a state perspective.
    #
    # State-gas restoration: the child may have charged state gas in
    # successful sub-grandchildren whose writes were rolled back
    # alongside the child's snapshot. Both `state_gas_used` (charged
    # by sub-frames that succeeded) and `state_gas_reservoir` (unspent
    # reservoir) are returned to the parent's reservoir.
    # `state_gas_used` is *not* added to the parent's `state_gas_used`
    # since no state was actually grown — only the budget round-trip
    # is preserved.
    #
    # `regular_gas_used` IS propagated because the child's CPU-style
    # work happened: the gas was burned on opcode execution (memory
    # expansion, hashing, etc.), even though state was rolled back.
    # The block-level regular-gas total has to count it.
    evm.gas_left += child_evm.gas_left
    evm.state_gas_reservoir += child_evm.state_gas_used + child_evm.state_gas_reservoir
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


def emit_burn_log(
    evm: Evm,
    account: Address,
    amount: U256,
) -> None:
    """
    Emit a LOG2 for ETH burn per EIP-7708.

    Parameters
    ----------
    evm :
        The state of the ethereum virtual machine
    account :
        The account address whose ETH is being burned
    amount :
        The amount of ETH being burned

    """
    if amount == 0:
        return

    padded_account = left_pad_zero_bytes(account, 32)
    log_entry = Log(
        address=SYSTEM_ADDRESS,
        topics=(
            BURN_TOPIC,
            Hash32(padded_account),
        ),
        data=amount.to_be_bytes32(),
    )

    evm.logs = evm.logs + (log_entry,)
