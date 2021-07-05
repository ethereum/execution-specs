from typing import Any

from ethereum import crypto, rlp
from ethereum.base_types import Uint
from ethereum.eth_types import (
    U256,
    Address,
    Bytes,
    Bytes8,
    Bytes32,
    Hash32,
    Root,
)


def to_bytes(x: str) -> Bytes:
    if x is None:
        return b""
    if has_hex_prefix(x):
        return hex2bytes(x)
    return x.encode()


def hex2bytes(x: str) -> Bytes:
    return bytes.fromhex(remove_hex_prefix(x))


def hex2bytes8(x: str) -> Bytes8:
    return Bytes8(bytes.fromhex(remove_hex_prefix(x).rjust(16, "0")))


def hex2bytes32(x: str) -> Bytes32:
    return Bytes32(bytes.fromhex(remove_hex_prefix(x).rjust(64, "0")))


def hex2hash(x: str) -> Hash32:
    return Hash32(bytes.fromhex(remove_hex_prefix(x)))


def hex2root(x: str) -> Root:
    return Root(bytes.fromhex(remove_hex_prefix(x)))


def hex2address(x: str) -> Address:
    return Address(bytes.fromhex(remove_hex_prefix(x).rjust(40, "0")))


def hex2uint(x: str) -> Uint:
    return Uint(int(x, 16))


def hex2u256(x: str) -> U256:
    return U256(int(x, 16))


def has_hex_prefix(x: str) -> bool:
    return x.startswith("0x")


def remove_hex_prefix(x: str) -> str:
    if has_hex_prefix(x):
        return x[len("0x") :]
    return x


def rlp_hash(x: Any) -> Bytes:
    return crypto.keccak256(rlp.encode(x))
