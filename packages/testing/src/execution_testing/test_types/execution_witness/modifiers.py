"""
Execution witness modifier functions for invalid test cases.

This module provides modifier functions that can be used to modify
execution witnesses for testing invalid block scenarios.
"""

from typing import Callable, Tuple

from execution_testing.base_types import Bytes

from .types import ExecutionWitness

PublicKeyModifier = Callable[[Tuple[Bytes, ...]], Tuple[Bytes, ...]]


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


def remove_code_at(
    index: int,
) -> Callable[[ExecutionWitness], ExecutionWitness]:
    """Remove the bytecode entry at `index` from the witness codes list."""

    def transform(
        witness: ExecutionWitness,
    ) -> ExecutionWitness:
        new_codes = list(witness.codes)
        try:
            new_codes.pop(index)
        except IndexError as exc:
            raise IndexError(
                f"Code index {index} out of range for witness codes"
            ) from exc
        return witness.model_copy(update={"codes": new_codes})

    return transform


def reverse_codes() -> Callable[[ExecutionWitness], ExecutionWitness]:
    """Reverse the order of witness codes."""

    def transform(
        witness: ExecutionWitness,
    ) -> ExecutionWitness:
        return witness.model_copy(
            update={"codes": list(reversed(witness.codes))}
        )

    return transform


def reverse_state_nodes() -> Callable[[ExecutionWitness], ExecutionWitness]:
    """Reverse the order of witness state nodes."""

    def transform(
        witness: ExecutionWitness,
    ) -> ExecutionWitness:
        return witness.model_copy(
            update={"state": list(reversed(witness.state))}
        )

    return transform


def clear_headers() -> Callable[[ExecutionWitness], ExecutionWitness]:
    """Remove all header entries from the witness."""

    def transform(
        witness: ExecutionWitness,
    ) -> ExecutionWitness:
        return witness.model_copy(update={"headers": []})

    return transform


def remove_header_at(
    index: int,
) -> Callable[[ExecutionWitness], ExecutionWitness]:
    """Remove the header entry at `index` from the witness."""

    def transform(
        witness: ExecutionWitness,
    ) -> ExecutionWitness:
        new_headers = list(witness.headers)
        try:
            new_headers.pop(index)
        except IndexError as exc:
            raise IndexError(
                f"Header index {index} out of range for witness headers"
            ) from exc
        return witness.model_copy(update={"headers": new_headers})

    return transform


def prepend_header(
    header: Bytes,
) -> Callable[[ExecutionWitness], ExecutionWitness]:
    """Prepend a header entry to the witness."""

    def transform(
        witness: ExecutionWitness,
    ) -> ExecutionWitness:
        return witness.model_copy(
            update={"headers": [header, *witness.headers]}
        )

    return transform


def reverse_headers() -> Callable[[ExecutionWitness], ExecutionWitness]:
    """Reverse the order of witness headers."""

    def transform(
        witness: ExecutionWitness,
    ) -> ExecutionWitness:
        return witness.model_copy(
            update={"headers": list(reversed(witness.headers))}
        )

    return transform


def replace_header_at(
    index: int,
    header: Bytes,
) -> Callable[[ExecutionWitness], ExecutionWitness]:
    """Replace the header entry at `index` with `header`."""

    def transform(
        witness: ExecutionWitness,
    ) -> ExecutionWitness:
        new_headers = list(witness.headers)
        try:
            new_headers[index] = header
        except IndexError as exc:
            raise IndexError(
                f"Header index {index} out of range for witness headers"
            ) from exc
        return witness.model_copy(update={"headers": new_headers})

    return transform


def replace_public_key_at(
    index: int,
    public_key: Bytes,
) -> PublicKeyModifier:
    """Replace the transaction public key at `index`."""

    def transform(
        public_keys: Tuple[Bytes, ...],
    ) -> Tuple[Bytes, ...]:
        new_public_keys = list(public_keys)
        try:
            new_public_keys[index] = public_key
        except IndexError as exc:
            raise IndexError(
                f"Public key index {index} out of range for stateless input"
            ) from exc
        return tuple(new_public_keys)

    return transform


__all__ = [
    "add_state_node",
    "add_code",
    "clear_headers",
    "PublicKeyModifier",
    "remove_state_node",
    "remove_code",
    "remove_code_at",
    "reverse_codes",
    "reverse_state_nodes",
    "prepend_header",
    "remove_header_at",
    "reverse_headers",
    "replace_header_at",
    "replace_public_key_at",
]
