"""
Execution witness modifier functions for invalid test cases.

This module provides modifier functions that can be used to modify
execution witnesses for testing invalid block scenarios.
"""

from typing import Callable

from execution_testing.base_types import Bytes

from .types import ExecutionWitness


def add_code(
    code: Bytes,
) -> Callable[[ExecutionWitness], ExecutionWitness]:
    """Add a bytecode entry to the witness codes list."""

    def transform(
        witness: ExecutionWitness,
    ) -> ExecutionWitness:
        new_codes = list(witness.codes)
        new_codes.append(code)
        new_codes.sort()
        return witness.model_copy(update={"codes": new_codes})

    return transform


def remove_code(
    code: Bytes,
) -> Callable[[ExecutionWitness], ExecutionWitness]:
    """Remove a bytecode entry from the witness codes list."""

    def transform(
        witness: ExecutionWitness,
    ) -> ExecutionWitness:
        new_codes = [c for c in witness.codes if c != code]
        if len(new_codes) == len(witness.codes):
            raise ValueError(
                f"Bytecode {code.hex()} not found in witness codes to remove"
            )
        return witness.model_copy(update={"codes": new_codes})

    return transform


__all__ = [
    "add_code",
    "remove_code",
]
