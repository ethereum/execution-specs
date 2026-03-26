"""
Ori Pomerantz qbzzt1@gmail.com

Ported from:
state_tests/VMTests/vmArithmeticTest/fibFiller.yml
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
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"

REFERENCE_SPEC_VERSION = "N/A"


@pytest.mark.ported_from(
    ["state_tests/VMTests/vmArithmeticTest/fibFiller.yml"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_fib(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Ori Pomerantz qbzzt1@gmail."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = EOA(
        key=0x40ac0fc28c27e961ee46ec43355a094de205856edbd4654cf2577c2608d4ec1e
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        difficulty=0x20000,
        base_fee_per_gas=10,
        gas_limit=100000000,
    )

    # Source: lll
    # {  
    #    (def 'fib (n) [[n]] (+ @@(- n 1) @@(- n 2)))
    #    (fib  2)
    #    (fib  3)
    #    (fib  4)
    #    (fib  5)
    #    (fib  6)
    #    (fib  7)
    #    (fib  8)
    #    (fib  9)
    #    (fib 10)
    # }
    target = pre.deploy_contract(
        code=Op.SSTORE(key=0x2, value=Op.ADD(Op.SLOAD(key=Op.SUB(0x2, 0x1)), Op.SLOAD(key=Op.SUB(0x2, 0x2))))  # noqa: E501
        + Op.SSTORE(key=0x3, value=Op.ADD(Op.SLOAD(key=Op.SUB(0x3, 0x1)), Op.SLOAD(key=Op.SUB(0x3, 0x2))))  # noqa: E501
        + Op.SSTORE(key=0x4, value=Op.ADD(Op.SLOAD(key=Op.SUB(0x4, 0x1)), Op.SLOAD(key=Op.SUB(0x4, 0x2))))  # noqa: E501
        + Op.SSTORE(key=0x5, value=Op.ADD(Op.SLOAD(key=Op.SUB(0x5, 0x1)), Op.SLOAD(key=Op.SUB(0x5, 0x2))))  # noqa: E501
        + Op.SSTORE(key=0x6, value=Op.ADD(Op.SLOAD(key=Op.SUB(0x6, 0x1)), Op.SLOAD(key=Op.SUB(0x6, 0x2))))  # noqa: E501
        + Op.SSTORE(key=0x7, value=Op.ADD(Op.SLOAD(key=Op.SUB(0x7, 0x1)), Op.SLOAD(key=Op.SUB(0x7, 0x2))))  # noqa: E501
        + Op.SSTORE(key=0x8, value=Op.ADD(Op.SLOAD(key=Op.SUB(0x8, 0x1)), Op.SLOAD(key=Op.SUB(0x8, 0x2))))  # noqa: E501
        + Op.SSTORE(key=0x9, value=Op.ADD(Op.SLOAD(key=Op.SUB(0x9, 0x1)), Op.SLOAD(key=Op.SUB(0x9, 0x2))))  # noqa: E501
        + Op.SSTORE(key=0xa, value=Op.ADD(Op.SLOAD(key=Op.SUB(0xa, 0x1)), Op.SLOAD(key=Op.SUB(0xa, 0x2))))  # noqa: E501
        + Op.STOP,
        storage={0: 0, 1: 1},
        balance=0xba1a9ce0ba1a9ce,
        nonce=0,
        address=Address("0xf8d9ff3e0cf16acf51098c85f2cb8f082ef588c2"),  # noqa: E501
    )
    pre[sender] = Account(balance=0xba1a9ce0ba1a9ce)


    tx = Transaction(
        sender=sender,
        to=target,
        data=bytes.fromhex("01"),
        gas_limit=16777216,
        value=1,
        nonce=0,
        gas_price=10,
    )

    post = {
        target: Account(
                storage={
            0: 0,
            1: 1,
            2: 1,
            3: 2,
            4: 3,
            5: 5,
            6: 8,
            7: 13,
            8: 21,
            9: 34,
            10: 55,
        },
            ),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
