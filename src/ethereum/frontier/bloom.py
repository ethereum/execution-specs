"""
Ethereum Logs Bloom
^^^^^^^^^^^^^^^^^^^

.. contents:: Table of Contents
    :backlinks: none
    :local:

Introduction
------------

Logs Bloom related functionalities used in Ethereum.
"""

from typing import Tuple

from ethereum.base_types import Uint
from ethereum.crypto import keccak256

from .eth_types import Bloom, Log


def add_to_bloom(bloom: bytearray, bloom_entry: bytes) -> None:
    """
    Add a bloom entry to the bloom filter (`bloom`).

    Parameters
    ----------
    bloom :
        The bloom filter.
    bloom_entry :
        An entry which is to be added to bloom filter.
    """
    # TODO: This functionality hasn't been tested rigorously yet.
    hash = keccak256(bloom_entry)

    for idx in (0, 2, 4):
        # Obtain the least significant 11 bits from the pair of bytes
        # (16 bits), and set this bit in bloom bytearray.
        # The obtained bit is 0-indexed in the bloom filter from the least
        # significant bit to the most significant bit.
        bit_to_set = Uint.from_be_bytes(hash[idx : idx + 2]) & 0x07FF
        # Below is the index of the bit in the bytearray (where 0-indexed
        # byte is the most significant byte)
        bit_index = 0x07FF - bit_to_set

        byte_index = bit_index // 8
        bit_value = 1 << (7 - (bit_index % 8))
        bloom[byte_index] = bloom[byte_index] | bit_value


def logs_bloom(logs: Tuple[Log, ...]) -> Bloom:
    """
    Obtain the logs bloom from a list of log entries.

    Parameters
    ----------
    logs :
        List of logs for which the logs bloom is to be obtained.

    Returns
    -------
    logs_bloom : `Bloom`
        The logs bloom obtained which is 256 bytes with some bits set as per
        the caller address and the log topics.
    """
    # TODO: Logs bloom functionality hasn't been tested rigorously yet. The
    # required test cases need `CALL` opcode to be implemented.
    bloom: bytearray = bytearray(b"\x00" * 256)

    for log in logs:
        add_to_bloom(bloom, log.address)
        for topic in log.topics:
            add_to_bloom(bloom, topic)

    return bytes(bloom)
