"""
Optimized Implementations (Frontier)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

..contents:: Table of Contents
    :backlinks: none
    :local:
"""

import ethereum.frontier.state as normal_state
import ethereum_optimized.frontier.state_db as optimized_state_db

optimized_state_db_patches = {
    "State": optimized_state_db.State,
    "get_account": optimized_state_db.get_account,
    "get_account_optional": optimized_state_db.get_account_optional,
    "set_account": optimized_state_db.set_account,
    "destroy_account": optimized_state_db.destroy_account,
    "get_storage": optimized_state_db.get_storage,
    "set_storage": optimized_state_db.set_storage,
    "state_root": optimized_state_db.state_root,
    "storage_root": optimized_state_db.storage_root,
    "begin_transaction": optimized_state_db.begin_transaction,
    "rollback_transaction": optimized_state_db.rollback_transaction,
    "commit_transaction": optimized_state_db.commit_transaction,
    "close_state": optimized_state_db.close_state,
}


def monkey_patch_optimized_state_db() -> None:
    """
    Replace the state interface with one that supports high performance
    updates and storing state in a database.

    This function must be called before the state interface is imported
    anywhere.
    """
    for (name, value) in optimized_state_db_patches.items():
        setattr(normal_state, name, value)
