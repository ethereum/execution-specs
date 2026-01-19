"""Utilities for working with Python type annotations."""

from typing import Any, get_args


def unwrap_annotation(hint: Any) -> Any:
    """
    Recursively unwrap Annotated and Union types to find the actual type.

    This function is useful for introspecting complex type annotations like:
    - `Annotated[int, ...]` -> `int`
    - `int | None` -> `int`
    - `Annotated[int, ...] | None` -> `int`

    Args:
        hint: Type annotation to unwrap

    Returns:
        The unwrapped base type

    """
    type_args = get_args(hint)
    if not type_args:
        # Base case: simple type with no parameters
        return hint

    # For Union types (including Optional), find the first non-None type
    for arg in type_args:
        if arg is not type(None):
            # Recursively unwrap (handles nested Annotated/Union)
            return unwrap_annotation(arg)

    # All args were None (shouldn't happen in practice)
    return hint
