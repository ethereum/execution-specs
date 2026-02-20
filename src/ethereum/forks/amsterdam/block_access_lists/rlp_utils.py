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

from ethereum_rlp import rlp

from ethereum.crypto.hash import Hash32, keccak256

from .rlp_types import BlockAccessList


def compute_block_access_list_hash(
    block_access_list: BlockAccessList,
) -> Hash32:
    """
    Compute the hash of a Block Access List.

    The Block Access List is RLP-encoded and then hashed with keccak256.
    """
    return keccak256(rlp.encode(block_access_list))
