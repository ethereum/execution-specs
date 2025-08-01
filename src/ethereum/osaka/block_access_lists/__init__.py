"""
Block Access Lists (EIP-7928) implementation for Ethereum Osaka fork.
"""

from .builder import (
    BlockAccessListBuilder,
    add_balance_change,
    add_code_change,
    add_nonce_change,
    add_storage_read,
    add_storage_write,
    add_touched_account,
    build,
)
from .tracker import (
    StateChangeTracker,
    set_transaction_index,
    track_address_access,
    track_balance_change,
    track_code_change,
    track_nonce_change,
    track_storage_read,
    track_storage_write,
)
from .utils import (
    compute_bal_hash,
    ssz_encode_block_access_list,
    validate_bal_against_execution,
)

__all__ = [
    "BlockAccessListBuilder",
    "StateChangeTracker",
    "add_balance_change",
    "add_code_change",
    "add_nonce_change",
    "add_storage_read",
    "add_storage_write",
    "add_touched_account",
    "build",
    "compute_bal_hash",
    "set_transaction_index",
    "ssz_encode_block_access_list",
    "track_address_access",
    "track_balance_change",
    "track_code_change",
    "track_nonce_change",
    "track_storage_read",
    "track_storage_write",
    "validate_bal_against_execution",
]