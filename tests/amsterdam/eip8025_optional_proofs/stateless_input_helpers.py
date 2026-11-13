"""Helpers for tests that modify stateless input bytes."""

from typing import Any, Callable, TypeAlias

from execution_testing import Bytes, Fork
from execution_testing.specs.blockchain_stateless import spec_fork

StatelessInput: TypeAlias = Any
"""
Decoded stateless input. Each fork has its own class, which is only known
once the test has its fork.
"""

StatelessInputBytesModifier = Callable[[Bytes], Bytes]
StatelessInputUpdate = Callable[[StatelessInput], StatelessInput]


def deserialize_stateless_input(
    fork: Fork, input_bytes: Bytes
) -> StatelessInput:
    """Decode stateless input bytes with the spec of `fork`."""
    return spec_fork(fork).deserialize_stateless_input(input_bytes)


def serialize_stateless_input(
    fork: Fork, stateless_input: StatelessInput
) -> Bytes:
    """Encode a stateless input with the spec of `fork`."""
    return Bytes(spec_fork(fork).serialize_stateless_input(stateless_input))


def modify_stateless_input(
    fork: Fork,
    update: StatelessInputUpdate,
) -> StatelessInputBytesModifier:
    """
    Return a modifier that applies `update` to the decoded stateless input.

    The updated input is re-encoded as valid SSZ, so a validation failure
    comes from the updated field rather than from decoding.
    """

    def modifier(input_bytes: Bytes) -> Bytes:
        stateless_input = deserialize_stateless_input(fork, input_bytes)
        return serialize_stateless_input(fork, update(stateless_input))

    return modifier
