"""Block Access List (BAL) for t8n tool communication and fixtures."""

from functools import cached_property
from typing import Any, List

import ethereum_rlp as eth_rlp
from pydantic import Field

from execution_testing.base_types import Bytes, EthereumTestRootModel
from execution_testing.base_types.serialization import (
    to_serializable_element,
)

from .account_changes import BalAccountChange
from .exceptions import BlockAccessListValidationError


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

    def validate_structure(self) -> None:
        """
        Validate BAL structure follows EIP-7928 requirements.

        Checks:
        - Addresses are in lexicographic (ascending) order
        - Transaction indices are sorted and unique within each change list
        - Storage slots are in ascending order
        - Storage reads are in ascending order

        Raises:
            BlockAccessListValidationError: If validation fails
        """
        # Check address ordering (ascending)
        for i in range(1, len(self.root)):
            if self.root[i - 1].address >= self.root[i].address:
                raise BlockAccessListValidationError(
                    f"BAL addresses are not in lexicographic order: "
                    f"{self.root[i - 1].address} >= {self.root[i].address}"
                )

        # Check transaction index ordering and uniqueness within accounts
        for account in self.root:
            changes_to_check: List[tuple[str, List[Any]]] = [
                ("nonce_changes", account.nonce_changes),
                ("balance_changes", account.balance_changes),
                ("code_changes", account.code_changes),
            ]

            for field_name, change_list in changes_to_check:
                if not change_list:
                    continue

                tx_indices = [c.tx_index for c in change_list]

                # Check both ordering and duplicates
                if tx_indices != sorted(tx_indices):
                    raise BlockAccessListValidationError(
                        f"Transaction indices not in ascending order in {field_name} of account "
                        f"{account.address}. Got: {tx_indices}, Expected: {sorted(tx_indices)}"
                    )

                if len(tx_indices) != len(set(tx_indices)):
                    duplicates = sorted(
                        {
                            idx
                            for idx in tx_indices
                            if tx_indices.count(idx) > 1
                        }
                    )
                    raise BlockAccessListValidationError(
                        f"Duplicate transaction indices in {field_name} of account "
                        f"{account.address}. Duplicates: {duplicates}"
                    )

            # Check storage slot ordering
            for i in range(1, len(account.storage_changes)):
                if (
                    account.storage_changes[i - 1].slot
                    >= account.storage_changes[i].slot
                ):
                    raise BlockAccessListValidationError(
                        f"Storage slots not in ascending order in account "
                        f"{account.address}: {account.storage_changes[i - 1].slot} >= "
                        f"{account.storage_changes[i].slot}"
                    )

            # Check transaction index ordering and uniqueness within storage slots
            for storage_slot in account.storage_changes:
                if not storage_slot.slot_changes:
                    continue

                tx_indices = [c.tx_index for c in storage_slot.slot_changes]

                # Check both ordering and duplicates
                if tx_indices != sorted(tx_indices):
                    raise BlockAccessListValidationError(
                        f"Transaction indices not in ascending order in storage slot "
                        f"{storage_slot.slot} of account {account.address}. "
                        f"Got: {tx_indices}, Expected: {sorted(tx_indices)}"
                    )

                if len(tx_indices) != len(set(tx_indices)):
                    duplicates = sorted(
                        {
                            idx
                            for idx in tx_indices
                            if tx_indices.count(idx) > 1
                        }
                    )
                    raise BlockAccessListValidationError(
                        f"Duplicate transaction indices in storage slot "
                        f"{storage_slot.slot} of account {account.address}. "
                        f"Duplicates: {duplicates}"
                    )

            # Check storage reads ordering
            for i in range(1, len(account.storage_reads)):
                if account.storage_reads[i - 1] >= account.storage_reads[i]:
                    raise BlockAccessListValidationError(
                        f"Storage reads not in ascending order in account "
                        f"{account.address}: {account.storage_reads[i - 1]} >= "
                        f"{account.storage_reads[i]}"
                    )
