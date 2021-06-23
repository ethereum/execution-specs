"""
State Trie
^^^^^^^^^^

.. contents:: Table of Contents
    :backlinks: none
    :local:

Introduction
------------

The state trie is the structure responsible for storing
`eth1spec.eth_types.Account` objects.
"""

from copy import copy
from typing import Mapping, MutableMapping, Set, Union, cast

from . import crypto, rlp
from .base_types import U256, Bytes, Uint
from .eth_types import Account, Receipt, Root

debug = False
verbose = False

Node = Union[Account, Bytes, Receipt, Uint, U256]


def nibble_list_to_compact(x: Bytes, terminal: bool) -> bytearray:
    """
    Compresses nibble-list into a standard byte array with a flag.

    A nibble-list is a list of byte values no greater than `15`. The flag is
    encoded in high nibble of the highest byte. The flag nibble can be broken
    down into two two-bit flags.

    Highest nibble:

    ```
    +---+---+----------+--------+
    | _ | _ | terminal | parity |
    +---+---+----------+--------+
      3   2      1         0

    ```

    The lowest bit of the nibble encodes the parity of the length of the
    remaining nibbles -- `0` when even and `1` when odd. The second lowest bit
    encodes whether the key maps to a terminal node. The other two bits are not
    used.

    Parameters
    ----------
    x : `eth1spec.eth_types.Bytes`
        Array of nibbles.
    terminal : `bool`
        Flag denoting if the key points to a terminal (leaf) node.

    Returns
    -------
    compressed : `bytearray`
        Compact byte array.
    """
    compact = bytearray()

    if len(x) % 2 == 0:  # ie even length
        compact.append(16 * (2 * terminal))
        for i in range(0, len(x), 2):
            compact.append(16 * x[i] + x[i + 1])
    else:
        compact.append(16 * ((2 * terminal) + 1) + x[0])
        for i in range(1, len(x), 2):
            compact.append(16 * x[i] + x[i + 1])

    return compact


def map_keys(
    obj: Mapping[Bytes, Node], secured: bool = True
) -> Mapping[Bytes, Node]:
    """
    Maps all compact keys to nibble-list format. Optionally hashes the keys.

    Parameters
    ----------
    obj : `Dict[Bytes, T]`
        Underlying trie key-value pairs.
    secured : `bool`
        Denotes whether the keys should be hashed. Defaults to `true`.

    Returns
    -------
    out : `Mapping[Bytes, T]`
        Object with keys mapped to nibble-byte form.
    """
    mapped: MutableMapping[Bytes, Node] = {}

    # skip empty values, these are defined to be omitted from the trie
    skip: Set[Bytes] = set()
    for (k, v) in obj.items():
        if v == b"":
            skip.add(k)

    for (preimage, value) in obj.items():
        if preimage in skip:
            continue

        # "secure" tries hash keys once before construction
        key = crypto.keccak256(preimage) if secured else preimage

        nibble_list = bytearray(2 * len(key))
        for i in range(2 * len(key)):
            byte_idx = i // 2
            if i % 2 == 0:
                # get upper nibble
                nibble_list[i] = (key[byte_idx] & 0xF0) >> 4
            else:
                # get lower nibble
                nibble_list[i] = key[byte_idx] & 0x0F

        mapped[Bytes(nibble_list)] = value

    return mapped


def root(obj: Mapping[Bytes, Node]) -> Root:
    """
    Computes the root of a modified merkle patricia trie (MPT).

    Parameters
    ----------
    obj : `Mapping[Bytes, Union[Bytes, Account, Receipt, Uint, U256]]`
        Underlying trie key-value pairs.

    Returns
    -------
    root : `eth1spec.eth_types.Root`
        MPT root of the underlying key-value pairs.
    """
    root_node = patricialize(obj, Uint(0))
    return crypto.keccak256(rlp.encode(root_node))


def node_cap(obj: Mapping[Bytes, Node], i: Uint) -> rlp.RLP:
    """
    Internal nodes less than 32 bytes in length are represented by themselves
    directly. Larger nodes are hashed once to cap their size to 32 bytes.

    Parameters
    ----------
    obj : `Mapping[Bytes, Union[Bytes, Account, Receipt, Uint, U256]]`
        Underlying trie key-value pairs.
    i : `eth1spec.eth_types.U256`
        Current trie level.

    Returns
    -------
    hash : `eth1spec.eth_types.Hash32`
        Internal node commitment.
    """
    if len(obj) == 0:
        return b""
    node = patricialize(obj, i)
    encoded = rlp.encode(node)
    if len(encoded) < 32:
        return node

    return crypto.keccak256(encoded)


def patricialize(obj: Mapping[Bytes, Node], i: Uint) -> rlp.RLP:
    """
    Structural composition function.

    Used to recursively patricialize and merkleize a dictionary. Includes
    memoization of the tree structure and hashes.

    Parameters
    ----------
    obj : `Mapping[Bytes, Union[Bytes, Account, Receipt, Uint, U256]]`
        Underlying trie key-value pairs.
    i : `eth1spec.eth_types.Uint`
        Current trie level.

    Returns
    -------
    node : `eth1spec.eth_types.Bytes`
        Root node of `obj`.
    """
    if len(obj) == 0:
        # note: empty storage tree has merkle root:
        #
        #   crypto.keccak256(RLP(b''))
        #       ==
        #   56e81f171bcc55a6ff8345e692c0f86e5b48e01b996cadc001622fb5e363b421 # noqa: E501,SC100
        #
        # also:
        #
        #   crypto.keccak256(RLP(()))
        #       ==
        #   1dcc4de8dec75d7aab85b567b6ccd41ad312451b948a7413f0a142fd40d49347 # noqa: E501,SC100
        #
        # which is the sha3Uncles hash in block header for no uncles

        return b""

    key = next(iter(obj))  # get first key, will reuse below

    # if leaf node
    if len(obj) == 1:
        leaf = obj[key]
        node: rlp.RLP

        if isinstance(leaf, Account):
            node = rlp.encode(
                (
                    leaf.nonce,
                    leaf.balance,
                    root(map_keys(leaf.storage)),
                    crypto.keccak256(leaf.code),
                )
            )
        elif isinstance(leaf, Receipt):
            node = rlp.encode(
                (
                    leaf.post_state,
                    leaf.cumulative_gas_used,
                    leaf.bloom,
                    leaf.logs,
                )
            )
        else:
            node = leaf

        return (nibble_list_to_compact(key[i:], True), node)

    # prepare for extension node check by finding max j such that all keys in
    # obj have the same key[i:j]
    substring = copy(key)
    j = Uint(len(substring))
    for key in obj:
        j = min(j, Uint(len(key)))
        substring = substring[:j]
        for x in range(i, j):
            # mismatch -- reduce j to best previous value
            if key[x] != substring[x]:
                j = Uint(x)
                substring = substring[:j]
                break
        # finished searching, found another key at the current level
        if i == j:
            break

    # if extension node
    if i != j:
        child = node_cap(obj, j)
        return (nibble_list_to_compact(key[i:j], False), child)

    # otherwise branch node
    def build_branch(j: int) -> rlp.RLP:
        branch = {}
        skip = {}
        for (k, v) in obj.items():
            if len(k) <= i:
                skip[k] = True
            if k in skip:
                continue
            if k[i] == j:
                branch[k] = v

        return node_cap(branch, i + 1)

    value: Bytes = b""
    for key in obj:
        if len(key) == i:
            # shouldn't ever have an account or receipt in an internal node
            if isinstance(obj[key], (Account, Receipt, Uint)):
                raise TypeError()
            value = cast(Bytes, obj[key])
            break

    return [build_branch(k) for k in range(16)] + [value]
