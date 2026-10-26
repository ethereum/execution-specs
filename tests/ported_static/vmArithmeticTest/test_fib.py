"""
Ori Pomerantz qbzzt1@gmail.com.

Ported from:
state_tests/VMTests/vmArithmeticTest/fibFiller.yml
"""

import pytest
from execution_testing import (
    Account,
    Alloc,
    Bytes,
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
def test_fib(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Ori Pomerantz qbzzt1@gmail."""
    sender = pre.fund_eoa(amount=0xBA1A9CE0BA1A9CE)

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
    )

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

    state_test(pre=pre, post=post, tx=tx)
