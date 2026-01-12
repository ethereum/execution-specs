"""
Tests for the sigrecover precompile.
"""

import pytest
from coincurve.keys import PrivateKey
from execution_testing import (
    Account,
    Alloc,
    Environment,
    StateTestFiller,
    Transaction,
)
from execution_testing.base_types.base_types import Address
from execution_testing.base_types.constants import TestAddress
from execution_testing.vm import Op

from ethereum.crypto.hash import keccak256

from . import (  # noqa: F401
    EIP7932_FORK_NAME,
    REFERENCE_SPEC_GIT_PATH,
    REFERENCE_SPEC_VERSION,
    SIGRECOVER_ADDRESS,
)

INVALID = b"\x00" * 32

secp256k1_test_key = PrivateKey(
    secret=bytes.fromhex(
        "1f7627096fa44f0b850f5d9a859d271723ee856e526b947d0d4b011168bdcac1"
    )
)

address = b"\x00" * 12 + bytes.fromhex(
    "d3eF791e8a9c9BD26787D262e66e673FE8E7262A"
)

zero_sig = secp256k1_test_key.sign_recoverable(b"\x00" * 32, hasher=None)
deadbeef_sig = secp256k1_test_key.sign_recoverable(
    bytes.fromhex("deadbeef"), hasher=keccak256
)

# Dutifully liberated from https://eips.ethereum.org/assets/eip-7932/precompile_test_cases.py
test_cases = [
    #
    # Invalid algorithm
    #
    # No data
    ("no_data", "", INVALID, 3000),
    # Invalid algorithm (without data)
    ("invalid_algorithm_without_data", b"\xfe".hex(), INVALID, 3000),
    # Invalid algorithm (with data at secp256k1 size)
    (
        "invalid_algorithm_with_secp256k1_sized_data",
        (b"\xfe" + b"\x01" * 65 + b"\x00" * 32).hex(),
        INVALID,
        3000,
    ),
    # Invalid algorithm (with data greater than secp256k1 size)
    (
        "invalid_algorithm_with_larger_than_secp256k1_data",
        (b"\xfe" + b"\x01" * 66 + b"\x00" * 32).hex(),
        INVALID,
        3000,
    ),
    #
    # secp256k1
    #
    # secp256k1 (without data)
    ("secp256k1_no_data", (b"\xff").hex(), INVALID, 3000),
    # secp256k1 (too little data)
    (
        "secp256k1_little_data",
        (b"\xff" + b"\xfe" * 64 + b"\x00" * 32).hex(),
        INVALID,
        3036,
    ),
    # secp256k1 (erroneous data)
    (
        "secp256k1_erroneous_data",
        (b"\xff" + b"\xfe" * 67 + b"\x00" * 32).hex(),
        INVALID,
        3042,
    ),
    # secp256k1 (invalid signature)
    (
        "secp256k1_bad_signature",
        (b"\xff" + b"\xfe" * 65 + b"\x00" * 32).hex(),
        INVALID,
        3000,
    ),
    # secp256k1 (valid signature)
    (
        "secp256k1_valid_signature",
        (b"\xff" + zero_sig + b"\x00" * 32).hex(),
        address,
        3000,
    ),
    # secp256k1 (invalid signature + non 32 byte signing data size)
    (
        "secp256k1_invalid_signature_non_normal_signing_data",
        (b"\xff" + b"\xfe" * 65 + b"\x00" * 30).hex(),
        INVALID,
        3036,
    ),
    # secp256k1 (valid signature + non 32 byte signing data size)
    (
        "secp256k1_valid_signature_non_normal_signing_data",
        (b"\xff" + deadbeef_sig + bytes.fromhex("deadbeef")).hex(),
        address,
        3036,
    ),
]


@pytest.mark.valid_from(EIP7932_FORK_NAME)
@pytest.mark.parametrize(
    "input_data,expected_address,expected_gas",
    [x[1:] for x in test_cases],
    ids=[x[0] for x in test_cases],
)
def test_sigrecover_gas_and_validity(
    state_test: StateTestFiller,
    pre: Alloc,
    input_data: bytes,
    expected_address: Address,
    expected_gas: int,
) -> None:
    """
    Test sigrecover for gas & address validity.
    """
    env = Environment()

    pre.fund_address(
        TestAddress,
        10000000,
    )

    tester_contract = pre.deploy_contract(
        (
            # Copy all the calldata to memory
            Op.CALLDATACOPY(0, 0, Op.CALLDATASIZE)
            # Store the return code of a bad gas value
            # to storage slot 0
            + Op.SSTORE(
                0,
                Op.CALL(
                    Op.SUB(expected_gas, 1),
                    SIGRECOVER_ADDRESS,
                    0,
                    0,
                    Op.CALLDATASIZE,
                    Op.CALLDATASIZE,
                    Op.ADD(Op.CALLDATASIZE, 0x20),
                ),
            )
            # Store the return code of good call
            # to storage slot 1
            + Op.SSTORE(
                1,
                Op.CALL(
                    expected_gas,
                    SIGRECOVER_ADDRESS,
                    0,
                    0,
                    Op.CALLDATASIZE,
                    Op.CALLDATASIZE,
                    Op.ADD(Op.CALLDATASIZE, 0x20),
                ),
            )
            # Store the return data to storage slot 2
            + Op.SSTORE(2, Op.MLOAD(Op.CALLDATASIZE))
            # Stop
            + Op.STOP()
        )
    )

    tx = Transaction(  # type: ignore
        ty=0x0,
        nonce=0,
        to=tester_contract,
        input=input_data,
        gas_limit=1000000,
        gas_price=10,
        protected=False,
    )

    post = {}
    post[tester_contract] = Account(storage={0: 0, 1: 1, 2: expected_address})
    state_test(env=env, pre=pre, post=post, tx=tx)
