"""
test_point_at_infinity_ec_recover

Ported from:
state_tests/stTransactionTest/PointAtInfinityECRecoverFiller.yml
"""

import pytest
from execution_testing import (
    EOA,
    Account,
    Address,
    Alloc,
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
    """test_point_at_infinity_ec_recover"""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = EOA(
        key=0xe04d1ac7ddda0c98397d56a0b501e960d4cd325a39286919ac23c1a07009a869
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        difficulty=0x20000,
        base_fee_per_gas=10,
        gas_limit=89128960,
    )

    # Source: yul
    # berlin { mstore(0, 0x6b8d2c81b11b2d699528dde488dbdf2f94293d0d33c32e347f255fa4a6c1f0a9) mstore(32, 0x1b) mstore(64, 0x79be667ef9dcbbac55a06295ce870b07029bfcdb2dce28d959f2815b16f81798) mstore(96, 0x6b8d2c81b11b2d699528dde488dbdf2f94293d0d33c32e347f255fa4a6c1f0a9) sstore(0, call(1000000, 1, 0, 0, 128, 0, 32)) sstore(1, mload(0)) }
    target = pre.deploy_contract(
        code=bytes.fromhex("6000805160206065833981519152600052601b6020527f79be667ef9dcbbac55a06295ce870b07029bfcdb2dce28d959f2815b16f81798604052600080516020606583398151915260605260206000608081806001620f4240f160005560005160015500fe6b8d2c81b11b2d699528dde488dbdf2f94293d0d33c32e347f255fa4a6c1f0a9"),  # noqa: E501
        balance=0xffffffff,
        nonce=0,
        address=Address("0xb9f36f1cb467544974bb7e0f5e1f0a499d4e6d7d"),  # noqa: E501
    )
    pre[sender] = Account(balance=0xde0b6b3a7640000)


    tx = Transaction(
        sender=sender,
        to=target,
        data=b'',
        gas_limit=10000000,
        nonce=0,
        gas_price=10,
    )

    post = {
        sender: Account(nonce=1),
        target: Account(
                storage={
            0: 1,
            1: 0x6b8d2c81b11b2d699528dde488dbdf2f94293d0d33c32e347f255fa4a6c1f0a9,
        },
                nonce=0,
            ),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
