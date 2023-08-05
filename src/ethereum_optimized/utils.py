"""
Optimized Implementation Utilities
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. contents:: Table of Contents
    :backlinks: none
    :local:

Introduction
------------

Utility functions for optimized implementations.
"""

from typing import Any, Dict


def add_item(patches: Dict[str, Any]) -> Any:
    """
    Decorator to add a function to a patches dictionary.
    """

    def inner(f: Any) -> Any:
        patches[f.__name__] = f
        return f

    return inner
