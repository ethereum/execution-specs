import pkgutil
from typing import List, cast

import pytest

from ethereum import rlp
from ethereum.base_types import U256, Bytes
from ethereum.genesis import get_genesis_configuration
from ethereum.utils.byte import left_pad_zero_bytes

MAINNET_GENESIS_CONFIGURATION = get_genesis_configuration("mainnet.json")


@pytest.fixture
def mainnet_alloc_rlp_encoding() -> bytes:
    rlp_encoding_hex = cast(
        bytes,
        pkgutil.get_data("ethereum", "assets/mainnet_genesis_alloc_rlp.hex"),
    ).decode()

    return bytes.fromhex(rlp_encoding_hex)


def test_mainnet_alloc_rlp_encoding(mainnet_alloc_rlp_encoding: bytes) -> None:
    # Test RLP encoding of alloc is expected hex value
    alloc_rlp_encoding = rlp.encode(
        [
            [U256.from_be_bytes(address), balance]
            for address, balance in MAINNET_GENESIS_CONFIGURATION.initial_balances.items()
        ]
    )

    assert alloc_rlp_encoding == mainnet_alloc_rlp_encoding


def test_rlp_decode_mainnet_alloc_rlp_encoding(
    mainnet_alloc_rlp_encoding: bytes,
) -> None:
    # Test RLP decoding of the hex is the expected alloc
    decoded_alloc = cast(
        List[List[Bytes]], rlp.decode(mainnet_alloc_rlp_encoding)
    )
    obtained_alloc = {
        left_pad_zero_bytes(addr, 20): U256.from_be_bytes(balance)
        for (addr, balance) in decoded_alloc
    }

    assert obtained_alloc == MAINNET_GENESIS_CONFIGURATION.initial_balances


def test_mainnet_genesis_config() -> None:
    # Test that mainnet genesis parameters are as expected
    assert MAINNET_GENESIS_CONFIGURATION.difficulty == int("400000000", 16)
    assert MAINNET_GENESIS_CONFIGURATION.extra_data == bytes.fromhex(
        "11bbe8db4e347b4e8c937c1c8370e4b5ed33adb3db69cbdb7a38e1e50b1b82fa"
    )
    assert MAINNET_GENESIS_CONFIGURATION.gas_limit == 5000
    assert (
        MAINNET_GENESIS_CONFIGURATION.nonce
        == b"\x00\x00\x00\x00\x00\x00\x00\x42"
    )
    assert MAINNET_GENESIS_CONFIGURATION.timestamp == 0
