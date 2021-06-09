from eth1spec.eth_types import (
    U256,
    Address,
    Bytes,
    Bytes8,
    Bytes32,
    Hash32,
    Root,
    Uint,
)


def hex2bytes(x: str) -> Bytes:
    return bytes.fromhex(remove_hex_prefix(x))


def hex2bytes8(x: str) -> Bytes8:
    return Bytes8(bytes.fromhex(remove_hex_prefix(x).rjust(16, "0")))


def hex2bytes32(x: str) -> Bytes32:
    return Bytes32(bytes.fromhex(remove_hex_prefix(x)))


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


def remove_hex_prefix(x):
    if x.startswith("0x"):
        return x[len("0x") :]
    return x
