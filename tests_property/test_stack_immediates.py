"""
Properties of the [EIP-8024] immediates of `DUPN`, `SWAPN` and `EXCHANGE`.

The framework encodes stack indices into an immediate byte and the spec
decodes one, each written from the EIP apart from the other. Every byte
has one of two fates, so the properties run over all 256 of them.

[EIP-8024]: https://eips.ethereum.org/EIPS/eip-8024
"""

from types import ModuleType
from typing import Dict, Tuple

import pytest
from ethereum_types.numeric import U8
from execution_testing import Op

from ethereum_spec_tools.forks import Hardfork

from .forks import requires

pytestmark = requires(lambda fork: fork.is_eip_enabled(8024))

# EIP-8024: an immediate is never one of these, so that skipping it during
# jump destination analysis cannot hide or invent a `JUMPDEST`.
JUMPDEST_ANALYSIS_OPCODES = {
    opcode.int()
    for opcode in [
        Op.JUMPDEST,
        *(getattr(Op, f"PUSH{n}") for n in range(1, 33)),
    ]
}


@pytest.fixture(scope="session")
def stack(spec: Hardfork) -> ModuleType:
    """Return the stack module of the fork under test."""
    return spec.module("vm.stack")


def single_immediates() -> Dict[int, int]:
    """Return the framework's immediate for every index it encodes."""
    immediates = {}
    for index in range(256):
        try:
            immediates[bytes(Op.DUPN[index])[1]] = index
        except ValueError:
            continue
    return immediates


def pair_immediates() -> Dict[int, Tuple[int, int]]:
    """Return the framework's immediate for every index pair it encodes."""
    immediates = {}
    for first in range(32):
        for second in range(32):
            try:
                immediate = bytes(Op.EXCHANGE[first, second])[1]
            except ValueError:
                continue
            immediates[immediate] = (first, second)
    return immediates


def test_single_immediates_decode_to_the_encoded_index(
    spec: Hardfork, stack: ModuleType
) -> None:
    """
    `DUPN` and `SWAPN` decode every immediate the framework encodes back
    to its index, and reject every other byte.
    """
    encoded = single_immediates()
    invalid = spec.module("vm.exceptions").InvalidParameter
    for byte in range(256):
        if byte in encoded:
            assert stack.decode_single(U8(byte)) == encoded[byte]
        else:
            with pytest.raises(invalid):
                stack.decode_single(U8(byte))


def test_pair_immediates_decode_to_the_encoded_indices(
    spec: Hardfork, stack: ModuleType
) -> None:
    """
    `EXCHANGE` decodes every immediate the framework encodes back to its
    two indices, and rejects every other byte.
    """
    encoded = pair_immediates()
    invalid = spec.module("vm.exceptions").InvalidParameter
    for byte in range(256):
        if byte in encoded:
            assert stack.decode_pair(U8(byte)) == encoded[byte]
        else:
            with pytest.raises(invalid):
                stack.decode_pair(U8(byte))


@pytest.mark.parametrize("decoder", ["decode_single", "decode_pair"])
def test_no_immediate_reads_as_a_jump_destination(
    spec: Hardfork, stack: ModuleType, decoder: str
) -> None:
    """
    No byte the spec accepts as an immediate is a `JUMPDEST` or a `PUSH`,
    and every accepted byte decodes to its own indices.
    """
    invalid = spec.module("vm.exceptions").InvalidParameter
    decoded = []
    for byte in range(256):
        try:
            decoded.append(getattr(stack, decoder)(U8(byte)))
        except invalid:
            continue
        assert byte not in JUMPDEST_ANALYSIS_OPCODES
    assert decoded
    assert len(set(decoded)) == len(decoded)
