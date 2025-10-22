"""Block Access List (BAL) for t8n tool communication and fixtures."""

from functools import cached_property
from typing import Any, List

import ethereum_rlp as eth_rlp
from pydantic import Field

from ethereum_test_base_types import Bytes, EthereumTestRootModel
from ethereum_test_base_types.serialization import to_serializable_element

from .account_changes import BalAccountChange


class BlockAccessList(EthereumTestRootModel[List[BalAccountChange]]):
    """
    Block Access List for t8n tool communication and fixtures.

    This model represents the BAL exactly as defined in EIP-7928
    - it is itself a list of account changes (root model), not a container.

    Used for:
    - Communication with t8n tools
    - Fixture generation
    - RLP encoding for hash verification

    Example:
        bal = BlockAccessList([
            BalAccountChange(address=alice, nonce_changes=[...]),
            BalAccountChange(address=bob, balance_changes=[...])
        ])

    """

    root: List[BalAccountChange] = Field(default_factory=list)

    def to_list(self) -> List[Any]:
        """Return the list for RLP encoding per EIP-7928."""
        return to_serializable_element(self.root)

    @cached_property
    def rlp(self) -> Bytes:
        """Return the RLP encoded block access list for hash verification."""
        return Bytes(eth_rlp.encode(self.to_list()))

    @cached_property
    def rlp_hash(self) -> Bytes:
        """Return the hash of the RLP encoded block access list."""
        return self.rlp.keccak256()
