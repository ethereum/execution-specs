"""
Block Access Lists (EIP-7928) implementation for Ethereum Amsterdam fork.
"""

from .builder import (
    BlockAccessListBuilder,
    add_balance_change,
    add_code_change,
    add_nonce_change,
    add_storage_read,
    add_storage_write,
    add_touched_account,
    build_block_access_list,
)
from .rlp_utils import (
    compute_block_access_list_hash,
    rlp_encode_block_access_list,
    validate_block_access_list_against_execution,
)

__all__ = [
    "BlockAccessListBuilder",
    "add_balance_change",
    "add_code_change",
    "add_nonce_change",
    "add_storage_read",
    "add_storage_write",
    "add_touched_account",
    "build_block_access_list",
    "compute_block_access_list_hash",
    "rlp_encode_block_access_list",
    "validate_block_access_list_against_execution",
]
