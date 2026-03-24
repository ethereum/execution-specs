"""
Ori Pomerantz qbzzt1@gmail.com.

Ported from:
tests/static/state_tests/VMTests/vmArithmeticTest/expPower256Of256Filler.yml
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
    [
        "tests/static/state_tests/VMTests/vmArithmeticTest/expPower256Of256Filler.yml",  # noqa: E501
    ],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_exp_power256_of256(
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
    #     (def 'storageJump 0x10)
    #
    #     (def 'calc (n) {
    #
    #          [[(* storageJump n)]]       (exp 256 (exp 256 n))
    #          [[(+ (* storageJump n) 1)]] (exp 256 (exp 255 n))
    #          [[(+ (* storageJump n) 2)]] (exp 256 (exp 257 n))
    #
    #          [[(+ (* storageJump n) 3)]] (exp 255 (exp 256 n))
    #          [[(+ (* storageJump n) 4)]] (exp 255 (exp 255 n))
    #          [[(+ (* storageJump n) 5)]] (exp 255 (exp 257 n))
    #
    #          [[(+ (* storageJump n) 6)]] (exp 257 (exp 256 n))
    #          [[(+ (* storageJump n) 7)]] (exp 257 (exp 255 n))
    #          [[(+ (* storageJump n) 8)]] (exp 257 (exp 257 n))
    #       }
    #     )
    #
    #     (calc 0)
    #     (calc 1)
    #     (calc 2)
    #     (calc 3)
    #     (calc 4)
    #     (calc 5)
    #     (calc 6)
    #     (calc 7)
    #     (calc 8)
    #     (calc 9)
    #     (calc 10)
    # ... (24 more lines)
    contract = pre.deploy_contract(
        code=(
            Op.SSTORE(
                key=Op.MUL(0x10, 0x0),
                value=Op.EXP(0x100, Op.EXP(0x100, 0x0)),
            )
            + Op.SSTORE(
                key=Op.ADD(Op.MUL(0x10, 0x0), 0x1),
                value=Op.EXP(0x100, Op.EXP(0xFF, 0x0)),
            )
            + Op.SSTORE(
                key=Op.ADD(Op.MUL(0x10, 0x0), 0x2),
                value=Op.EXP(0x100, Op.EXP(0x101, 0x0)),
            )
            + Op.SSTORE(
                key=Op.ADD(Op.MUL(0x10, 0x0), 0x3),
                value=Op.EXP(0xFF, Op.EXP(0x100, 0x0)),
            )
            + Op.SSTORE(
                key=Op.ADD(Op.MUL(0x10, 0x0), 0x4),
                value=Op.EXP(0xFF, Op.EXP(0xFF, 0x0)),
            )
            + Op.SSTORE(
                key=Op.ADD(Op.MUL(0x10, 0x0), 0x5),
                value=Op.EXP(0xFF, Op.EXP(0x101, 0x0)),
            )
            + Op.SSTORE(
                key=Op.ADD(Op.MUL(0x10, 0x0), 0x6),
                value=Op.EXP(0x101, Op.EXP(0x100, 0x0)),
            )
            + Op.SSTORE(
                key=Op.ADD(Op.MUL(0x10, 0x0), 0x7),
                value=Op.EXP(0x101, Op.EXP(0xFF, 0x0)),
            )
            + Op.SSTORE(
                key=Op.ADD(Op.MUL(0x10, 0x0), 0x8),
                value=Op.EXP(0x101, Op.EXP(0x101, 0x0)),
            )
            + Op.SSTORE(
                key=Op.MUL(0x10, 0x1),
                value=Op.EXP(0x100, Op.EXP(0x100, 0x1)),
            )
            + Op.SSTORE(
                key=Op.ADD(Op.MUL(0x10, 0x1), 0x1),
                value=Op.EXP(0x100, Op.EXP(0xFF, 0x1)),
            )
            + Op.SSTORE(
                key=Op.ADD(Op.MUL(0x10, 0x1), 0x2),
                value=Op.EXP(0x100, Op.EXP(0x101, 0x1)),
            )
            + Op.SSTORE(
                key=Op.ADD(Op.MUL(0x10, 0x1), 0x3),
                value=Op.EXP(0xFF, Op.EXP(0x100, 0x1)),
            )
            + Op.SSTORE(
                key=Op.ADD(Op.MUL(0x10, 0x1), 0x4),
                value=Op.EXP(0xFF, Op.EXP(0xFF, 0x1)),
            )
            + Op.SSTORE(
                key=Op.ADD(Op.MUL(0x10, 0x1), 0x5),
                value=Op.EXP(0xFF, Op.EXP(0x101, 0x1)),
            )
            + Op.SSTORE(
                key=Op.ADD(Op.MUL(0x10, 0x1), 0x6),
                value=Op.EXP(0x101, Op.EXP(0x100, 0x1)),
            )
            + Op.SSTORE(
                key=Op.ADD(Op.MUL(0x10, 0x1), 0x7),
                value=Op.EXP(0x101, Op.EXP(0xFF, 0x1)),
            )
            + Op.SSTORE(
                key=Op.ADD(Op.MUL(0x10, 0x1), 0x8),
                value=Op.EXP(0x101, Op.EXP(0x101, 0x1)),
            )
            + Op.SSTORE(
                key=Op.MUL(0x10, 0x2),
                value=Op.EXP(0x100, Op.EXP(0x100, 0x2)),
            )
            + Op.SSTORE(
                key=Op.ADD(Op.MUL(0x10, 0x2), 0x1),
                value=Op.EXP(0x100, Op.EXP(0xFF, 0x2)),
            )
            + Op.SSTORE(
                key=Op.ADD(Op.MUL(0x10, 0x2), 0x2),
                value=Op.EXP(0x100, Op.EXP(0x101, 0x2)),
            )
            + Op.SSTORE(
                key=Op.ADD(Op.MUL(0x10, 0x2), 0x3),
                value=Op.EXP(0xFF, Op.EXP(0x100, 0x2)),
            )
            + Op.SSTORE(
                key=Op.ADD(Op.MUL(0x10, 0x2), 0x4),
                value=Op.EXP(0xFF, Op.EXP(0xFF, 0x2)),
            )
            + Op.SSTORE(
                key=Op.ADD(Op.MUL(0x10, 0x2), 0x5),
                value=Op.EXP(0xFF, Op.EXP(0x101, 0x2)),
            )
            + Op.SSTORE(
                key=Op.ADD(Op.MUL(0x10, 0x2), 0x6),
                value=Op.EXP(0x101, Op.EXP(0x100, 0x2)),
            )
            + Op.SSTORE(
                key=Op.ADD(Op.MUL(0x10, 0x2), 0x7),
                value=Op.EXP(0x101, Op.EXP(0xFF, 0x2)),
            )
            + Op.SSTORE(
                key=Op.ADD(Op.MUL(0x10, 0x2), 0x8),
                value=Op.EXP(0x101, Op.EXP(0x101, 0x2)),
            )
            + Op.SSTORE(
                key=Op.MUL(0x10, 0x3),
                value=Op.EXP(0x100, Op.EXP(0x100, 0x3)),
            )
            + Op.SSTORE(
                key=Op.ADD(Op.MUL(0x10, 0x3), 0x1),
                value=Op.EXP(0x100, Op.EXP(0xFF, 0x3)),
            )
            + Op.SSTORE(
                key=Op.ADD(Op.MUL(0x10, 0x3), 0x2),
                value=Op.EXP(0x100, Op.EXP(0x101, 0x3)),
            )
            + Op.SSTORE(
                key=Op.ADD(Op.MUL(0x10, 0x3), 0x3),
                value=Op.EXP(0xFF, Op.EXP(0x100, 0x3)),
            )
            + Op.SSTORE(
                key=Op.ADD(Op.MUL(0x10, 0x3), 0x4),
                value=Op.EXP(0xFF, Op.EXP(0xFF, 0x3)),
            )
            + Op.SSTORE(
                key=Op.ADD(Op.MUL(0x10, 0x3), 0x5),
                value=Op.EXP(0xFF, Op.EXP(0x101, 0x3)),
            )
            + Op.SSTORE(
                key=Op.ADD(Op.MUL(0x10, 0x3), 0x6),
                value=Op.EXP(0x101, Op.EXP(0x100, 0x3)),
            )
            + Op.SSTORE(
                key=Op.ADD(Op.MUL(0x10, 0x3), 0x7),
                value=Op.EXP(0x101, Op.EXP(0xFF, 0x3)),
            )
            + Op.SSTORE(
                key=Op.ADD(Op.MUL(0x10, 0x3), 0x8),
                value=Op.EXP(0x101, Op.EXP(0x101, 0x3)),
            )
            + Op.SSTORE(
                key=Op.MUL(0x10, 0x4),
                value=Op.EXP(0x100, Op.EXP(0x100, 0x4)),
            )
            + Op.SSTORE(
                key=Op.ADD(Op.MUL(0x10, 0x4), 0x1),
                value=Op.EXP(0x100, Op.EXP(0xFF, 0x4)),
            )
            + Op.SSTORE(
                key=Op.ADD(Op.MUL(0x10, 0x4), 0x2),
                value=Op.EXP(0x100, Op.EXP(0x101, 0x4)),
            )
            + Op.SSTORE(
                key=Op.ADD(Op.MUL(0x10, 0x4), 0x3),
                value=Op.EXP(0xFF, Op.EXP(0x100, 0x4)),
            )
            + Op.SSTORE(
                key=Op.ADD(Op.MUL(0x10, 0x4), 0x4),
                value=Op.EXP(0xFF, Op.EXP(0xFF, 0x4)),
            )
            + Op.SSTORE(
                key=Op.ADD(Op.MUL(0x10, 0x4), 0x5),
                value=Op.EXP(0xFF, Op.EXP(0x101, 0x4)),
            )
            + Op.SSTORE(
                key=Op.ADD(Op.MUL(0x10, 0x4), 0x6),
                value=Op.EXP(0x101, Op.EXP(0x100, 0x4)),
            )
            + Op.SSTORE(
                key=Op.ADD(Op.MUL(0x10, 0x4), 0x7),
                value=Op.EXP(0x101, Op.EXP(0xFF, 0x4)),
            )
            + Op.SSTORE(
                key=Op.ADD(Op.MUL(0x10, 0x4), 0x8),
                value=Op.EXP(0x101, Op.EXP(0x101, 0x4)),
            )
            + Op.SSTORE(
                key=Op.MUL(0x10, 0x5),
                value=Op.EXP(0x100, Op.EXP(0x100, 0x5)),
            )
            + Op.SSTORE(
                key=Op.ADD(Op.MUL(0x10, 0x5), 0x1),
                value=Op.EXP(0x100, Op.EXP(0xFF, 0x5)),
            )
            + Op.SSTORE(
                key=Op.ADD(Op.MUL(0x10, 0x5), 0x2),
                value=Op.EXP(0x100, Op.EXP(0x101, 0x5)),
            )
            + Op.SSTORE(
                key=Op.ADD(Op.MUL(0x10, 0x5), 0x3),
                value=Op.EXP(0xFF, Op.EXP(0x100, 0x5)),
            )
            + Op.SSTORE(
                key=Op.ADD(Op.MUL(0x10, 0x5), 0x4),
                value=Op.EXP(0xFF, Op.EXP(0xFF, 0x5)),
            )
            + Op.SSTORE(
                key=Op.ADD(Op.MUL(0x10, 0x5), 0x5),
                value=Op.EXP(0xFF, Op.EXP(0x101, 0x5)),
            )
            + Op.SSTORE(
                key=Op.ADD(Op.MUL(0x10, 0x5), 0x6),
                value=Op.EXP(0x101, Op.EXP(0x100, 0x5)),
            )
            + Op.SSTORE(
                key=Op.ADD(Op.MUL(0x10, 0x5), 0x7),
                value=Op.EXP(0x101, Op.EXP(0xFF, 0x5)),
            )
            + Op.SSTORE(
                key=Op.ADD(Op.MUL(0x10, 0x5), 0x8),
                value=Op.EXP(0x101, Op.EXP(0x101, 0x5)),
            )
            + Op.SSTORE(
                key=Op.MUL(0x10, 0x6),
                value=Op.EXP(0x100, Op.EXP(0x100, 0x6)),
            )
            + Op.SSTORE(
                key=Op.ADD(Op.MUL(0x10, 0x6), 0x1),
                value=Op.EXP(0x100, Op.EXP(0xFF, 0x6)),
            )
            + Op.SSTORE(
                key=Op.ADD(Op.MUL(0x10, 0x6), 0x2),
                value=Op.EXP(0x100, Op.EXP(0x101, 0x6)),
            )
            + Op.SSTORE(
                key=Op.ADD(Op.MUL(0x10, 0x6), 0x3),
                value=Op.EXP(0xFF, Op.EXP(0x100, 0x6)),
            )
            + Op.SSTORE(
                key=Op.ADD(Op.MUL(0x10, 0x6), 0x4),
                value=Op.EXP(0xFF, Op.EXP(0xFF, 0x6)),
            )
            + Op.SSTORE(
                key=Op.ADD(Op.MUL(0x10, 0x6), 0x5),
                value=Op.EXP(0xFF, Op.EXP(0x101, 0x6)),
            )
            + Op.SSTORE(
                key=Op.ADD(Op.MUL(0x10, 0x6), 0x6),
                value=Op.EXP(0x101, Op.EXP(0x100, 0x6)),
            )
            + Op.SSTORE(
                key=Op.ADD(Op.MUL(0x10, 0x6), 0x7),
                value=Op.EXP(0x101, Op.EXP(0xFF, 0x6)),
            )
            + Op.SSTORE(
                key=Op.ADD(Op.MUL(0x10, 0x6), 0x8),
                value=Op.EXP(0x101, Op.EXP(0x101, 0x6)),
            )
            + Op.SSTORE(
                key=Op.MUL(0x10, 0x7),
                value=Op.EXP(0x100, Op.EXP(0x100, 0x7)),
            )
            + Op.SSTORE(
                key=Op.ADD(Op.MUL(0x10, 0x7), 0x1),
                value=Op.EXP(0x100, Op.EXP(0xFF, 0x7)),
            )
            + Op.SSTORE(
                key=Op.ADD(Op.MUL(0x10, 0x7), 0x2),
                value=Op.EXP(0x100, Op.EXP(0x101, 0x7)),
            )
            + Op.SSTORE(
                key=Op.ADD(Op.MUL(0x10, 0x7), 0x3),
                value=Op.EXP(0xFF, Op.EXP(0x100, 0x7)),
            )
            + Op.SSTORE(
                key=Op.ADD(Op.MUL(0x10, 0x7), 0x4),
                value=Op.EXP(0xFF, Op.EXP(0xFF, 0x7)),
            )
            + Op.SSTORE(
                key=Op.ADD(Op.MUL(0x10, 0x7), 0x5),
                value=Op.EXP(0xFF, Op.EXP(0x101, 0x7)),
            )
            + Op.SSTORE(
                key=Op.ADD(Op.MUL(0x10, 0x7), 0x6),
                value=Op.EXP(0x101, Op.EXP(0x100, 0x7)),
            )
            + Op.SSTORE(
                key=Op.ADD(Op.MUL(0x10, 0x7), 0x7),
                value=Op.EXP(0x101, Op.EXP(0xFF, 0x7)),
            )
            + Op.SSTORE(
                key=Op.ADD(Op.MUL(0x10, 0x7), 0x8),
                value=Op.EXP(0x101, Op.EXP(0x101, 0x7)),
            )
            + Op.SSTORE(
                key=Op.MUL(0x10, 0x8),
                value=Op.EXP(0x100, Op.EXP(0x100, 0x8)),
            )
            + Op.SSTORE(
                key=Op.ADD(Op.MUL(0x10, 0x8), 0x1),
                value=Op.EXP(0x100, Op.EXP(0xFF, 0x8)),
            )
            + Op.SSTORE(
                key=Op.ADD(Op.MUL(0x10, 0x8), 0x2),
                value=Op.EXP(0x100, Op.EXP(0x101, 0x8)),
            )
            + Op.SSTORE(
                key=Op.ADD(Op.MUL(0x10, 0x8), 0x3),
                value=Op.EXP(0xFF, Op.EXP(0x100, 0x8)),
            )
            + Op.SSTORE(
                key=Op.ADD(Op.MUL(0x10, 0x8), 0x4),
                value=Op.EXP(0xFF, Op.EXP(0xFF, 0x8)),
            )
            + Op.SSTORE(
                key=Op.ADD(Op.MUL(0x10, 0x8), 0x5),
                value=Op.EXP(0xFF, Op.EXP(0x101, 0x8)),
            )
            + Op.SSTORE(
                key=Op.ADD(Op.MUL(0x10, 0x8), 0x6),
                value=Op.EXP(0x101, Op.EXP(0x100, 0x8)),
            )
            + Op.SSTORE(
                key=Op.ADD(Op.MUL(0x10, 0x8), 0x7),
                value=Op.EXP(0x101, Op.EXP(0xFF, 0x8)),
            )
            + Op.SSTORE(
                key=Op.ADD(Op.MUL(0x10, 0x8), 0x8),
                value=Op.EXP(0x101, Op.EXP(0x101, 0x8)),
            )
            + Op.SSTORE(
                key=Op.MUL(0x10, 0x9),
                value=Op.EXP(0x100, Op.EXP(0x100, 0x9)),
            )
            + Op.SSTORE(
                key=Op.ADD(Op.MUL(0x10, 0x9), 0x1),
                value=Op.EXP(0x100, Op.EXP(0xFF, 0x9)),
            )
            + Op.SSTORE(
                key=Op.ADD(Op.MUL(0x10, 0x9), 0x2),
                value=Op.EXP(0x100, Op.EXP(0x101, 0x9)),
            )
            + Op.SSTORE(
                key=Op.ADD(Op.MUL(0x10, 0x9), 0x3),
                value=Op.EXP(0xFF, Op.EXP(0x100, 0x9)),
            )
            + Op.SSTORE(
                key=Op.ADD(Op.MUL(0x10, 0x9), 0x4),
                value=Op.EXP(0xFF, Op.EXP(0xFF, 0x9)),
            )
            + Op.SSTORE(
                key=Op.ADD(Op.MUL(0x10, 0x9), 0x5),
                value=Op.EXP(0xFF, Op.EXP(0x101, 0x9)),
            )
            + Op.SSTORE(
                key=Op.ADD(Op.MUL(0x10, 0x9), 0x6),
                value=Op.EXP(0x101, Op.EXP(0x100, 0x9)),
            )
            + Op.SSTORE(
                key=Op.ADD(Op.MUL(0x10, 0x9), 0x7),
                value=Op.EXP(0x101, Op.EXP(0xFF, 0x9)),
            )
            + Op.SSTORE(
                key=Op.ADD(Op.MUL(0x10, 0x9), 0x8),
                value=Op.EXP(0x101, Op.EXP(0x101, 0x9)),
            )
            + Op.SSTORE(
                key=Op.MUL(0x10, 0xA),
                value=Op.EXP(0x100, Op.EXP(0x100, 0xA)),
            )
            + Op.SSTORE(
                key=Op.ADD(Op.MUL(0x10, 0xA), 0x1),
                value=Op.EXP(0x100, Op.EXP(0xFF, 0xA)),
            )
            + Op.SSTORE(
                key=Op.ADD(Op.MUL(0x10, 0xA), 0x2),
                value=Op.EXP(0x100, Op.EXP(0x101, 0xA)),
            )
            + Op.SSTORE(
                key=Op.ADD(Op.MUL(0x10, 0xA), 0x3),
                value=Op.EXP(0xFF, Op.EXP(0x100, 0xA)),
            )
            + Op.SSTORE(
                key=Op.ADD(Op.MUL(0x10, 0xA), 0x4),
                value=Op.EXP(0xFF, Op.EXP(0xFF, 0xA)),
            )
            + Op.SSTORE(
                key=Op.ADD(Op.MUL(0x10, 0xA), 0x5),
                value=Op.EXP(0xFF, Op.EXP(0x101, 0xA)),
            )
            + Op.SSTORE(
                key=Op.ADD(Op.MUL(0x10, 0xA), 0x6),
                value=Op.EXP(0x101, Op.EXP(0x100, 0xA)),
            )
            + Op.SSTORE(
                key=Op.ADD(Op.MUL(0x10, 0xA), 0x7),
                value=Op.EXP(0x101, Op.EXP(0xFF, 0xA)),
            )
            + Op.SSTORE(
                key=Op.ADD(Op.MUL(0x10, 0xA), 0x8),
                value=Op.EXP(0x101, Op.EXP(0x101, 0xA)),
            )
            + Op.SSTORE(
                key=Op.MUL(0x10, 0xB),
                value=Op.EXP(0x100, Op.EXP(0x100, 0xB)),
            )
            + Op.SSTORE(
                key=Op.ADD(Op.MUL(0x10, 0xB), 0x1),
                value=Op.EXP(0x100, Op.EXP(0xFF, 0xB)),
            )
            + Op.SSTORE(
                key=Op.ADD(Op.MUL(0x10, 0xB), 0x2),
                value=Op.EXP(0x100, Op.EXP(0x101, 0xB)),
            )
            + Op.SSTORE(
                key=Op.ADD(Op.MUL(0x10, 0xB), 0x3),
                value=Op.EXP(0xFF, Op.EXP(0x100, 0xB)),
            )
            + Op.SSTORE(
                key=Op.ADD(Op.MUL(0x10, 0xB), 0x4),
                value=Op.EXP(0xFF, Op.EXP(0xFF, 0xB)),
            )
            + Op.SSTORE(
                key=Op.ADD(Op.MUL(0x10, 0xB), 0x5),
                value=Op.EXP(0xFF, Op.EXP(0x101, 0xB)),
            )
            + Op.SSTORE(
                key=Op.ADD(Op.MUL(0x10, 0xB), 0x6),
                value=Op.EXP(0x101, Op.EXP(0x100, 0xB)),
            )
            + Op.SSTORE(
                key=Op.ADD(Op.MUL(0x10, 0xB), 0x7),
                value=Op.EXP(0x101, Op.EXP(0xFF, 0xB)),
            )
            + Op.SSTORE(
                key=Op.ADD(Op.MUL(0x10, 0xB), 0x8),
                value=Op.EXP(0x101, Op.EXP(0x101, 0xB)),
            )
            + Op.SSTORE(
                key=Op.MUL(0x10, 0xC),
                value=Op.EXP(0x100, Op.EXP(0x100, 0xC)),
            )
            + Op.SSTORE(
                key=Op.ADD(Op.MUL(0x10, 0xC), 0x1),
                value=Op.EXP(0x100, Op.EXP(0xFF, 0xC)),
            )
            + Op.SSTORE(
                key=Op.ADD(Op.MUL(0x10, 0xC), 0x2),
                value=Op.EXP(0x100, Op.EXP(0x101, 0xC)),
            )
            + Op.SSTORE(
                key=Op.ADD(Op.MUL(0x10, 0xC), 0x3),
                value=Op.EXP(0xFF, Op.EXP(0x100, 0xC)),
            )
            + Op.SSTORE(
                key=Op.ADD(Op.MUL(0x10, 0xC), 0x4),
                value=Op.EXP(0xFF, Op.EXP(0xFF, 0xC)),
            )
            + Op.SSTORE(
                key=Op.ADD(Op.MUL(0x10, 0xC), 0x5),
                value=Op.EXP(0xFF, Op.EXP(0x101, 0xC)),
            )
            + Op.SSTORE(
                key=Op.ADD(Op.MUL(0x10, 0xC), 0x6),
                value=Op.EXP(0x101, Op.EXP(0x100, 0xC)),
            )
            + Op.SSTORE(
                key=Op.ADD(Op.MUL(0x10, 0xC), 0x7),
                value=Op.EXP(0x101, Op.EXP(0xFF, 0xC)),
            )
            + Op.SSTORE(
                key=Op.ADD(Op.MUL(0x10, 0xC), 0x8),
                value=Op.EXP(0x101, Op.EXP(0x101, 0xC)),
            )
            + Op.SSTORE(
                key=Op.MUL(0x10, 0xD),
                value=Op.EXP(0x100, Op.EXP(0x100, 0xD)),
            )
            + Op.SSTORE(
                key=Op.ADD(Op.MUL(0x10, 0xD), 0x1),
                value=Op.EXP(0x100, Op.EXP(0xFF, 0xD)),
            )
            + Op.SSTORE(
                key=Op.ADD(Op.MUL(0x10, 0xD), 0x2),
                value=Op.EXP(0x100, Op.EXP(0x101, 0xD)),
            )
            + Op.SSTORE(
                key=Op.ADD(Op.MUL(0x10, 0xD), 0x3),
                value=Op.EXP(0xFF, Op.EXP(0x100, 0xD)),
            )
            + Op.SSTORE(
                key=Op.ADD(Op.MUL(0x10, 0xD), 0x4),
                value=Op.EXP(0xFF, Op.EXP(0xFF, 0xD)),
            )
            + Op.SSTORE(
                key=Op.ADD(Op.MUL(0x10, 0xD), 0x5),
                value=Op.EXP(0xFF, Op.EXP(0x101, 0xD)),
            )
            + Op.SSTORE(
                key=Op.ADD(Op.MUL(0x10, 0xD), 0x6),
                value=Op.EXP(0x101, Op.EXP(0x100, 0xD)),
            )
            + Op.SSTORE(
                key=Op.ADD(Op.MUL(0x10, 0xD), 0x7),
                value=Op.EXP(0x101, Op.EXP(0xFF, 0xD)),
            )
            + Op.SSTORE(
                key=Op.ADD(Op.MUL(0x10, 0xD), 0x8),
                value=Op.EXP(0x101, Op.EXP(0x101, 0xD)),
            )
            + Op.SSTORE(
                key=Op.MUL(0x10, 0xE),
                value=Op.EXP(0x100, Op.EXP(0x100, 0xE)),
            )
            + Op.SSTORE(
                key=Op.ADD(Op.MUL(0x10, 0xE), 0x1),
                value=Op.EXP(0x100, Op.EXP(0xFF, 0xE)),
            )
            + Op.SSTORE(
                key=Op.ADD(Op.MUL(0x10, 0xE), 0x2),
                value=Op.EXP(0x100, Op.EXP(0x101, 0xE)),
            )
            + Op.SSTORE(
                key=Op.ADD(Op.MUL(0x10, 0xE), 0x3),
                value=Op.EXP(0xFF, Op.EXP(0x100, 0xE)),
            )
            + Op.SSTORE(
                key=Op.ADD(Op.MUL(0x10, 0xE), 0x4),
                value=Op.EXP(0xFF, Op.EXP(0xFF, 0xE)),
            )
            + Op.SSTORE(
                key=Op.ADD(Op.MUL(0x10, 0xE), 0x5),
                value=Op.EXP(0xFF, Op.EXP(0x101, 0xE)),
            )
            + Op.SSTORE(
                key=Op.ADD(Op.MUL(0x10, 0xE), 0x6),
                value=Op.EXP(0x101, Op.EXP(0x100, 0xE)),
            )
            + Op.SSTORE(
                key=Op.ADD(Op.MUL(0x10, 0xE), 0x7),
                value=Op.EXP(0x101, Op.EXP(0xFF, 0xE)),
            )
            + Op.SSTORE(
                key=Op.ADD(Op.MUL(0x10, 0xE), 0x8),
                value=Op.EXP(0x101, Op.EXP(0x101, 0xE)),
            )
            + Op.SSTORE(
                key=Op.MUL(0x10, 0xF),
                value=Op.EXP(0x100, Op.EXP(0x100, 0xF)),
            )
            + Op.SSTORE(
                key=Op.ADD(Op.MUL(0x10, 0xF), 0x1),
                value=Op.EXP(0x100, Op.EXP(0xFF, 0xF)),
            )
            + Op.SSTORE(
                key=Op.ADD(Op.MUL(0x10, 0xF), 0x2),
                value=Op.EXP(0x100, Op.EXP(0x101, 0xF)),
            )
            + Op.SSTORE(
                key=Op.ADD(Op.MUL(0x10, 0xF), 0x3),
                value=Op.EXP(0xFF, Op.EXP(0x100, 0xF)),
            )
            + Op.SSTORE(
                key=Op.ADD(Op.MUL(0x10, 0xF), 0x4),
                value=Op.EXP(0xFF, Op.EXP(0xFF, 0xF)),
            )
            + Op.SSTORE(
                key=Op.ADD(Op.MUL(0x10, 0xF), 0x5),
                value=Op.EXP(0xFF, Op.EXP(0x101, 0xF)),
            )
            + Op.SSTORE(
                key=Op.ADD(Op.MUL(0x10, 0xF), 0x6),
                value=Op.EXP(0x101, Op.EXP(0x100, 0xF)),
            )
            + Op.SSTORE(
                key=Op.ADD(Op.MUL(0x10, 0xF), 0x7),
                value=Op.EXP(0x101, Op.EXP(0xFF, 0xF)),
            )
            + Op.SSTORE(
                key=Op.ADD(Op.MUL(0x10, 0xF), 0x8),
                value=Op.EXP(0x101, Op.EXP(0x101, 0xF)),
            )
            + Op.SSTORE(
                key=Op.MUL(0x10, 0x10),
                value=Op.EXP(0x100, Op.EXP(0x100, 0x10)),
            )
            + Op.SSTORE(
                key=Op.ADD(Op.MUL(0x10, 0x10), 0x1),
                value=Op.EXP(0x100, Op.EXP(0xFF, 0x10)),
            )
            + Op.SSTORE(
                key=Op.ADD(Op.MUL(0x10, 0x10), 0x2),
                value=Op.EXP(0x100, Op.EXP(0x101, 0x10)),
            )
            + Op.SSTORE(
                key=Op.ADD(Op.MUL(0x10, 0x10), 0x3),
                value=Op.EXP(0xFF, Op.EXP(0x100, 0x10)),
            )
            + Op.SSTORE(
                key=Op.ADD(Op.MUL(0x10, 0x10), 0x4),
                value=Op.EXP(0xFF, Op.EXP(0xFF, 0x10)),
            )
            + Op.SSTORE(
                key=Op.ADD(Op.MUL(0x10, 0x10), 0x5),
                value=Op.EXP(0xFF, Op.EXP(0x101, 0x10)),
            )
            + Op.SSTORE(
                key=Op.ADD(Op.MUL(0x10, 0x10), 0x6),
                value=Op.EXP(0x101, Op.EXP(0x100, 0x10)),
            )
            + Op.SSTORE(
                key=Op.ADD(Op.MUL(0x10, 0x10), 0x7),
                value=Op.EXP(0x101, Op.EXP(0xFF, 0x10)),
            )
            + Op.SSTORE(
                key=Op.ADD(Op.MUL(0x10, 0x10), 0x8),
                value=Op.EXP(0x101, Op.EXP(0x101, 0x10)),
            )
            + Op.SSTORE(
                key=Op.MUL(0x10, 0x11),
                value=Op.EXP(0x100, Op.EXP(0x100, 0x11)),
            )
            + Op.SSTORE(
                key=Op.ADD(Op.MUL(0x10, 0x11), 0x1),
                value=Op.EXP(0x100, Op.EXP(0xFF, 0x11)),
            )
            + Op.SSTORE(
                key=Op.ADD(Op.MUL(0x10, 0x11), 0x2),
                value=Op.EXP(0x100, Op.EXP(0x101, 0x11)),
            )
            + Op.SSTORE(
                key=Op.ADD(Op.MUL(0x10, 0x11), 0x3),
                value=Op.EXP(0xFF, Op.EXP(0x100, 0x11)),
            )
            + Op.SSTORE(
                key=Op.ADD(Op.MUL(0x10, 0x11), 0x4),
                value=Op.EXP(0xFF, Op.EXP(0xFF, 0x11)),
            )
            + Op.SSTORE(
                key=Op.ADD(Op.MUL(0x10, 0x11), 0x5),
                value=Op.EXP(0xFF, Op.EXP(0x101, 0x11)),
            )
            + Op.SSTORE(
                key=Op.ADD(Op.MUL(0x10, 0x11), 0x6),
                value=Op.EXP(0x101, Op.EXP(0x100, 0x11)),
            )
            + Op.SSTORE(
                key=Op.ADD(Op.MUL(0x10, 0x11), 0x7),
                value=Op.EXP(0x101, Op.EXP(0xFF, 0x11)),
            )
            + Op.SSTORE(
                key=Op.ADD(Op.MUL(0x10, 0x11), 0x8),
                value=Op.EXP(0x101, Op.EXP(0x101, 0x11)),
            )
            + Op.SSTORE(
                key=Op.MUL(0x10, 0x12),
                value=Op.EXP(0x100, Op.EXP(0x100, 0x12)),
            )
            + Op.SSTORE(
                key=Op.ADD(Op.MUL(0x10, 0x12), 0x1),
                value=Op.EXP(0x100, Op.EXP(0xFF, 0x12)),
            )
            + Op.SSTORE(
                key=Op.ADD(Op.MUL(0x10, 0x12), 0x2),
                value=Op.EXP(0x100, Op.EXP(0x101, 0x12)),
            )
            + Op.SSTORE(
                key=Op.ADD(Op.MUL(0x10, 0x12), 0x3),
                value=Op.EXP(0xFF, Op.EXP(0x100, 0x12)),
            )
            + Op.SSTORE(
                key=Op.ADD(Op.MUL(0x10, 0x12), 0x4),
                value=Op.EXP(0xFF, Op.EXP(0xFF, 0x12)),
            )
            + Op.SSTORE(
                key=Op.ADD(Op.MUL(0x10, 0x12), 0x5),
                value=Op.EXP(0xFF, Op.EXP(0x101, 0x12)),
            )
            + Op.SSTORE(
                key=Op.ADD(Op.MUL(0x10, 0x12), 0x6),
                value=Op.EXP(0x101, Op.EXP(0x100, 0x12)),
            )
            + Op.SSTORE(
                key=Op.ADD(Op.MUL(0x10, 0x12), 0x7),
                value=Op.EXP(0x101, Op.EXP(0xFF, 0x12)),
            )
            + Op.SSTORE(
                key=Op.ADD(Op.MUL(0x10, 0x12), 0x8),
                value=Op.EXP(0x101, Op.EXP(0x101, 0x12)),
            )
            + Op.SSTORE(
                key=Op.MUL(0x10, 0x13),
                value=Op.EXP(0x100, Op.EXP(0x100, 0x13)),
            )
            + Op.SSTORE(
                key=Op.ADD(Op.MUL(0x10, 0x13), 0x1),
                value=Op.EXP(0x100, Op.EXP(0xFF, 0x13)),
            )
            + Op.SSTORE(
                key=Op.ADD(Op.MUL(0x10, 0x13), 0x2),
                value=Op.EXP(0x100, Op.EXP(0x101, 0x13)),
            )
            + Op.SSTORE(
                key=Op.ADD(Op.MUL(0x10, 0x13), 0x3),
                value=Op.EXP(0xFF, Op.EXP(0x100, 0x13)),
            )
            + Op.SSTORE(
                key=Op.ADD(Op.MUL(0x10, 0x13), 0x4),
                value=Op.EXP(0xFF, Op.EXP(0xFF, 0x13)),
            )
            + Op.SSTORE(
                key=Op.ADD(Op.MUL(0x10, 0x13), 0x5),
                value=Op.EXP(0xFF, Op.EXP(0x101, 0x13)),
            )
            + Op.SSTORE(
                key=Op.ADD(Op.MUL(0x10, 0x13), 0x6),
                value=Op.EXP(0x101, Op.EXP(0x100, 0x13)),
            )
            + Op.SSTORE(
                key=Op.ADD(Op.MUL(0x10, 0x13), 0x7),
                value=Op.EXP(0x101, Op.EXP(0xFF, 0x13)),
            )
            + Op.SSTORE(
                key=Op.ADD(Op.MUL(0x10, 0x13), 0x8),
                value=Op.EXP(0x101, Op.EXP(0x101, 0x13)),
            )
            + Op.SSTORE(
                key=Op.MUL(0x10, 0x14),
                value=Op.EXP(0x100, Op.EXP(0x100, 0x14)),
            )
            + Op.SSTORE(
                key=Op.ADD(Op.MUL(0x10, 0x14), 0x1),
                value=Op.EXP(0x100, Op.EXP(0xFF, 0x14)),
            )
            + Op.SSTORE(
                key=Op.ADD(Op.MUL(0x10, 0x14), 0x2),
                value=Op.EXP(0x100, Op.EXP(0x101, 0x14)),
            )
            + Op.SSTORE(
                key=Op.ADD(Op.MUL(0x10, 0x14), 0x3),
                value=Op.EXP(0xFF, Op.EXP(0x100, 0x14)),
            )
            + Op.SSTORE(
                key=Op.ADD(Op.MUL(0x10, 0x14), 0x4),
                value=Op.EXP(0xFF, Op.EXP(0xFF, 0x14)),
            )
            + Op.SSTORE(
                key=Op.ADD(Op.MUL(0x10, 0x14), 0x5),
                value=Op.EXP(0xFF, Op.EXP(0x101, 0x14)),
            )
            + Op.SSTORE(
                key=Op.ADD(Op.MUL(0x10, 0x14), 0x6),
                value=Op.EXP(0x101, Op.EXP(0x100, 0x14)),
            )
            + Op.SSTORE(
                key=Op.ADD(Op.MUL(0x10, 0x14), 0x7),
                value=Op.EXP(0x101, Op.EXP(0xFF, 0x14)),
            )
            + Op.SSTORE(
                key=Op.ADD(Op.MUL(0x10, 0x14), 0x8),
                value=Op.EXP(0x101, Op.EXP(0x101, 0x14)),
            )
            + Op.SSTORE(
                key=Op.MUL(0x10, 0x15),
                value=Op.EXP(0x100, Op.EXP(0x100, 0x15)),
            )
            + Op.SSTORE(
                key=Op.ADD(Op.MUL(0x10, 0x15), 0x1),
                value=Op.EXP(0x100, Op.EXP(0xFF, 0x15)),
            )
            + Op.SSTORE(
                key=Op.ADD(Op.MUL(0x10, 0x15), 0x2),
                value=Op.EXP(0x100, Op.EXP(0x101, 0x15)),
            )
            + Op.SSTORE(
                key=Op.ADD(Op.MUL(0x10, 0x15), 0x3),
                value=Op.EXP(0xFF, Op.EXP(0x100, 0x15)),
            )
            + Op.SSTORE(
                key=Op.ADD(Op.MUL(0x10, 0x15), 0x4),
                value=Op.EXP(0xFF, Op.EXP(0xFF, 0x15)),
            )
            + Op.SSTORE(
                key=Op.ADD(Op.MUL(0x10, 0x15), 0x5),
                value=Op.EXP(0xFF, Op.EXP(0x101, 0x15)),
            )
            + Op.SSTORE(
                key=Op.ADD(Op.MUL(0x10, 0x15), 0x6),
                value=Op.EXP(0x101, Op.EXP(0x100, 0x15)),
            )
            + Op.SSTORE(
                key=Op.ADD(Op.MUL(0x10, 0x15), 0x7),
                value=Op.EXP(0x101, Op.EXP(0xFF, 0x15)),
            )
            + Op.SSTORE(
                key=Op.ADD(Op.MUL(0x10, 0x15), 0x8),
                value=Op.EXP(0x101, Op.EXP(0x101, 0x15)),
            )
            + Op.SSTORE(
                key=Op.MUL(0x10, 0x16),
                value=Op.EXP(0x100, Op.EXP(0x100, 0x16)),
            )
            + Op.SSTORE(
                key=Op.ADD(Op.MUL(0x10, 0x16), 0x1),
                value=Op.EXP(0x100, Op.EXP(0xFF, 0x16)),
            )
            + Op.SSTORE(
                key=Op.ADD(Op.MUL(0x10, 0x16), 0x2),
                value=Op.EXP(0x100, Op.EXP(0x101, 0x16)),
            )
            + Op.SSTORE(
                key=Op.ADD(Op.MUL(0x10, 0x16), 0x3),
                value=Op.EXP(0xFF, Op.EXP(0x100, 0x16)),
            )
            + Op.SSTORE(
                key=Op.ADD(Op.MUL(0x10, 0x16), 0x4),
                value=Op.EXP(0xFF, Op.EXP(0xFF, 0x16)),
            )
            + Op.SSTORE(
                key=Op.ADD(Op.MUL(0x10, 0x16), 0x5),
                value=Op.EXP(0xFF, Op.EXP(0x101, 0x16)),
            )
            + Op.SSTORE(
                key=Op.ADD(Op.MUL(0x10, 0x16), 0x6),
                value=Op.EXP(0x101, Op.EXP(0x100, 0x16)),
            )
            + Op.SSTORE(
                key=Op.ADD(Op.MUL(0x10, 0x16), 0x7),
                value=Op.EXP(0x101, Op.EXP(0xFF, 0x16)),
            )
            + Op.SSTORE(
                key=Op.ADD(Op.MUL(0x10, 0x16), 0x8),
                value=Op.EXP(0x101, Op.EXP(0x101, 0x16)),
            )
            + Op.SSTORE(
                key=Op.MUL(0x10, 0x17),
                value=Op.EXP(0x100, Op.EXP(0x100, 0x17)),
            )
            + Op.SSTORE(
                key=Op.ADD(Op.MUL(0x10, 0x17), 0x1),
                value=Op.EXP(0x100, Op.EXP(0xFF, 0x17)),
            )
            + Op.SSTORE(
                key=Op.ADD(Op.MUL(0x10, 0x17), 0x2),
                value=Op.EXP(0x100, Op.EXP(0x101, 0x17)),
            )
            + Op.SSTORE(
                key=Op.ADD(Op.MUL(0x10, 0x17), 0x3),
                value=Op.EXP(0xFF, Op.EXP(0x100, 0x17)),
            )
            + Op.SSTORE(
                key=Op.ADD(Op.MUL(0x10, 0x17), 0x4),
                value=Op.EXP(0xFF, Op.EXP(0xFF, 0x17)),
            )
            + Op.SSTORE(
                key=Op.ADD(Op.MUL(0x10, 0x17), 0x5),
                value=Op.EXP(0xFF, Op.EXP(0x101, 0x17)),
            )
            + Op.SSTORE(
                key=Op.ADD(Op.MUL(0x10, 0x17), 0x6),
                value=Op.EXP(0x101, Op.EXP(0x100, 0x17)),
            )
            + Op.SSTORE(
                key=Op.ADD(Op.MUL(0x10, 0x17), 0x7),
                value=Op.EXP(0x101, Op.EXP(0xFF, 0x17)),
            )
            + Op.SSTORE(
                key=Op.ADD(Op.MUL(0x10, 0x17), 0x8),
                value=Op.EXP(0x101, Op.EXP(0x101, 0x17)),
            )
            + Op.SSTORE(
                key=Op.MUL(0x10, 0x18),
                value=Op.EXP(0x100, Op.EXP(0x100, 0x18)),
            )
            + Op.SSTORE(
                key=Op.ADD(Op.MUL(0x10, 0x18), 0x1),
                value=Op.EXP(0x100, Op.EXP(0xFF, 0x18)),
            )
            + Op.SSTORE(
                key=Op.ADD(Op.MUL(0x10, 0x18), 0x2),
                value=Op.EXP(0x100, Op.EXP(0x101, 0x18)),
            )
            + Op.SSTORE(
                key=Op.ADD(Op.MUL(0x10, 0x18), 0x3),
                value=Op.EXP(0xFF, Op.EXP(0x100, 0x18)),
            )
            + Op.SSTORE(
                key=Op.ADD(Op.MUL(0x10, 0x18), 0x4),
                value=Op.EXP(0xFF, Op.EXP(0xFF, 0x18)),
            )
            + Op.SSTORE(
                key=Op.ADD(Op.MUL(0x10, 0x18), 0x5),
                value=Op.EXP(0xFF, Op.EXP(0x101, 0x18)),
            )
            + Op.SSTORE(
                key=Op.ADD(Op.MUL(0x10, 0x18), 0x6),
                value=Op.EXP(0x101, Op.EXP(0x100, 0x18)),
            )
            + Op.SSTORE(
                key=Op.ADD(Op.MUL(0x10, 0x18), 0x7),
                value=Op.EXP(0x101, Op.EXP(0xFF, 0x18)),
            )
            + Op.SSTORE(
                key=Op.ADD(Op.MUL(0x10, 0x18), 0x8),
                value=Op.EXP(0x101, Op.EXP(0x101, 0x18)),
            )
            + Op.SSTORE(
                key=Op.MUL(0x10, 0x19),
                value=Op.EXP(0x100, Op.EXP(0x100, 0x19)),
            )
            + Op.SSTORE(
                key=Op.ADD(Op.MUL(0x10, 0x19), 0x1),
                value=Op.EXP(0x100, Op.EXP(0xFF, 0x19)),
            )
            + Op.SSTORE(
                key=Op.ADD(Op.MUL(0x10, 0x19), 0x2),
                value=Op.EXP(0x100, Op.EXP(0x101, 0x19)),
            )
            + Op.SSTORE(
                key=Op.ADD(Op.MUL(0x10, 0x19), 0x3),
                value=Op.EXP(0xFF, Op.EXP(0x100, 0x19)),
            )
            + Op.SSTORE(
                key=Op.ADD(Op.MUL(0x10, 0x19), 0x4),
                value=Op.EXP(0xFF, Op.EXP(0xFF, 0x19)),
            )
            + Op.SSTORE(
                key=Op.ADD(Op.MUL(0x10, 0x19), 0x5),
                value=Op.EXP(0xFF, Op.EXP(0x101, 0x19)),
            )
            + Op.SSTORE(
                key=Op.ADD(Op.MUL(0x10, 0x19), 0x6),
                value=Op.EXP(0x101, Op.EXP(0x100, 0x19)),
            )
            + Op.SSTORE(
                key=Op.ADD(Op.MUL(0x10, 0x19), 0x7),
                value=Op.EXP(0x101, Op.EXP(0xFF, 0x19)),
            )
            + Op.SSTORE(
                key=Op.ADD(Op.MUL(0x10, 0x19), 0x8),
                value=Op.EXP(0x101, Op.EXP(0x101, 0x19)),
            )
            + Op.SSTORE(
                key=Op.MUL(0x10, 0x1A),
                value=Op.EXP(0x100, Op.EXP(0x100, 0x1A)),
            )
            + Op.SSTORE(
                key=Op.ADD(Op.MUL(0x10, 0x1A), 0x1),
                value=Op.EXP(0x100, Op.EXP(0xFF, 0x1A)),
            )
            + Op.SSTORE(
                key=Op.ADD(Op.MUL(0x10, 0x1A), 0x2),
                value=Op.EXP(0x100, Op.EXP(0x101, 0x1A)),
            )
            + Op.SSTORE(
                key=Op.ADD(Op.MUL(0x10, 0x1A), 0x3),
                value=Op.EXP(0xFF, Op.EXP(0x100, 0x1A)),
            )
            + Op.SSTORE(
                key=Op.ADD(Op.MUL(0x10, 0x1A), 0x4),
                value=Op.EXP(0xFF, Op.EXP(0xFF, 0x1A)),
            )
            + Op.SSTORE(
                key=Op.ADD(Op.MUL(0x10, 0x1A), 0x5),
                value=Op.EXP(0xFF, Op.EXP(0x101, 0x1A)),
            )
            + Op.SSTORE(
                key=Op.ADD(Op.MUL(0x10, 0x1A), 0x6),
                value=Op.EXP(0x101, Op.EXP(0x100, 0x1A)),
            )
            + Op.SSTORE(
                key=Op.ADD(Op.MUL(0x10, 0x1A), 0x7),
                value=Op.EXP(0x101, Op.EXP(0xFF, 0x1A)),
            )
            + Op.SSTORE(
                key=Op.ADD(Op.MUL(0x10, 0x1A), 0x8),
                value=Op.EXP(0x101, Op.EXP(0x101, 0x1A)),
            )
            + Op.SSTORE(
                key=Op.MUL(0x10, 0x1B),
                value=Op.EXP(0x100, Op.EXP(0x100, 0x1B)),
            )
            + Op.SSTORE(
                key=Op.ADD(Op.MUL(0x10, 0x1B), 0x1),
                value=Op.EXP(0x100, Op.EXP(0xFF, 0x1B)),
            )
            + Op.SSTORE(
                key=Op.ADD(Op.MUL(0x10, 0x1B), 0x2),
                value=Op.EXP(0x100, Op.EXP(0x101, 0x1B)),
            )
            + Op.SSTORE(
                key=Op.ADD(Op.MUL(0x10, 0x1B), 0x3),
                value=Op.EXP(0xFF, Op.EXP(0x100, 0x1B)),
            )
            + Op.SSTORE(
                key=Op.ADD(Op.MUL(0x10, 0x1B), 0x4),
                value=Op.EXP(0xFF, Op.EXP(0xFF, 0x1B)),
            )
            + Op.SSTORE(
                key=Op.ADD(Op.MUL(0x10, 0x1B), 0x5),
                value=Op.EXP(0xFF, Op.EXP(0x101, 0x1B)),
            )
            + Op.SSTORE(
                key=Op.ADD(Op.MUL(0x10, 0x1B), 0x6),
                value=Op.EXP(0x101, Op.EXP(0x100, 0x1B)),
            )
            + Op.SSTORE(
                key=Op.ADD(Op.MUL(0x10, 0x1B), 0x7),
                value=Op.EXP(0x101, Op.EXP(0xFF, 0x1B)),
            )
            + Op.SSTORE(
                key=Op.ADD(Op.MUL(0x10, 0x1B), 0x8),
                value=Op.EXP(0x101, Op.EXP(0x101, 0x1B)),
            )
            + Op.SSTORE(
                key=Op.MUL(0x10, 0x1C),
                value=Op.EXP(0x100, Op.EXP(0x100, 0x1C)),
            )
            + Op.SSTORE(
                key=Op.ADD(Op.MUL(0x10, 0x1C), 0x1),
                value=Op.EXP(0x100, Op.EXP(0xFF, 0x1C)),
            )
            + Op.SSTORE(
                key=Op.ADD(Op.MUL(0x10, 0x1C), 0x2),
                value=Op.EXP(0x100, Op.EXP(0x101, 0x1C)),
            )
            + Op.SSTORE(
                key=Op.ADD(Op.MUL(0x10, 0x1C), 0x3),
                value=Op.EXP(0xFF, Op.EXP(0x100, 0x1C)),
            )
            + Op.SSTORE(
                key=Op.ADD(Op.MUL(0x10, 0x1C), 0x4),
                value=Op.EXP(0xFF, Op.EXP(0xFF, 0x1C)),
            )
            + Op.SSTORE(
                key=Op.ADD(Op.MUL(0x10, 0x1C), 0x5),
                value=Op.EXP(0xFF, Op.EXP(0x101, 0x1C)),
            )
            + Op.SSTORE(
                key=Op.ADD(Op.MUL(0x10, 0x1C), 0x6),
                value=Op.EXP(0x101, Op.EXP(0x100, 0x1C)),
            )
            + Op.SSTORE(
                key=Op.ADD(Op.MUL(0x10, 0x1C), 0x7),
                value=Op.EXP(0x101, Op.EXP(0xFF, 0x1C)),
            )
            + Op.SSTORE(
                key=Op.ADD(Op.MUL(0x10, 0x1C), 0x8),
                value=Op.EXP(0x101, Op.EXP(0x101, 0x1C)),
            )
            + Op.SSTORE(
                key=Op.MUL(0x10, 0x1D),
                value=Op.EXP(0x100, Op.EXP(0x100, 0x1D)),
            )
            + Op.SSTORE(
                key=Op.ADD(Op.MUL(0x10, 0x1D), 0x1),
                value=Op.EXP(0x100, Op.EXP(0xFF, 0x1D)),
            )
            + Op.SSTORE(
                key=Op.ADD(Op.MUL(0x10, 0x1D), 0x2),
                value=Op.EXP(0x100, Op.EXP(0x101, 0x1D)),
            )
            + Op.SSTORE(
                key=Op.ADD(Op.MUL(0x10, 0x1D), 0x3),
                value=Op.EXP(0xFF, Op.EXP(0x100, 0x1D)),
            )
            + Op.SSTORE(
                key=Op.ADD(Op.MUL(0x10, 0x1D), 0x4),
                value=Op.EXP(0xFF, Op.EXP(0xFF, 0x1D)),
            )
            + Op.SSTORE(
                key=Op.ADD(Op.MUL(0x10, 0x1D), 0x5),
                value=Op.EXP(0xFF, Op.EXP(0x101, 0x1D)),
            )
            + Op.SSTORE(
                key=Op.ADD(Op.MUL(0x10, 0x1D), 0x6),
                value=Op.EXP(0x101, Op.EXP(0x100, 0x1D)),
            )
            + Op.SSTORE(
                key=Op.ADD(Op.MUL(0x10, 0x1D), 0x7),
                value=Op.EXP(0x101, Op.EXP(0xFF, 0x1D)),
            )
            + Op.SSTORE(
                key=Op.ADD(Op.MUL(0x10, 0x1D), 0x8),
                value=Op.EXP(0x101, Op.EXP(0x101, 0x1D)),
            )
            + Op.SSTORE(
                key=Op.MUL(0x10, 0x1E),
                value=Op.EXP(0x100, Op.EXP(0x100, 0x1E)),
            )
            + Op.SSTORE(
                key=Op.ADD(Op.MUL(0x10, 0x1E), 0x1),
                value=Op.EXP(0x100, Op.EXP(0xFF, 0x1E)),
            )
            + Op.SSTORE(
                key=Op.ADD(Op.MUL(0x10, 0x1E), 0x2),
                value=Op.EXP(0x100, Op.EXP(0x101, 0x1E)),
            )
            + Op.SSTORE(
                key=Op.ADD(Op.MUL(0x10, 0x1E), 0x3),
                value=Op.EXP(0xFF, Op.EXP(0x100, 0x1E)),
            )
            + Op.SSTORE(
                key=Op.ADD(Op.MUL(0x10, 0x1E), 0x4),
                value=Op.EXP(0xFF, Op.EXP(0xFF, 0x1E)),
            )
            + Op.SSTORE(
                key=Op.ADD(Op.MUL(0x10, 0x1E), 0x5),
                value=Op.EXP(0xFF, Op.EXP(0x101, 0x1E)),
            )
            + Op.SSTORE(
                key=Op.ADD(Op.MUL(0x10, 0x1E), 0x6),
                value=Op.EXP(0x101, Op.EXP(0x100, 0x1E)),
            )
            + Op.SSTORE(
                key=Op.ADD(Op.MUL(0x10, 0x1E), 0x7),
                value=Op.EXP(0x101, Op.EXP(0xFF, 0x1E)),
            )
            + Op.SSTORE(
                key=Op.ADD(Op.MUL(0x10, 0x1E), 0x8),
                value=Op.EXP(0x101, Op.EXP(0x101, 0x1E)),
            )
            + Op.SSTORE(
                key=Op.MUL(0x10, 0x1F),
                value=Op.EXP(0x100, Op.EXP(0x100, 0x1F)),
            )
            + Op.SSTORE(
                key=Op.ADD(Op.MUL(0x10, 0x1F), 0x1),
                value=Op.EXP(0x100, Op.EXP(0xFF, 0x1F)),
            )
            + Op.SSTORE(
                key=Op.ADD(Op.MUL(0x10, 0x1F), 0x2),
                value=Op.EXP(0x100, Op.EXP(0x101, 0x1F)),
            )
            + Op.SSTORE(
                key=Op.ADD(Op.MUL(0x10, 0x1F), 0x3),
                value=Op.EXP(0xFF, Op.EXP(0x100, 0x1F)),
            )
            + Op.SSTORE(
                key=Op.ADD(Op.MUL(0x10, 0x1F), 0x4),
                value=Op.EXP(0xFF, Op.EXP(0xFF, 0x1F)),
            )
            + Op.SSTORE(
                key=Op.ADD(Op.MUL(0x10, 0x1F), 0x5),
                value=Op.EXP(0xFF, Op.EXP(0x101, 0x1F)),
            )
            + Op.SSTORE(
                key=Op.ADD(Op.MUL(0x10, 0x1F), 0x6),
                value=Op.EXP(0x101, Op.EXP(0x100, 0x1F)),
            )
            + Op.SSTORE(
                key=Op.ADD(Op.MUL(0x10, 0x1F), 0x7),
                value=Op.EXP(0x101, Op.EXP(0xFF, 0x1F)),
            )
            + Op.SSTORE(
                key=Op.ADD(Op.MUL(0x10, 0x1F), 0x8),
                value=Op.EXP(0x101, Op.EXP(0x101, 0x1F)),
            )
            + Op.SSTORE(
                key=Op.MUL(0x10, 0x20),
                value=Op.EXP(0x100, Op.EXP(0x100, 0x20)),
            )
            + Op.SSTORE(
                key=Op.ADD(Op.MUL(0x10, 0x20), 0x1),
                value=Op.EXP(0x100, Op.EXP(0xFF, 0x20)),
            )
            + Op.SSTORE(
                key=Op.ADD(Op.MUL(0x10, 0x20), 0x2),
                value=Op.EXP(0x100, Op.EXP(0x101, 0x20)),
            )
            + Op.SSTORE(
                key=Op.ADD(Op.MUL(0x10, 0x20), 0x3),
                value=Op.EXP(0xFF, Op.EXP(0x100, 0x20)),
            )
            + Op.SSTORE(
                key=Op.ADD(Op.MUL(0x10, 0x20), 0x4),
                value=Op.EXP(0xFF, Op.EXP(0xFF, 0x20)),
            )
            + Op.SSTORE(
                key=Op.ADD(Op.MUL(0x10, 0x20), 0x5),
                value=Op.EXP(0xFF, Op.EXP(0x101, 0x20)),
            )
            + Op.SSTORE(
                key=Op.ADD(Op.MUL(0x10, 0x20), 0x6),
                value=Op.EXP(0x101, Op.EXP(0x100, 0x20)),
            )
            + Op.SSTORE(
                key=Op.ADD(Op.MUL(0x10, 0x20), 0x7),
                value=Op.EXP(0x101, Op.EXP(0xFF, 0x20)),
            )
            + Op.SSTORE(
                key=Op.ADD(Op.MUL(0x10, 0x20), 0x8),
                value=Op.EXP(0x101, Op.EXP(0x101, 0x20)),
            )
            + Op.SSTORE(
                key=Op.MUL(0x10, 0x21),
                value=Op.EXP(0x100, Op.EXP(0x100, 0x21)),
            )
            + Op.SSTORE(
                key=Op.ADD(Op.MUL(0x10, 0x21), 0x1),
                value=Op.EXP(0x100, Op.EXP(0xFF, 0x21)),
            )
            + Op.SSTORE(
                key=Op.ADD(Op.MUL(0x10, 0x21), 0x2),
                value=Op.EXP(0x100, Op.EXP(0x101, 0x21)),
            )
            + Op.SSTORE(
                key=Op.ADD(Op.MUL(0x10, 0x21), 0x3),
                value=Op.EXP(0xFF, Op.EXP(0x100, 0x21)),
            )
            + Op.SSTORE(
                key=Op.ADD(Op.MUL(0x10, 0x21), 0x4),
                value=Op.EXP(0xFF, Op.EXP(0xFF, 0x21)),
            )
            + Op.SSTORE(
                key=Op.ADD(Op.MUL(0x10, 0x21), 0x5),
                value=Op.EXP(0xFF, Op.EXP(0x101, 0x21)),
            )
            + Op.SSTORE(
                key=Op.ADD(Op.MUL(0x10, 0x21), 0x6),
                value=Op.EXP(0x101, Op.EXP(0x100, 0x21)),
            )
            + Op.SSTORE(
                key=Op.ADD(Op.MUL(0x10, 0x21), 0x7),
                value=Op.EXP(0x101, Op.EXP(0xFF, 0x21)),
            )
            + Op.SSTORE(
                key=Op.ADD(Op.MUL(0x10, 0x21), 0x8),
                value=Op.EXP(0x101, Op.EXP(0x101, 0x21)),
            )
            + Op.STOP
        ),
        balance=0xBA1A9CE0BA1A9CE,
        nonce=0,
        address=Address("0x9f233ef2d697929edf542064b125e7d620270363"),  # noqa: E501
    )

    tx = Transaction(
        sender=sender,
        to=contract,
        data=bytes.fromhex(
            "693c61390000000000000000000000000000000000000000000000000000000000000000"  # noqa: E501
        ),
        gas_limit=16777216,
        value=1,
    )

    post = {
        contract: Account(
            storage={
                0: 256,
                1: 256,
                2: 256,
                3: 255,
                4: 255,
                5: 255,
                6: 257,
                7: 257,
                8: 257,
                19: 0x6C3ACD330B959AD6EFABCE6D2D2125E73A88A65A9880D203DDDF5957F7F0001,  # noqa: E501
                20: 0x8F965A06DA0AC41DCB3A34F1D8AB7D8FEE620A94FAA42C395997756B007FFEFF,  # noqa: E501
                21: 0xBCE9265D88A053C18BC229EBFF404C1534E1DB43DE85131DA0179FE9FF8100FF,  # noqa: E501
                22: 0x2B5E9D7A094C19F5EBDD4F2E618F859ED15E4F1F0351F286BF849EB7F810001,  # noqa: E501
                23: 0xC73B7A6F68385C653A24993BB72EEA0E4BA17470816EC658CF9C5BEDFD81FF01,  # noqa: E501
                24: 0xB89FC178355660FE1C92C7D8FF11524702FAD6E2255447946442356B00810101,  # noqa: E501
                35: 0x4EE4CEEAAC565C81F55A87C43F82F7C889EF4FC7C679671E28D594FF7F000001,  # noqa: E501
                36: 0x82F46A1B4E34D66712910615D2571D75606CEAC51FA8CA8C58CF6CA881FE00FF,  # noqa: E501
                37: 0x81C9FCEFA5DE158AE2007F25D35C0D11CD735342A48905955A5A6852800200FF,  # noqa: E501
                38: 0x666AC362902470ED850709E2A29969D10CBA09DEBC03C38D172AEAFF81000001,  # noqa: E501
                39: 0xEB30A3C678A01BDE914548F98F3366DC0FFE9F85384EBF1111D03DAD7FFE0101,  # noqa: E501
                40: 0x72D0A7939B6303CE1D46E6E3F1B8BE303BFDB2B00F41AD8076B0975782020101,  # noqa: E501
                51: 0x109A00E1370D2D2922BF892E85BECB54297354B2E5C75388D514FF7F00000001,  # noqa: E501
                52: 0x54A792F15E9ABA7E4AD9E716BC169EEA3A6E2E9C49BF9B335874613C8081FEFF,  # noqa: E501
                53: 0x5D24A14D8E5E039372CD0F6A0F31E9ED6B75ADBA9F16B1C5B3EDD5BA818300FF,  # noqa: E501
                54: 0x298E2F316B4CCDED5EBF515998D9EC20DF69404B04A441782A6AFF8100000001,  # noqa: E501
                55: 0x4335694E98F372183C62A2339FA4AD161E9B4C42240BDC9452ABFFD07783FF01,  # noqa: E501
                56: 0xF0F0820797315ACD063056BBA76F6A9C3E281CDB5197A233967CA94684830101,  # noqa: E501
                67: 0xE6540CE46EAF70DA9D644015A661E0E245B13F307CB3885514FF7F0000000001,  # noqa: E501
                68: 0x6526B38B05A6325B80E1C84AB41DC934FD70F33F1BD0EAB3D1F61A4707FC00FF,  # noqa: E501
                69: 0xE959516CD27E5D8FD487B72DB2989B3EC2BA9FB7EAD41554526FE5A3040400FF,  # noqa: E501
                70: 0xE7498A48C6CE2530BBE814EE3440C8C44FFFAB7AD8A277AA6AFF810000000001,  # noqa: E501
                71: 0x2DFFA3E901E5A392D15B79F4193D2168147D2AA7C55870B46C3A905D03FC0101,  # noqa: E501
                72: 0xE16EA721C96539EDB4F7FB82DE0DAD8CCCB1E7A6966A6777635F6FB908040101,  # noqa: E501
                83: 0xB581AC185AAD71DB2D177C286929C4C22809E5DCB3085514FF7F000000000001,  # noqa: E501
                84: 0x75789EB2A64BC971389FBD11A1E6D7ABBF95AD25E23FB9AA25E73A0BFC83FEFF,  # noqa: E501
                85: 0xFC403FA42CEB6A0D0D3321BD9B2D8AF25B1B667F87A04F496C78168D078500FF,  # noqa: E501
                86: 0xCEC5EC213B9CB5811F6AE00428FD7B6EF5A1AF39A1F7AA6AFF81000000000001,  # noqa: E501
                87: 0x70AB32233202B98D382D17713FA0BE391EAF74F85BA1740C9C3238C4ED85FF01,  # noqa: E501
                88: 0xB622672A213FAA79B32185FF93A7B27A8499E48F7B032CDB4D1A70300C850101,  # noqa: E501
                99: 0x1948059DE1DEF03C4EC35FC22C2BB8F2BF45DC33085514FF7F00000000000001,  # noqa: E501
                100: 0x41F818A8E24EB6D7BB7B193B4F2B5FDCF4BD0D453F2AC3499D8830D391FA00FF,  # noqa: E501
                101: 0xEDE6FE4A943DFB5D967A2B85D6728759D40D2EF0AE4BC28BBB1867F98C0600FF,  # noqa: E501
                102: 0x83C936CBAAD5DE592BADC2E142FE4EBD6103921F7AA6AFF8100000000000001,  # noqa: E501
                103: 0x57385019FE4E0939CA3F35C37CADFAF52FBA5B1CDFB02DEF3866E8068BFA0101,  # noqa: E501
                104: 0x810AC878BD98428F6BE8C6426BA9F9DA09E3E33BF4FE10BFA3F8B12C92060101,  # noqa: E501
                115: 0x8BB02654111AD8C60AD8AF132283A81F455C33085514FF7F0000000000000001,  # noqa: E501
                116: 0xA8F75C129DBB8466D6703A2A0B8212131B3248D70E2478862AC40FE17485FEFF,  # noqa: E501
                117: 0x5FD4D2DE580383EE59F5E800DDB3F1717CEAE03AEDE19D3DEC5E5A69918700FF,  # noqa: E501
                118: 0xC8624230B524B85D6340DA48A5DB20370FB921F7AA6AFF810000000000000001,  # noqa: E501
                119: 0x287B58A5A13CD7F454468CA616C181712F5ED25433A7D5A894B6CED35F87FF01,  # noqa: E501
                120: 0x9930D11AC2804FA977BF951593C8DFF8498779CC0CDC5812A4FBA2F98870101,  # noqa: E501
                131: 0x230041A0E7602D6E459609ED39081EC55C33085514FF7F000000000000000001,  # noqa: E501
                132: 0xC407D8A413EF9079EAD457ED686A05AC81039C0CAE0A7F6AFD01E8461FF800FF,  # noqa: E501
                133: 0x67A397E0692385E4CD83853AABCE220A94D449E885FA867E96D3EF5E180800FF,  # noqa: E501
                134: 0x70ADD926E753655D6D0EBE9C0F81368FB921F7AA6AFF81000000000000000001,  # noqa: E501
                135: 0xBDCE80B8378E43F13D454B9D0A4C83CF311B8EAA45D5122CFD544A217F80101,  # noqa: E501
                136: 0x629C25790E1488998877A9ECDF0FB69637E77D8A4BDC1B46270093BA20080101,  # noqa: E501
                147: 0x53017D8EB210DB2C8CD4A299079EC55C33085514FF7F00000000000000000001,  # noqa: E501
                148: 0x48BE09B6C6AE2AA660F1972125CECBB1038B5D236ECF766BA786E2C4E887FEFF,  # noqa: E501
                149: 0x2E350D847BA73DC2099F83F532951C47269D9FD7E411B50BAE00A9581F8900FF,  # noqa: E501
                150: 0x13AB9E1F0DF89A184B4D07080B68FB921F7AA6AFF8100000000000000000001,  # noqa: E501
                151: 0xF387ED41C1050F9DA667F429A3E8FB30B61A55EDE97D7B8ACD797A03CD89FF01,  # noqa: E501
                152: 0x525696C22BB3CE00FD2E3F6BBB9B4EA1046A5E31FCFF2FEDF8F8C74D28890101,  # noqa: E501
                163: 0xFE0F60957DC223578A0298879EC55C33085514FF7F0000000000000000000001,  # noqa: E501
                164: 0xC1EA45F348B5D351C4D8FE5C77DA979CADC33D866ACC42E981278896B1F600FF,  # noqa: E501
                165: 0x56DDB29BCA94FB986AC0A40188B3B53F3216B3559BD8324A77EA8BD8A80A00FF,  # noqa: E501
                166: 0x2D49FF6B0BBE177AE9317000B68FB921F7AA6AFF810000000000000000000001,  # noqa: E501
                167: 0x185FA9EAB94CFE3016B69657E83B23FD24CC6960218254231C3DB627A7F60101,  # noqa: E501
                168: 0xA7A0223829F26D6C635368034320563DF4AA5EB62EFC87A42BB35F69B20A0101,  # noqa: E501
                179: 0xE1440264B8EE0CEA0218879EC55C33085514FF7F000000000000000000000001,  # noqa: E501
                180: 0x29575FDCE377B23043E489E358581474BC863187FA85F9945473A2BE5889FEFF,  # noqa: E501
                181: 0x3DF8C030EC521FB109C4D887DBBC14C7C9C9921B27058E3503971B60B18B00FF,  # noqa: E501
                182: 0x67799740340DAF4A30F000B68FB921F7AA6AFF81000000000000000000000001,  # noqa: E501
                183: 0x540A4E4635B40585E09FF10B63FFE310DD717FCA5C0A51570091E25E378BFF01,  # noqa: E501
                184: 0xDBBAEF5C49FFEE61B08CDE6EBC8DBA6E9A62D56C2355D1980CB9E790BC8B0101,  # noqa: E501
                195: 0xB0E95B83A36CE98218879EC55C33085514FF7F00000000000000000000000001,  # noqa: E501
                196: 0xC482AB56EC19186DC48C88F30861A850B2253B1EA6DC021589E569BD47F400FF,  # noqa: E501
                197: 0xCF45C7F9AF4BBE4A83055B55B97777AD5E0A3F08B129C9AE208C5D713C0C00FF,  # noqa: E501
                198: 0xA5CBB62A421049B0F000B68FB921F7AA6AFF8100000000000000000000000001,  # noqa: E501
                199: 0x3BDE6CA66DFFE1BF5D727C3EDEA74C7A4AF43B3912E6256D37705C8F3BF40101,  # noqa: E501
                200: 0x3F49A1E40C5213AA4FFED57EB4C1AD2D181B2AAA289E9D59C2256C43480C0101,  # noqa: E501
                211: 0xE02639036C698218879EC55C33085514FF7F0000000000000000000000000001,  # noqa: E501
                212: 0x8BE664BDE946D939CE551B948B503787942D2A7734509288C1B62FD5C48BFEFF,  # noqa: E501
                213: 0xA923A28E7A75AEF26C51580FFC686879E4A0B404B089BDBCD751D88B478D00FF,  # noqa: E501
                214: 0x41AC5EA30FC9B0F000B68FB921F7AA6AFF810000000000000000000000000001,  # noqa: E501
                215: 0xDAA3A177EC975CB69BB4ACF4A6E1BE7BCC1AD33D1FFAD97510F9FEA9D8DFF01,  # noqa: E501
                216: 0x19E6822BEB889BE28310060F4FB9741BFD50A31FA81EC65DE21F7B02548D0101,  # noqa: E501
                227: 0xDB9902EC698218879EC55C33085514FF7F000000000000000000000000000001,  # noqa: E501
                228: 0x83FAB06C6C8FEF761EBBB9534C06AC2A9D61820623008069062FF3B1E1F200FF,  # noqa: E501
                229: 0x3F791DD183ED5B963BD86E0DBA1A9DD5B8CEEB078F15C73062F1942FD40E00FF,  # noqa: E501
                230: 0xE0BFA28FC9B0F000B68FB921F7AA6AFF81000000000000000000000000000001,  # noqa: E501
                231: 0x8133B760DFAE27560EB490F235DDFA301F058DEE4F01F3FE4B3567D0D3F20101,  # noqa: E501
                232: 0xCD4CD0124E983AF71620FB5F98275965C6A8BEBC4B8ADC288B63224EE20E0101,  # noqa: E501
                243: 0x9882EC698218879EC55C33085514FF7F00000000000000000000000000000001,  # noqa: E501
                244: 0x75C4915E18B96704209738F5CA765568BB4DC4113D56683977825A132C8DFEFF,  # noqa: E501
                245: 0x5C76839BF5A80B1DA705DBDF43E4DD6770CD7501AF11FF2DAB7918DFE18F00FF,  # noqa: E501
                246: 0xBF228FC9B0F000B68FB921F7AA6AFF8100000000000000000000000000000001,  # noqa: E501
                247: 0xC6A29131E7594004BC2AA79F0D2C402A1409C57C77D284C14B1A3AB0FF8FFF01,  # noqa: E501
                248: 0xE6B3E5CF6EC90E532FEF7D08455EBF92A03E9E3F6E224EA0FEBDF1A9F08F0101,  # noqa: E501
                259: 0x82EC698218879EC55C33085514FF7F0000000000000000000000000000000001,  # noqa: E501
                260: 0x3122F4BCDF6DD8B265CD18EB6AF28C879AED44A35E0BF59273E39E6C7FF000FF,  # noqa: E501
                261: 0x6A2B3BC87A02C29B9D27757DF43047ECD0F15485270FCA27417A701C701000FF,  # noqa: E501
                262: 0x228FC9B0F000B68FB921F7AA6AFF810000000000000000000000000000000001,  # noqa: E501
                263: 0x88E1259502EEF93D46060AACC9E2FF506C734DADE0B6714AB12D17E46FF00101,  # noqa: E501
                264: 0x4A103813C12C12169B218296BB0A9EAE80CF8D2B158AA70EB990F99480100101,  # noqa: E501
                275: 0xEC698218879EC55C33085514FF7F000000000000000000000000000000000001,  # noqa: E501
                276: 0x722AD218EB1995A2D257C4C06D8DE993C203CFC8E3512DF7D633E17E908FFEFF,  # noqa: E501
                277: 0x8AC9B5EC08D74612CB29F941481D274B51721AF2296207C0DA8D24667F9100FF,  # noqa: E501
                278: 0x8FC9B0F000B68FB921F7AA6AFF81000000000000000000000000000000000001,  # noqa: E501
                279: 0x81D5FF63680841482299F3EAB616446DCD336F537C0C565AA4112AB95D91FF01,  # noqa: E501
                280: 0x9C6CA90DAC4E97DEA02AC969E8649EE9E6232E0C3F4797411151CB8F90910101,  # noqa: E501
                291: 0x698218879EC55C33085514FF7F00000000000000000000000000000000000001,  # noqa: E501
                292: 0x8A2CBD9F40794E2205B13306F2AA0A43C60823C64B95D8601FA4F1E521EE00FF,  # noqa: E501
                293: 0xC1B5A1E3A81DA51B10D84E880F0113FF67B863DDAD3FAF1F4ECF413F101200FF,  # noqa: E501
                294: 0xC9B0F000B68FB921F7AA6AFF8100000000000000000000000000000000000001,  # noqa: E501
                295: 0x410BE68E49452A1FBCD863BF6E8D637F8EAE4979C34C88D552AFBCC20FEE0101,  # noqa: E501
                296: 0xF540CB714754B5B1EB0373833833BD7FB0EE925CE8B92962500B7A1C22120101,  # noqa: E501
                307: 0x8218879EC55C33085514FF7F0000000000000000000000000000000000000001,  # noqa: E501
                308: 0xB795AD7AC24CFBB7435CF53BD3584F3D4B2709935635C3CEB66E761FF091FEFF,  # noqa: E501
                309: 0x1F0BB7BE91A0CCD0CCA93D75CF03DE3E6B56FE8F1C54242617665327219300FF,  # noqa: E501
                310: 0xB0F000B68FB921F7AA6AFF810000000000000000000000000000000000000001,  # noqa: E501
                311: 0xAD571756ECBFF1BFDEF064861E5E92C5D897A9CC380E54BDBAABD80BB793FF01,  # noqa: E501
                312: 0xD8B5B531989E689F700DCDB43AB90E79A49DFBBB5A13DBF751DF98BB34930101,  # noqa: E501
                323: 0x18879EC55C33085514FF7F000000000000000000000000000000000000000001,  # noqa: E501
                324: 0x67E4797DC21F02CE4A7C52218C7DBEA5D212E6C244E24F0BA4C08613C7EC00FF,  # noqa: E501
                325: 0xA1CE1A085F258785846939CC1D2E8725AC94AD4DFF8913234E00679FB41400FF,  # noqa: E501
                326: 0xF000B68FB921F7AA6AFF81000000000000000000000000000000000000000001,  # noqa: E501
                327: 0xCCE501857A1CB45473915A28082AF950E0F78F7E2DE68CE748ADB661B3EC0101,  # noqa: E501
                328: 0x3B2E28D274A16C08B58A23BAD63BBA6D7B09685769D1F68CA3873BEDC8140101,  # noqa: E501
                339: 0x879EC55C33085514FF7F00000000000000000000000000000000000000000001,  # noqa: E501
                340: 0x7FD07055FF50CDFE4B4BD9A15133D72D3607D92EB7AC81BAC93DB7FF4C93FEFF,  # noqa: E501
                341: 0x665AC5C769E87F61D5993ABC26522FBFCA2734D76A63216B2D550D29C79500FF,  # noqa: E501
                342: 0xB68FB921F7AA6AFF8100000000000000000000000000000000000000000001,  # noqa: E501
                343: 0x1C93DB67C9884BC694686D69A25A5D7ED089841D5CE147FDD7199AB00D95FF01,  # noqa: E501
                344: 0x485053D8FF66BE52036597520344FAC87B6A305426A9E49221D3F934DC950101,  # noqa: E501
                355: 0x9EC55C33085514FF7F0000000000000000000000000000000000000000000001,  # noqa: E501
                356: 0xEC447E662AC08957D7E290A421DBF54C0AAF43AADC9CC465AD0B02F071EA00FF,  # noqa: E501
                357: 0xDC9178D3BAB470096F01477C859B5F4173986640B659426412A653465C1600FF,  # noqa: E501
                358: 0xB68FB921F7AA6AFF810000000000000000000000000000000000000000000001,  # noqa: E501
                359: 0xDCF0A770777610503596AE0311AF46C171151ED45107D7E7BB8F74BB5BEA0101,  # noqa: E501
                360: 0x4D65773387993928C95C861274232D3FB6F6B7FE1B22E4E61A30E71172160101,  # noqa: E501
                371: 0xC55C33085514FF7F000000000000000000000000000000000000000000000001,  # noqa: E501
                372: 0x537CA0F03F974303005F1E6693B55B72315A166841732E42B8353724A495FEFF,  # noqa: E501
                373: 0x86418797EC60058DE6CCA47DFDBEE79923AC49D7801E01840041CA76719700FF,  # noqa: E501
                374: 0x8FB921F7AA6AFF81000000000000000000000000000000000000000000000001,  # noqa: E501
                375: 0x56A55341AB8D4318F1CFB55D5F21E2BA35D7E070A72BAC6B2B21BAAE5F97FF01,  # noqa: E501
                376: 0x55DDD0EC77909DE6D8311116CF520398E816F928B06FDD90EC239D0488970101,  # noqa: E501
                387: 0x5C33085514FF7F00000000000000000000000000000000000000000000000001,  # noqa: E501
                388: 0xD542E526003539EAD104274AFF2D78332366E29D328C2161F0C120731FE800FF,  # noqa: E501
                389: 0xC706CB25E8384CE9BB5C9CB48415238BA03E16C448E292C0A101843B081800FF,  # noqa: E501
                390: 0xB921F7AA6AFF8100000000000000000000000000000000000000000000000001,  # noqa: E501
                391: 0x4CA55F89202C524CB0F1CB3195D13C8D94A9F7A05C59E1D4031577C707E80101,  # noqa: E501
                392: 0x8C4B0574E9156B80035F3ECDCF1FE79D273ED7559747A4322BCD338F20180101,  # noqa: E501
                403: 0x33085514FF7F0000000000000000000000000000000000000000000000000001,  # noqa: E501
                404: 0x7F510DD7198CAC0A92FF7EA80451838C0DFA12114C41A0EF05907397F897FEFF,  # noqa: E501
                405: 0x1275E752B6AEE228ECBA5E9B57EF1111DEFF3C651E2CFBF2CCCD13151F9900FF,  # noqa: E501
                406: 0x21F7AA6AFF810000000000000000000000000000000000000000000000000001,  # noqa: E501
                407: 0x6646340AD51A03BB710CAF05756B685B33C7DAD62AE68D369243700EAD99FF01,  # noqa: E501
                408: 0x29D80E8060EF2221929BB18215586C742686D6860E028CA0456B443238990101,  # noqa: E501
                419: 0x85514FF7F000000000000000000000000000000000000000000000000000001,  # noqa: E501
                420: 0x1D164DB738EB6893868B361AD2803F97BE35764456E82A837667A693D1E600FF,  # noqa: E501
                421: 0x8B92C24ABEBF376A5AAB5FF4DFD3538A03D38A10BCED2AAE8E1A8A85B81A00FF,  # noqa: E501
                422: 0xF7AA6AFF81000000000000000000000000000000000000000000000000000001,  # noqa: E501
                423: 0x6931BDA98C70E860A1F6A5224940F1EC7E6734CD9456C95806384F7CB7E60101,  # noqa: E501
                424: 0x3402A9DB66492DFC2A220715E76243469462F24EDC56903BA1D8E96ED21A0101,  # noqa: E501
                435: 0x5514FF7F00000000000000000000000000000000000000000000000000000001,  # noqa: E501
                436: 0x178918FFBCB401D4EFD2F7DFB4D01A897172267F0F491121AC52DD614899FEFF,  # noqa: E501
                437: 0x38ECFF71480CA0B422F2ED6F780D5FEAD2AE234A49104B10A86F7F0DD19B00FF,  # noqa: E501
                438: 0xAA6AFF8100000000000000000000000000000000000000000000000000000001,  # noqa: E501
                439: 0xD02811CB5DC1D80567E810532B235B7672F5C78CD6E89BB511D5E2D8F79BFF01,  # noqa: E501
                440: 0x1B4E6404F474C18055D30BB8987672F59E97980D6F9DE1764C0FBEC5EC9B0101,  # noqa: E501
                451: 0x14FF7F0000000000000000000000000000000000000000000000000000000001,  # noqa: E501
                452: 0xFFD368E44B3F85CB81AE394C9809CA9FA2DB46A83D7880A912AB6D4A87E400FF,  # noqa: E501
                453: 0x981AD53C19B15A94BCF0BF20235DD0DA9DF25F46AE635029FE2062E6C1C00FF,  # noqa: E501
                454: 0x6AFF810000000000000000000000000000000000000000000000000000000001,  # noqa: E501
                455: 0x19DF06FFA28250867006726405FBC05D43DC2F9D2F025006DB089BD46BE40101,  # noqa: E501
                456: 0x243FFFE3A4F2982F45055C08F379648AB886DA8027A7401117A8E0B8881C0101,  # noqa: E501
                467: 0xFF7F000000000000000000000000000000000000000000000000000000000001,  # noqa: E501
                468: 0x41E065D46E0349CFE624C4E8A2034AEA1F7EDFFF80E511CD8067D488949BFEFF,  # noqa: E501
                469: 0xA84162CA6675A22C4C79DFC4EA15F760DB5A04DBF04246764199B668879D00FF,  # noqa: E501
                470: 0xFF81000000000000000000000000000000000000000000000000000000000001,  # noqa: E501
                471: 0x1226984FAA6B05EBDBD45D8477FA4FD5B55BFD5061DE03C319282B153D9DFF01,  # noqa: E501
                472: 0x5CC9E6B0B749FD94541AD00364BDEC2FCA7816981CA3E38F485DECC7A49D0101,  # noqa: E501
                483: 0x7F00000000000000000000000000000000000000000000000000000000000001,  # noqa: E501
                484: 0xE9772778F50FA0A69CD10FA019AC56D72AC7A7D7AF26C4BA28415C8F41E200FF,  # noqa: E501
                485: 0x33F0385EF73FEEBDB952E5ADB643DD0FA178FD9271578219AD50A73D241E00FF,  # noqa: E501
                486: 0x8100000000000000000000000000000000000000000000000000000000000001,  # noqa: E501
                487: 0xFD405CCE8F73DFFC04A6F0FF6FFC6BF7961876D09C5B4933A68F0CC623E20101,  # noqa: E501
                488: 0xC5A8F4566FD2E96E4CE3A8B3EC0863E7B20BC3B2F3DC5261BA8A0174421E0101,  # noqa: E501
                499: 1,
                500: 0xF9CB87F5B1AB58602F52A1E9D392E5675B86A59A53943A8D4EC2A915DC9DFEFF,  # noqa: E501
                501: 0x893D729A64E318860EC5047E70E598DA163EB41E71E74B04DFD4712D419F00FF,  # noqa: E501
                502: 1,
                503: 0xEE5F2839C1B4F6CA05E6FDB04E2FB49C0F860B3765C27DC781A150CB7F9FFF01,  # noqa: E501
                504: 0xB4C358E3C6BCDDFB509EA487D733DF0E1854F29C3B6BFD4A8CAABE3F609F0101,  # noqa: E501
                512: 1,
                515: 1,
                516: 0xB8247842BB5CE75C08D0C251669ED5870FA24A22952E5DB3A7C66C59FFE000FF,  # noqa: E501
                517: 0xEE526E5A06F2A990B2BF6C951E5FEABF0E07EE16877296E1BE872DB9E02000FF,  # noqa: E501
                518: 1,
                519: 0xEDA7D024B6DE40A9D3B966E71F10A4667EDC5B71CAB07AEABCAC6249DFE00101,  # noqa: E501
                520: 0x512ECFAEEB11205F0833E1054DCB1300488E0954BE5AF77A49E143AA00200101,  # noqa: E501
                528: 1,
                531: 1,
                532: 0x8DCB65B5494EBA78CD6756A6F9851F6E26D0F2BB9ECD7E9ABD7E9B11209FFEFF,  # noqa: E501
                533: 0x6694BB31B20CD625F3756897DAE6D738F2E64467B5B6F10FA3E07763FFA100FF,  # noqa: E501
                534: 1,
                535: 0xE678999AEFFD1F1F45081F64DE7F80AB083DD7DF04721ED64EE04C03BDA1FF01,  # noqa: E501
                536: 0x39B68FB9898DD7568ABD178397251CE8226A25C1D305A4E79573333520A10101,  # noqa: E501
            },
        ),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
