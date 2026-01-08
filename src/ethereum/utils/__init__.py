"""
Utility functions used in this specification.

This package contains utility modules for common operations:

- `address`: Address validation, conversion, and checksumming utilities
- `byte`: Byte string padding and manipulation
- `hexadecimal`: Hex string parsing and conversion
- `numeric`: Numeric operations and conversions
- `validation`: Data validation utilities for Ethereum types
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
