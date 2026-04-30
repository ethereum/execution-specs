"""
Test_point_at_infinity_ec_recover.

Ported from:
state_tests/stTransactionTest/PointAtInfinityECRecoverFiller.yml
"""

import pytest
from execution_testing import (
    EOA,
    Account,
    Address,
    Alloc,
    Bytes,
    Environment,
    StateTestFiller,
    Transaction,
)

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


@pytest.mark.ported_from(
    ["state_tests/stTransactionTest/PointAtInfinityECRecoverFiller.yml"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_point_at_infinity_ec_recover(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test_point_at_infinity_ec_recover."""
    coinbase = Address(0x2ADC25665018AA1FE0E6BC666DAC8FC2697FF9BA)
    sender = EOA(
        key=0xE04D1AC7DDDA0C98397D56A0B501E960D4CD325A39286919AC23C1A07009A869
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=89128960,
    )

    pre[sender] = Account(balance=0xDE0B6B3A7640000)
    # Source: yul
    # berlin { mstore(0, 0x6b8d2c81b11b2d699528dde488dbdf2f94293d0d33c32e347f255fa4a6c1f0a9) mstore(32, 0x1b) mstore(64, 0x79be667ef9dcbbac55a06295ce870b07029bfcdb2dce28d959f2815b16f81798) mstore(96, 0x6b8d2c81b11b2d699528dde488dbdf2f94293d0d33c32e347f255fa4a6c1f0a9) sstore(0, call(1000000, 1, 0, 0, 128, 0, 32)) sstore(1, mload(0)) }  # noqa: E501
    target = pre.deploy_contract(  # noqa: F841
        code=bytes.fromhex(
            "6000805160206065833981519152600052601b6020527f79be667ef9dcbbac55a06295ce870b07029bfcdb2dce28d959f2815b16f81798604052600080516020606583398151915260605260206000608081806001620f4240f160005560005160015500fe6b8d2c81b11b2d699528dde488dbdf2f94293d0d33c32e347f255fa4a6c1f0a9"  # noqa: E501
        ),
        balance=0xFFFFFFFF,
        nonce=0,
        address=Address(0xB9F36F1CB467544974BB7E0F5E1F0A499D4E6D7D),  # noqa: E501
    )

    tx = Transaction(
        sender=sender,
        to=target,
        data=Bytes(""),
        gas_limit=10000000,
    )

    post = {
        sender: Account(nonce=1),
        target: Account(
            storage={
                0: 1,
                1: 0x6B8D2C81B11B2D699528DDE488DBDF2F94293D0D33C32E347F255FA4A6C1F0A9,  # noqa: E501
            },
            nonce=0,
        ),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
