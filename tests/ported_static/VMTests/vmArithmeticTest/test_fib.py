"""
Ori Pomerantz qbzzt1@gmail.com.

Ported from:
tests/static/state_tests/VMTests/vmArithmeticTest/fibFiller.yml
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
    ["tests/static/state_tests/VMTests/vmArithmeticTest/fibFiller.yml"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_fib(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Ori Pomerantz qbzzt1@gmail.com."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
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

    pre[sender] = Account(balance=0xBA1A9CE0BA1A9CE)
    # Source: LLL
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
    contract = pre.deploy_contract(
        code=(
            Op.SSTORE(
                key=0x2,
                value=Op.ADD(
                    Op.SLOAD(key=Op.SUB(0x2, 0x1)),
                    Op.SLOAD(key=Op.SUB(0x2, 0x2)),
                ),
            )
            + Op.SSTORE(
                key=0x3,
                value=Op.ADD(
                    Op.SLOAD(key=Op.SUB(0x3, 0x1)),
                    Op.SLOAD(key=Op.SUB(0x3, 0x2)),
                ),
            )
            + Op.SSTORE(
                key=0x4,
                value=Op.ADD(
                    Op.SLOAD(key=Op.SUB(0x4, 0x1)),
                    Op.SLOAD(key=Op.SUB(0x4, 0x2)),
                ),
            )
            + Op.SSTORE(
                key=0x5,
                value=Op.ADD(
                    Op.SLOAD(key=Op.SUB(0x5, 0x1)),
                    Op.SLOAD(key=Op.SUB(0x5, 0x2)),
                ),
            )
            + Op.SSTORE(
                key=0x6,
                value=Op.ADD(
                    Op.SLOAD(key=Op.SUB(0x6, 0x1)),
                    Op.SLOAD(key=Op.SUB(0x6, 0x2)),
                ),
            )
            + Op.SSTORE(
                key=0x7,
                value=Op.ADD(
                    Op.SLOAD(key=Op.SUB(0x7, 0x1)),
                    Op.SLOAD(key=Op.SUB(0x7, 0x2)),
                ),
            )
            + Op.SSTORE(
                key=0x8,
                value=Op.ADD(
                    Op.SLOAD(key=Op.SUB(0x8, 0x1)),
                    Op.SLOAD(key=Op.SUB(0x8, 0x2)),
                ),
            )
            + Op.SSTORE(
                key=0x9,
                value=Op.ADD(
                    Op.SLOAD(key=Op.SUB(0x9, 0x1)),
                    Op.SLOAD(key=Op.SUB(0x9, 0x2)),
                ),
            )
            + Op.SSTORE(
                key=0xA,
                value=Op.ADD(
                    Op.SLOAD(key=Op.SUB(0xA, 0x1)),
                    Op.SLOAD(key=Op.SUB(0xA, 0x2)),
                ),
            )
            + Op.STOP
        ),
        storage={0x0: 0x0, 0x1: 0x1},
        balance=0xBA1A9CE0BA1A9CE,
        nonce=0,
        address=Address("0xf8d9ff3e0cf16acf51098c85f2cb8f082ef588c2"),  # noqa: E501
    )

    tx = Transaction(
        sender=sender,
        to=contract,
        data=bytes.fromhex("01"),
        gas_limit=16777216,
        value=1,
    )

    post = {
        contract: Account(
            storage={
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
