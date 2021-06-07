"""
State Trie
----------

The state trie is the structure responsible for storing
`eth1spec.eth_types.Account` objects.
"""

from typing import Mapping, Tuple, TypeVar, Union

from . import crypto, rlp
from .eth_types import U256, Account, Bytes, Bytes64, Receipt, Root, Uint

debug = False
verbose = False


def HP(x: Bytes, t: Union[bool, int]) -> bytearray:
    """
    Hex prefix encoding.

    Parameters
    ----------
    x : `eth1spec.eth_types.Bytes`
        Array of values less than 16.
    t : `Union[bool, int]`
        Any of `0`, `1`, `False`, or `True`.

    Returns
    -------
    encoded : `bytearray`
        TODO
    """
    if verbose:
        print("HP(", x, t, ")")
    # x = bytes([int(d,16) for d in x.hex()])
    encoded = bytearray()
    if len(x) % 2 == 0:  # ie even length
        encoded.append(16 * f(t))
        for i in range(0, len(x), 2):
            encoded.append(16 * x[i] + x[i + 1])
    else:
        encoded.append(16 * (f(t) + 1) + x[0])
        for i in range(1, len(x), 2):
            encoded.append(16 * x[i] + x[i + 1])
    if debug:
        print("HP() returning", encoded)
    return encoded


def f(t: Union[bool, int]) -> int:
    """
    Encodes `t` as a bit flag.

    Parameters
    ----------
    t : `Union[bool, int]`
        Arbitrary boolean.

    Returns
    -------
    flag : `int`
        `t` encoded as a bit flag.
    """
    if t:
        return 0b10
    else:
        return 0


def HP_inverse(buffer: Bytes) -> Tuple[str, bool]:
    """
    Hex prefix decoding.

    Parameters
    ----------
    buffer : `Bytes`
        TODO

    Returns
    -------
    nibbles : `str`
        Decoded prefix
    t : `bool`
        TODO
    """
    nibbles = ""
    odd_length = (buffer[0] >> 4) % 2 == 1  # sixth lowest bit
    t = (buffer[0] >> 5) % 2 != 0  # fifth lowest bit
    if odd_length:
        nibbles += buffer[0:1].hex()[1]
    for b in buffer[1:]:
        nibbles += bytes([b]).hex()
    return nibbles, t


T = TypeVar("T")


def y(J: Mapping[Bytes, T]) -> Mapping[Bytes64, T]:
    """
    TODO

    Parameters
    ----------
    J : `Dict[Bytes, Bytes]`
        TODO

    Returns
    -------
    TODO
    """
    yJ = {}
    for kn in J:
        kn_ = crypto.keccak256(kn)
        knprime = bytearray(2 * len(kn_))
        for i in range(2 * len(kn_)):
            if i % 2 == 0:  # even
                knprime[i] = kn_[i // 2] // 16
            else:
                knprime[i] = kn_[i // 2] % 16
        # print(kn.hex(),kn_.hex(),knprime.hex())
        yJ[bytes(knprime)] = J[kn]
    return yJ


def TRIE(J: Mapping[Bytes, Union[Account, Bytes, Receipt]]) -> Root:
    """
    Computes the root hash of the storage trie.

    Parameters
    ----------
    J : `Mapping[Bytes, Union[Bytes, Account, Receipt]]`
        TODO

    Returns
    -------
    root : `eth1spec.eth_types.Root`
        TODO
    """
    cJ0 = c(J, Uint(0))
    # print("cJ0",cJ0.hex())
    return crypto.keccak256(cJ0)


def n(J: Mapping[Bytes, Union[Bytes, Account, Receipt]], i: U256) -> Bytes:
    """
    Node composition function.

    Parameters
    ----------
    J : `Mapping[Bytes, Union[Bytes, Account, Receipt]]`
        TODO
    i : `eth1spec.eth_types.U256`
        TODO

    Returns
    -------
    hash : `eth1spec.eth_types.Hash32`
        TODO
    """
    # print("n(",i,")")
    if len(J) == 0:
        return b""
    cJi = c(J, i)
    if len(cJi) < 32:
        return cJi
    else:
        # print("cJi,crypto.keccak256(cJi)",cJi.hex(),crypto.keccak256(cJi).hex())
        return crypto.keccak256(cJi)


def c(J: Mapping[Bytes, Union[Bytes, Account, Receipt]], i: Uint) -> Bytes:
    """
    Structural composition function.

    Used to patricialize and merkleize a dictionary. Includes memoization of
    the tree structure and hashes.

    Parameters
    ----------
    J : `Mapping[Bytes, Union[Bytes, Account, Receipt]]`
        TODO
    i : `eth1spec.number.Uint`
        TODO

    Returns
    -------
    value : `eth1spec.eth_types.Bytes`
        TODO
    """
    # print("c(",J,i,")")
    # print("c(",i,")")

    if len(J) == 0:
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

        return rlp.encode(b"")

    I_0 = next(iter(J))  # get first key, will reuse below

    # if leaf node
    if len(J) == 1:
        leaf = J[I_0]
        if isinstance(leaf, Account):
            I_1 = rlp.encode(
                (
                    leaf.nonce,
                    leaf.balance,
                    TRIE(y(leaf.storage)),
                    crypto.keccak256(leaf.code),
                )
            )
        elif isinstance(leaf, Receipt):
            raise NotImplementedError()  # TODO
        else:
            # I_1 = leaf
            I_1 = rlp.encode(leaf)
            print("c() leaf", I_0.hex(), I_1.hex())
        # print(I_1.hex())
        value = rlp.encode((HP(I_0[i:], 1), I_1))
        # print("leaf rlp",rlp.hex(),crypto.keccak256(rlp).hex())
        return value

    # prepare for extension node check by finding max j such that all keys I in
    # J have the same I[i:j]
    elle = I_0[:]
    j = U256(len(elle))
    for I_0 in J:
        j = min(j, U256(len(I_0)))
        elle = elle[:j]
        for x in range(i, j):
            if I_0[x] != elle[x]:
                j = Uint(x)
                elle = elle[:j]
                break
        if i == j:
            break

    # if extension node
    if i != j:
        child = n(J, j)
        # print("extension,child",I_0[i:j].hex(),child.hex())
        value = rlp.encode((HP(I_0[i:j], 0), child))
        # print("extension rlp",rlp.hex(),crypto.keccak256(rlp).hex())
        return value

    # otherwise branch node
    def u(j: int) -> Bytes:
        # print("u(",j,")")
        # print([k.hex() for k in J.keys()])
        return n({I_0: I_1 for I_0, I_1 in J.items() if I_0[i] == j}, i + 1)

    v = b""
    for I_0 in J:
        if len(I_0) == i:
            J_I_0 = J[I_0]
            if isinstance(J_I_0, (Account, Receipt)):
                raise TypeError()  # TODO: Not sure if this is correct?
            v = J_I_0
            break
    # print("v",v)
    value = rlp.encode([u(k) for k in range(16)] + [v])
    # print("branch rlp",rlp.hex(),crypto.keccak256(rlp).hex())
    return value
