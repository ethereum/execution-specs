"""
Optimized Implementations (Homestead)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. contents:: Table of Contents
    :backlinks: none
    :local:
"""

from typing import Optional


def monkey_patch_optimized_state_db(state_path: Optional[str]) -> None:
    """
    Replace the state interface with one that supports high performance
    updates and storing state in a database.

    This function must be called before the state interface is imported
    anywhere.
    """
    import ethereum.homestead.state as slow_state

    from . import state_db as fast_state

    optimized_state_db_patches = {
        "State": fast_state.State,
        "get_account_optional": fast_state.get_account_optional,
        "set_account": fast_state.set_account,
        "destroy_storage": fast_state.destroy_storage,
        "get_storage": fast_state.get_storage,
        "get_storage_original": fast_state.get_storage_original,
        "set_storage": fast_state.set_storage,
        "state_root": fast_state.state_root,
        "storage_root": fast_state.storage_root,
        "begin_transaction": fast_state.begin_transaction,
        "rollback_transaction": fast_state.rollback_transaction,
        "commit_transaction": fast_state.commit_transaction,
        "close_state": fast_state.close_state,
    }

    for (name, value) in optimized_state_db_patches.items():
        setattr(slow_state, name, value)

    if state_path is not None:
        fast_state.State.default_path = state_path


def monkey_patch_optimized_spec() -> None:
    """
    Replace the ethash implementation with one that supports higher
    performance.

    This function must be called before the spec interface is imported
    anywhere.
    """
    import ethereum.homestead.fork as slow_spec

    from . import fork as fast_spec

    slow_spec.validate_proof_of_work = fast_spec.validate_proof_of_work


def monkey_patch(state_path: Optional[str]) -> None:
    """
    Apply all monkey patches to swap in high performance implementations.

    This function must be called before any of the ethereum modules are
    imported anywhere.
    """
    monkey_patch_optimized_state_db(state_path)
    monkey_patch_optimized_spec()
