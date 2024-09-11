"""
Utility functions used in this specification.
"""

from dataclasses import fields
from typing import Any


def has_field(class_: Any, name: str) -> bool:
    """
    Returns `True` if `class_` has a field with the given `name`.
    """
    try:
        all_fields = fields(class_)
    except TypeError:
        return False

    return any(x.name == name for x in all_fields)
