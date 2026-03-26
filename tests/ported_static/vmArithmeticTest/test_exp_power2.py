"""
Ori Pomerantz qbzzt1@gmail.com

Ported from:
state_tests/VMTests/vmArithmeticTest/expPower2Filler.yml
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
    ["state_tests/VMTests/vmArithmeticTest/expPower2Filler.yml"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_exp_power2(
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
        code=Op.SSTORE(key=Op.MUL(0x10, 0x1), value=Op.EXP(0x2, Op.EXP(0x2, 0x1)))  # noqa: E501
        + Op.SSTORE(key=Op.ADD(Op.MUL(0x10, 0x1), 0x1), value=Op.EXP(0x2, Op.SUB(Op.EXP(0x2, 0x1), 0x1)))  # noqa: E501
        + Op.SSTORE(key=Op.ADD(Op.MUL(0x10, 0x1), 0x2), value=Op.EXP(0x2, Op.ADD(Op.EXP(0x2, 0x1), 0x1)))  # noqa: E501
        + Op.SSTORE(key=Op.MUL(0x10, 0x2), value=Op.EXP(0x2, Op.EXP(0x2, 0x2)))
        + Op.SSTORE(key=Op.ADD(Op.MUL(0x10, 0x2), 0x1), value=Op.EXP(0x2, Op.SUB(Op.EXP(0x2, 0x2), 0x1)))  # noqa: E501
        + Op.SSTORE(key=Op.ADD(Op.MUL(0x10, 0x2), 0x2), value=Op.EXP(0x2, Op.ADD(Op.EXP(0x2, 0x2), 0x1)))  # noqa: E501
        + Op.SSTORE(key=Op.MUL(0x10, 0x3), value=Op.EXP(0x2, Op.EXP(0x2, 0x3)))
        + Op.SSTORE(key=Op.ADD(Op.MUL(0x10, 0x3), 0x1), value=Op.EXP(0x2, Op.SUB(Op.EXP(0x2, 0x3), 0x1)))  # noqa: E501
        + Op.SSTORE(key=Op.ADD(Op.MUL(0x10, 0x3), 0x2), value=Op.EXP(0x2, Op.ADD(Op.EXP(0x2, 0x3), 0x1)))  # noqa: E501
        + Op.SSTORE(key=Op.MUL(0x10, 0x4), value=Op.EXP(0x2, Op.EXP(0x2, 0x4)))
        + Op.SSTORE(key=Op.ADD(Op.MUL(0x10, 0x4), 0x1), value=Op.EXP(0x2, Op.SUB(Op.EXP(0x2, 0x4), 0x1)))  # noqa: E501
        + Op.SSTORE(key=Op.ADD(Op.MUL(0x10, 0x4), 0x2), value=Op.EXP(0x2, Op.ADD(Op.EXP(0x2, 0x4), 0x1)))  # noqa: E501
        + Op.SSTORE(key=Op.MUL(0x10, 0x5), value=Op.EXP(0x2, Op.EXP(0x2, 0x5)))
        + Op.SSTORE(key=Op.ADD(Op.MUL(0x10, 0x5), 0x1), value=Op.EXP(0x2, Op.SUB(Op.EXP(0x2, 0x5), 0x1)))  # noqa: E501
        + Op.SSTORE(key=Op.ADD(Op.MUL(0x10, 0x5), 0x2), value=Op.EXP(0x2, Op.ADD(Op.EXP(0x2, 0x5), 0x1)))  # noqa: E501
        + Op.SSTORE(key=Op.MUL(0x10, 0x6), value=Op.EXP(0x2, Op.EXP(0x2, 0x6)))
        + Op.SSTORE(key=Op.ADD(Op.MUL(0x10, 0x6), 0x1), value=Op.EXP(0x2, Op.SUB(Op.EXP(0x2, 0x6), 0x1)))  # noqa: E501
        + Op.SSTORE(key=Op.ADD(Op.MUL(0x10, 0x6), 0x2), value=Op.EXP(0x2, Op.ADD(Op.EXP(0x2, 0x6), 0x1)))  # noqa: E501
        + Op.SSTORE(key=Op.MUL(0x10, 0x7), value=Op.EXP(0x2, Op.EXP(0x2, 0x7)))
        + Op.SSTORE(key=Op.ADD(Op.MUL(0x10, 0x7), 0x1), value=Op.EXP(0x2, Op.SUB(Op.EXP(0x2, 0x7), 0x1)))  # noqa: E501
        + Op.SSTORE(key=Op.ADD(Op.MUL(0x10, 0x7), 0x2), value=Op.EXP(0x2, Op.ADD(Op.EXP(0x2, 0x7), 0x1)))  # noqa: E501
        + Op.SSTORE(key=Op.MUL(0x10, 0x8), value=Op.EXP(0x2, Op.EXP(0x2, 0x8)))
        + Op.SSTORE(key=Op.ADD(Op.MUL(0x10, 0x8), 0x1), value=Op.EXP(0x2, Op.SUB(Op.EXP(0x2, 0x8), 0x1)))  # noqa: E501
        + Op.SSTORE(key=Op.ADD(Op.MUL(0x10, 0x8), 0x2), value=Op.EXP(0x2, Op.ADD(Op.EXP(0x2, 0x8), 0x1)))  # noqa: E501
        + Op.STOP,
        balance=0xba1a9ce0ba1a9ce,
        nonce=0,
        address=Address("0x5a18b275908ad6766155191a40654188fe012dc6"),  # noqa: E501
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
            129: 0x8000000000000000000000000000000000000000000000000000000000000000,
        },
            ),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
