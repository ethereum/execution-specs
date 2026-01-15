"""
Utilities for working with Block Access Lists using RLP encoding,
as specified in EIP-7928.

This module provides:

- RLP encoding functions for all Block Access List types
- Hash computation using [`keccak256`]
- Validation logic to ensure structural correctness

The encoding follows the RLP specification used throughout Ethereum.

[`keccak256`]: ref:ethereum.crypto.hash.keccak256
"""

from typing import cast

from ethereum_rlp import Extended, rlp
from ethereum_types.bytes import Bytes
from ethereum_types.numeric import Uint

from ethereum.crypto.hash import Hash32, keccak256

from .rlp_types import BlockAccessList


def compute_block_access_list_hash(
    block_access_list: BlockAccessList,
) -> Hash32:
    """
    Compute the hash of a Block Access List.

    The Block Access List is RLP-encoded and then hashed with keccak256.

    Parameters
    ----------
    block_access_list :
        The Block Access List to hash.

    Returns
    -------
    hash :
        The keccak256 hash of the RLP-encoded Block Access List.

    """
    block_access_list_bytes = rlp_encode_block_access_list(block_access_list)
    return keccak256(block_access_list_bytes)


def rlp_encode_block_access_list(block_access_list: BlockAccessList) -> Bytes:
    """
    Encode a [`BlockAccessList`] to RLP bytes.

    This is the top-level encoding function that produces the final RLP
    representation of a block's access list, following the updated EIP-7928
    specification.

    Parameters
    ----------
    block_access_list :
        The block access list to encode.

    Returns
    -------
    encoded :
        The complete RLP-encoded block access list.

    [`BlockAccessList`]: ref:ethereum.forks.amsterdam.block_access_lists.rlp_types.BlockAccessList  # noqa: E501

    """
    # Encode as a list of AccountChanges directly (not wrapped)
    account_changes_list = []
    for account in block_access_list:
        # Each account is encoded as:
        # [address, storage_changes, storage_reads,
        # balance_changes, nonce_changes, code_changes]
        storage_changes_list = [
            [
                slot_changes.slot,
                [
                    [Uint(c.block_access_index), c.new_value]
                    for c in slot_changes.changes
                ],
            ]
            for slot_changes in account.storage_changes
        ]

        storage_reads_list = list(account.storage_reads)

        balance_changes_list = [
            [Uint(bc.block_access_index), Uint(bc.post_balance)]
            for bc in account.balance_changes
        ]

        nonce_changes_list = [
            [Uint(nc.block_access_index), Uint(nc.new_nonce)]
            for nc in account.nonce_changes
        ]

        code_changes_list = [
            [Uint(cc.block_access_index), cc.new_code]
            for cc in account.code_changes
        ]

        account_changes_list.append(
            [
                account.address,
                storage_changes_list,
                storage_reads_list,
                balance_changes_list,
                nonce_changes_list,
                code_changes_list,
            ]
        )

    encoded = rlp.encode(cast(Extended, account_changes_list))
    return Bytes(encoded)
