"""Block Access List (BAL) for t8n tool communication and fixtures."""

from functools import cached_property
from typing import Any, Callable, List, Sequence, Union

import ethereum_rlp as eth_rlp
from ethereum_rlp import Simple
from pydantic import Field

from execution_testing.base_types import (
    Address,
    Bytes,
    EthereumTestRootModel,
    ZeroPaddedHexNumber,
)
from execution_testing.base_types.serialization import (
    to_serializable_element,
)

from .account_changes import (
    BalAccountChange,
    BalBalanceChange,
    BalCodeChange,
    BalNonceChange,
    BalStorageChange,
    BalStorageSlot,
)
from .exceptions import BlockAccessListValidationError


def _bytes_from_rlp(data: Simple) -> bytes:
    """Extract bytes from an RLP-decoded Simple value."""
    assert isinstance(data, bytes), f"expected bytes, got {type(data)}"
    return data


def _int_from_rlp(data: Simple) -> int:
    """Decode an RLP Simple value to int."""
    raw = _bytes_from_rlp(data)
    if len(raw) == 0:
        return 0
    return int.from_bytes(raw, "big")


def _seq_from_rlp(data: Simple) -> Sequence[Simple]:
    """Extract a sequence from an RLP-decoded Simple value."""
    assert not isinstance(data, bytes), "expected sequence, got bytes"
    return data


IndexedChange = Union[
    BalBalanceChange, BalCodeChange, BalNonceChange, BalStorageChange
]


def _hex_from_rlp(data: Simple) -> ZeroPaddedHexNumber:
    """Decode an RLP Simple value to ZeroPaddedHexNumber."""
    return ZeroPaddedHexNumber(_int_from_rlp(data))


def _decode_indexed_changes(
    rlp_list: Simple,
    cls: type[IndexedChange],
    value_field: str,
    value_fn: Callable[[Simple], Any] = _hex_from_rlp,
) -> list[IndexedChange]:
    """Decode a list of [block_access_index, value] RLP pairs."""
    result: list[IndexedChange] = []
    for item in _seq_from_rlp(rlp_list):
        idx, val = _seq_from_rlp(item)
        result.append(
            cls(
                block_access_index=_hex_from_rlp(idx),
                **{value_field: value_fn(val)},
            )
        )
    return result


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

    @classmethod
    def from_rlp(cls, data: Bytes) -> "BlockAccessList":
        """
        Decode an RLP-encoded block access list into a BlockAccessList.

        The RLP structure per EIP-7928 is:
        [
          [address, storage_changes, storage_reads,
           balance_changes, nonce_changes, code_changes],
          ...
        ]
        """
        decoded = _seq_from_rlp(eth_rlp.decode(data))
        accounts = []
        for account_rlp in decoded:
            fields = _seq_from_rlp(account_rlp)

            storage_changes = []
            for slot_entry in _seq_from_rlp(fields[1]):
                slot_fields = _seq_from_rlp(slot_entry)
                storage_changes.append(
                    BalStorageSlot(
                        slot=_hex_from_rlp(slot_fields[0]),
                        slot_changes=_decode_indexed_changes(
                            slot_fields[1],
                            BalStorageChange,
                            "post_value",
                        ),
                    )
                )

            accounts.append(
                BalAccountChange(
                    address=Address(_bytes_from_rlp(fields[0])),
                    storage_changes=storage_changes,
                    storage_reads=[
                        _hex_from_rlp(sr) for sr in _seq_from_rlp(fields[2])
                    ],
                    balance_changes=_decode_indexed_changes(
                        fields[3], BalBalanceChange, "post_balance"
                    ),
                    nonce_changes=_decode_indexed_changes(
                        fields[4], BalNonceChange, "post_nonce"
                    ),
                    code_changes=_decode_indexed_changes(
                        fields[5],
                        BalCodeChange,
                        "new_code",
                        value_fn=lambda v: Bytes(_bytes_from_rlp(v)),
                    ),
                )
            )

        return cls(root=accounts)

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

                bal_indices = [c.block_access_index for c in change_list]

                # Check both ordering and duplicates
                if bal_indices != sorted(bal_indices):
                    raise BlockAccessListValidationError(
                        f"Block access indices not in ascending order in "
                        f"{field_name} of account {account.address}. Got: "
                        f"{bal_indices}, Expected: {sorted(bal_indices)}"
                    )

                if len(bal_indices) != len(set(bal_indices)):
                    duplicates = sorted(
                        {
                            idx
                            for idx in bal_indices
                            if bal_indices.count(idx) > 1
                        }
                    )
                    raise BlockAccessListValidationError(
                        f"Duplicate transaction indices in {field_name} of "
                        f"account {account.address}. Duplicates: {duplicates}"
                    )

            # Check storage slot ordering
            for i in range(1, len(account.storage_changes)):
                if (
                    account.storage_changes[i - 1].slot
                    >= account.storage_changes[i].slot
                ):
                    raise BlockAccessListValidationError(
                        f"Storage slots not in ascending order in account "
                        f"{account.address}: "
                        f"{account.storage_changes[i - 1].slot} >= "
                        f"{account.storage_changes[i].slot}"
                    )

            # Check bal index ordering and uniqueness within storage slots
            for storage_slot in account.storage_changes:
                if not storage_slot.slot_changes:
                    continue

                bal_indices = [
                    c.block_access_index for c in storage_slot.slot_changes
                ]

                # Check both ordering and duplicates
                if bal_indices != sorted(bal_indices):
                    raise BlockAccessListValidationError(
                        f"Transaction indices not in ascending order in "
                        f"storage slot {storage_slot.slot} of account "
                        f"{account.address}. Got: {bal_indices}, Expected: "
                        f"{sorted(bal_indices)}"
                    )

                if len(bal_indices) != len(set(bal_indices)):
                    duplicates = sorted(
                        {
                            idx
                            for idx in bal_indices
                            if bal_indices.count(idx) > 1
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
                        f"{account.address}: "
                        f"{account.storage_reads[i - 1]} >= "
                        f"{account.storage_reads[i]}"
                    )
