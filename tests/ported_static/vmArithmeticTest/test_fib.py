"""
Ori Pomerantz qbzzt1@gmail.com.

Ported from:
state_tests/VMTests/vmArithmeticTest/fibFiller.yml
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
    coinbase = Address(0x2ADC25665018AA1FE0E6BC666DAC8FC2697FF9BA)
    sender = EOA(
        key=0x40AC0FC28C27E961EE46EC43355A094DE205856EDBD4654CF2577C2608D4EC1E
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
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
    target = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(
            key=0x2,
            value=Op.ADD(
                Op.SLOAD(key=Op.SUB(0x2, 0x1)), Op.SLOAD(key=Op.SUB(0x2, 0x2))
            ),
        )
        + Op.SSTORE(
            key=0x3,
            value=Op.ADD(
                Op.SLOAD(key=Op.SUB(0x3, 0x1)), Op.SLOAD(key=Op.SUB(0x3, 0x2))
            ),
        )
        + Op.SSTORE(
            key=0x4,
            value=Op.ADD(
                Op.SLOAD(key=Op.SUB(0x4, 0x1)), Op.SLOAD(key=Op.SUB(0x4, 0x2))
            ),
        )
        + Op.SSTORE(
            key=0x5,
            value=Op.ADD(
                Op.SLOAD(key=Op.SUB(0x5, 0x1)), Op.SLOAD(key=Op.SUB(0x5, 0x2))
            ),
        )
        + Op.SSTORE(
            key=0x6,
            value=Op.ADD(
                Op.SLOAD(key=Op.SUB(0x6, 0x1)), Op.SLOAD(key=Op.SUB(0x6, 0x2))
            ),
        )
        + Op.SSTORE(
            key=0x7,
            value=Op.ADD(
                Op.SLOAD(key=Op.SUB(0x7, 0x1)), Op.SLOAD(key=Op.SUB(0x7, 0x2))
            ),
        )
        + Op.SSTORE(
            key=0x8,
            value=Op.ADD(
                Op.SLOAD(key=Op.SUB(0x8, 0x1)), Op.SLOAD(key=Op.SUB(0x8, 0x2))
            ),
        )
        + Op.SSTORE(
            key=0x9,
            value=Op.ADD(
                Op.SLOAD(key=Op.SUB(0x9, 0x1)), Op.SLOAD(key=Op.SUB(0x9, 0x2))
            ),
        )
        + Op.SSTORE(
            key=0xA,
            value=Op.ADD(
                Op.SLOAD(key=Op.SUB(0xA, 0x1)), Op.SLOAD(key=Op.SUB(0xA, 0x2))
            ),
        )
        + Op.STOP,
        storage={0: 0, 1: 1},
        balance=0xBA1A9CE0BA1A9CE,
        nonce=0,
        address=Address(0xF8D9FF3E0CF16ACF51098C85F2CB8F082EF588C2),  # noqa: E501
    )
    pre[sender] = Account(balance=0xBA1A9CE0BA1A9CE)

    tx = Transaction(
        sender=sender,
        to=target,
        data=Bytes("01"),
        gas_limit=16777216,
        value=1,
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
