"""
Ethash is a proof-of-work algorithm designed to be [ASIC] resistant through
[memory hardness][mem-hard].

To achieve memory hardness, computing Ethash requires access to subsets of a
large structure. The particular subsets chosen are based on the nonce and block
header, while the set itself is changed every [`epoch`].

At a high level, the Ethash algorithm is as follows:

1. Create a **seed** value, generated with [`generate_seed`] and based on the
   preceding block numbers.
1. From the seed, compute a pseudorandom **cache** with [`generate_cache`].
1. From the cache, generate a **dataset** with [`generate_dataset`]. The
   dataset grows over time based on [`DATASET_EPOCH_GROWTH_SIZE`].
1. Miners hash slices of the dataset together, which is where the memory
   hardness is introduced. Verification of the proof-of-work only requires the
   cache to be able to recompute a much smaller subset of the full dataset.

[`DATASET_EPOCH_GROWTH_SIZE`]: ref:ethereum.ethash.DATASET_EPOCH_GROWTH_SIZE
[`generate_dataset`]: ref:ethereum.ethash.generate_dataset
[`generate_cache`]: ref:ethereum.ethash.generate_cache
[`generate_seed`]: ref:ethereum.ethash.generate_seed
[`epoch`]: ref:ethereum.ethash.epoch
[ASIC]: https://en.wikipedia.org/wiki/Application-specific_integrated_circuit
[mem-hard]: https://en.wikipedia.org/wiki/Memory-hard_function
"""

from typing import Callable, Tuple, Union

from ethereum_types.bytes import Bytes8
from ethereum_types.numeric import U32, Uint, ulen

from ethereum.crypto.hash import Hash32, Hash64, keccak256, keccak512
from ethereum.utils.numeric import (
    is_prime,
    le_bytes_to_uint32_sequence,
    le_uint32_sequence_to_bytes,
    le_uint32_sequence_to_uint,
)

EPOCH_SIZE = Uint(30000)
"""
Number of blocks before a dataset needs to be regenerated (known as an
"epoch".) See [`epoch`].

[`epoch`]: ref:ethereum.ethash.epoch
"""

INITIAL_CACHE_SIZE = Uint(2**24)
"""
Size of the cache (in bytes) during the first epoch. Each subsequent epoch's
cache roughly grows by [`CACHE_EPOCH_GROWTH_SIZE`] bytes. See [`cache_size`].

[`CACHE_EPOCH_GROWTH_SIZE`]: ref:ethereum.ethash.CACHE_EPOCH_GROWTH_SIZE
[`cache_size`]: ref:ethereum.ethash.cache_size
"""

CACHE_EPOCH_GROWTH_SIZE = Uint(2**17)
"""
After the first epoch, the cache size grows by roughly this amount. See
[`cache_size`].

[`cache_size`]: ref:ethereum.ethash.cache_size
"""

INITIAL_DATASET_SIZE = Uint(2**30)
"""
Size of the dataset (in bytes) during the first epoch. Each subsequent epoch's
dataset roughly grows by [`DATASET_EPOCH_GROWTH_SIZE`] bytes. See
[`dataset_size`].

[`DATASET_EPOCH_GROWTH_SIZE`]: ref:ethereum.ethash.DATASET_EPOCH_GROWTH_SIZE
[`dataset_size`]: ref:ethereum.ethash.dataset_size
"""

DATASET_EPOCH_GROWTH_SIZE = Uint(2**23)
"""
After the first epoch, the dataset size grows by roughly this amount. See
[`dataset_size`].

[`dataset_size`]: ref:ethereum.ethash.dataset_size
"""

HASH_BYTES = Uint(64)
"""
Length of a hash, in bytes.
"""

MIX_BYTES = Uint(128)
"""
Width of mix, in bytes. See [`generate_dataset_item`].

[`generate_dataset_item`]: ref:ethereum.ethash.generate_dataset_item
"""

CACHE_ROUNDS = 3
"""
Number of times to repeat the [`keccak512`] step while generating the hash. See
[`generate_cache`].

[`keccak512`]: ref:ethereum.crypto.hash.keccak512
[`generate_cache`]: ref:ethereum.ethash.generate_cache
"""

DATASET_PARENTS = Uint(256)
"""
Number of parents of each dataset element. See [`generate_dataset_item`].

[`generate_dataset_item`]: ref:ethereum.ethash.generate_dataset_item
"""

HASHIMOTO_ACCESSES = 64
"""
Number of accesses in the [`hashimoto`] loop.

[`hashimoto`]: ref:ethereum.ethash.hashimoto
"""


def epoch(block_number: Uint) -> Uint:
    """
    Obtain the epoch number to which the block identified by `block_number`
    belongs. The first epoch is numbered zero.

    An Ethash epoch is a fixed number of blocks ([`EPOCH_SIZE`]) long, during
    which the dataset remains constant. At the end of each epoch, the dataset
    is generated anew. See [`generate_dataset`].

    [`EPOCH_SIZE`]: ref:ethereum.ethash.EPOCH_SIZE
    [`generate_dataset`]: ref:ethereum.ethash.generate_dataset
    """
    return block_number // EPOCH_SIZE


def cache_size(block_number: Uint) -> Uint:
    """
    Obtain the cache size (in bytes) of the epoch to which `block_number`
    belongs.

    See [`INITIAL_CACHE_SIZE`] and [`CACHE_EPOCH_GROWTH_SIZE`] for the initial
    size and linear growth rate, respectively. The cache is generated in
    [`generate_cache`].

    The actual cache size is smaller than simply multiplying
    `CACHE_EPOCH_GROWTH_SIZE` by the epoch number to minimize the risk of
    unintended cyclic behavior. It is defined as the highest prime number below
    what linear growth would calculate.

    [`INITIAL_CACHE_SIZE`]: ref:ethereum.ethash.INITIAL_CACHE_SIZE
    [`CACHE_EPOCH_GROWTH_SIZE`]: ref:ethereum.ethash.CACHE_EPOCH_GROWTH_SIZE
    [`generate_cache`]: ref:ethereum.ethash.generate_cache
    """
    size = INITIAL_CACHE_SIZE + (CACHE_EPOCH_GROWTH_SIZE * epoch(block_number))
    size -= HASH_BYTES
    while not is_prime(size // HASH_BYTES):
        size -= Uint(2) * HASH_BYTES

    return size


def dataset_size(block_number: Uint) -> Uint:
    """
    Obtain the dataset size (in bytes) of the epoch to which `block_number`
    belongs.

    See [`INITIAL_DATASET_SIZE`] and [`DATASET_EPOCH_GROWTH_SIZE`][ds] for the
    initial size and linear growth rate, respectively. The complete dataset is
    generated in [`generate_dataset`], while the slices used in verification
    are generated in [`generate_dataset_item`].

    The actual dataset size is smaller than simply multiplying
    `DATASET_EPOCH_GROWTH_SIZE` by the epoch number to minimize the risk of
    unintended cyclic behavior. It is defined as the highest prime number below
    what linear growth would calculate.

    [`INITIAL_DATASET_SIZE`]: ref:ethereum.ethash.INITIAL_DATASET_SIZE
    [ds]: ref:ethereum.ethash.DATASET_EPOCH_GROWTH_SIZE
    [`generate_dataset`]: ref:ethereum.ethash.generate_dataset
    [`generate_dataset_item`]: ref:ethereum.ethash.generate_dataset_item
    """
    size = INITIAL_DATASET_SIZE + (
        DATASET_EPOCH_GROWTH_SIZE * epoch(block_number)
    )
    size -= MIX_BYTES
    while not is_prime(size // MIX_BYTES):
        size -= Uint(2) * MIX_BYTES

    return size


def generate_seed(block_number: Uint) -> Hash32:
    """
    Obtain the cache generation seed for the block identified by
    `block_number`. See [`generate_cache`].

    [`generate_cache`]: ref:ethereum.ethash.generate_cache
    """
    epoch_number = epoch(block_number)

    seed = b"\x00" * 32
    while epoch_number != 0:
        seed = keccak256(seed)
        epoch_number -= Uint(1)

    return Hash32(seed)


def generate_cache(block_number: Uint) -> Tuple[Tuple[U32, ...], ...]:
    """
    Generate the cache for the block identified by `block_number`. See
    [`generate_dataset`] for how the cache is used.

    The cache is generated in two steps: filling the array with a chain of
    [`keccak512`] hashes, then running two rounds of Sergio Demian Lerner's
    [RandMemoHash] on those bytes.

    [`keccak512`]: ref:ethereum.crypto.hash.keccak512
    [`generate_dataset`]: ref:ethereum.ethash.generate_dataset
    [RandMemoHash]: http://www.hashcash.org/papers/memohash.pdf
    """
    seed = generate_seed(block_number)
    cache_size_bytes = cache_size(block_number)

    cache_size_words = cache_size_bytes // HASH_BYTES
    cache = [keccak512(seed)]

    for index in range(1, cache_size_words):
        cache_item = keccak512(cache[index - 1])
        cache.append(cache_item)

    for _ in range(CACHE_ROUNDS):
        for index in range(cache_size_words):
            # Converting `cache_size_words` to int as `-1 + Uint(5)` is an
            # error.
            first_cache_item = cache[
                (index - 1 + int(cache_size_words)) % int(cache_size_words)
            ]
            second_cache_item = cache[
                U32.from_le_bytes(cache[index][0:4]) % U32(cache_size_words)
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
    A non-associative substitute for XOR, inspired by the [FNV] hash by Fowler,
    Noll, and Vo. See [`fnv_hash`], [`generate_dataset_item`], and
    [`hashimoto`].

    Note that here we multiply the prime with the full 32-bit input, in
    contrast with the [FNV-1] spec which multiplies the prime with one byte
    (octet) in turn.

    [`hashimoto`]: ref:ethereum.ethash.hashimoto
    [`generate_dataset_item`]: ref:ethereum.ethash.generate_dataset_item
    [`fnv_hash`]: ref:ethereum.ethash.fnv_hash
    [FNV]: https://w.wiki/XKZ
    [FNV-1]: http://www.isthe.com/chongo/tech/comp/fnv/#FNV-1
    """
    # This is a faster way of doing `number % (2 ** 32)`.
    result = ((Uint(a) * Uint(0x01000193)) ^ Uint(b)) & Uint(U32.MAX_VALUE)
    return U32(result)


def fnv_hash(
    mix_integers: Tuple[U32, ...], data: Tuple[U32, ...]
) -> Tuple[U32, ...]:
    """
    Combines `data` into `mix_integers` using [`fnv`]. See [`hashimoto`] and
    [`generate_dataset_item`].

    [`hashimoto`]: ref:ethereum.ethash.hashimoto
    [`generate_dataset_item`]: ref:ethereum.ethash.generate_dataset_item
    [`fnv`]: ref:ethereum.ethash.fnv
    """
    return tuple(
        fnv(mix_integers[i], data[i]) for i in range(len(mix_integers))
    )


def generate_dataset_item(
    cache: Tuple[Tuple[U32, ...], ...], index: Uint
) -> Hash64:
    """
    Generate a particular dataset item 0-indexed by `index` by hashing
    pseudorandomly-selected entries from `cache` together. See [`fnv`] and
    [`fnv_hash`] for the digest function, [`generate_cache`] for generating
    `cache`, and [`generate_dataset`] for the full dataset generation
    algorithm.

    [`fnv`]: ref:ethereum.ethash.fnv
    [`fnv_hash`]: ref:ethereum.ethash.fnv_hash
    [`generate_dataset`]: ref:ethereum.ethash.generate_dataset
    [`generate_cache`]: ref:ethereum.ethash.generate_cache
    """
    mix = keccak512(
        (
            le_uint32_sequence_to_uint(cache[index % ulen(cache)]) ^ index
        ).to_le_bytes64()
    )

    mix_integers = le_bytes_to_uint32_sequence(mix)

    for j in (Uint(k) for k in range(DATASET_PARENTS)):
        mix_word: U32 = mix_integers[j % Uint(16)]
        cache_index = fnv(index ^ j, mix_word) % U32(len(cache))
        parent = cache[cache_index]
        mix_integers = fnv_hash(mix_integers, parent)

    mix = Hash64(le_uint32_sequence_to_bytes(mix_integers))

    return keccak512(mix)


def generate_dataset(block_number: Uint) -> Tuple[Hash64, ...]:
    """
    Generate the full dataset for the block identified by `block_number`.

    This function is present only for demonstration purposes. It is not used
    while validating blocks.
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

    #### Parameters

    - `header_hash` is a valid RLP hash of a block header.
    - `nonce` is the propagated nonce for the given block.
    - `dataset_size` is the size of the dataset. See [`dataset_size`].
    - `fetch_dataset_item` is a function that retrieves a specific dataset item
      based on its index.

    #### Returns

    - The mix digest generated from the header hash and propagated nonce.
    - The final result obtained which will be checked for leading zeros (in
      byte representation) in correspondence with the block difficulty.

    [`dataset_size`]: ref:ethereum.ethash.dataset_size
    """
    nonce_le = bytes(reversed(nonce))
    seed_hash = keccak512(header_hash + nonce_le)
    seed_head = U32.from_le_bytes(seed_hash[:4])

    rows = dataset_size // Uint(128)
    mix = le_bytes_to_uint32_sequence(seed_hash) * (MIX_BYTES // HASH_BYTES)

    for i in range(HASHIMOTO_ACCESSES):
        new_data: Tuple[U32, ...] = ()
        parent = fnv(U32(i) ^ seed_head, mix[i % len(mix)]) % U32(rows)
        for j in range(MIX_BYTES // HASH_BYTES):
            # Typecasting `parent` from U32 to Uint as 2*parent + j may
            # overflow U32.
            new_data += fetch_dataset_item(Uint(2) * Uint(parent) + Uint(j))

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
    Run the [`hashimoto`] algorithm by generating dataset item using the cache
    instead of loading the full dataset into main memory.

    #### Parameters

    - `header_hash` is a valid RLP hash of a block header.
    - `nonce` is the propagated nonce for the given block.
    - `cache` is the cache generated by [`generate_cache`].
    - `dataset_size` is the size of the dataset. See [`dataset_size`].

    #### Returns

    - The mix digest generated from the header hash and propagated nonce.
    - The final result obtained which will be checked for leading zeros (in
      byte representation) in correspondence with the block difficulty.

    [`dataset_size`]: ref:ethereum.ethash.dataset_size
    [`generate_cache`]: ref:ethereum.ethash.generate_cache
    [`hashimoto`]: ref:ethereum.ethash.hashimoto
    """

    def fetch_dataset_item(index: Uint) -> Tuple[U32, ...]:
        item: Hash64 = generate_dataset_item(cache, index)
        return le_bytes_to_uint32_sequence(item)

    return hashimoto(header_hash, nonce, dataset_size, fetch_dataset_item)
