"""
Ori Pomerantz qbzzt1@gmail.com.

Ported from:
state_tests/VMTests/vmArithmeticTest/expPower2Filler.yml
"""

import pytest
from execution_testing import (
    Account,
    Alloc,
    Bytes,
    Hash,
    StateTestFiller,
    Transaction,
)
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


@pytest.mark.ported_from(
    ["state_tests/VMTests/vmArithmeticTest/expPower2Filler.yml"],
)
@pytest.mark.valid_from("Cancun")
def test_exp_power2(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Ori Pomerantz qbzzt1@gmail."""
    sender = pre.fund_eoa(amount=0xBA1A9CE0BA1A9CE)

    # Source: lll
    # {
    #     (def 'storageJump 0x10)
    #
    #     (def 'calc (m) {
    #          (def 'n (exp 2 m))
    #
    #          [[(* storageJump m)]]       (exp 2 n)
    #          [[(+ (* storageJump m) 1)]] (exp 2 (- n 1))
    #          [[(+ (* storageJump m) 2)]] (exp 2 (+ n 1))
    #       }
    #     )
    #
    #     (calc 1)
    #     (calc 2)
    #     (calc 3)
    #     (calc 4)
    #     (calc 5)
    #     (calc 6)
    #     (calc 7)
    #     (calc 8)
    # }
    target = pre.deploy_contract(
        code=Op.SSTORE(
            key=Op.MUL(0x10, 0x1), value=Op.EXP(0x2, Op.EXP(0x2, 0x1))
        )
        + Op.SSTORE(
            key=Op.ADD(Op.MUL(0x10, 0x1), 0x1),
            value=Op.EXP(0x2, Op.SUB(Op.EXP(0x2, 0x1), 0x1)),
        )
        + Op.SSTORE(
            key=Op.ADD(Op.MUL(0x10, 0x1), 0x2),
            value=Op.EXP(0x2, Op.ADD(Op.EXP(0x2, 0x1), 0x1)),
        )
        + Op.SSTORE(key=Op.MUL(0x10, 0x2), value=Op.EXP(0x2, Op.EXP(0x2, 0x2)))
        + Op.SSTORE(
            key=Op.ADD(Op.MUL(0x10, 0x2), 0x1),
            value=Op.EXP(0x2, Op.SUB(Op.EXP(0x2, 0x2), 0x1)),
        )
        + Op.SSTORE(
            key=Op.ADD(Op.MUL(0x10, 0x2), 0x2),
            value=Op.EXP(0x2, Op.ADD(Op.EXP(0x2, 0x2), 0x1)),
        )
        + Op.SSTORE(key=Op.MUL(0x10, 0x3), value=Op.EXP(0x2, Op.EXP(0x2, 0x3)))
        + Op.SSTORE(
            key=Op.ADD(Op.MUL(0x10, 0x3), 0x1),
            value=Op.EXP(0x2, Op.SUB(Op.EXP(0x2, 0x3), 0x1)),
        )
        + Op.SSTORE(
            key=Op.ADD(Op.MUL(0x10, 0x3), 0x2),
            value=Op.EXP(0x2, Op.ADD(Op.EXP(0x2, 0x3), 0x1)),
        )
        + Op.SSTORE(key=Op.MUL(0x10, 0x4), value=Op.EXP(0x2, Op.EXP(0x2, 0x4)))
        + Op.SSTORE(
            key=Op.ADD(Op.MUL(0x10, 0x4), 0x1),
            value=Op.EXP(0x2, Op.SUB(Op.EXP(0x2, 0x4), 0x1)),
        )
        + Op.SSTORE(
            key=Op.ADD(Op.MUL(0x10, 0x4), 0x2),
            value=Op.EXP(0x2, Op.ADD(Op.EXP(0x2, 0x4), 0x1)),
        )
        + Op.SSTORE(key=Op.MUL(0x10, 0x5), value=Op.EXP(0x2, Op.EXP(0x2, 0x5)))
        + Op.SSTORE(
            key=Op.ADD(Op.MUL(0x10, 0x5), 0x1),
            value=Op.EXP(0x2, Op.SUB(Op.EXP(0x2, 0x5), 0x1)),
        )
        + Op.SSTORE(
            key=Op.ADD(Op.MUL(0x10, 0x5), 0x2),
            value=Op.EXP(0x2, Op.ADD(Op.EXP(0x2, 0x5), 0x1)),
        )
        + Op.SSTORE(key=Op.MUL(0x10, 0x6), value=Op.EXP(0x2, Op.EXP(0x2, 0x6)))
        + Op.SSTORE(
            key=Op.ADD(Op.MUL(0x10, 0x6), 0x1),
            value=Op.EXP(0x2, Op.SUB(Op.EXP(0x2, 0x6), 0x1)),
        )
        + Op.SSTORE(
            key=Op.ADD(Op.MUL(0x10, 0x6), 0x2),
            value=Op.EXP(0x2, Op.ADD(Op.EXP(0x2, 0x6), 0x1)),
        )
        + Op.SSTORE(key=Op.MUL(0x10, 0x7), value=Op.EXP(0x2, Op.EXP(0x2, 0x7)))
        + Op.SSTORE(
            key=Op.ADD(Op.MUL(0x10, 0x7), 0x1),
            value=Op.EXP(0x2, Op.SUB(Op.EXP(0x2, 0x7), 0x1)),
        )
        + Op.SSTORE(
            key=Op.ADD(Op.MUL(0x10, 0x7), 0x2),
            value=Op.EXP(0x2, Op.ADD(Op.EXP(0x2, 0x7), 0x1)),
        )
        + Op.SSTORE(key=Op.MUL(0x10, 0x8), value=Op.EXP(0x2, Op.EXP(0x2, 0x8)))
        + Op.SSTORE(
            key=Op.ADD(Op.MUL(0x10, 0x8), 0x1),
            value=Op.EXP(0x2, Op.SUB(Op.EXP(0x2, 0x8), 0x1)),
        )
        + Op.SSTORE(
            key=Op.ADD(Op.MUL(0x10, 0x8), 0x2),
            value=Op.EXP(0x2, Op.ADD(Op.EXP(0x2, 0x8), 0x1)),
        )
        + Op.STOP,
        balance=0xBA1A9CE0BA1A9CE,
    )

    tx = Transaction(
        sender=sender,
        to=target,
        data=Bytes("693c6139") + Hash(0x0),
        gas_limit=16777216,
        value=1,
    )

    post = {
        target: Account(
            storage={
                16: 4,
                17: 2,
                18: 8,
                32: 16,
                33: 8,
                34: 32,
                48: 256,
                49: 128,
                50: 512,
                64: 0x10000,
                65: 32768,
                66: 0x20000,
                80: 0x100000000,
                81: 0x80000000,
                82: 0x200000000,
                96: 0x10000000000000000,
                97: 0x8000000000000000,
                98: 0x20000000000000000,
                112: 0x100000000000000000000000000000000,
                113: 0x80000000000000000000000000000000,
                114: 0x200000000000000000000000000000000,
                129: 0x8000000000000000000000000000000000000000000000000000000000000000,  # noqa: E501
            },
        ),
    }

    state_test(pre=pre, post=post, tx=tx)
