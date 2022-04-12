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
function.
"""

from typing import Optional


def monkey_patch(state_path: Optional[str]) -> None:
    """
    Apply all monkey patches to the specification.
    """
    from . import (
        byzantium,
        constantinople,
        dao_fork,
        frontier,
        homestead,
        spurious_dragon,
        tangerine_whistle,
    )

    frontier.monkey_patch(state_path)
    homestead.monkey_patch(state_path)
    dao_fork.monkey_patch(state_path)
    tangerine_whistle.monkey_patch(state_path)
    spurious_dragon.monkey_patch(state_path)
    byzantium.monkey_patch(state_path)
    constantinople.monkey_patch(state_path)
