"""
Common procedures to test
[EIP-5656: MCOPY - Memory copying instruction](https://eips.ethereum.org/EIPS/eip-5656)
"""  # noqa: E501

from copy import copy

REFERENCE_SPEC_GIT_PATH = "EIPS/eip-5656.md"
REFERENCE_SPEC_VERSION = "2ade0452efe8124378f35284676ddfd16dd56ecd"


def mcopy(*, src: int, dest: int, length: int, memory: bytes) -> bytes:
    """
    Performs the mcopy routine as the EVM would do it.
    """
    if length == 0:
        return memory

    res = bytearray(copy(memory))

    # If the destination or source are larger than the memory, we need to extend the memory
    max_byte_index = max(src, dest) + length
    if max_byte_index > len(memory):
        res.extend(b"\x00" * (max_byte_index - len(memory)))

    for i in range(length):
        if (src + i) >= len(memory):
            src_b = 0
        else:
            src_b = memory[src + i]

        res[dest + i] = src_b
    return bytes(res)
