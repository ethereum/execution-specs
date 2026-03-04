"""
Shared state types and the `PreState` protocol used by the state transition
function.

The `PreState` protocol specifies the operations that any pre-execution state
provider must support, allowing multiple backing implementations (in-memory
`dict`, on-disk database, witness, etc.).
"""

from dataclasses import dataclass
from typing import Dict, List, Optional, Protocol, Tuple

from ethereum_rlp import Extended
from ethereum_types.bytes import Bytes, Bytes20, Bytes32
from ethereum_types.frozen import slotted_freezable
from ethereum_types.numeric import U256, Uint

from ethereum.crypto.hash import Hash32, keccak256

Address = Bytes20
Root = Hash32

EMPTY_CODE_HASH = keccak256(b"")


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


@slotted_freezable
@dataclass
class LeafNode:
    """Leaf node in the Merkle Trie."""

    rest_of_key: Bytes
    value: Extended


@slotted_freezable
@dataclass
class ExtensionNode:
    """Extension node in the Merkle Trie."""

    key_segment: Bytes
    subnode: Extended


BranchSubnodes = Tuple[
    Extended,
    Extended,
    Extended,
    Extended,
    Extended,
    Extended,
    Extended,
    Extended,
    Extended,
    Extended,
    Extended,
    Extended,
    Extended,
    Extended,
    Extended,
    Extended,
]


@slotted_freezable
@dataclass
class BranchNode:
    """Branch node in the Merkle Trie."""

    subnodes: BranchSubnodes
    value: Extended


InternalNode = LeafNode | ExtensionNode | BranchNode


@dataclass
class BlockDiff:
    """
    State changes produced by executing a block.
    """

    account_changes: Dict[Address, Optional[Account]]
    """Per-address account diffs produced by execution."""

    storage_changes: Dict[Address, Dict[Bytes32, U256]]
    """Per-address storage diffs produced by execution."""

    code_changes: Dict[Hash32, Bytes]
    """New bytecodes (keyed by code hash) introduced by execution."""


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

    def account_has_storage(self, address: Address) -> bool:
        """
        Check whether an account has any storage.

        Only needed for EIP-7610.
        """
        ...

    def compute_state_root_and_trie_changes(
        self,
        account_changes: Dict[Address, Optional[Account]],
        storage_changes: Dict[Address, Dict[Bytes32, U256]],
    ) -> Tuple[Root, List[InternalNode]]:
        """
        Compute the state root after applying changes to the pre-state.

        Return the new state root together with the internal trie nodes
        that were created or modified.
        """
        ...
