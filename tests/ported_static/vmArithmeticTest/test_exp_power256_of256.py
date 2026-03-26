"""
Ori Pomerantz qbzzt1@gmail.com

Ported from:
state_tests/VMTests/vmArithmeticTest/expPower256Of256Filler.yml
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
    ["state_tests/VMTests/vmArithmeticTest/expPower256Of256Filler.yml"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_exp_power256_of256(
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
    target = pre.deploy_contract(
        code=Op.SSTORE(key=Op.MUL(0x10, 0x0), value=Op.EXP(0x100, Op.EXP(0x100, 0x0)))  # noqa: E501
        + Op.SSTORE(key=Op.ADD(Op.MUL(0x10, 0x0), 0x1), value=Op.EXP(0x100, Op.EXP(0xff, 0x0)))  # noqa: E501
        + Op.SSTORE(key=Op.ADD(Op.MUL(0x10, 0x0), 0x2), value=Op.EXP(0x100, Op.EXP(0x101, 0x0)))  # noqa: E501
        + Op.SSTORE(key=Op.ADD(Op.MUL(0x10, 0x0), 0x3), value=Op.EXP(0xff, Op.EXP(0x100, 0x0)))  # noqa: E501
        + Op.SSTORE(key=Op.ADD(Op.MUL(0x10, 0x0), 0x4), value=Op.EXP(0xff, Op.EXP(0xff, 0x0)))  # noqa: E501
        + Op.SSTORE(key=Op.ADD(Op.MUL(0x10, 0x0), 0x5), value=Op.EXP(0xff, Op.EXP(0x101, 0x0)))  # noqa: E501
        + Op.SSTORE(key=Op.ADD(Op.MUL(0x10, 0x0), 0x6), value=Op.EXP(0x101, Op.EXP(0x100, 0x0)))  # noqa: E501
        + Op.SSTORE(key=Op.ADD(Op.MUL(0x10, 0x0), 0x7), value=Op.EXP(0x101, Op.EXP(0xff, 0x0)))  # noqa: E501
        + Op.SSTORE(key=Op.ADD(Op.MUL(0x10, 0x0), 0x8), value=Op.EXP(0x101, Op.EXP(0x101, 0x0)))  # noqa: E501
        + Op.SSTORE(key=Op.MUL(0x10, 0x1), value=Op.EXP(0x100, Op.EXP(0x100, 0x1)))  # noqa: E501
        + Op.SSTORE(key=Op.ADD(Op.MUL(0x10, 0x1), 0x1), value=Op.EXP(0x100, Op.EXP(0xff, 0x1)))  # noqa: E501
        + Op.SSTORE(key=Op.ADD(Op.MUL(0x10, 0x1), 0x2), value=Op.EXP(0x100, Op.EXP(0x101, 0x1)))  # noqa: E501
        + Op.SSTORE(key=Op.ADD(Op.MUL(0x10, 0x1), 0x3), value=Op.EXP(0xff, Op.EXP(0x100, 0x1)))  # noqa: E501
        + Op.SSTORE(key=Op.ADD(Op.MUL(0x10, 0x1), 0x4), value=Op.EXP(0xff, Op.EXP(0xff, 0x1)))  # noqa: E501
        + Op.SSTORE(key=Op.ADD(Op.MUL(0x10, 0x1), 0x5), value=Op.EXP(0xff, Op.EXP(0x101, 0x1)))  # noqa: E501
        + Op.SSTORE(key=Op.ADD(Op.MUL(0x10, 0x1), 0x6), value=Op.EXP(0x101, Op.EXP(0x100, 0x1)))  # noqa: E501
        + Op.SSTORE(key=Op.ADD(Op.MUL(0x10, 0x1), 0x7), value=Op.EXP(0x101, Op.EXP(0xff, 0x1)))  # noqa: E501
        + Op.SSTORE(key=Op.ADD(Op.MUL(0x10, 0x1), 0x8), value=Op.EXP(0x101, Op.EXP(0x101, 0x1)))  # noqa: E501
        + Op.SSTORE(key=Op.MUL(0x10, 0x2), value=Op.EXP(0x100, Op.EXP(0x100, 0x2)))  # noqa: E501
        + Op.SSTORE(key=Op.ADD(Op.MUL(0x10, 0x2), 0x1), value=Op.EXP(0x100, Op.EXP(0xff, 0x2)))  # noqa: E501
        + Op.SSTORE(key=Op.ADD(Op.MUL(0x10, 0x2), 0x2), value=Op.EXP(0x100, Op.EXP(0x101, 0x2)))  # noqa: E501
        + Op.SSTORE(key=Op.ADD(Op.MUL(0x10, 0x2), 0x3), value=Op.EXP(0xff, Op.EXP(0x100, 0x2)))  # noqa: E501
        + Op.SSTORE(key=Op.ADD(Op.MUL(0x10, 0x2), 0x4), value=Op.EXP(0xff, Op.EXP(0xff, 0x2)))  # noqa: E501
        + Op.SSTORE(key=Op.ADD(Op.MUL(0x10, 0x2), 0x5), value=Op.EXP(0xff, Op.EXP(0x101, 0x2)))  # noqa: E501
        + Op.SSTORE(key=Op.ADD(Op.MUL(0x10, 0x2), 0x6), value=Op.EXP(0x101, Op.EXP(0x100, 0x2)))  # noqa: E501
        + Op.SSTORE(key=Op.ADD(Op.MUL(0x10, 0x2), 0x7), value=Op.EXP(0x101, Op.EXP(0xff, 0x2)))  # noqa: E501
        + Op.SSTORE(key=Op.ADD(Op.MUL(0x10, 0x2), 0x8), value=Op.EXP(0x101, Op.EXP(0x101, 0x2)))  # noqa: E501
        + Op.SSTORE(key=Op.MUL(0x10, 0x3), value=Op.EXP(0x100, Op.EXP(0x100, 0x3)))  # noqa: E501
        + Op.SSTORE(key=Op.ADD(Op.MUL(0x10, 0x3), 0x1), value=Op.EXP(0x100, Op.EXP(0xff, 0x3)))  # noqa: E501
        + Op.SSTORE(key=Op.ADD(Op.MUL(0x10, 0x3), 0x2), value=Op.EXP(0x100, Op.EXP(0x101, 0x3)))  # noqa: E501
        + Op.SSTORE(key=Op.ADD(Op.MUL(0x10, 0x3), 0x3), value=Op.EXP(0xff, Op.EXP(0x100, 0x3)))  # noqa: E501
        + Op.SSTORE(key=Op.ADD(Op.MUL(0x10, 0x3), 0x4), value=Op.EXP(0xff, Op.EXP(0xff, 0x3)))  # noqa: E501
        + Op.SSTORE(key=Op.ADD(Op.MUL(0x10, 0x3), 0x5), value=Op.EXP(0xff, Op.EXP(0x101, 0x3)))  # noqa: E501
        + Op.SSTORE(key=Op.ADD(Op.MUL(0x10, 0x3), 0x6), value=Op.EXP(0x101, Op.EXP(0x100, 0x3)))  # noqa: E501
        + Op.SSTORE(key=Op.ADD(Op.MUL(0x10, 0x3), 0x7), value=Op.EXP(0x101, Op.EXP(0xff, 0x3)))  # noqa: E501
        + Op.SSTORE(key=Op.ADD(Op.MUL(0x10, 0x3), 0x8), value=Op.EXP(0x101, Op.EXP(0x101, 0x3)))  # noqa: E501
        + Op.SSTORE(key=Op.MUL(0x10, 0x4), value=Op.EXP(0x100, Op.EXP(0x100, 0x4)))  # noqa: E501
        + Op.SSTORE(key=Op.ADD(Op.MUL(0x10, 0x4), 0x1), value=Op.EXP(0x100, Op.EXP(0xff, 0x4)))  # noqa: E501
        + Op.SSTORE(key=Op.ADD(Op.MUL(0x10, 0x4), 0x2), value=Op.EXP(0x100, Op.EXP(0x101, 0x4)))  # noqa: E501
        + Op.SSTORE(key=Op.ADD(Op.MUL(0x10, 0x4), 0x3), value=Op.EXP(0xff, Op.EXP(0x100, 0x4)))  # noqa: E501
        + Op.SSTORE(key=Op.ADD(Op.MUL(0x10, 0x4), 0x4), value=Op.EXP(0xff, Op.EXP(0xff, 0x4)))  # noqa: E501
        + Op.SSTORE(key=Op.ADD(Op.MUL(0x10, 0x4), 0x5), value=Op.EXP(0xff, Op.EXP(0x101, 0x4)))  # noqa: E501
        + Op.SSTORE(key=Op.ADD(Op.MUL(0x10, 0x4), 0x6), value=Op.EXP(0x101, Op.EXP(0x100, 0x4)))  # noqa: E501
        + Op.SSTORE(key=Op.ADD(Op.MUL(0x10, 0x4), 0x7), value=Op.EXP(0x101, Op.EXP(0xff, 0x4)))  # noqa: E501
        + Op.SSTORE(key=Op.ADD(Op.MUL(0x10, 0x4), 0x8), value=Op.EXP(0x101, Op.EXP(0x101, 0x4)))  # noqa: E501
        + Op.SSTORE(key=Op.MUL(0x10, 0x5), value=Op.EXP(0x100, Op.EXP(0x100, 0x5)))  # noqa: E501
        + Op.SSTORE(key=Op.ADD(Op.MUL(0x10, 0x5), 0x1), value=Op.EXP(0x100, Op.EXP(0xff, 0x5)))  # noqa: E501
        + Op.SSTORE(key=Op.ADD(Op.MUL(0x10, 0x5), 0x2), value=Op.EXP(0x100, Op.EXP(0x101, 0x5)))  # noqa: E501
        + Op.SSTORE(key=Op.ADD(Op.MUL(0x10, 0x5), 0x3), value=Op.EXP(0xff, Op.EXP(0x100, 0x5)))  # noqa: E501
        + Op.SSTORE(key=Op.ADD(Op.MUL(0x10, 0x5), 0x4), value=Op.EXP(0xff, Op.EXP(0xff, 0x5)))  # noqa: E501
        + Op.SSTORE(key=Op.ADD(Op.MUL(0x10, 0x5), 0x5), value=Op.EXP(0xff, Op.EXP(0x101, 0x5)))  # noqa: E501
        + Op.SSTORE(key=Op.ADD(Op.MUL(0x10, 0x5), 0x6), value=Op.EXP(0x101, Op.EXP(0x100, 0x5)))  # noqa: E501
        + Op.SSTORE(key=Op.ADD(Op.MUL(0x10, 0x5), 0x7), value=Op.EXP(0x101, Op.EXP(0xff, 0x5)))  # noqa: E501
        + Op.SSTORE(key=Op.ADD(Op.MUL(0x10, 0x5), 0x8), value=Op.EXP(0x101, Op.EXP(0x101, 0x5)))  # noqa: E501
        + Op.SSTORE(key=Op.MUL(0x10, 0x6), value=Op.EXP(0x100, Op.EXP(0x100, 0x6)))  # noqa: E501
        + Op.SSTORE(key=Op.ADD(Op.MUL(0x10, 0x6), 0x1), value=Op.EXP(0x100, Op.EXP(0xff, 0x6)))  # noqa: E501
        + Op.SSTORE(key=Op.ADD(Op.MUL(0x10, 0x6), 0x2), value=Op.EXP(0x100, Op.EXP(0x101, 0x6)))  # noqa: E501
        + Op.SSTORE(key=Op.ADD(Op.MUL(0x10, 0x6), 0x3), value=Op.EXP(0xff, Op.EXP(0x100, 0x6)))  # noqa: E501
        + Op.SSTORE(key=Op.ADD(Op.MUL(0x10, 0x6), 0x4), value=Op.EXP(0xff, Op.EXP(0xff, 0x6)))  # noqa: E501
        + Op.SSTORE(key=Op.ADD(Op.MUL(0x10, 0x6), 0x5), value=Op.EXP(0xff, Op.EXP(0x101, 0x6)))  # noqa: E501
        + Op.SSTORE(key=Op.ADD(Op.MUL(0x10, 0x6), 0x6), value=Op.EXP(0x101, Op.EXP(0x100, 0x6)))  # noqa: E501
        + Op.SSTORE(key=Op.ADD(Op.MUL(0x10, 0x6), 0x7), value=Op.EXP(0x101, Op.EXP(0xff, 0x6)))  # noqa: E501
        + Op.SSTORE(key=Op.ADD(Op.MUL(0x10, 0x6), 0x8), value=Op.EXP(0x101, Op.EXP(0x101, 0x6)))  # noqa: E501
        + Op.SSTORE(key=Op.MUL(0x10, 0x7), value=Op.EXP(0x100, Op.EXP(0x100, 0x7)))  # noqa: E501
        + Op.SSTORE(key=Op.ADD(Op.MUL(0x10, 0x7), 0x1), value=Op.EXP(0x100, Op.EXP(0xff, 0x7)))  # noqa: E501
        + Op.SSTORE(key=Op.ADD(Op.MUL(0x10, 0x7), 0x2), value=Op.EXP(0x100, Op.EXP(0x101, 0x7)))  # noqa: E501
        + Op.SSTORE(key=Op.ADD(Op.MUL(0x10, 0x7), 0x3), value=Op.EXP(0xff, Op.EXP(0x100, 0x7)))  # noqa: E501
        + Op.SSTORE(key=Op.ADD(Op.MUL(0x10, 0x7), 0x4), value=Op.EXP(0xff, Op.EXP(0xff, 0x7)))  # noqa: E501
        + Op.SSTORE(key=Op.ADD(Op.MUL(0x10, 0x7), 0x5), value=Op.EXP(0xff, Op.EXP(0x101, 0x7)))  # noqa: E501
        + Op.SSTORE(key=Op.ADD(Op.MUL(0x10, 0x7), 0x6), value=Op.EXP(0x101, Op.EXP(0x100, 0x7)))  # noqa: E501
        + Op.SSTORE(key=Op.ADD(Op.MUL(0x10, 0x7), 0x7), value=Op.EXP(0x101, Op.EXP(0xff, 0x7)))  # noqa: E501
        + Op.SSTORE(key=Op.ADD(Op.MUL(0x10, 0x7), 0x8), value=Op.EXP(0x101, Op.EXP(0x101, 0x7)))  # noqa: E501
        + Op.SSTORE(key=Op.MUL(0x10, 0x8), value=Op.EXP(0x100, Op.EXP(0x100, 0x8)))  # noqa: E501
        + Op.SSTORE(key=Op.ADD(Op.MUL(0x10, 0x8), 0x1), value=Op.EXP(0x100, Op.EXP(0xff, 0x8)))  # noqa: E501
        + Op.SSTORE(key=Op.ADD(Op.MUL(0x10, 0x8), 0x2), value=Op.EXP(0x100, Op.EXP(0x101, 0x8)))  # noqa: E501
        + Op.SSTORE(key=Op.ADD(Op.MUL(0x10, 0x8), 0x3), value=Op.EXP(0xff, Op.EXP(0x100, 0x8)))  # noqa: E501
        + Op.SSTORE(key=Op.ADD(Op.MUL(0x10, 0x8), 0x4), value=Op.EXP(0xff, Op.EXP(0xff, 0x8)))  # noqa: E501
        + Op.SSTORE(key=Op.ADD(Op.MUL(0x10, 0x8), 0x5), value=Op.EXP(0xff, Op.EXP(0x101, 0x8)))  # noqa: E501
        + Op.SSTORE(key=Op.ADD(Op.MUL(0x10, 0x8), 0x6), value=Op.EXP(0x101, Op.EXP(0x100, 0x8)))  # noqa: E501
        + Op.SSTORE(key=Op.ADD(Op.MUL(0x10, 0x8), 0x7), value=Op.EXP(0x101, Op.EXP(0xff, 0x8)))  # noqa: E501
        + Op.SSTORE(key=Op.ADD(Op.MUL(0x10, 0x8), 0x8), value=Op.EXP(0x101, Op.EXP(0x101, 0x8)))  # noqa: E501
        + Op.SSTORE(key=Op.MUL(0x10, 0x9), value=Op.EXP(0x100, Op.EXP(0x100, 0x9)))  # noqa: E501
        + Op.SSTORE(key=Op.ADD(Op.MUL(0x10, 0x9), 0x1), value=Op.EXP(0x100, Op.EXP(0xff, 0x9)))  # noqa: E501
        + Op.SSTORE(key=Op.ADD(Op.MUL(0x10, 0x9), 0x2), value=Op.EXP(0x100, Op.EXP(0x101, 0x9)))  # noqa: E501
        + Op.SSTORE(key=Op.ADD(Op.MUL(0x10, 0x9), 0x3), value=Op.EXP(0xff, Op.EXP(0x100, 0x9)))  # noqa: E501
        + Op.SSTORE(key=Op.ADD(Op.MUL(0x10, 0x9), 0x4), value=Op.EXP(0xff, Op.EXP(0xff, 0x9)))  # noqa: E501
        + Op.SSTORE(key=Op.ADD(Op.MUL(0x10, 0x9), 0x5), value=Op.EXP(0xff, Op.EXP(0x101, 0x9)))  # noqa: E501
        + Op.SSTORE(key=Op.ADD(Op.MUL(0x10, 0x9), 0x6), value=Op.EXP(0x101, Op.EXP(0x100, 0x9)))  # noqa: E501
        + Op.SSTORE(key=Op.ADD(Op.MUL(0x10, 0x9), 0x7), value=Op.EXP(0x101, Op.EXP(0xff, 0x9)))  # noqa: E501
        + Op.SSTORE(key=Op.ADD(Op.MUL(0x10, 0x9), 0x8), value=Op.EXP(0x101, Op.EXP(0x101, 0x9)))  # noqa: E501
        + Op.SSTORE(key=Op.MUL(0x10, 0xa), value=Op.EXP(0x100, Op.EXP(0x100, 0xa)))  # noqa: E501
        + Op.SSTORE(key=Op.ADD(Op.MUL(0x10, 0xa), 0x1), value=Op.EXP(0x100, Op.EXP(0xff, 0xa)))  # noqa: E501
        + Op.SSTORE(key=Op.ADD(Op.MUL(0x10, 0xa), 0x2), value=Op.EXP(0x100, Op.EXP(0x101, 0xa)))  # noqa: E501
        + Op.SSTORE(key=Op.ADD(Op.MUL(0x10, 0xa), 0x3), value=Op.EXP(0xff, Op.EXP(0x100, 0xa)))  # noqa: E501
        + Op.SSTORE(key=Op.ADD(Op.MUL(0x10, 0xa), 0x4), value=Op.EXP(0xff, Op.EXP(0xff, 0xa)))  # noqa: E501
        + Op.SSTORE(key=Op.ADD(Op.MUL(0x10, 0xa), 0x5), value=Op.EXP(0xff, Op.EXP(0x101, 0xa)))  # noqa: E501
        + Op.SSTORE(key=Op.ADD(Op.MUL(0x10, 0xa), 0x6), value=Op.EXP(0x101, Op.EXP(0x100, 0xa)))  # noqa: E501
        + Op.SSTORE(key=Op.ADD(Op.MUL(0x10, 0xa), 0x7), value=Op.EXP(0x101, Op.EXP(0xff, 0xa)))  # noqa: E501
        + Op.SSTORE(key=Op.ADD(Op.MUL(0x10, 0xa), 0x8), value=Op.EXP(0x101, Op.EXP(0x101, 0xa)))  # noqa: E501
        + Op.SSTORE(key=Op.MUL(0x10, 0xb), value=Op.EXP(0x100, Op.EXP(0x100, 0xb)))  # noqa: E501
        + Op.SSTORE(key=Op.ADD(Op.MUL(0x10, 0xb), 0x1), value=Op.EXP(0x100, Op.EXP(0xff, 0xb)))  # noqa: E501
        + Op.SSTORE(key=Op.ADD(Op.MUL(0x10, 0xb), 0x2), value=Op.EXP(0x100, Op.EXP(0x101, 0xb)))  # noqa: E501
        + Op.SSTORE(key=Op.ADD(Op.MUL(0x10, 0xb), 0x3), value=Op.EXP(0xff, Op.EXP(0x100, 0xb)))  # noqa: E501
        + Op.SSTORE(key=Op.ADD(Op.MUL(0x10, 0xb), 0x4), value=Op.EXP(0xff, Op.EXP(0xff, 0xb)))  # noqa: E501
        + Op.SSTORE(key=Op.ADD(Op.MUL(0x10, 0xb), 0x5), value=Op.EXP(0xff, Op.EXP(0x101, 0xb)))  # noqa: E501
        + Op.SSTORE(key=Op.ADD(Op.MUL(0x10, 0xb), 0x6), value=Op.EXP(0x101, Op.EXP(0x100, 0xb)))  # noqa: E501
        + Op.SSTORE(key=Op.ADD(Op.MUL(0x10, 0xb), 0x7), value=Op.EXP(0x101, Op.EXP(0xff, 0xb)))  # noqa: E501
        + Op.SSTORE(key=Op.ADD(Op.MUL(0x10, 0xb), 0x8), value=Op.EXP(0x101, Op.EXP(0x101, 0xb)))  # noqa: E501
        + Op.SSTORE(key=Op.MUL(0x10, 0xc), value=Op.EXP(0x100, Op.EXP(0x100, 0xc)))  # noqa: E501
        + Op.SSTORE(key=Op.ADD(Op.MUL(0x10, 0xc), 0x1), value=Op.EXP(0x100, Op.EXP(0xff, 0xc)))  # noqa: E501
        + Op.SSTORE(key=Op.ADD(Op.MUL(0x10, 0xc), 0x2), value=Op.EXP(0x100, Op.EXP(0x101, 0xc)))  # noqa: E501
        + Op.SSTORE(key=Op.ADD(Op.MUL(0x10, 0xc), 0x3), value=Op.EXP(0xff, Op.EXP(0x100, 0xc)))  # noqa: E501
        + Op.SSTORE(key=Op.ADD(Op.MUL(0x10, 0xc), 0x4), value=Op.EXP(0xff, Op.EXP(0xff, 0xc)))  # noqa: E501
        + Op.SSTORE(key=Op.ADD(Op.MUL(0x10, 0xc), 0x5), value=Op.EXP(0xff, Op.EXP(0x101, 0xc)))  # noqa: E501
        + Op.SSTORE(key=Op.ADD(Op.MUL(0x10, 0xc), 0x6), value=Op.EXP(0x101, Op.EXP(0x100, 0xc)))  # noqa: E501
        + Op.SSTORE(key=Op.ADD(Op.MUL(0x10, 0xc), 0x7), value=Op.EXP(0x101, Op.EXP(0xff, 0xc)))  # noqa: E501
        + Op.SSTORE(key=Op.ADD(Op.MUL(0x10, 0xc), 0x8), value=Op.EXP(0x101, Op.EXP(0x101, 0xc)))  # noqa: E501
        + Op.SSTORE(key=Op.MUL(0x10, 0xd), value=Op.EXP(0x100, Op.EXP(0x100, 0xd)))  # noqa: E501
        + Op.SSTORE(key=Op.ADD(Op.MUL(0x10, 0xd), 0x1), value=Op.EXP(0x100, Op.EXP(0xff, 0xd)))  # noqa: E501
        + Op.SSTORE(key=Op.ADD(Op.MUL(0x10, 0xd), 0x2), value=Op.EXP(0x100, Op.EXP(0x101, 0xd)))  # noqa: E501
        + Op.SSTORE(key=Op.ADD(Op.MUL(0x10, 0xd), 0x3), value=Op.EXP(0xff, Op.EXP(0x100, 0xd)))  # noqa: E501
        + Op.SSTORE(key=Op.ADD(Op.MUL(0x10, 0xd), 0x4), value=Op.EXP(0xff, Op.EXP(0xff, 0xd)))  # noqa: E501
        + Op.SSTORE(key=Op.ADD(Op.MUL(0x10, 0xd), 0x5), value=Op.EXP(0xff, Op.EXP(0x101, 0xd)))  # noqa: E501
        + Op.SSTORE(key=Op.ADD(Op.MUL(0x10, 0xd), 0x6), value=Op.EXP(0x101, Op.EXP(0x100, 0xd)))  # noqa: E501
        + Op.SSTORE(key=Op.ADD(Op.MUL(0x10, 0xd), 0x7), value=Op.EXP(0x101, Op.EXP(0xff, 0xd)))  # noqa: E501
        + Op.SSTORE(key=Op.ADD(Op.MUL(0x10, 0xd), 0x8), value=Op.EXP(0x101, Op.EXP(0x101, 0xd)))  # noqa: E501
        + Op.SSTORE(key=Op.MUL(0x10, 0xe), value=Op.EXP(0x100, Op.EXP(0x100, 0xe)))  # noqa: E501
        + Op.SSTORE(key=Op.ADD(Op.MUL(0x10, 0xe), 0x1), value=Op.EXP(0x100, Op.EXP(0xff, 0xe)))  # noqa: E501
        + Op.SSTORE(key=Op.ADD(Op.MUL(0x10, 0xe), 0x2), value=Op.EXP(0x100, Op.EXP(0x101, 0xe)))  # noqa: E501
        + Op.SSTORE(key=Op.ADD(Op.MUL(0x10, 0xe), 0x3), value=Op.EXP(0xff, Op.EXP(0x100, 0xe)))  # noqa: E501
        + Op.SSTORE(key=Op.ADD(Op.MUL(0x10, 0xe), 0x4), value=Op.EXP(0xff, Op.EXP(0xff, 0xe)))  # noqa: E501
        + Op.SSTORE(key=Op.ADD(Op.MUL(0x10, 0xe), 0x5), value=Op.EXP(0xff, Op.EXP(0x101, 0xe)))  # noqa: E501
        + Op.SSTORE(key=Op.ADD(Op.MUL(0x10, 0xe), 0x6), value=Op.EXP(0x101, Op.EXP(0x100, 0xe)))  # noqa: E501
        + Op.SSTORE(key=Op.ADD(Op.MUL(0x10, 0xe), 0x7), value=Op.EXP(0x101, Op.EXP(0xff, 0xe)))  # noqa: E501
        + Op.SSTORE(key=Op.ADD(Op.MUL(0x10, 0xe), 0x8), value=Op.EXP(0x101, Op.EXP(0x101, 0xe)))  # noqa: E501
        + Op.SSTORE(key=Op.MUL(0x10, 0xf), value=Op.EXP(0x100, Op.EXP(0x100, 0xf)))  # noqa: E501
        + Op.SSTORE(key=Op.ADD(Op.MUL(0x10, 0xf), 0x1), value=Op.EXP(0x100, Op.EXP(0xff, 0xf)))  # noqa: E501
        + Op.SSTORE(key=Op.ADD(Op.MUL(0x10, 0xf), 0x2), value=Op.EXP(0x100, Op.EXP(0x101, 0xf)))  # noqa: E501
        + Op.SSTORE(key=Op.ADD(Op.MUL(0x10, 0xf), 0x3), value=Op.EXP(0xff, Op.EXP(0x100, 0xf)))  # noqa: E501
        + Op.SSTORE(key=Op.ADD(Op.MUL(0x10, 0xf), 0x4), value=Op.EXP(0xff, Op.EXP(0xff, 0xf)))  # noqa: E501
        + Op.SSTORE(key=Op.ADD(Op.MUL(0x10, 0xf), 0x5), value=Op.EXP(0xff, Op.EXP(0x101, 0xf)))  # noqa: E501
        + Op.SSTORE(key=Op.ADD(Op.MUL(0x10, 0xf), 0x6), value=Op.EXP(0x101, Op.EXP(0x100, 0xf)))  # noqa: E501
        + Op.SSTORE(key=Op.ADD(Op.MUL(0x10, 0xf), 0x7), value=Op.EXP(0x101, Op.EXP(0xff, 0xf)))  # noqa: E501
        + Op.SSTORE(key=Op.ADD(Op.MUL(0x10, 0xf), 0x8), value=Op.EXP(0x101, Op.EXP(0x101, 0xf)))  # noqa: E501
        + Op.SSTORE(key=Op.MUL(0x10, 0x10), value=Op.EXP(0x100, Op.EXP(0x100, 0x10)))  # noqa: E501
        + Op.SSTORE(key=Op.ADD(Op.MUL(0x10, 0x10), 0x1), value=Op.EXP(0x100, Op.EXP(0xff, 0x10)))  # noqa: E501
        + Op.SSTORE(key=Op.ADD(Op.MUL(0x10, 0x10), 0x2), value=Op.EXP(0x100, Op.EXP(0x101, 0x10)))  # noqa: E501
        + Op.SSTORE(key=Op.ADD(Op.MUL(0x10, 0x10), 0x3), value=Op.EXP(0xff, Op.EXP(0x100, 0x10)))  # noqa: E501
        + Op.SSTORE(key=Op.ADD(Op.MUL(0x10, 0x10), 0x4), value=Op.EXP(0xff, Op.EXP(0xff, 0x10)))  # noqa: E501
        + Op.SSTORE(key=Op.ADD(Op.MUL(0x10, 0x10), 0x5), value=Op.EXP(0xff, Op.EXP(0x101, 0x10)))  # noqa: E501
        + Op.SSTORE(key=Op.ADD(Op.MUL(0x10, 0x10), 0x6), value=Op.EXP(0x101, Op.EXP(0x100, 0x10)))  # noqa: E501
        + Op.SSTORE(key=Op.ADD(Op.MUL(0x10, 0x10), 0x7), value=Op.EXP(0x101, Op.EXP(0xff, 0x10)))  # noqa: E501
        + Op.SSTORE(key=Op.ADD(Op.MUL(0x10, 0x10), 0x8), value=Op.EXP(0x101, Op.EXP(0x101, 0x10)))  # noqa: E501
        + Op.SSTORE(key=Op.MUL(0x10, 0x11), value=Op.EXP(0x100, Op.EXP(0x100, 0x11)))  # noqa: E501
        + Op.SSTORE(key=Op.ADD(Op.MUL(0x10, 0x11), 0x1), value=Op.EXP(0x100, Op.EXP(0xff, 0x11)))  # noqa: E501
        + Op.SSTORE(key=Op.ADD(Op.MUL(0x10, 0x11), 0x2), value=Op.EXP(0x100, Op.EXP(0x101, 0x11)))  # noqa: E501
        + Op.SSTORE(key=Op.ADD(Op.MUL(0x10, 0x11), 0x3), value=Op.EXP(0xff, Op.EXP(0x100, 0x11)))  # noqa: E501
        + Op.SSTORE(key=Op.ADD(Op.MUL(0x10, 0x11), 0x4), value=Op.EXP(0xff, Op.EXP(0xff, 0x11)))  # noqa: E501
        + Op.SSTORE(key=Op.ADD(Op.MUL(0x10, 0x11), 0x5), value=Op.EXP(0xff, Op.EXP(0x101, 0x11)))  # noqa: E501
        + Op.SSTORE(key=Op.ADD(Op.MUL(0x10, 0x11), 0x6), value=Op.EXP(0x101, Op.EXP(0x100, 0x11)))  # noqa: E501
        + Op.SSTORE(key=Op.ADD(Op.MUL(0x10, 0x11), 0x7), value=Op.EXP(0x101, Op.EXP(0xff, 0x11)))  # noqa: E501
        + Op.SSTORE(key=Op.ADD(Op.MUL(0x10, 0x11), 0x8), value=Op.EXP(0x101, Op.EXP(0x101, 0x11)))  # noqa: E501
        + Op.SSTORE(key=Op.MUL(0x10, 0x12), value=Op.EXP(0x100, Op.EXP(0x100, 0x12)))  # noqa: E501
        + Op.SSTORE(key=Op.ADD(Op.MUL(0x10, 0x12), 0x1), value=Op.EXP(0x100, Op.EXP(0xff, 0x12)))  # noqa: E501
        + Op.SSTORE(key=Op.ADD(Op.MUL(0x10, 0x12), 0x2), value=Op.EXP(0x100, Op.EXP(0x101, 0x12)))  # noqa: E501
        + Op.SSTORE(key=Op.ADD(Op.MUL(0x10, 0x12), 0x3), value=Op.EXP(0xff, Op.EXP(0x100, 0x12)))  # noqa: E501
        + Op.SSTORE(key=Op.ADD(Op.MUL(0x10, 0x12), 0x4), value=Op.EXP(0xff, Op.EXP(0xff, 0x12)))  # noqa: E501
        + Op.SSTORE(key=Op.ADD(Op.MUL(0x10, 0x12), 0x5), value=Op.EXP(0xff, Op.EXP(0x101, 0x12)))  # noqa: E501
        + Op.SSTORE(key=Op.ADD(Op.MUL(0x10, 0x12), 0x6), value=Op.EXP(0x101, Op.EXP(0x100, 0x12)))  # noqa: E501
        + Op.SSTORE(key=Op.ADD(Op.MUL(0x10, 0x12), 0x7), value=Op.EXP(0x101, Op.EXP(0xff, 0x12)))  # noqa: E501
        + Op.SSTORE(key=Op.ADD(Op.MUL(0x10, 0x12), 0x8), value=Op.EXP(0x101, Op.EXP(0x101, 0x12)))  # noqa: E501
        + Op.SSTORE(key=Op.MUL(0x10, 0x13), value=Op.EXP(0x100, Op.EXP(0x100, 0x13)))  # noqa: E501
        + Op.SSTORE(key=Op.ADD(Op.MUL(0x10, 0x13), 0x1), value=Op.EXP(0x100, Op.EXP(0xff, 0x13)))  # noqa: E501
        + Op.SSTORE(key=Op.ADD(Op.MUL(0x10, 0x13), 0x2), value=Op.EXP(0x100, Op.EXP(0x101, 0x13)))  # noqa: E501
        + Op.SSTORE(key=Op.ADD(Op.MUL(0x10, 0x13), 0x3), value=Op.EXP(0xff, Op.EXP(0x100, 0x13)))  # noqa: E501
        + Op.SSTORE(key=Op.ADD(Op.MUL(0x10, 0x13), 0x4), value=Op.EXP(0xff, Op.EXP(0xff, 0x13)))  # noqa: E501
        + Op.SSTORE(key=Op.ADD(Op.MUL(0x10, 0x13), 0x5), value=Op.EXP(0xff, Op.EXP(0x101, 0x13)))  # noqa: E501
        + Op.SSTORE(key=Op.ADD(Op.MUL(0x10, 0x13), 0x6), value=Op.EXP(0x101, Op.EXP(0x100, 0x13)))  # noqa: E501
        + Op.SSTORE(key=Op.ADD(Op.MUL(0x10, 0x13), 0x7), value=Op.EXP(0x101, Op.EXP(0xff, 0x13)))  # noqa: E501
        + Op.SSTORE(key=Op.ADD(Op.MUL(0x10, 0x13), 0x8), value=Op.EXP(0x101, Op.EXP(0x101, 0x13)))  # noqa: E501
        + Op.SSTORE(key=Op.MUL(0x10, 0x14), value=Op.EXP(0x100, Op.EXP(0x100, 0x14)))  # noqa: E501
        + Op.SSTORE(key=Op.ADD(Op.MUL(0x10, 0x14), 0x1), value=Op.EXP(0x100, Op.EXP(0xff, 0x14)))  # noqa: E501
        + Op.SSTORE(key=Op.ADD(Op.MUL(0x10, 0x14), 0x2), value=Op.EXP(0x100, Op.EXP(0x101, 0x14)))  # noqa: E501
        + Op.SSTORE(key=Op.ADD(Op.MUL(0x10, 0x14), 0x3), value=Op.EXP(0xff, Op.EXP(0x100, 0x14)))  # noqa: E501
        + Op.SSTORE(key=Op.ADD(Op.MUL(0x10, 0x14), 0x4), value=Op.EXP(0xff, Op.EXP(0xff, 0x14)))  # noqa: E501
        + Op.SSTORE(key=Op.ADD(Op.MUL(0x10, 0x14), 0x5), value=Op.EXP(0xff, Op.EXP(0x101, 0x14)))  # noqa: E501
        + Op.SSTORE(key=Op.ADD(Op.MUL(0x10, 0x14), 0x6), value=Op.EXP(0x101, Op.EXP(0x100, 0x14)))  # noqa: E501
        + Op.SSTORE(key=Op.ADD(Op.MUL(0x10, 0x14), 0x7), value=Op.EXP(0x101, Op.EXP(0xff, 0x14)))  # noqa: E501
        + Op.SSTORE(key=Op.ADD(Op.MUL(0x10, 0x14), 0x8), value=Op.EXP(0x101, Op.EXP(0x101, 0x14)))  # noqa: E501
        + Op.SSTORE(key=Op.MUL(0x10, 0x15), value=Op.EXP(0x100, Op.EXP(0x100, 0x15)))  # noqa: E501
        + Op.SSTORE(key=Op.ADD(Op.MUL(0x10, 0x15), 0x1), value=Op.EXP(0x100, Op.EXP(0xff, 0x15)))  # noqa: E501
        + Op.SSTORE(key=Op.ADD(Op.MUL(0x10, 0x15), 0x2), value=Op.EXP(0x100, Op.EXP(0x101, 0x15)))  # noqa: E501
        + Op.SSTORE(key=Op.ADD(Op.MUL(0x10, 0x15), 0x3), value=Op.EXP(0xff, Op.EXP(0x100, 0x15)))  # noqa: E501
        + Op.SSTORE(key=Op.ADD(Op.MUL(0x10, 0x15), 0x4), value=Op.EXP(0xff, Op.EXP(0xff, 0x15)))  # noqa: E501
        + Op.SSTORE(key=Op.ADD(Op.MUL(0x10, 0x15), 0x5), value=Op.EXP(0xff, Op.EXP(0x101, 0x15)))  # noqa: E501
        + Op.SSTORE(key=Op.ADD(Op.MUL(0x10, 0x15), 0x6), value=Op.EXP(0x101, Op.EXP(0x100, 0x15)))  # noqa: E501
        + Op.SSTORE(key=Op.ADD(Op.MUL(0x10, 0x15), 0x7), value=Op.EXP(0x101, Op.EXP(0xff, 0x15)))  # noqa: E501
        + Op.SSTORE(key=Op.ADD(Op.MUL(0x10, 0x15), 0x8), value=Op.EXP(0x101, Op.EXP(0x101, 0x15)))  # noqa: E501
        + Op.SSTORE(key=Op.MUL(0x10, 0x16), value=Op.EXP(0x100, Op.EXP(0x100, 0x16)))  # noqa: E501
        + Op.SSTORE(key=Op.ADD(Op.MUL(0x10, 0x16), 0x1), value=Op.EXP(0x100, Op.EXP(0xff, 0x16)))  # noqa: E501
        + Op.SSTORE(key=Op.ADD(Op.MUL(0x10, 0x16), 0x2), value=Op.EXP(0x100, Op.EXP(0x101, 0x16)))  # noqa: E501
        + Op.SSTORE(key=Op.ADD(Op.MUL(0x10, 0x16), 0x3), value=Op.EXP(0xff, Op.EXP(0x100, 0x16)))  # noqa: E501
        + Op.SSTORE(key=Op.ADD(Op.MUL(0x10, 0x16), 0x4), value=Op.EXP(0xff, Op.EXP(0xff, 0x16)))  # noqa: E501
        + Op.SSTORE(key=Op.ADD(Op.MUL(0x10, 0x16), 0x5), value=Op.EXP(0xff, Op.EXP(0x101, 0x16)))  # noqa: E501
        + Op.SSTORE(key=Op.ADD(Op.MUL(0x10, 0x16), 0x6), value=Op.EXP(0x101, Op.EXP(0x100, 0x16)))  # noqa: E501
        + Op.SSTORE(key=Op.ADD(Op.MUL(0x10, 0x16), 0x7), value=Op.EXP(0x101, Op.EXP(0xff, 0x16)))  # noqa: E501
        + Op.SSTORE(key=Op.ADD(Op.MUL(0x10, 0x16), 0x8), value=Op.EXP(0x101, Op.EXP(0x101, 0x16)))  # noqa: E501
        + Op.SSTORE(key=Op.MUL(0x10, 0x17), value=Op.EXP(0x100, Op.EXP(0x100, 0x17)))  # noqa: E501
        + Op.SSTORE(key=Op.ADD(Op.MUL(0x10, 0x17), 0x1), value=Op.EXP(0x100, Op.EXP(0xff, 0x17)))  # noqa: E501
        + Op.SSTORE(key=Op.ADD(Op.MUL(0x10, 0x17), 0x2), value=Op.EXP(0x100, Op.EXP(0x101, 0x17)))  # noqa: E501
        + Op.SSTORE(key=Op.ADD(Op.MUL(0x10, 0x17), 0x3), value=Op.EXP(0xff, Op.EXP(0x100, 0x17)))  # noqa: E501
        + Op.SSTORE(key=Op.ADD(Op.MUL(0x10, 0x17), 0x4), value=Op.EXP(0xff, Op.EXP(0xff, 0x17)))  # noqa: E501
        + Op.SSTORE(key=Op.ADD(Op.MUL(0x10, 0x17), 0x5), value=Op.EXP(0xff, Op.EXP(0x101, 0x17)))  # noqa: E501
        + Op.SSTORE(key=Op.ADD(Op.MUL(0x10, 0x17), 0x6), value=Op.EXP(0x101, Op.EXP(0x100, 0x17)))  # noqa: E501
        + Op.SSTORE(key=Op.ADD(Op.MUL(0x10, 0x17), 0x7), value=Op.EXP(0x101, Op.EXP(0xff, 0x17)))  # noqa: E501
        + Op.SSTORE(key=Op.ADD(Op.MUL(0x10, 0x17), 0x8), value=Op.EXP(0x101, Op.EXP(0x101, 0x17)))  # noqa: E501
        + Op.SSTORE(key=Op.MUL(0x10, 0x18), value=Op.EXP(0x100, Op.EXP(0x100, 0x18)))  # noqa: E501
        + Op.SSTORE(key=Op.ADD(Op.MUL(0x10, 0x18), 0x1), value=Op.EXP(0x100, Op.EXP(0xff, 0x18)))  # noqa: E501
        + Op.SSTORE(key=Op.ADD(Op.MUL(0x10, 0x18), 0x2), value=Op.EXP(0x100, Op.EXP(0x101, 0x18)))  # noqa: E501
        + Op.SSTORE(key=Op.ADD(Op.MUL(0x10, 0x18), 0x3), value=Op.EXP(0xff, Op.EXP(0x100, 0x18)))  # noqa: E501
        + Op.SSTORE(key=Op.ADD(Op.MUL(0x10, 0x18), 0x4), value=Op.EXP(0xff, Op.EXP(0xff, 0x18)))  # noqa: E501
        + Op.SSTORE(key=Op.ADD(Op.MUL(0x10, 0x18), 0x5), value=Op.EXP(0xff, Op.EXP(0x101, 0x18)))  # noqa: E501
        + Op.SSTORE(key=Op.ADD(Op.MUL(0x10, 0x18), 0x6), value=Op.EXP(0x101, Op.EXP(0x100, 0x18)))  # noqa: E501
        + Op.SSTORE(key=Op.ADD(Op.MUL(0x10, 0x18), 0x7), value=Op.EXP(0x101, Op.EXP(0xff, 0x18)))  # noqa: E501
        + Op.SSTORE(key=Op.ADD(Op.MUL(0x10, 0x18), 0x8), value=Op.EXP(0x101, Op.EXP(0x101, 0x18)))  # noqa: E501
        + Op.SSTORE(key=Op.MUL(0x10, 0x19), value=Op.EXP(0x100, Op.EXP(0x100, 0x19)))  # noqa: E501
        + Op.SSTORE(key=Op.ADD(Op.MUL(0x10, 0x19), 0x1), value=Op.EXP(0x100, Op.EXP(0xff, 0x19)))  # noqa: E501
        + Op.SSTORE(key=Op.ADD(Op.MUL(0x10, 0x19), 0x2), value=Op.EXP(0x100, Op.EXP(0x101, 0x19)))  # noqa: E501
        + Op.SSTORE(key=Op.ADD(Op.MUL(0x10, 0x19), 0x3), value=Op.EXP(0xff, Op.EXP(0x100, 0x19)))  # noqa: E501
        + Op.SSTORE(key=Op.ADD(Op.MUL(0x10, 0x19), 0x4), value=Op.EXP(0xff, Op.EXP(0xff, 0x19)))  # noqa: E501
        + Op.SSTORE(key=Op.ADD(Op.MUL(0x10, 0x19), 0x5), value=Op.EXP(0xff, Op.EXP(0x101, 0x19)))  # noqa: E501
        + Op.SSTORE(key=Op.ADD(Op.MUL(0x10, 0x19), 0x6), value=Op.EXP(0x101, Op.EXP(0x100, 0x19)))  # noqa: E501
        + Op.SSTORE(key=Op.ADD(Op.MUL(0x10, 0x19), 0x7), value=Op.EXP(0x101, Op.EXP(0xff, 0x19)))  # noqa: E501
        + Op.SSTORE(key=Op.ADD(Op.MUL(0x10, 0x19), 0x8), value=Op.EXP(0x101, Op.EXP(0x101, 0x19)))  # noqa: E501
        + Op.SSTORE(key=Op.MUL(0x10, 0x1a), value=Op.EXP(0x100, Op.EXP(0x100, 0x1a)))  # noqa: E501
        + Op.SSTORE(key=Op.ADD(Op.MUL(0x10, 0x1a), 0x1), value=Op.EXP(0x100, Op.EXP(0xff, 0x1a)))  # noqa: E501
        + Op.SSTORE(key=Op.ADD(Op.MUL(0x10, 0x1a), 0x2), value=Op.EXP(0x100, Op.EXP(0x101, 0x1a)))  # noqa: E501
        + Op.SSTORE(key=Op.ADD(Op.MUL(0x10, 0x1a), 0x3), value=Op.EXP(0xff, Op.EXP(0x100, 0x1a)))  # noqa: E501
        + Op.SSTORE(key=Op.ADD(Op.MUL(0x10, 0x1a), 0x4), value=Op.EXP(0xff, Op.EXP(0xff, 0x1a)))  # noqa: E501
        + Op.SSTORE(key=Op.ADD(Op.MUL(0x10, 0x1a), 0x5), value=Op.EXP(0xff, Op.EXP(0x101, 0x1a)))  # noqa: E501
        + Op.SSTORE(key=Op.ADD(Op.MUL(0x10, 0x1a), 0x6), value=Op.EXP(0x101, Op.EXP(0x100, 0x1a)))  # noqa: E501
        + Op.SSTORE(key=Op.ADD(Op.MUL(0x10, 0x1a), 0x7), value=Op.EXP(0x101, Op.EXP(0xff, 0x1a)))  # noqa: E501
        + Op.SSTORE(key=Op.ADD(Op.MUL(0x10, 0x1a), 0x8), value=Op.EXP(0x101, Op.EXP(0x101, 0x1a)))  # noqa: E501
        + Op.SSTORE(key=Op.MUL(0x10, 0x1b), value=Op.EXP(0x100, Op.EXP(0x100, 0x1b)))  # noqa: E501
        + Op.SSTORE(key=Op.ADD(Op.MUL(0x10, 0x1b), 0x1), value=Op.EXP(0x100, Op.EXP(0xff, 0x1b)))  # noqa: E501
        + Op.SSTORE(key=Op.ADD(Op.MUL(0x10, 0x1b), 0x2), value=Op.EXP(0x100, Op.EXP(0x101, 0x1b)))  # noqa: E501
        + Op.SSTORE(key=Op.ADD(Op.MUL(0x10, 0x1b), 0x3), value=Op.EXP(0xff, Op.EXP(0x100, 0x1b)))  # noqa: E501
        + Op.SSTORE(key=Op.ADD(Op.MUL(0x10, 0x1b), 0x4), value=Op.EXP(0xff, Op.EXP(0xff, 0x1b)))  # noqa: E501
        + Op.SSTORE(key=Op.ADD(Op.MUL(0x10, 0x1b), 0x5), value=Op.EXP(0xff, Op.EXP(0x101, 0x1b)))  # noqa: E501
        + Op.SSTORE(key=Op.ADD(Op.MUL(0x10, 0x1b), 0x6), value=Op.EXP(0x101, Op.EXP(0x100, 0x1b)))  # noqa: E501
        + Op.SSTORE(key=Op.ADD(Op.MUL(0x10, 0x1b), 0x7), value=Op.EXP(0x101, Op.EXP(0xff, 0x1b)))  # noqa: E501
        + Op.SSTORE(key=Op.ADD(Op.MUL(0x10, 0x1b), 0x8), value=Op.EXP(0x101, Op.EXP(0x101, 0x1b)))  # noqa: E501
        + Op.SSTORE(key=Op.MUL(0x10, 0x1c), value=Op.EXP(0x100, Op.EXP(0x100, 0x1c)))  # noqa: E501
        + Op.SSTORE(key=Op.ADD(Op.MUL(0x10, 0x1c), 0x1), value=Op.EXP(0x100, Op.EXP(0xff, 0x1c)))  # noqa: E501
        + Op.SSTORE(key=Op.ADD(Op.MUL(0x10, 0x1c), 0x2), value=Op.EXP(0x100, Op.EXP(0x101, 0x1c)))  # noqa: E501
        + Op.SSTORE(key=Op.ADD(Op.MUL(0x10, 0x1c), 0x3), value=Op.EXP(0xff, Op.EXP(0x100, 0x1c)))  # noqa: E501
        + Op.SSTORE(key=Op.ADD(Op.MUL(0x10, 0x1c), 0x4), value=Op.EXP(0xff, Op.EXP(0xff, 0x1c)))  # noqa: E501
        + Op.SSTORE(key=Op.ADD(Op.MUL(0x10, 0x1c), 0x5), value=Op.EXP(0xff, Op.EXP(0x101, 0x1c)))  # noqa: E501
        + Op.SSTORE(key=Op.ADD(Op.MUL(0x10, 0x1c), 0x6), value=Op.EXP(0x101, Op.EXP(0x100, 0x1c)))  # noqa: E501
        + Op.SSTORE(key=Op.ADD(Op.MUL(0x10, 0x1c), 0x7), value=Op.EXP(0x101, Op.EXP(0xff, 0x1c)))  # noqa: E501
        + Op.SSTORE(key=Op.ADD(Op.MUL(0x10, 0x1c), 0x8), value=Op.EXP(0x101, Op.EXP(0x101, 0x1c)))  # noqa: E501
        + Op.SSTORE(key=Op.MUL(0x10, 0x1d), value=Op.EXP(0x100, Op.EXP(0x100, 0x1d)))  # noqa: E501
        + Op.SSTORE(key=Op.ADD(Op.MUL(0x10, 0x1d), 0x1), value=Op.EXP(0x100, Op.EXP(0xff, 0x1d)))  # noqa: E501
        + Op.SSTORE(key=Op.ADD(Op.MUL(0x10, 0x1d), 0x2), value=Op.EXP(0x100, Op.EXP(0x101, 0x1d)))  # noqa: E501
        + Op.SSTORE(key=Op.ADD(Op.MUL(0x10, 0x1d), 0x3), value=Op.EXP(0xff, Op.EXP(0x100, 0x1d)))  # noqa: E501
        + Op.SSTORE(key=Op.ADD(Op.MUL(0x10, 0x1d), 0x4), value=Op.EXP(0xff, Op.EXP(0xff, 0x1d)))  # noqa: E501
        + Op.SSTORE(key=Op.ADD(Op.MUL(0x10, 0x1d), 0x5), value=Op.EXP(0xff, Op.EXP(0x101, 0x1d)))  # noqa: E501
        + Op.SSTORE(key=Op.ADD(Op.MUL(0x10, 0x1d), 0x6), value=Op.EXP(0x101, Op.EXP(0x100, 0x1d)))  # noqa: E501
        + Op.SSTORE(key=Op.ADD(Op.MUL(0x10, 0x1d), 0x7), value=Op.EXP(0x101, Op.EXP(0xff, 0x1d)))  # noqa: E501
        + Op.SSTORE(key=Op.ADD(Op.MUL(0x10, 0x1d), 0x8), value=Op.EXP(0x101, Op.EXP(0x101, 0x1d)))  # noqa: E501
        + Op.SSTORE(key=Op.MUL(0x10, 0x1e), value=Op.EXP(0x100, Op.EXP(0x100, 0x1e)))  # noqa: E501
        + Op.SSTORE(key=Op.ADD(Op.MUL(0x10, 0x1e), 0x1), value=Op.EXP(0x100, Op.EXP(0xff, 0x1e)))  # noqa: E501
        + Op.SSTORE(key=Op.ADD(Op.MUL(0x10, 0x1e), 0x2), value=Op.EXP(0x100, Op.EXP(0x101, 0x1e)))  # noqa: E501
        + Op.SSTORE(key=Op.ADD(Op.MUL(0x10, 0x1e), 0x3), value=Op.EXP(0xff, Op.EXP(0x100, 0x1e)))  # noqa: E501
        + Op.SSTORE(key=Op.ADD(Op.MUL(0x10, 0x1e), 0x4), value=Op.EXP(0xff, Op.EXP(0xff, 0x1e)))  # noqa: E501
        + Op.SSTORE(key=Op.ADD(Op.MUL(0x10, 0x1e), 0x5), value=Op.EXP(0xff, Op.EXP(0x101, 0x1e)))  # noqa: E501
        + Op.SSTORE(key=Op.ADD(Op.MUL(0x10, 0x1e), 0x6), value=Op.EXP(0x101, Op.EXP(0x100, 0x1e)))  # noqa: E501
        + Op.SSTORE(key=Op.ADD(Op.MUL(0x10, 0x1e), 0x7), value=Op.EXP(0x101, Op.EXP(0xff, 0x1e)))  # noqa: E501
        + Op.SSTORE(key=Op.ADD(Op.MUL(0x10, 0x1e), 0x8), value=Op.EXP(0x101, Op.EXP(0x101, 0x1e)))  # noqa: E501
        + Op.SSTORE(key=Op.MUL(0x10, 0x1f), value=Op.EXP(0x100, Op.EXP(0x100, 0x1f)))  # noqa: E501
        + Op.SSTORE(key=Op.ADD(Op.MUL(0x10, 0x1f), 0x1), value=Op.EXP(0x100, Op.EXP(0xff, 0x1f)))  # noqa: E501
        + Op.SSTORE(key=Op.ADD(Op.MUL(0x10, 0x1f), 0x2), value=Op.EXP(0x100, Op.EXP(0x101, 0x1f)))  # noqa: E501
        + Op.SSTORE(key=Op.ADD(Op.MUL(0x10, 0x1f), 0x3), value=Op.EXP(0xff, Op.EXP(0x100, 0x1f)))  # noqa: E501
        + Op.SSTORE(key=Op.ADD(Op.MUL(0x10, 0x1f), 0x4), value=Op.EXP(0xff, Op.EXP(0xff, 0x1f)))  # noqa: E501
        + Op.SSTORE(key=Op.ADD(Op.MUL(0x10, 0x1f), 0x5), value=Op.EXP(0xff, Op.EXP(0x101, 0x1f)))  # noqa: E501
        + Op.SSTORE(key=Op.ADD(Op.MUL(0x10, 0x1f), 0x6), value=Op.EXP(0x101, Op.EXP(0x100, 0x1f)))  # noqa: E501
        + Op.SSTORE(key=Op.ADD(Op.MUL(0x10, 0x1f), 0x7), value=Op.EXP(0x101, Op.EXP(0xff, 0x1f)))  # noqa: E501
        + Op.SSTORE(key=Op.ADD(Op.MUL(0x10, 0x1f), 0x8), value=Op.EXP(0x101, Op.EXP(0x101, 0x1f)))  # noqa: E501
        + Op.SSTORE(key=Op.MUL(0x10, 0x20), value=Op.EXP(0x100, Op.EXP(0x100, 0x20)))  # noqa: E501
        + Op.SSTORE(key=Op.ADD(Op.MUL(0x10, 0x20), 0x1), value=Op.EXP(0x100, Op.EXP(0xff, 0x20)))  # noqa: E501
        + Op.SSTORE(key=Op.ADD(Op.MUL(0x10, 0x20), 0x2), value=Op.EXP(0x100, Op.EXP(0x101, 0x20)))  # noqa: E501
        + Op.SSTORE(key=Op.ADD(Op.MUL(0x10, 0x20), 0x3), value=Op.EXP(0xff, Op.EXP(0x100, 0x20)))  # noqa: E501
        + Op.SSTORE(key=Op.ADD(Op.MUL(0x10, 0x20), 0x4), value=Op.EXP(0xff, Op.EXP(0xff, 0x20)))  # noqa: E501
        + Op.SSTORE(key=Op.ADD(Op.MUL(0x10, 0x20), 0x5), value=Op.EXP(0xff, Op.EXP(0x101, 0x20)))  # noqa: E501
        + Op.SSTORE(key=Op.ADD(Op.MUL(0x10, 0x20), 0x6), value=Op.EXP(0x101, Op.EXP(0x100, 0x20)))  # noqa: E501
        + Op.SSTORE(key=Op.ADD(Op.MUL(0x10, 0x20), 0x7), value=Op.EXP(0x101, Op.EXP(0xff, 0x20)))  # noqa: E501
        + Op.SSTORE(key=Op.ADD(Op.MUL(0x10, 0x20), 0x8), value=Op.EXP(0x101, Op.EXP(0x101, 0x20)))  # noqa: E501
        + Op.SSTORE(key=Op.MUL(0x10, 0x21), value=Op.EXP(0x100, Op.EXP(0x100, 0x21)))  # noqa: E501
        + Op.SSTORE(key=Op.ADD(Op.MUL(0x10, 0x21), 0x1), value=Op.EXP(0x100, Op.EXP(0xff, 0x21)))  # noqa: E501
        + Op.SSTORE(key=Op.ADD(Op.MUL(0x10, 0x21), 0x2), value=Op.EXP(0x100, Op.EXP(0x101, 0x21)))  # noqa: E501
        + Op.SSTORE(key=Op.ADD(Op.MUL(0x10, 0x21), 0x3), value=Op.EXP(0xff, Op.EXP(0x100, 0x21)))  # noqa: E501
        + Op.SSTORE(key=Op.ADD(Op.MUL(0x10, 0x21), 0x4), value=Op.EXP(0xff, Op.EXP(0xff, 0x21)))  # noqa: E501
        + Op.SSTORE(key=Op.ADD(Op.MUL(0x10, 0x21), 0x5), value=Op.EXP(0xff, Op.EXP(0x101, 0x21)))  # noqa: E501
        + Op.SSTORE(key=Op.ADD(Op.MUL(0x10, 0x21), 0x6), value=Op.EXP(0x101, Op.EXP(0x100, 0x21)))  # noqa: E501
        + Op.SSTORE(key=Op.ADD(Op.MUL(0x10, 0x21), 0x7), value=Op.EXP(0x101, Op.EXP(0xff, 0x21)))  # noqa: E501
        + Op.SSTORE(key=Op.ADD(Op.MUL(0x10, 0x21), 0x8), value=Op.EXP(0x101, Op.EXP(0x101, 0x21)))  # noqa: E501
        + Op.STOP,
        balance=0xba1a9ce0ba1a9ce,
        nonce=0,
        address=Address("0x9f233ef2d697929edf542064b125e7d620270363"),  # noqa: E501
    )
    pre[sender] = Account(balance=0xba1a9ce0ba1a9ce)


    tx = Transaction(
        sender=sender,
        to=target,
        data=bytes.fromhex("693c61390000000000000000000000000000000000000000000000000000000000000000"),  # noqa: E501
        gas_limit=16777216,
        value=1,
        nonce=0,
        gas_price=10,
    )

    post = {
        target: Account(
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
            19: 0x6c3acd330b959ad6efabce6d2d2125e73a88a65a9880d203dddf5957f7f0001,
            20: 0x8f965a06da0ac41dcb3a34f1d8ab7d8fee620a94faa42c395997756b007ffeff,
            21: 0xbce9265d88a053c18bc229ebff404c1534e1db43de85131da0179fe9ff8100ff,
            22: 0x2b5e9d7a094c19f5ebdd4f2e618f859ed15e4f1f0351f286bf849eb7f810001,
            23: 0xc73b7a6f68385c653a24993bb72eea0e4ba17470816ec658cf9c5bedfd81ff01,
            24: 0xb89fc178355660fe1c92c7d8ff11524702fad6e2255447946442356b00810101,
            35: 0x4ee4ceeaac565c81f55a87c43f82f7c889ef4fc7c679671e28d594ff7f000001,
            36: 0x82f46a1b4e34d66712910615d2571d75606ceac51fa8ca8c58cf6ca881fe00ff,
            37: 0x81c9fcefa5de158ae2007f25d35c0d11cd735342a48905955a5a6852800200ff,
            38: 0x666ac362902470ed850709e2a29969d10cba09debc03c38d172aeaff81000001,
            39: 0xeb30a3c678a01bde914548f98f3366dc0ffe9f85384ebf1111d03dad7ffe0101,
            40: 0x72d0a7939b6303ce1d46e6e3f1b8be303bfdb2b00f41ad8076b0975782020101,
            51: 0x109a00e1370d2d2922bf892e85becb54297354b2e5c75388d514ff7f00000001,
            52: 0x54a792f15e9aba7e4ad9e716bc169eea3a6e2e9c49bf9b335874613c8081feff,
            53: 0x5d24a14d8e5e039372cd0f6a0f31e9ed6b75adba9f16b1c5b3edd5ba818300ff,
            54: 0x298e2f316b4ccded5ebf515998d9ec20df69404b04a441782a6aff8100000001,
            55: 0x4335694e98f372183c62a2339fa4ad161e9b4c42240bdc9452abffd07783ff01,
            56: 0xf0f0820797315acd063056bba76f6a9c3e281cdb5197a233967ca94684830101,
            67: 0xe6540ce46eaf70da9d644015a661e0e245b13f307cb3885514ff7f0000000001,
            68: 0x6526b38b05a6325b80e1c84ab41dc934fd70f33f1bd0eab3d1f61a4707fc00ff,
            69: 0xe959516cd27e5d8fd487b72db2989b3ec2ba9fb7ead41554526fe5a3040400ff,
            70: 0xe7498a48c6ce2530bbe814ee3440c8c44fffab7ad8a277aa6aff810000000001,
            71: 0x2dffa3e901e5a392d15b79f4193d2168147d2aa7c55870b46c3a905d03fc0101,
            72: 0xe16ea721c96539edb4f7fb82de0dad8cccb1e7a6966a6777635f6fb908040101,
            83: 0xb581ac185aad71db2d177c286929c4c22809e5dcb3085514ff7f000000000001,
            84: 0x75789eb2a64bc971389fbd11a1e6d7abbf95ad25e23fb9aa25e73a0bfc83feff,
            85: 0xfc403fa42ceb6a0d0d3321bd9b2d8af25b1b667f87a04f496c78168d078500ff,
            86: 0xcec5ec213b9cb5811f6ae00428fd7b6ef5a1af39a1f7aa6aff81000000000001,
            87: 0x70ab32233202b98d382d17713fa0be391eaf74f85ba1740c9c3238c4ed85ff01,
            88: 0xb622672a213faa79b32185ff93a7b27a8499e48f7b032cdb4d1a70300c850101,
            99: 0x1948059de1def03c4ec35fc22c2bb8f2bf45dc33085514ff7f00000000000001,
            100: 0x41f818a8e24eb6d7bb7b193b4f2b5fdcf4bd0d453f2ac3499d8830d391fa00ff,
            101: 0xede6fe4a943dfb5d967a2b85d6728759d40d2ef0ae4bc28bbb1867f98c0600ff,
            102: 0x83c936cbaad5de592badc2e142fe4ebd6103921f7aa6aff8100000000000001,
            103: 0x57385019fe4e0939ca3f35c37cadfaf52fba5b1cdfb02def3866e8068bfa0101,
            104: 0x810ac878bd98428f6be8c6426ba9f9da09e3e33bf4fe10bfa3f8b12c92060101,
            115: 0x8bb02654111ad8c60ad8af132283a81f455c33085514ff7f0000000000000001,
            116: 0xa8f75c129dbb8466d6703a2a0b8212131b3248d70e2478862ac40fe17485feff,
            117: 0x5fd4d2de580383ee59f5e800ddb3f1717ceae03aede19d3dec5e5a69918700ff,
            118: 0xc8624230b524b85d6340da48a5db20370fb921f7aa6aff810000000000000001,
            119: 0x287b58a5a13cd7f454468ca616c181712f5ed25433a7d5a894b6ced35f87ff01,
            120: 0x9930d11ac2804fa977bf951593c8dff8498779cc0cdc5812a4fba2f98870101,
            131: 0x230041a0e7602d6e459609ed39081ec55c33085514ff7f000000000000000001,
            132: 0xc407d8a413ef9079ead457ed686a05ac81039c0cae0a7f6afd01e8461ff800ff,
            133: 0x67a397e0692385e4cd83853aabce220a94d449e885fa867e96d3ef5e180800ff,
            134: 0x70add926e753655d6d0ebe9c0f81368fb921f7aa6aff81000000000000000001,
            135: 0xbdce80b8378e43f13d454b9d0a4c83cf311b8eaa45d5122cfd544a217f80101,
            136: 0x629c25790e1488998877a9ecdf0fb69637e77d8a4bdc1b46270093ba20080101,
            147: 0x53017d8eb210db2c8cd4a299079ec55c33085514ff7f00000000000000000001,
            148: 0x48be09b6c6ae2aa660f1972125cecbb1038b5d236ecf766ba786e2c4e887feff,
            149: 0x2e350d847ba73dc2099f83f532951c47269d9fd7e411b50bae00a9581f8900ff,
            150: 0x13ab9e1f0df89a184b4d07080b68fb921f7aa6aff8100000000000000000001,
            151: 0xf387ed41c1050f9da667f429a3e8fb30b61a55ede97d7b8acd797a03cd89ff01,
            152: 0x525696c22bb3ce00fd2e3f6bbb9b4ea1046a5e31fcff2fedf8f8c74d28890101,
            163: 0xfe0f60957dc223578a0298879ec55c33085514ff7f0000000000000000000001,
            164: 0xc1ea45f348b5d351c4d8fe5c77da979cadc33d866acc42e981278896b1f600ff,
            165: 0x56ddb29bca94fb986ac0a40188b3b53f3216b3559bd8324a77ea8bd8a80a00ff,
            166: 0x2d49ff6b0bbe177ae9317000b68fb921f7aa6aff810000000000000000000001,
            167: 0x185fa9eab94cfe3016b69657e83b23fd24cc6960218254231c3db627a7f60101,
            168: 0xa7a0223829f26d6c635368034320563df4aa5eb62efc87a42bb35f69b20a0101,
            179: 0xe1440264b8ee0cea0218879ec55c33085514ff7f000000000000000000000001,
            180: 0x29575fdce377b23043e489e358581474bc863187fa85f9945473a2be5889feff,
            181: 0x3df8c030ec521fb109c4d887dbbc14c7c9c9921b27058e3503971b60b18b00ff,
            182: 0x67799740340daf4a30f000b68fb921f7aa6aff81000000000000000000000001,
            183: 0x540a4e4635b40585e09ff10b63ffe310dd717fca5c0a51570091e25e378bff01,
            184: 0xdbbaef5c49ffee61b08cde6ebc8dba6e9a62d56c2355d1980cb9e790bc8b0101,
            195: 0xb0e95b83a36ce98218879ec55c33085514ff7f00000000000000000000000001,
            196: 0xc482ab56ec19186dc48c88f30861a850b2253b1ea6dc021589e569bd47f400ff,
            197: 0xcf45c7f9af4bbe4a83055b55b97777ad5e0a3f08b129c9ae208c5d713c0c00ff,
            198: 0xa5cbb62a421049b0f000b68fb921f7aa6aff8100000000000000000000000001,
            199: 0x3bde6ca66dffe1bf5d727c3edea74c7a4af43b3912e6256d37705c8f3bf40101,
            200: 0x3f49a1e40c5213aa4ffed57eb4c1ad2d181b2aaa289e9d59c2256c43480c0101,
            211: 0xe02639036c698218879ec55c33085514ff7f0000000000000000000000000001,
            212: 0x8be664bde946d939ce551b948b503787942d2a7734509288c1b62fd5c48bfeff,
            213: 0xa923a28e7a75aef26c51580ffc686879e4a0b404b089bdbcd751d88b478d00ff,
            214: 0x41ac5ea30fc9b0f000b68fb921f7aa6aff810000000000000000000000000001,
            215: 0xdaa3a177ec975cb69bb4acf4a6e1be7bcc1ad33d1ffad97510f9fea9d8dff01,
            216: 0x19e6822beb889be28310060f4fb9741bfd50a31fa81ec65de21f7b02548d0101,
            227: 0xdb9902ec698218879ec55c33085514ff7f000000000000000000000000000001,
            228: 0x83fab06c6c8fef761ebbb9534c06ac2a9d61820623008069062ff3b1e1f200ff,
            229: 0x3f791dd183ed5b963bd86e0dba1a9dd5b8ceeb078f15c73062f1942fd40e00ff,
            230: 0xe0bfa28fc9b0f000b68fb921f7aa6aff81000000000000000000000000000001,
            231: 0x8133b760dfae27560eb490f235ddfa301f058dee4f01f3fe4b3567d0d3f20101,
            232: 0xcd4cd0124e983af71620fb5f98275965c6a8bebc4b8adc288b63224ee20e0101,
            243: 0x9882ec698218879ec55c33085514ff7f00000000000000000000000000000001,
            244: 0x75c4915e18b96704209738f5ca765568bb4dc4113d56683977825a132c8dfeff,
            245: 0x5c76839bf5a80b1da705dbdf43e4dd6770cd7501af11ff2dab7918dfe18f00ff,
            246: 0xbf228fc9b0f000b68fb921f7aa6aff8100000000000000000000000000000001,
            247: 0xc6a29131e7594004bc2aa79f0d2c402a1409c57c77d284c14b1a3ab0ff8fff01,
            248: 0xe6b3e5cf6ec90e532fef7d08455ebf92a03e9e3f6e224ea0febdf1a9f08f0101,
            259: 0x82ec698218879ec55c33085514ff7f0000000000000000000000000000000001,
            260: 0x3122f4bcdf6dd8b265cd18eb6af28c879aed44a35e0bf59273e39e6c7ff000ff,
            261: 0x6a2b3bc87a02c29b9d27757df43047ecd0f15485270fca27417a701c701000ff,
            262: 0x228fc9b0f000b68fb921f7aa6aff810000000000000000000000000000000001,
            263: 0x88e1259502eef93d46060aacc9e2ff506c734dade0b6714ab12d17e46ff00101,
            264: 0x4a103813c12c12169b218296bb0a9eae80cf8d2b158aa70eb990f99480100101,
            275: 0xec698218879ec55c33085514ff7f000000000000000000000000000000000001,
            276: 0x722ad218eb1995a2d257c4c06d8de993c203cfc8e3512df7d633e17e908ffeff,
            277: 0x8ac9b5ec08d74612cb29f941481d274b51721af2296207c0da8d24667f9100ff,
            278: 0x8fc9b0f000b68fb921f7aa6aff81000000000000000000000000000000000001,
            279: 0x81d5ff63680841482299f3eab616446dcd336f537c0c565aa4112ab95d91ff01,
            280: 0x9c6ca90dac4e97dea02ac969e8649ee9e6232e0c3f4797411151cb8f90910101,
            291: 0x698218879ec55c33085514ff7f00000000000000000000000000000000000001,
            292: 0x8a2cbd9f40794e2205b13306f2aa0a43c60823c64b95d8601fa4f1e521ee00ff,
            293: 0xc1b5a1e3a81da51b10d84e880f0113ff67b863ddad3faf1f4ecf413f101200ff,
            294: 0xc9b0f000b68fb921f7aa6aff8100000000000000000000000000000000000001,
            295: 0x410be68e49452a1fbcd863bf6e8d637f8eae4979c34c88d552afbcc20fee0101,
            296: 0xf540cb714754b5b1eb0373833833bd7fb0ee925ce8b92962500b7a1c22120101,
            307: 0x8218879ec55c33085514ff7f0000000000000000000000000000000000000001,
            308: 0xb795ad7ac24cfbb7435cf53bd3584f3d4b2709935635c3ceb66e761ff091feff,
            309: 0x1f0bb7be91a0ccd0cca93d75cf03de3e6b56fe8f1c54242617665327219300ff,
            310: 0xb0f000b68fb921f7aa6aff810000000000000000000000000000000000000001,
            311: 0xad571756ecbff1bfdef064861e5e92c5d897a9cc380e54bdbaabd80bb793ff01,
            312: 0xd8b5b531989e689f700dcdb43ab90e79a49dfbbb5a13dbf751df98bb34930101,
            323: 0x18879ec55c33085514ff7f000000000000000000000000000000000000000001,
            324: 0x67e4797dc21f02ce4a7c52218c7dbea5d212e6c244e24f0ba4c08613c7ec00ff,
            325: 0xa1ce1a085f258785846939cc1d2e8725ac94ad4dff8913234e00679fb41400ff,
            326: 0xf000b68fb921f7aa6aff81000000000000000000000000000000000000000001,
            327: 0xcce501857a1cb45473915a28082af950e0f78f7e2de68ce748adb661b3ec0101,
            328: 0x3b2e28d274a16c08b58a23bad63bba6d7b09685769d1f68ca3873bedc8140101,
            339: 0x879ec55c33085514ff7f00000000000000000000000000000000000000000001,
            340: 0x7fd07055ff50cdfe4b4bd9a15133d72d3607d92eb7ac81bac93db7ff4c93feff,
            341: 0x665ac5c769e87f61d5993abc26522fbfca2734d76a63216b2d550d29c79500ff,
            342: 0xb68fb921f7aa6aff8100000000000000000000000000000000000000000001,
            343: 0x1c93db67c9884bc694686d69a25a5d7ed089841d5ce147fdd7199ab00d95ff01,
            344: 0x485053d8ff66be52036597520344fac87b6a305426a9e49221d3f934dc950101,
            355: 0x9ec55c33085514ff7f0000000000000000000000000000000000000000000001,
            356: 0xec447e662ac08957d7e290a421dbf54c0aaf43aadc9cc465ad0b02f071ea00ff,
            357: 0xdc9178d3bab470096f01477c859b5f4173986640b659426412a653465c1600ff,
            358: 0xb68fb921f7aa6aff810000000000000000000000000000000000000000000001,
            359: 0xdcf0a770777610503596ae0311af46c171151ed45107d7e7bb8f74bb5bea0101,
            360: 0x4d65773387993928c95c861274232d3fb6f6b7fe1b22e4e61a30e71172160101,
            371: 0xc55c33085514ff7f000000000000000000000000000000000000000000000001,
            372: 0x537ca0f03f974303005f1e6693b55b72315a166841732e42b8353724a495feff,
            373: 0x86418797ec60058de6cca47dfdbee79923ac49d7801e01840041ca76719700ff,
            374: 0x8fb921f7aa6aff81000000000000000000000000000000000000000000000001,
            375: 0x56a55341ab8d4318f1cfb55d5f21e2ba35d7e070a72bac6b2b21baae5f97ff01,
            376: 0x55ddd0ec77909de6d8311116cf520398e816f928b06fdd90ec239d0488970101,
            387: 0x5c33085514ff7f00000000000000000000000000000000000000000000000001,
            388: 0xd542e526003539ead104274aff2d78332366e29d328c2161f0c120731fe800ff,
            389: 0xc706cb25e8384ce9bb5c9cb48415238ba03e16c448e292c0a101843b081800ff,
            390: 0xb921f7aa6aff8100000000000000000000000000000000000000000000000001,
            391: 0x4ca55f89202c524cb0f1cb3195d13c8d94a9f7a05c59e1d4031577c707e80101,
            392: 0x8c4b0574e9156b80035f3ecdcf1fe79d273ed7559747a4322bcd338f20180101,
            403: 0x33085514ff7f0000000000000000000000000000000000000000000000000001,
            404: 0x7f510dd7198cac0a92ff7ea80451838c0dfa12114c41a0ef05907397f897feff,
            405: 0x1275e752b6aee228ecba5e9b57ef1111deff3c651e2cfbf2cccd13151f9900ff,
            406: 0x21f7aa6aff810000000000000000000000000000000000000000000000000001,
            407: 0x6646340ad51a03bb710caf05756b685b33c7dad62ae68d369243700ead99ff01,
            408: 0x29d80e8060ef2221929bb18215586c742686d6860e028ca0456b443238990101,
            419: 0x85514ff7f000000000000000000000000000000000000000000000000000001,
            420: 0x1d164db738eb6893868b361ad2803f97be35764456e82a837667a693d1e600ff,
            421: 0x8b92c24abebf376a5aab5ff4dfd3538a03d38a10bced2aae8e1a8a85b81a00ff,
            422: 0xf7aa6aff81000000000000000000000000000000000000000000000000000001,
            423: 0x6931bda98c70e860a1f6a5224940f1ec7e6734cd9456c95806384f7cb7e60101,
            424: 0x3402a9db66492dfc2a220715e76243469462f24edc56903ba1d8e96ed21a0101,
            435: 0x5514ff7f00000000000000000000000000000000000000000000000000000001,
            436: 0x178918ffbcb401d4efd2f7dfb4d01a897172267f0f491121ac52dd614899feff,
            437: 0x38ecff71480ca0b422f2ed6f780d5fead2ae234a49104b10a86f7f0dd19b00ff,
            438: 0xaa6aff8100000000000000000000000000000000000000000000000000000001,
            439: 0xd02811cb5dc1d80567e810532b235b7672f5c78cd6e89bb511d5e2d8f79bff01,
            440: 0x1b4e6404f474c18055d30bb8987672f59e97980d6f9de1764c0fbec5ec9b0101,
            451: 0x14ff7f0000000000000000000000000000000000000000000000000000000001,
            452: 0xffd368e44b3f85cb81ae394c9809ca9fa2db46a83d7880a912ab6d4a87e400ff,
            453: 0x981ad53c19b15a94bcf0bf20235dd0da9df25f46ae635029fe2062e6c1c00ff,
            454: 0x6aff810000000000000000000000000000000000000000000000000000000001,
            455: 0x19df06ffa28250867006726405fbc05d43dc2f9d2f025006db089bd46be40101,
            456: 0x243fffe3a4f2982f45055c08f379648ab886da8027a7401117a8e0b8881c0101,
            467: 0xff7f000000000000000000000000000000000000000000000000000000000001,
            468: 0x41e065d46e0349cfe624c4e8a2034aea1f7edfff80e511cd8067d488949bfeff,
            469: 0xa84162ca6675a22c4c79dfc4ea15f760db5a04dbf04246764199b668879d00ff,
            470: 0xff81000000000000000000000000000000000000000000000000000000000001,
            471: 0x1226984faa6b05ebdbd45d8477fa4fd5b55bfd5061de03c319282b153d9dff01,
            472: 0x5cc9e6b0b749fd94541ad00364bdec2fca7816981ca3e38f485decc7a49d0101,
            483: 0x7f00000000000000000000000000000000000000000000000000000000000001,
            484: 0xe9772778f50fa0a69cd10fa019ac56d72ac7a7d7af26c4ba28415c8f41e200ff,
            485: 0x33f0385ef73feebdb952e5adb643dd0fa178fd9271578219ad50a73d241e00ff,
            486: 0x8100000000000000000000000000000000000000000000000000000000000001,
            487: 0xfd405cce8f73dffc04a6f0ff6ffc6bf7961876d09c5b4933a68f0cc623e20101,
            488: 0xc5a8f4566fd2e96e4ce3a8b3ec0863e7b20bc3b2f3dc5261ba8a0174421e0101,
            499: 1,
            500: 0xf9cb87f5b1ab58602f52a1e9d392e5675b86a59a53943a8d4ec2a915dc9dfeff,
            501: 0x893d729a64e318860ec5047e70e598da163eb41e71e74b04dfd4712d419f00ff,
            502: 1,
            503: 0xee5f2839c1b4f6ca05e6fdb04e2fb49c0f860b3765c27dc781a150cb7f9fff01,
            504: 0xb4c358e3c6bcddfb509ea487d733df0e1854f29c3b6bfd4a8caabe3f609f0101,
            512: 1,
            515: 1,
            516: 0xb8247842bb5ce75c08d0c251669ed5870fa24a22952e5db3a7c66c59ffe000ff,
            517: 0xee526e5a06f2a990b2bf6c951e5feabf0e07ee16877296e1be872db9e02000ff,
            518: 1,
            519: 0xeda7d024b6de40a9d3b966e71f10a4667edc5b71cab07aeabcac6249dfe00101,
            520: 0x512ecfaeeb11205f0833e1054dcb1300488e0954be5af77a49e143aa00200101,
            528: 1,
            531: 1,
            532: 0x8dcb65b5494eba78cd6756a6f9851f6e26d0f2bb9ecd7e9abd7e9b11209ffeff,
            533: 0x6694bb31b20cd625f3756897dae6d738f2e64467b5b6f10fa3e07763ffa100ff,
            534: 1,
            535: 0xe678999aeffd1f1f45081f64de7f80ab083dd7df04721ed64ee04c03bda1ff01,
            536: 0x39b68fb9898dd7568abd178397251ce8226a25c1d305a4e79573333520a10101,
        },
            ),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
