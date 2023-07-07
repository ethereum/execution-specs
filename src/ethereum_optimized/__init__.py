"""
Optimized Implementations
^^^^^^^^^^^^^^^^^^^^^^^^^

.. contents:: Table of Contents
    :backlinks: none
    :local:

Introduction
------------

This module contains alternative implementations of routines in the spec that
have been optimized for speed rather than clarity.

They can be monkey patched in during start up by calling the `monkey_patch()`
function. This must be done before those modules are imported anywhere.
"""

from importlib import import_module
from typing import Any, Optional, cast

from .fork import get_optimized_pow_patches
from .state_db import get_optimized_state_patches


def monkey_patch_optimized_state_db(
    fork_name: str, state_path: Optional[str]
) -> None:
    """
    Replace the state interface with one that supports high performance
    updates and storing state in a database.

    This function must be called before the state interface is imported
    anywhere.
    """
    slow_state = cast(Any, import_module("ethereum." + fork_name + ".state"))

    optimized_state_db_patches = get_optimized_state_patches(fork_name)

    for (name, value) in optimized_state_db_patches.items():
        setattr(slow_state, name, value)

    if state_path is not None:
        slow_state.State.default_path = state_path


def monkey_patch_optimized_spec(fork_name: str) -> None:
    """
    Replace the ethash implementation with one that supports higher
    performance.

    This function must be called before the spec interface is imported
    anywhere.
    """
    slow_spec = import_module("ethereum." + fork_name + ".fork")

    optimized_pow_patches = get_optimized_pow_patches(fork_name)

    for (name, value) in optimized_pow_patches.items():
        setattr(slow_spec, name, value)


def monkey_patch(state_path: Optional[str]) -> None:
    """
    Apply all monkey patches to the specification.
    """
    for fork_name in (
        "frontier",
        "homestead",
        "dao_fork",
        "tangerine_whistle",
        "spurious_dragon",
        "byzantium",
        "constantinople",
        "istanbul",
        "muir_glacier",
        "berlin",
        "london",
        "arrow_glacier",
        "gray_glacier",
    ):
        monkey_patch_optimized_state_db(fork_name, state_path)
        monkey_patch_optimized_spec(fork_name)

    for fork_name in (
        "paris",
        "shanghai",
    ):
        monkey_patch_optimized_state_db(fork_name, state_path)
