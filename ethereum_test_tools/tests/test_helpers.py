"""
Test suite for `ethereum_test.helpers` module.
"""

import pytest

from ..common import compute_create2_address, compute_create_address, to_address


def test_to_address():
    """
    Test `ethereum_test.helpers.to_address`.
    """
    assert to_address("0x0") == "0x0000000000000000000000000000000000000000"
    assert to_address(0) == "0x0000000000000000000000000000000000000000"
    assert to_address(1) == "0x0000000000000000000000000000000000000001"
    assert to_address("10") == "0x000000000000000000000000000000000000000a"
    assert to_address("0x10") == "0x0000000000000000000000000000000000000010"
    assert to_address(2 ** (20 * 8) - 1) == "0xffffffffffffffffffffffffffffffffffffffff"


@pytest.mark.parametrize(
    "address,nonce,expected_contract_address",
    [
        pytest.param(
            "0x00caa64684700d2825da7cac6ba0c6ed9fd2a1bb",
            0,
            "0x863df6bfa4469f3ead0be8f9f2aae51c91a907b4",
            id="zero-nonce-0x-str-address",
        ),
        pytest.param(
            "00caa64684700d2825da7cac6ba0c6ed9fd2a1bb",
            0,
            "0x863df6bfa4469f3ead0be8f9f2aae51c91a907b4",
            id="zero-nonce-str-address",
        ),
        pytest.param(
            int("0x00caa64684700d2825da7cac6ba0c6ed9fd2a1bb", 16),
            0,
            "0x863df6bfa4469f3ead0be8f9f2aae51c91a907b4",
            id="zero-nonce-int-address",
        ),
        pytest.param(
            "0x9c33eacc2f50e39940d3afaf2c7b8246b681a374",
            3,
            "0x7a250d5630b4cf539739df2c5dacb4c659f2488d",
            id="non-zero-nonce-0x-str-address",
        ),
        pytest.param(
            "0xba52c75764d6f594735dc735be7f1830cdf58ddf",
            3515,
            "0x06012c8cf97bead5deae237070f9587f8e7a266d",
            id="large-nonce-0x-str-address",
            marks=pytest.mark.xfail(
                reason="Nonce too large to convert with hard-coded to_bytes " "length of 1"
            ),
        ),
    ],
)
def test_compute_create_address(address: str | int, nonce: int, expected_contract_address: str):
    """
    Test `ethereum_test.helpers.compute_create_address` with some famous
    contracts:
    - https://etherscan.io/address/0x863df6bfa4469f3ead0be8f9f2aae51c91a907b4
    - https://etherscan.io/address/0x7a250d5630b4cf539739df2c5dacb4c659f2488d
    - https://etherscan.io/address/0x06012c8cf97bead5deae237070f9587f8e7a266d

    """
    assert compute_create_address(address, nonce) == expected_contract_address


@pytest.mark.parametrize(
    "address,salt,initcode,expected_contract_address",
    [
        pytest.param(
            "0x0000000000000000000000000000000000000000",
            "0x0000000000000000000000000000000000000000",
            "0x00",
            "0x4d1a2e2bb4f88f0250f26ffff098b0b30b26bf38",
        ),
        pytest.param(
            "0xdeadbeef00000000000000000000000000000000",
            "0x0000000000000000000000000000000000000000",
            "0x00",
            "0xB928f69Bb1D91Cd65274e3c79d8986362984fDA3",
        ),
        pytest.param(
            "0xdeadbeef00000000000000000000000000000000",
            "0xfeed000000000000000000000000000000000000",
            "0x00",
            "0xD04116cDd17beBE565EB2422F2497E06cC1C9833",
        ),
        pytest.param(
            "0x0000000000000000000000000000000000000000",
            "0x0000000000000000000000000000000000000000",
            "0xdeadbeef",
            "0x70f2b2914A2a4b783FaEFb75f459A580616Fcb5e",
        ),
        pytest.param(
            "0x00000000000000000000000000000000deadbeef",
            "0xcafebabe",
            "0xdeadbeef",
            "0x60f3f640a8508fC6a86d45DF051962668E1e8AC7",
        ),
        pytest.param(
            "0x00000000000000000000000000000000deadbeef",
            "0xcafebabe",
            (
                "0xdeadbeefdeadbeefdeadbeefdeadbeefdeadbeefdeadbeef"
                "deadbeefdeadbeefdeadbeefdeadbeefdeadbeef"
            ),
            "0x1d8bfDC5D46DC4f61D6b6115972536eBE6A8854C",
        ),
        pytest.param(
            "0x0000000000000000000000000000000000000000",
            "0x0000000000000000000000000000000000000000",
            "0x",
            "0xE33C0C7F7df4809055C3ebA6c09CFe4BaF1BD9e0",
        ),
    ],
)
def test_compute_create2_address(
    address: str | int,
    salt: str,
    initcode: str,
    expected_contract_address: str,
):
    """
    Test `ethereum_test.helpers.compute_create2_address` using the CREATE2 geth
    test cases from:
    https://github.com/ethereum/go-ethereum/blob/2189773093b2fe6d161b6477589f964470ff5bce/core/vm/instructions_test.go

    Note: `compute_create2_address` does not generate checksum addresses; s
    """
    salt_as_int = int(salt, 16)
    initcode_as_bytes = bytes.fromhex(initcode[2:])
    assert (
        compute_create2_address(address, salt_as_int, initcode_as_bytes)
        == expected_contract_address.lower()
    )
