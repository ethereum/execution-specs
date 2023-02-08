"""
Ethash Functions
^^^^^^^^^^^^^^^^

.. contents:: Table of Contents
    :backlinks: none
    :local:

Introduction
------------

Ethash algorithm related functionalities.
"""

from typing import Callable, Tuple, Union

from ethereum.base_types import U32, U32_MAX_VALUE, Bytes8, Uint
from ethereum.crypto.hash import Hash32, Hash64, keccak256, keccak512
from ethereum.utils.numeric import (
    is_prime,
    le_bytes_to_uint32_sequence,
    le_uint32_sequence_to_bytes,
    le_uint32_sequence_to_uint,
)

EPOCH_SIZE = 30000
INITIAL_CACHE_SIZE = 2**24
CACHE_EPOCH_GROWTH_SIZE = 2**17
INITIAL_DATASET_SIZE = 2**30
DATASET_EPOCH_GROWTH_SIZE = 2**23
HASH_BYTES = 64
MIX_BYTES = 128
CACHE_ROUNDS = 3
DATASET_PARENTS = 256
HASHIMOTO_ACCESSES = 64


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

    return Hash32(seed)


def generate_cache(block_number: Uint) -> Tuple[Tuple[U32, ...], ...]:
    """
    Generate the cache for the block identified by `block_number`. This cache
    would later be used to generate the full dataset.

    Parameters
    ----------
    block_number :
        The number of the block of interest.

    Returns
    -------
    cache : `Tuple[Tuple[U32, ...], ...]`
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
                U32.from_le_bytes(cache[index][0:4]) % cache_size_words
            ]
            result = bytes(
                [a ^ b for a, b in zip(first_cache_item, second_cache_item)]
            )
            cache[index] = keccak512(result)

    return tuple(
        le_bytes_to_uint32_sequence(cache_item) for cache_item in cache
    )


def fnv(a: Union[Uint, U32], b: Union[Uint, U32]) -> U32:
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
    modified_mix_integers : `U32`
        The result of performing fnv on the passed in data points.
    """
    # This is a faster way of doing [number % (2 ** 32)]
    result = ((Uint(a) * 0x01000193) ^ Uint(b)) & U32_MAX_VALUE
    return U32(result)


def fnv_hash(
    mix_integers: Tuple[U32, ...], data: Tuple[U32, ...]
) -> Tuple[U32, ...]:
    """
    FNV Hash mixes in data into mix using the ethash fnv method.

    Parameters
    ----------
    mix_integers:
        Mix data in the form of a sequence of U32.
    data :
        The data (sequence of U32) to be hashed into the mix.

    Returns
    -------
    modified_mix_integers : `Tuple[U32, ...]`
        The result of performing the fnv hash on the mix and the passed in
        data.
    """
    return tuple(
        fnv(mix_integers[i], data[i]) for i in range(len(mix_integers))
    )


def generate_dataset_item(
    cache: Tuple[Tuple[U32, ...], ...], index: Uint
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
    dataset_item : `Hash64`
        The generated dataset item for passed index.
    """
    mix = keccak512(
        (
            le_uint32_sequence_to_uint(cache[index % len(cache)]) ^ index
        ).to_le_bytes(number_bytes=HASH_BYTES)
    )

    mix_integers = le_bytes_to_uint32_sequence(mix)

    for j in range(DATASET_PARENTS):
        mix_word: U32 = mix_integers[j % 16]
        cache_index = fnv(index ^ j, mix_word) % len(cache)
        parent = cache[cache_index]
        mix_integers = fnv_hash(mix_integers, parent)

    mix = Hash64(le_uint32_sequence_to_bytes(mix_integers))

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
    cache: Tuple[Tuple[U32, ...], ...] = generate_cache(block_number)

    # TODO: Parallelize this later on if it adds value
    return tuple(
        generate_dataset_item(cache, Uint(index))
        for index in range(dataset_size_bytes // HASH_BYTES)
    )


def hashimoto(
    header_hash: Hash32,
    nonce: Bytes8,
    dataset_size: Uint,
    fetch_dataset_item: Callable[[Uint], Tuple[U32, ...]],
) -> Tuple[bytes, Hash32]:
    """
    Obtain the mix digest and the final value for a header, by aggregating
    data from the full dataset.

    Parameters
    ----------
    header_hash :
        The PoW valid rlp hash of a header.
    nonce :
        The propogated nonce for the given block.
    dataset_size :
        Dataset size for the epoch to which the current block belongs to.
    fetch_dataset_item :
        The function which will be used to obtain a specific dataset item
        from an index.

    Returns
    -------
    mix_digest : `bytes`
        The mix digest generated from the header hash and propogated nonce.
    result : `Hash32`
        The final result obtained which will be checked for leading zeros (in
        byte representation) in correspondance with the block difficulty.
    """
    nonce_le = bytes(reversed(nonce))
    seed_hash = keccak512(header_hash + nonce_le)
    seed_head = U32.from_le_bytes(seed_hash[:4])

    rows = dataset_size // 128
    mix = le_bytes_to_uint32_sequence(seed_hash) * (MIX_BYTES // HASH_BYTES)

    for i in range(HASHIMOTO_ACCESSES):
        new_data: Tuple[U32, ...] = ()
        parent = fnv(i ^ seed_head, mix[i % len(mix)]) % rows
        for j in range(MIX_BYTES // HASH_BYTES):
            # Typecasting `parent` from U32 to Uint as 2*parent + j may
            # overflow U32.
            new_data += fetch_dataset_item(2 * Uint(parent) + j)

        mix = fnv_hash(mix, new_data)

    compressed_mix = []
    for i in range(0, len(mix), 4):
        compressed_mix.append(
            fnv(fnv(fnv(mix[i], mix[i + 1]), mix[i + 2]), mix[i + 3])
        )

    mix_digest = le_uint32_sequence_to_bytes(compressed_mix)
    result = keccak256(seed_hash + mix_digest)

    return mix_digest, result


def hashimoto_light(
    header_hash: Hash32,
    nonce: Bytes8,
    cache: Tuple[Tuple[U32, ...], ...],
    dataset_size: Uint,
) -> Tuple[bytes, Hash32]:
    """
    Run the hashimoto algorithm by generating dataset item using the cache
    instead of loading the full dataset into main memory.

    Parameters
    ----------
    header_hash :
        The PoW valid rlp hash of a header.
    nonce :
        The propogated nonce for the given block.
    cache:
        The generated cache for the epoch to which the current block belongs
        to.
    dataset_size :
        Dataset size for the epoch to which the current block belongs to.

    Returns
    -------
    mix_digest : `bytes`
        The mix digest generated from the header hash and propogated nonce.
    result : `Hash32`
        The final result obtained which will be checked for leading zeros (in
        byte representation) in correspondance with the block difficulty.
    """

    def fetch_dataset_item(index: Uint) -> Tuple[U32, ...]:
        """
        Generate dataset item (as tuple of U32 numbers) from cache.

        Parameters
        ----------
        index :
            The index of the dataset item to generate.

        Returns
        -------
        dataset_item : `Tuple[U32, ...]`
            The generated dataset item for passed index.
        """
        item: Hash64 = generate_dataset_item(cache, index)
        return le_bytes_to_uint32_sequence(item)

    return hashimoto(header_hash, nonce, dataset_size, fetch_dataset_item)
