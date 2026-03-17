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


def add_state_node(
    node: Bytes,
) -> Callable[[ExecutionWitness], ExecutionWitness]:
    """Add an encoded trie node entry to the witness state list."""

    def transform(
        witness: ExecutionWitness,
    ) -> ExecutionWitness:
        new_state = list(witness.state)
        new_state.append(node)
        new_state.sort()
        return witness.model_copy(update={"state": new_state})

    return transform


def remove_state_node(
    node: Bytes,
) -> Callable[[ExecutionWitness], ExecutionWitness]:
    """Remove an encoded trie node entry from the witness state list."""

    def transform(
        witness: ExecutionWitness,
    ) -> ExecutionWitness:
        new_state = [entry for entry in witness.state if entry != node]
        if len(new_state) == len(witness.state):
            raise ValueError(
                f"Trie node {node.hex()} not found in witness state to remove"
            )
        return witness.model_copy(update={"state": new_state})

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
    "add_state_node",
    "add_code",
    "remove_state_node",
    "remove_code",
]
