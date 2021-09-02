"""
Optimized Implementations
^^^^^^^^^^^^^^^^^^^^^^^^^

..contents:: Table of Contents
    :backlinks: none
    :local:

Introduction
------------

This module contains alternative implementations of routines in the spec that
have been optimized for speed rather than clarity.

They can be monkey patched in during start up by calling the `monkey_patch_X()`
functions.
"""

import ethereum.frontier.state as normal_state
import ethereum_optimized.state as optimized_state
import ethereum_optimized.trie as optimized_trie

optimized_state_patches = {
    "Trie": optimized_trie.Trie,
    "root": optimized_trie.root,
    "trie_get": optimized_trie.trie_get,
    "trie_set": optimized_trie.trie_set,
    "State": optimized_state.State,
    "set_storage": optimized_state.set_storage,
    "get_storage": optimized_state.get_storage,
}


def monkey_patch_optimized_state() -> None:
    """
    Replace the state interface with one that supports high performance
    updates.

    This function must be called before the state interface imported anywhere.
    """
    for (name, value) in optimized_state_patches.items():
        setattr(normal_state, name, value)
