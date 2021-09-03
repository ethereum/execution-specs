"""
Ethash Functions
^^^^^^^^^^^^^^^^

..contents:: Table of Contents
    :backlinks: none
    :local:

Introduction
------------

Ethash algorithm related functionalities.
"""

from typing import Tuple, Union

from ethereum.base_types import UINT32_MAX_VALUE, Uint, Uint32
from ethereum.crypto import Hash32, Hash64, keccak256, keccak512
from ethereum.utils.numeric import (
    is_prime,
    le_bytes_to_uint32_sequence,
    le_uint32_sequence_to_bytes,
    le_uint32_sequence_to_uint,
)

EPOCH_SIZE = 30000
INITIAL_CACHE_SIZE = 2 ** 24
CACHE_EPOCH_GROWTH_SIZE = 2 ** 17
INITIAL_DATASET_SIZE = 2 ** 30
DATASET_EPOCH_GROWTH_SIZE = 2 ** 23
HASH_BYTES = 64
MIX_BYTES = 128
CACHE_ROUNDS = 3
DATASET_PARENTS = 256


def epoch(block_number: Uint) -> Uint:
    """
    Obtain the epoch number to which the block identified by `block_number`
    belongs.

    Parameters
    ----------
    block_number :
        The number of the block of interest.

    Returns
    -------
    epoch_number : `Uint`
        The epoch number to which the passed in block belongs.
    """
    return block_number // EPOCH_SIZE


def cache_size(block_number: Uint) -> Uint:
    """
    Obtain the cache size (in bytes) of the epoch to which `block_number`
    belongs.

    Parameters
    ----------
    block_number :
        The number of the block of interest.

    Returns
    -------
    cache_size_bytes : `Uint`
        The cache size in bytes for the passed in block.
    """
    size = INITIAL_CACHE_SIZE + (CACHE_EPOCH_GROWTH_SIZE * epoch(block_number))
    size -= HASH_BYTES
    while not is_prime(size // HASH_BYTES):
        size -= 2 * HASH_BYTES

    return size


def dataset_size(block_number: Uint) -> Uint:
    """
    Obtain the dataset size (in bytes) of the epoch to which `block_number`
    belongs.

    Parameters
    ----------
    block_number :
        The number of the block of interest.

    Returns
    -------
    dataset_size_bytes : `Uint`
        The dataset size in bytes for the passed in block.
    """
    size = INITIAL_DATASET_SIZE + (
        DATASET_EPOCH_GROWTH_SIZE * epoch(block_number)
    )
    size -= MIX_BYTES
    while not is_prime(size // MIX_BYTES):
        size -= 2 * MIX_BYTES

    return size


def generate_seed(block_number: Uint) -> Hash32:
    """
    Obtain the cache generation seed for the block identified by
    `block_number`.

    Parameters
    ----------
    block_number :
        The number of the block of interest.

    Returns
    -------
    seed : `Hash32`
        The cache generation seed for the passed in block.
    """
    epoch_number = epoch(block_number)

    seed = b"\x00" * 32
    while epoch_number != 0:
        seed = keccak256(seed)
        epoch_number -= 1

    return seed


def generate_cache(block_number: Uint) -> Tuple[Tuple[Uint32, ...], ...]:
    """
    Generate the cache for the block identified by `block_number`. This cache
    would later be used to generate the full dataset.

    Parameters
    ----------
    block_number :
        The number of the block of interest.

    Returns
    -------
    cache : `Tuple[Tuple[Uint32, ...], ...]`
        The cache generated for the passed in block.
    """
    seed = generate_seed(block_number)
    cache_size_bytes = cache_size(block_number)

    cache_size_words = cache_size_bytes // HASH_BYTES
    cache = [keccak512(seed)]

    previous_cache_item = cache[0]
    for _ in range(1, cache_size_words):
        cache_item = keccak512(previous_cache_item)
        cache.append(cache_item)
        previous_cache_item = cache_item

    for _ in range(CACHE_ROUNDS):
        for index in range(cache_size_words):
            # Converting `cache_size_words` to int as `-1 + Uint(5)` is an
            # error.
            first_cache_item = cache[
                (index - 1 + int(cache_size_words)) % cache_size_words
            ]
            second_cache_item = cache[
                Uint32.from_le_bytes(cache[index][0:4]) % cache_size_words
            ]
            result = bytes(
                [a ^ b for a, b in zip(first_cache_item, second_cache_item)]
            )
            cache[index] = keccak512(result)

    return tuple(
        le_bytes_to_uint32_sequence(cache_item) for cache_item in cache
    )


def fnv(a: Union[Uint, Uint32], b: Union[Uint, Uint32]) -> Uint32:
    """
    FNV algorithm is inspired by the FNV hash, which in some cases is used
    as a non-associative substitute for XOR.

    Note that here we multiply the prime with the full 32-bit input, in
    contrast with the FNV-1 spec which multiplies the prime with
    one byte (octet) in turn.

    Parameters
    ----------
    a:
        The first data point.
    b :
        The second data point.

    Returns
    -------
    modified_mix_integers : `Uint32`
        The result of performing fnv on the passed in data points.
    """
    # This is a faster way of doing [number % (2 ** 32)]
    result = ((Uint(a) * 0x01000193) ^ Uint(b)) & UINT32_MAX_VALUE
    return Uint32(result)


def fnv_hash(
    mix_integers: Tuple[Uint32, ...], data: Tuple[Uint32, ...]
) -> Tuple[Uint32, ...]:
    """
    FNV Hash mixes in data into mix using the ethash fnv method.

    Parameters
    ----------
    mix_integers:
        Mix data in the form of a sequence of Uint32.
    data :
        The data (sequence of Uint32) to be hashed into the mix.

    Returns
    -------
    modified_mix_integers : `Tuple[Uint32, ...]`
        The result of performing the fnv hash on the mix and the passed in
        data.
    """
    return tuple(
        fnv(mix_integers[i], data[i]) for i in range(len(mix_integers))
    )


def generate_dataset_item(
    cache: Tuple[Tuple[Uint32, ...], ...], index: Uint
) -> Hash64:
    """
    Generate a particular dataset item 0-indexed by `index` using `cache`.
    Each dataset item is a byte stream of 64 bytes or a stream of 16 uint32
    numbers.

    Parameters
    ----------
    cache:
        The cache from which a subset of items will be used to generate the
        dataset item.
    index :
        The index of the dataset item to generate.

    Returns
    -------
    dataset_item : `Hash32`
        The cache generation seed for the passed in block.
    """
    mix = keccak512(
        (
            le_uint32_sequence_to_uint(cache[index % len(cache)]) ^ index
        ).to_le_bytes(number_bytes=HASH_BYTES)
    )

    mix_integers = le_bytes_to_uint32_sequence(mix)

    for j in range(DATASET_PARENTS):
        mix_word: Uint32 = mix_integers[j % 16]
        cache_index = fnv(index ^ j, mix_word) % len(cache)
        parent = cache[cache_index]
        mix_integers = fnv_hash(mix_integers, parent)

    mix = le_uint32_sequence_to_bytes(mix_integers)

    return keccak512(mix)


def generate_dataset(block_number: Uint) -> Tuple[Hash64, ...]:
    """
    Generate the full dataset for the block identified by `block_number`.

    This function is present only for demonstration purposes, as it will take
    a long time to execute.

    Parameters
    ----------
    block_number :
        The number of the block of interest.

    Returns
    -------
    dataset : `Tuple[Hash64, ...]`
        The dataset generated for the passed in block.
    """
    dataset_size_bytes: Uint = dataset_size(block_number)
    cache: Tuple[Tuple[Uint32, ...], ...] = generate_cache(block_number)

    # TODO: Parallelize this later on if it adds value
    return tuple(
        generate_dataset_item(cache, Uint(index))
        for index in range(dataset_size_bytes // HASH_BYTES)
    )
