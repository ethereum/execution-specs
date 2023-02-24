"""
Ethereum Logs Bloom
^^^^^^^^^^^^^^^^^^^

.. contents:: Table of Contents
    :backlinks: none
    :local:

Introduction
------------

This modules defines functions for calculating bloom filters of logs. For the
general theory of bloom filters see e.g. `Wikipedia
<https://en.wikipedia.org/wiki/Bloom_filter>`_. Bloom filters are used to allow
for efficient searching of logs by address and/or topic, by rapidly
eliminating blocks and reciepts from their search.
"""

from typing import Tuple

from ethereum.base_types import Uint
from ethereum.crypto.hash import keccak256

from .fork_types import Bloom, Log


def add_to_bloom(bloom: bytearray, bloom_entry: bytes) -> None:
    """
    Add a bloom entry to the bloom filter (`bloom`).

    The number of hash functions used is 3. They are calculated by taking the
    least significant 11 bits from the first 3 16-bit words of the
    `keccak_256()` hash of `bloom_entry`.

    Parameters
    ----------
    bloom :
        The bloom filter.
    bloom_entry :
        An entry which is to be added to bloom filter.
    """
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

    The address and each topic of a log are added to the bloom filter.

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
    bloom: bytearray = bytearray(b"\x00" * 256)

    for log in logs:
        add_to_bloom(bloom, log.address)
        for topic in log.topics:
            add_to_bloom(bloom, topic)

    return Bloom(bloom)
