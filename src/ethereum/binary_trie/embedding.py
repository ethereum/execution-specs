"""
The [EIP-8297] embedding of Ethereum state into the binary tree.

Account and storage tries are merged into the single key/value tree
defined in [`ethereum.binary_trie.trie`], which also holds contract
code. This module defines how accounts, storage slots, and code
chunks are assigned keys and packed into values, and the operations
that write ([`embed_account`], [`embed_storage_slot`]) and remove
([`remove_account`], [`remove_storage_slot`], [`remove_code_chunks`])
them.

The first byte of every key is a **zone** identifier that labels the
category of state the key holds. Account headers live in
[`ACCOUNT_ZONE`], content-addressed overflow code in [`CODE_ZONE`],
and overflow storage in [`STORAGE_ZONE`].

Keys are variable length, however importantly every key of a zone has
the same length, keeping keys prefix-free as the tree requires.

A key's **stem** is every byte except its final sub-index byte. Keys
sharing a stem form one group of up to [`STEM_SUBTREE_WIDTH`]
co-located values, all reachable through the same branch of the
tree.

This keeps data that is accessed together cheap to prove: an
account's header stem holds its basic data, code hash, first storage
slots, and first code chunks, so one proof path covers them all.

Data past the header keeps the grouping at coarser granularity;
overflow storage and code share a stem per [`STEM_SUBTREE_WIDTH`]
consecutive slots or chunks, so neighboring values are still proved
through one shared path rather than one path each.

[EIP-8297]: https://eips.ethereum.org/EIPS/eip-8297
[`ethereum.binary_trie.trie`]: ref:ethereum.binary_trie.trie
[`ACCOUNT_ZONE`]: ref:ethereum.binary_trie.embedding.ACCOUNT_ZONE
[`CODE_ZONE`]: ref:ethereum.binary_trie.embedding.CODE_ZONE
[`STORAGE_ZONE`]: ref:ethereum.binary_trie.embedding.STORAGE_ZONE
[`STEM_SUBTREE_WIDTH`]: ref:ethereum.binary_trie.embedding.STEM_SUBTREE_WIDTH
[`embed_account`]: ref:ethereum.binary_trie.embedding.embed_account
[`embed_storage_slot`]: ref:ethereum.binary_trie.embedding.embed_storage_slot
[`remove_account`]: ref:ethereum.binary_trie.embedding.remove_account
[`remove_storage_slot`]: ref:ethereum.binary_trie.embedding.remove_storage_slot
[`remove_code_chunks`]: ref:ethereum.binary_trie.embedding.remove_code_chunks
"""  # noqa: E501

from typing import List

from ethereum_types.bytes import Bytes, Bytes20, Bytes32
from ethereum_types.numeric import U8, U32, U64, U256, Uint

from ethereum.crypto.hash import Hash32, keccak256
from ethereum.utils.byte import left_pad_zero_bytes, right_pad_zero_bytes

from .trie import BinaryTrie, Key, blake3_hash, trie_set

Zone = U8
"""
One-byte identifier labeling the category of state a key holds,
prepended as the first byte of every key.

Zones are the partitions of the Partitioned Binary Tree: because the
tree consumes key bits most significant first, every zone owns its
own region of the key space.
Defined zones are [`ACCOUNT_ZONE`],[`CODE_ZONE`], and [`STORAGE_ZONE`]
The remaining values are reserved for future state categories.

[`ACCOUNT_ZONE`]: ref:ethereum.binary_trie.embedding.ACCOUNT_ZONE
[`CODE_ZONE`]: ref:ethereum.binary_trie.embedding.CODE_ZONE
[`STORAGE_ZONE`]: ref:ethereum.binary_trie.embedding.STORAGE_ZONE
"""

Address32 = Bytes32
"""
32-byte address used to key the tree.

Legacy 20-byte addresses are converted by [`address20_to_address32`].

[`address20_to_address32`]: ref:ethereum.binary_trie.embedding.address20_to_address32
"""  # noqa: E501

BASIC_DATA_LEAF_KEY = Uint(0)
"""
Sub-index of the account header leaf packing version, code size,
nonce, and balance.
"""

BASIC_DATA_VERSION = Uint(0)
"""
Version of the basic data leaf layout, packed as the leaf's first
byte by [`encode_basic_data`]. A future change to the layout bumps
the version so readers can tell the encodings apart.

[`encode_basic_data`]: ref:ethereum.binary_trie.embedding.encode_basic_data
"""

CODE_HASH_LEAF_KEY = Uint(1)
"""
Sub-index of the account header leaf holding the code hash.
"""

EMPTY_CODE_HASH = keccak256(b"")
"""
Code hash for accounts without code.

The leaf is written on account creation; EOAs included and holds
the Keccak hash of empty bytecode: `EXTCODEHASH` of an existing
codeless account must keep returning this value (and new accounts).

Note: The tree's own hash function is different to the hash
function being used for `code_hash`. `code_hash` is an
EVM-observable value stored in a leaf, not a tree commitment, so it
stays Keccak even though the tree hashes with [`blake3_hash`].

[`blake3_hash`]: ref:ethereum.binary_trie.trie.blake3_hash
"""

HEADER_STORAGE_OFFSET = Uint(64)
"""
Sub-index of storage slot `0` within the account header stem. Slots
`0` through `63` live in the header.
"""

CODE_OFFSET = Uint(128)
"""
Sub-index of code chunk `0` within the account header stem. Chunks
`0` through `127` live in the header.
"""

STEM_SUBTREE_WIDTH = Uint(256)
"""
Maximum number of values grouped under a single stem: the size of
the sub-index byte's space.
"""

HEADER_CHUNK_COUNT = STEM_SUBTREE_WIDTH - CODE_OFFSET
"""
Number of code chunks that fit in the account header stem. Chunks at
this index and above are content-addressed in [`CODE_ZONE`] and
shared between accounts with identical bytecode; see
[`get_tree_key_for_code_chunk`].

[`CODE_ZONE`]: ref:ethereum.binary_trie.embedding.CODE_ZONE
[`get_tree_key_for_code_chunk`]: ref:ethereum.binary_trie.embedding.get_tree_key_for_code_chunk
"""  # noqa: E501

ACCOUNT_ZONE = Zone(0)
"""
Zone byte of account header stems.
"""

CODE_ZONE = Zone(1)
"""
Zone byte of content-addressed overflow code stems.
"""

STORAGE_ZONE = Zone(255)
"""
Zone byte of overflow storage stems.

Storage sits at the far end of the zone byte, leaving zones `2`
through `254` reserved for future state categories.

Note: Because keys are variable length, a zone's one-byte label
says nothing about its capacity so every zone's key space is
unbounded behind its prefix.
"""

ACCOUNT_KEY_LENGTH = Uint(34)
"""
Length of every account zone key: the zone byte, a full address
digest, and the sub-index byte.
"""

CODE_KEY_LENGTH = Uint(34)
"""
Length of every code zone key: the zone byte, a full digest of the
code hash and group index, and the sub-index byte.
"""

STORAGE_KEY_LENGTH = Uint(66)
"""
Length of every storage zone key: the zone byte, two full digests
binding the account and its group index, and the sub-index byte.
"""

PUSH_OFFSET = Uint(95)
"""
Opcode value one below `PUSH1`, so `PUSH_OFFSET + n` is the opcode
pushing `n` bytes.
"""

PUSH1 = PUSH_OFFSET + Uint(1)
"""
Opcode of the smallest push instruction.
"""

PUSH32 = PUSH_OFFSET + Uint(32)
"""
Opcode of the largest push instruction.
"""


def address20_to_address32(address: Bytes20) -> Address32:
    """
    Convert a legacy 20-byte address by prepending 12 zero bytes.

    The embedding keys the tree by 32-byte addresses so that a future
    address-space extension needs no re-keying.
    """
    return Address32(left_pad_zero_bytes(address, 32))


def key_hash(data: Bytes) -> Hash32:
    """
    Hash `data` for use in tree key derivation.

    In practice, we reuse [`blake3_hash`], the hash being used for
    tree merkelization.

    [`blake3_hash`]: ref:ethereum.binary_trie.trie.blake3_hash
    """
    return blake3_hash(data)


def get_tree_key(zone: Zone, tree_position: Bytes, sub_index: U8) -> Key:
    """
    Build a key from its three parts: the `zone` byte, the
    hash-derived `tree_position`, and the final `sub_index` byte.
    """
    return Key(bytes([int(zone)]) + tree_position + bytes([int(sub_index)]))


def get_tree_key_for_header(address: Address32, sub_index: Uint) -> Key:
    """
    Compute the key of the account header leaf at `sub_index`.

    The header stem is in [`ACCOUNT_ZONE`] and is keyed by the address
    alone, so each account has exactly one header stem. The header is
    not one key: it is up to [`STEM_SUBTREE_WIDTH`] separate leaves
    sharing that stem, and `sub_index` selects which one; basic
    data, code hash, an early storage slot, or an early code chunk.

    [`ACCOUNT_ZONE`]: ref:ethereum.binary_trie.embedding.ACCOUNT_ZONE
    [`STEM_SUBTREE_WIDTH`]: ref:ethereum.binary_trie.embedding.STEM_SUBTREE_WIDTH
    """  # noqa: E501
    key = get_tree_key(ACCOUNT_ZONE, key_hash(address), U8(sub_index))
    assert len(key) == int(ACCOUNT_KEY_LENGTH)
    return key


def get_tree_key_for_basic_data(address: Address32) -> Key:
    """
    Compute the key of the account's basic data leaf.
    """
    return get_tree_key_for_header(address, BASIC_DATA_LEAF_KEY)


def get_tree_key_for_code_hash(address: Address32) -> Key:
    """
    Compute the key of the account's code hash leaf.
    """
    return get_tree_key_for_header(address, CODE_HASH_LEAF_KEY)


def storage_tree_position(address: Address32, tree_index: U256) -> Bytes:
    """
    Build the hash-derived position of an account's overflow storage
    group at `tree_index`.

    The position carries two full digests:

    - `key_hash(address)` gathers all of an account's overflow
      storage under one subtree, which future expiry and sync
      schemes could use as their unit of work: a contract's whole
      storage is one contiguous key range that can be expired or
      served as a single subtree, rather than locations scattered
      across the whole tree.
    - `key_hash(address ‖ tree_index)` spreads the account's groups
      within that subtree.

    Both digests depend on the address, so storage keys that an
    attacker grinds to sit close together under one contract cannot
    be reused against a different contract.

    `key_hash(address)` is the same digest [`get_tree_key_for_header`]
    uses for the account's header stem; the two never collide because
    they sit in different zones, differing in the key's first byte.

    [`get_tree_key_for_header`]: ref:ethereum.binary_trie.embedding.get_tree_key_for_header
    """  # noqa: E501
    prefix = key_hash(address)
    suffix = key_hash(address + tree_index.to_be_bytes32())
    return Bytes(prefix + suffix)


def get_tree_key_for_storage_slot(
    address: Address32, storage_key: U256
) -> Key:
    """
    Compute the key of a storage slot.

    Slots `0` through `63` live in the account header stem and all other
    slots live in the storage zone.

    This leaves group `0` (`tree_index == 0`) short; its
    storage-zone leaves are only sub-indices `64`-`255`, 192 slots
    rather than the full 256 every later group has.
    # TODO: still need to check why first 64
    """
    if storage_key < U256(CODE_OFFSET - HEADER_STORAGE_OFFSET):
        return get_tree_key_for_header(
            address, HEADER_STORAGE_OFFSET + Uint(storage_key)
        )
    tree_index = storage_key // U256(STEM_SUBTREE_WIDTH)
    sub_index = storage_key % U256(STEM_SUBTREE_WIDTH)
    key = get_tree_key(
        STORAGE_ZONE,
        storage_tree_position(address, tree_index),
        U8(sub_index),
    )
    assert len(key) == int(STORAGE_KEY_LENGTH)
    return key


def get_tree_key_for_code_chunk(
    address: Address32, code_hash: Hash32, chunk_id: Uint
) -> Key:
    """
    Compute the key of a code chunk.

    Chunks `0` through `127` live in the account header stem: the
    start of a contract's code (usually dispatchers and entry points)
    is its most executed region, so the first chunks open with the
    same branch as the account's basic data.

    Chunks at index `128` and above live in [`CODE_ZONE`],
    content-addressed by `code_hash` so contracts with identical
    bytecode share leaves.

    [`CODE_ZONE`]: ref:ethereum.binary_trie.embedding.CODE_ZONE
    """
    header_chunk_count = STEM_SUBTREE_WIDTH - CODE_OFFSET
    if chunk_id < header_chunk_count:
        return get_tree_key_for_header(address, CODE_OFFSET + chunk_id)
    overflow = chunk_id - header_chunk_count
    tree_index = overflow // STEM_SUBTREE_WIDTH
    sub_index = overflow % STEM_SUBTREE_WIDTH
    key = get_tree_key(
        CODE_ZONE,
        key_hash(code_hash + tree_index.to_be_bytes32()),
        U8(sub_index),
    )
    assert len(key) == int(CODE_KEY_LENGTH)
    return key


def chunkify_code(code: Bytes) -> List[Bytes32]:
    """
    Split `code` into the 32-byte chunks stored in the tree.

    Chunk `i` holds the `i`-th 31-byte slice of the code in bytes `1`
    through `31`, preceded by one byte counting how many of the
    slice's leading bytes are data of a push instruction that began in
    an earlier chunk.

    The count lets a chunk be interpreted without
    its predecessors and is capped at `31`, the chunk payload size.
    """
    if len(code) % 31 != 0:
        pad_amount = 31 - (len(code) % 31)
        code = Bytes(right_pad_zero_bytes(code, len(code) + pad_amount))

    # Number of push-data bytes remaining at each position, counting
    # the position itself; `0` marks executable bytes. The extra 32
    # entries let the largest push record data past the end of the
    # code.
    remaining_push_data = [0] * (len(code) + 32)
    position = 0
    while position < len(code):
        opcode = Uint(code[position])
        if PUSH1 <= opcode <= PUSH32:
            push_data_bytes = int(opcode - PUSH_OFFSET)
        else:
            push_data_bytes = 0
        position += 1
        for offset in range(push_data_bytes):
            remaining_push_data[position + offset] = push_data_bytes - offset
        position += push_data_bytes

    return [
        Bytes32(
            bytes([min(remaining_push_data[start], 31)])
            + code[start : start + 31]
        )
        for start in range(0, len(code), 31)
    ]


def encode_basic_data(code_size: U32, nonce: U64, balance: U256) -> Bytes32:
    """
    Pack an account's basic data into the 32-byte value stored at
    [`BASIC_DATA_LEAF_KEY`].

    The fields are packed big-endian, consistent with every other
    encoding in the embedding:

    - one version byte, currently zero
    - three reserved zero bytes
    - four bytes of code size
    - eight bytes of nonce
    - sixteen bytes of balance

    The code size and nonce parameters are typed at their field
    widths; the nonce cannot exceed eight bytes by [EIP-2681].
    Balances are protocol-level `U256` values, so the parameter
    keeps that type and the sixteen-byte field bound is asserted
    here instead.

    TODO: `code_size` is four bytes at offset four here, one
    byte wider than EIP-7864's three-byte field at offset five.

    [`BASIC_DATA_LEAF_KEY`]: ref:ethereum.binary_trie.embedding.BASIC_DATA_LEAF_KEY
    [EIP-2681]: https://eips.ethereum.org/EIPS/eip-2681
    """  # noqa: E501
    assert balance < U256(2) ** U256(128)  # U128 doesn't exist
    return Bytes32(
        bytes([int(BASIC_DATA_VERSION)])
        # Reserved bytes: headroom for future header fields.
        + b"\x00" * 3
        + code_size.to_be_bytes4()
        + nonce.to_be_bytes8()
        + int(balance).to_bytes(16, "big")
    )


def embed_account(
    trie: BinaryTrie,
    address32: Address32,
    nonce: U64,
    balance: U256,
    code_hash: Hash32,
    code: Bytes,
) -> None:
    """
    Write an account's leaves into `trie`: packed basic data, the
    code hash, and one leaf per chunk of `code`.

    Writing over an existing account updates its leaves in place;
    chunk leaves of a previous, different code are not touched and
    must be removed with [`remove_code_chunks`] first.

    [`remove_code_chunks`]: ref:ethereum.binary_trie.embedding.remove_code_chunks
    """  # noqa: E501
    trie_set(
        trie,
        get_tree_key_for_basic_data(address32),
        encode_basic_data(
            code_size=U32(len(code)),
            nonce=nonce,
            balance=balance,
        ),
    )
    trie_set(
        trie,
        get_tree_key_for_code_hash(address32),
        Bytes32(code_hash),
    )
    for chunk_id, chunk in enumerate(chunkify_code(code)):
        trie_set(
            trie,
            get_tree_key_for_code_chunk(address32, code_hash, Uint(chunk_id)),
            chunk,
        )


def embed_storage_slot(
    trie: BinaryTrie,
    address32: Address32,
    storage_key: U256,
    value: Bytes32,
) -> None:
    """
    Write one storage slot's leaf into `trie`, in the account header
    stem or the account's overflow storage subtree as the slot
    number dictates.
    """
    trie_set(
        trie, get_tree_key_for_storage_slot(address32, storage_key), value
    )


def remove_account(trie: BinaryTrie, address32: Address32) -> None:
    """
    Remove a bare account from `trie`: delete its basic data and
    code hash leaves, the only leaves such an account owns.

    The account must be bare; no code chunk leaves, no storage slot
    leaves. Protocol rules guarantee every deletable account is:
    [EIP-6780] restricts deletion to accounts destroyed in the
    transaction that created them, and creation requires empty code
    ([EIP-684]) and empty storage ([EIP-7610]), so an account both
    present in the pre-state and deletable holds a balance at most.
    Callers enforce the invariant; see
    [`ethereum.state_pbt.apply_diff_to_trie`].

    [EIP-6780]: https://eips.ethereum.org/EIPS/eip-6780
    [EIP-684]: https://eips.ethereum.org/EIPS/eip-684
    [EIP-7610]: https://eips.ethereum.org/EIPS/eip-7610
    [`ethereum.state_pbt.apply_diff_to_trie`]: ref:ethereum.state_pbt.apply_diff_to_trie
    """  # noqa: E501
    trie_set(trie, get_tree_key_for_basic_data(address32), None)
    trie_set(trie, get_tree_key_for_code_hash(address32), None)


def remove_storage_slot(
    trie: BinaryTrie, address32: Address32, storage_key: U256
) -> None:
    """
    Remove one storage slot's leaf from `trie`; removing an absent
    slot does nothing.
    """
    trie_set(
        trie, get_tree_key_for_storage_slot(address32, storage_key), None
    )


def remove_code_chunks(
    trie: BinaryTrie, address32: Address32, code_hash: Hash32, code: Bytes
) -> None:
    """
    Remove `code`'s chunk leaves from `trie`, one deletion per chunk.

    Chunks past [`HEADER_CHUNK_COUNT`] are content-addressed and
    shared between accounts with identical bytecode, so the caller
    must know that no other account still references `code_hash`
    before removing a code that overflows the header. Header chunks
    are keyed by `address32` and always safe to remove.

    [`HEADER_CHUNK_COUNT`]: ref:ethereum.binary_trie.embedding.HEADER_CHUNK_COUNT
    """  # noqa: E501
    for chunk_id in range(len(chunkify_code(code))):
        trie_set(
            trie,
            get_tree_key_for_code_chunk(address32, code_hash, Uint(chunk_id)),
            None,
        )
