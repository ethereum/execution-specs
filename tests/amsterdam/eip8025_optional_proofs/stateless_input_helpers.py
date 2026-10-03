"""Helpers for tests that modify stateless input bytes."""

from typing import Callable

from execution_testing import Bytes

from ethereum.forks.amsterdam.stateless import StatelessInput
from ethereum.forks.amsterdam.stateless_guest import (
    deserialize_stateless_input,
)
from ethereum.forks.amsterdam.stateless_host import serialize_stateless_input

StatelessInputBytesModifier = Callable[[Bytes], Bytes]
StatelessInputUpdate = Callable[[StatelessInput], StatelessInput]


def modify_stateless_input(
    update: StatelessInputUpdate,
) -> StatelessInputBytesModifier:
    """
    Return a modifier that applies `update` to the decoded stateless input.

    The updated input is re-encoded as valid SSZ, so a validation failure
    comes from the updated field rather than from decoding.
    """

    def modifier(input_bytes: Bytes) -> Bytes:
        stateless_input = deserialize_stateless_input(input_bytes)
        return Bytes(serialize_stateless_input(update(stateless_input)))

    return modifier
