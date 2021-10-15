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
    from . import frontier

    frontier.monkey_patch(state_path)
