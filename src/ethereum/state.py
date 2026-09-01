"""
Shared state model and the `PreState` protocol used by the state
transition function.

The `PreState` protocol specifies the operations that any
pre-execution state provider must support, allowing multiple backing
implementations (in-memory `dict`, on-disk database, witness, etc.).
This module is commitment-agnostic: it defines what state *is*, not
how it is committed to. The Merkle-Patricia-Trie-backed in-memory
implementation lives in [`ethereum.state_mpt`].

There is a distinction between an account that does not exist and
`EMPTY_ACCOUNT`.

[`ethereum.state_mpt`]: ref:ethereum.state_mpt
"""

from dataclasses import dataclass, field
from typing import (
    Dict,
    Optional,
    Protocol,
    Set,
    final,
)

from ethereum_types.bytes import Bytes, Bytes20, Bytes32
from ethereum_types.frozen import slotted_freezable
from ethereum_types.numeric import U256, Uint

from ethereum.crypto.hash import Hash32, keccak256

Address = Bytes20
Root = Hash32

EMPTY_CODE_HASH = keccak256(b"")


@final
@slotted_freezable
@dataclass
class Account:
    """
    State associated with an address.
    """

    nonce: Uint
    balance: U256
    code_hash: Hash32


EMPTY_ACCOUNT = Account(
    nonce=Uint(0),
    balance=U256(0),
    code_hash=EMPTY_CODE_HASH,
)


@final
@dataclass
class BlockDiff:
    """
    State changes produced by executing a block.
    """

    account_changes: Dict[Address, Optional[Account]] = field(
        default_factory=dict
    )
    """Per-address account diffs produced by execution."""

    storage_changes: Dict[Address, Dict[Bytes32, U256]] = field(
        default_factory=dict
    )
    """Per-address storage diffs produced by execution."""

    code_changes: Dict[Hash32, Bytes] = field(default_factory=dict)
    """New bytecodes (keyed by code hash) introduced by execution."""

    storage_clears: Set[Address] = field(default_factory=set)
    """
    Addresses whose pre-existing storage was wiped during block
    execution (via a pre-EIP-6780 `SELFDESTRUCT`). Their storage
    tries are dropped before [`storage_changes`][sc] is applied, so any
    post-wipe writes begin from empty storage.

    [sc]: ref:ethereum.state.BlockDiff.storage_changes
    """


class PreState(Protocol):
    """
    Protocol for providing pre-execution state.

    Specify the operations that any pre-state provider (dict, database,
    witness, etc.) must support for the EELS state transition.
    """

    def get_account_optional(self, address: Address) -> Optional[Account]:
        """
        Get the account at an address.

        Return ``None`` if there is no account at the address.
        """
        ...

    def get_storage(self, address: Address, key: Bytes32) -> U256:
        """
        Get a storage value.

        Return ``U256(0)`` if the key has not been set.
        """
        ...

    def get_code(self, code_hash: Hash32) -> Bytes:
        """
        Get the bytecode for a given code hash.

        Return ``b""`` for ``EMPTY_CODE_HASH``.
        """
        ...

    def compute_state_root(self, block_diff: BlockDiff) -> Root:
        """
        Compute the state root after applying `block_diff` to the
        pre-state. The pre-state itself is not modified.

        The diff carries bytecode deployed during the block in
        ``code_changes``, keyed by code hash. Commitments over code
        hashes alone can ignore it; a commitment over code contents
        resolves each account's bytecode through its ``code_hash``,
        joining ``account_changes`` to ``code_changes``, because the
        new bytecode is not yet in the provider's code store when the
        root is computed.

        Return the new state root.
        """
        ...
