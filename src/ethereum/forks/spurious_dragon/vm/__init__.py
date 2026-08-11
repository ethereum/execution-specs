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
from typing import Callable, List, Mapping, Optional, Set, Tuple, final

from ethereum_types.bytes import Bytes, Bytes0
from ethereum_types.numeric import U64, U256, Uint

from ethereum.crypto.hash import Hash32
from ethereum.exceptions import EthereumException
from ethereum.merkle_patricia_trie import Trie
from ethereum.state import Address

from ..blocks import Log, Receipt
from ..state_tracker import (
    BlockState,
    TransactionState,
    account_exists_and_is_empty,
)
from ..transactions import Transaction
from .precompiled_contracts import RIPEMD160_ADDRESS

__all__ = ("Environment", "Evm", "Message")


def canonical_precompiles() -> Mapping[Address, Callable]:
    """
    Return the fork's precompiles at the addresses they answer at on
    chain.

    The import is deferred because every precompile implementation
    imports `Evm` from this module, so the mapping only becomes
    importable once this module has finished defining it.
    """
    from .precompiled_contracts.mapping import PRE_COMPILED_CONTRACTS

    return PRE_COMPILED_CONTRACTS


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
    time: U256
    difficulty: Uint
    precompiles: Mapping[Address, Callable] = field(
        default_factory=canonical_precompiles
    )
    """
    The precompiles execution dispatches to, keyed by address.

    Defaults to the fork's own arrangement, so a block on chain never
    has to name them. A caller that wants a precompile somewhere else,
    or gone, supplies its own mapping here; because it reaches no
    further than this environment, the rearrangement dies with the
    execution it was built for.
    """


@final
@dataclass
class BlockOutput:
    """
    Output from applying the block body to the present state.

    Contains the following:

    block_gas_used : `ethereum.base_types.Uint`
        Gas used for executing all transactions.
    transactions_trie : `ethereum.fork_types.Root`
        Trie of all the transactions in the block.
    receipts_trie : `ethereum.fork_types.Root`
        Trie root of all the receipts in the block.
    receipt_keys :
        Keys of all the receipts in the block.
    block_logs : `Bloom`
        Logs bloom of all the logs included in all the transactions of the
        block.
    """

    block_gas_used: Uint = Uint(0)
    transactions_trie: Trie[Bytes, Optional[Transaction]] = field(
        default_factory=lambda: Trie(secured=False, default=None)
    )
    receipts_trie: Trie[Bytes, Optional[Receipt]] = field(
        default_factory=lambda: Trie(secured=False, default=None)
    )
    receipt_keys: Tuple[Bytes, ...] = field(default_factory=tuple)
    block_logs: Tuple[Log, ...] = field(default_factory=tuple)


@final
@dataclass
class TransactionEnvironment:
    """
    Items that are used while processing a transaction.
    """

    origin: Address
    gas_price: Uint
    gas: Uint
    state: TransactionState
    index_in_block: Uint
    tx_hash: Optional[Hash32]


@final
@dataclass
class TransactionResult:
    """
    Outcome of executing a transaction.

    Carry what the block accumulators and the receipt do not preserve:
    the return data of the transaction's top-level frame, the gas it
    consumed before refunds, and the error it halted with.
    """

    return_data: Bytes
    """The output of the transaction's top-level frame."""

    gas_used: Uint
    """Gas charged to the sender, after refunds."""

    gas_used_before_refund: Uint
    """Gas the transaction consumed before refunds were applied."""

    error: Optional[EthereumException]
    """The error the transaction halted with, if any."""


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
    value: U256
    data: Bytes
    code_address: Optional[Address]
    code: Bytes
    depth: Uint
    should_transfer_value: bool
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
    valid_jump_destinations: Set[Uint]
    logs: Tuple[Log, ...]
    refund_counter: int
    running: bool
    message: Message
    output: Bytes
    accounts_to_delete: Set[Address]
    touched_accounts: Set[Address]
    error: Optional[EthereumException]


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
    evm.logs += child_evm.logs
    evm.refund_counter += child_evm.refund_counter
    evm.accounts_to_delete.update(child_evm.accounts_to_delete)
    evm.touched_accounts.update(child_evm.touched_accounts)
    if account_exists_and_is_empty(
        evm.message.tx_env.state, child_evm.message.current_target
    ):
        evm.touched_accounts.add(child_evm.message.current_target)


def incorporate_child_on_error(evm: Evm, child_evm: Evm) -> None:
    """
    Incorporate the state of an unsuccessful `child_evm` into the parent `evm`.

    Parameters
    ----------
    evm :
        The parent `EVM`.
    child_evm :
        The child evm to incorporate.

    """
    # In block 2675119, the empty account at 0x3 (the RIPEMD160 precompile) was
    # cleared despite running out of gas. This is an obscure edge case that can
    # only happen to a precompile.
    # According to the general rules governing clearing of empty accounts, the
    # touch should have been reverted. Due to client bugs, this event went
    # unnoticed and 0x3 has been exempted from the rule that touches are
    # reverted in order to preserve this historical behaviour.
    if RIPEMD160_ADDRESS in child_evm.touched_accounts:
        evm.touched_accounts.add(RIPEMD160_ADDRESS)
    if child_evm.message.current_target == RIPEMD160_ADDRESS:
        if account_exists_and_is_empty(
            evm.message.tx_env.state, child_evm.message.current_target
        ):
            evm.touched_accounts.add(RIPEMD160_ADDRESS)
    evm.gas_left += child_evm.gas_left
