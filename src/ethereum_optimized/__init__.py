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


def monkey_patch() -> None:
    """
    Apply all monkey patches to the specification.
    """
    from . import frontier

    frontier.monkey_patch()
