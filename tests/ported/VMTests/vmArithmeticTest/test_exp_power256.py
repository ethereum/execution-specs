"""
Ori Pomerantz qbzzt1@gmail.com

Ported from:
tests/static/state_tests/VMTests/vmArithmeticTest/expPower256Filler.yml

contract code:
    push1 0x00
    push2 0x0100
    exp
    push1 0x00
    push1 0x10
    mul
    sstore
    push1 0x00
    push1 0xff
    exp
    push1 0x01
    push1 0x00
    push1 0x10
    mul
    add
    sstore
    push1 0x00
    push2 0x0101
    exp
    push1 0x02
    ... (831 more instructions)
"""

import pytest
from execution_testing import (
    Account,
    Address,
    Alloc,
    Environment,
    Hash,
    StateTestFiller,
    Transaction,
)
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


@pytest.mark.ported_from(
    ["tests/static/state_tests/VMTests/vmArithmeticTest/expPower256Filler.yml"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_exp_power256(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Ori Pomerantz qbzzt1@gmail.com."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = Address("0x56724d001b4f2a2888a81971a64aad37cd43f881")
    contract = Address("0xe660d528e4a7ad36825f9d64f5f141596feff7ae")

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=100000000,
    )

    pre[sender] = Account(balance=0xba1a9ce0ba1a9ce, nonce=0)
    pre[contract] = Account(
        balance=0xba1a9ce0ba1a9ce,
        nonce=0,
        code=(
        Op.PUSH1[0x0] + Op.PUSH2[0x100] + Op.EXP + Op.PUSH1[0x0] + Op.PUSH1[0x10]
        + Op.MUL + Op.SSTORE + Op.PUSH1[0x0] + Op.PUSH1[0xff] + Op.EXP + Op.PUSH1[0x1]
        + Op.PUSH1[0x0] + Op.PUSH1[0x10] + Op.MUL + Op.ADD + Op.SSTORE + Op.PUSH1[0x0]
        + Op.PUSH2[0x101] + Op.EXP + Op.PUSH1[0x2] + Op.PUSH1[0x0] + Op.PUSH1[0x10]
        + Op.MUL + Op.ADD + Op.SSTORE + Op.PUSH1[0x1] + Op.PUSH2[0x100] + Op.EXP
        + Op.PUSH1[0x1] + Op.PUSH1[0x10] + Op.MUL + Op.SSTORE + Op.PUSH1[0x1]
        + Op.PUSH1[0xff] + Op.EXP + Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.PUSH1[0x10]
        + Op.MUL + Op.ADD + Op.SSTORE + Op.PUSH1[0x1] + Op.PUSH2[0x101] + Op.EXP
        + Op.PUSH1[0x2] + Op.PUSH1[0x1] + Op.PUSH1[0x10] + Op.MUL + Op.ADD + Op.SSTORE
        + Op.PUSH1[0x2] + Op.PUSH2[0x100] + Op.EXP + Op.PUSH1[0x2] + Op.PUSH1[0x10]
        + Op.MUL + Op.SSTORE + Op.PUSH1[0x2] + Op.PUSH1[0xff] + Op.EXP + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.PUSH1[0x10] + Op.MUL + Op.ADD + Op.SSTORE + Op.PUSH1[0x2]
        + Op.PUSH2[0x101] + Op.EXP + Op.PUSH1[0x2] + Op.PUSH1[0x2] + Op.PUSH1[0x10]
        + Op.MUL + Op.ADD + Op.SSTORE + Op.PUSH1[0x3] + Op.PUSH2[0x100] + Op.EXP
        + Op.PUSH1[0x3] + Op.PUSH1[0x10] + Op.MUL + Op.SSTORE + Op.PUSH1[0x3]
        + Op.PUSH1[0xff] + Op.EXP + Op.PUSH1[0x1] + Op.PUSH1[0x3] + Op.PUSH1[0x10]
        + Op.MUL + Op.ADD + Op.SSTORE + Op.PUSH1[0x3] + Op.PUSH2[0x101] + Op.EXP
        + Op.PUSH1[0x2] + Op.PUSH1[0x3] + Op.PUSH1[0x10] + Op.MUL + Op.ADD + Op.SSTORE
        + Op.PUSH1[0x4] + Op.PUSH2[0x100] + Op.EXP + Op.PUSH1[0x4] + Op.PUSH1[0x10]
        + Op.MUL + Op.SSTORE + Op.PUSH1[0x4] + Op.PUSH1[0xff] + Op.EXP + Op.PUSH1[0x1]
        + Op.PUSH1[0x4] + Op.PUSH1[0x10] + Op.MUL + Op.ADD + Op.SSTORE + Op.PUSH1[0x4]
        + Op.PUSH2[0x101] + Op.EXP + Op.PUSH1[0x2] + Op.PUSH1[0x4] + Op.PUSH1[0x10]
        + Op.MUL + Op.ADD + Op.SSTORE + Op.PUSH1[0x5] + Op.PUSH2[0x100] + Op.EXP
        + Op.PUSH1[0x5] + Op.PUSH1[0x10] + Op.MUL + Op.SSTORE + Op.PUSH1[0x5]
        + Op.PUSH1[0xff] + Op.EXP + Op.PUSH1[0x1] + Op.PUSH1[0x5] + Op.PUSH1[0x10]
        + Op.MUL + Op.ADD + Op.SSTORE + Op.PUSH1[0x5] + Op.PUSH2[0x101] + Op.EXP
        + Op.PUSH1[0x2] + Op.PUSH1[0x5] + Op.PUSH1[0x10] + Op.MUL + Op.ADD + Op.SSTORE
        + Op.PUSH1[0x6] + Op.PUSH2[0x100] + Op.EXP + Op.PUSH1[0x6] + Op.PUSH1[0x10]
        + Op.MUL + Op.SSTORE + Op.PUSH1[0x6] + Op.PUSH1[0xff] + Op.EXP + Op.PUSH1[0x1]
        + Op.PUSH1[0x6] + Op.PUSH1[0x10] + Op.MUL + Op.ADD + Op.SSTORE + Op.PUSH1[0x6]
        + Op.PUSH2[0x101] + Op.EXP + Op.PUSH1[0x2] + Op.PUSH1[0x6] + Op.PUSH1[0x10]
        + Op.MUL + Op.ADD + Op.SSTORE + Op.PUSH1[0x7] + Op.PUSH2[0x100] + Op.EXP
        + Op.PUSH1[0x7] + Op.PUSH1[0x10] + Op.MUL + Op.SSTORE + Op.PUSH1[0x7]
        + Op.PUSH1[0xff] + Op.EXP + Op.PUSH1[0x1] + Op.PUSH1[0x7] + Op.PUSH1[0x10]
        + Op.MUL + Op.ADD + Op.SSTORE + Op.PUSH1[0x7] + Op.PUSH2[0x101] + Op.EXP
        + Op.PUSH1[0x2] + Op.PUSH1[0x7] + Op.PUSH1[0x10] + Op.MUL + Op.ADD + Op.SSTORE
        + Op.PUSH1[0x8] + Op.PUSH2[0x100] + Op.EXP + Op.PUSH1[0x8] + Op.PUSH1[0x10]
        + Op.MUL + Op.SSTORE + Op.PUSH1[0x8] + Op.PUSH1[0xff] + Op.EXP + Op.PUSH1[0x1]
        + Op.PUSH1[0x8] + Op.PUSH1[0x10] + Op.MUL + Op.ADD + Op.SSTORE + Op.PUSH1[0x8]
        + Op.PUSH2[0x101] + Op.EXP + Op.PUSH1[0x2] + Op.PUSH1[0x8] + Op.PUSH1[0x10]
        + Op.MUL + Op.ADD + Op.SSTORE + Op.PUSH1[0x9] + Op.PUSH2[0x100] + Op.EXP
        + Op.PUSH1[0x9] + Op.PUSH1[0x10] + Op.MUL + Op.SSTORE + Op.PUSH1[0x9]
        + Op.PUSH1[0xff] + Op.EXP + Op.PUSH1[0x1] + Op.PUSH1[0x9] + Op.PUSH1[0x10]
        + Op.MUL + Op.ADD + Op.SSTORE + Op.PUSH1[0x9] + Op.PUSH2[0x101] + Op.EXP
        + Op.PUSH1[0x2] + Op.PUSH1[0x9] + Op.PUSH1[0x10] + Op.MUL + Op.ADD + Op.SSTORE
        + Op.PUSH1[0xa] + Op.PUSH2[0x100] + Op.EXP + Op.PUSH1[0xa] + Op.PUSH1[0x10]
        + Op.MUL + Op.SSTORE + Op.PUSH1[0xa] + Op.PUSH1[0xff] + Op.EXP + Op.PUSH1[0x1]
        + Op.PUSH1[0xa] + Op.PUSH1[0x10] + Op.MUL + Op.ADD + Op.SSTORE + Op.PUSH1[0xa]
        + Op.PUSH2[0x101] + Op.EXP + Op.PUSH1[0x2] + Op.PUSH1[0xa] + Op.PUSH1[0x10]
        + Op.MUL + Op.ADD + Op.SSTORE + Op.PUSH1[0xb] + Op.PUSH2[0x100] + Op.EXP
        + Op.PUSH1[0xb] + Op.PUSH1[0x10] + Op.MUL + Op.SSTORE + Op.PUSH1[0xb]
        + Op.PUSH1[0xff] + Op.EXP + Op.PUSH1[0x1] + Op.PUSH1[0xb] + Op.PUSH1[0x10]
        + Op.MUL + Op.ADD + Op.SSTORE + Op.PUSH1[0xb] + Op.PUSH2[0x101] + Op.EXP
        + Op.PUSH1[0x2] + Op.PUSH1[0xb] + Op.PUSH1[0x10] + Op.MUL + Op.ADD + Op.SSTORE
        + Op.PUSH1[0xc] + Op.PUSH2[0x100] + Op.EXP + Op.PUSH1[0xc] + Op.PUSH1[0x10]
        + Op.MUL + Op.SSTORE + Op.PUSH1[0xc] + Op.PUSH1[0xff] + Op.EXP + Op.PUSH1[0x1]
        + Op.PUSH1[0xc] + Op.PUSH1[0x10] + Op.MUL + Op.ADD + Op.SSTORE + Op.PUSH1[0xc]
        + Op.PUSH2[0x101] + Op.EXP + Op.PUSH1[0x2] + Op.PUSH1[0xc] + Op.PUSH1[0x10]
        + Op.MUL + Op.ADD + Op.SSTORE + Op.PUSH1[0xd] + Op.PUSH2[0x100] + Op.EXP
        + Op.PUSH1[0xd] + Op.PUSH1[0x10] + Op.MUL + Op.SSTORE + Op.PUSH1[0xd]
        + Op.PUSH1[0xff] + Op.EXP + Op.PUSH1[0x1] + Op.PUSH1[0xd] + Op.PUSH1[0x10]
        + Op.MUL + Op.ADD + Op.SSTORE + Op.PUSH1[0xd] + Op.PUSH2[0x101] + Op.EXP
        + Op.PUSH1[0x2] + Op.PUSH1[0xd] + Op.PUSH1[0x10] + Op.MUL + Op.ADD + Op.SSTORE
        + Op.PUSH1[0xe] + Op.PUSH2[0x100] + Op.EXP + Op.PUSH1[0xe] + Op.PUSH1[0x10]
        + Op.MUL + Op.SSTORE + Op.PUSH1[0xe] + Op.PUSH1[0xff] + Op.EXP + Op.PUSH1[0x1]
        + Op.PUSH1[0xe] + Op.PUSH1[0x10] + Op.MUL + Op.ADD + Op.SSTORE + Op.PUSH1[0xe]
        + Op.PUSH2[0x101] + Op.EXP + Op.PUSH1[0x2] + Op.PUSH1[0xe] + Op.PUSH1[0x10]
        + Op.MUL + Op.ADD + Op.SSTORE + Op.PUSH1[0xf] + Op.PUSH2[0x100] + Op.EXP
        + Op.PUSH1[0xf] + Op.PUSH1[0x10] + Op.MUL + Op.SSTORE + Op.PUSH1[0xf]
        + Op.PUSH1[0xff] + Op.EXP + Op.PUSH1[0x1] + Op.PUSH1[0xf] + Op.PUSH1[0x10]
        + Op.MUL + Op.ADD + Op.SSTORE + Op.PUSH1[0xf] + Op.PUSH2[0x101] + Op.EXP
        + Op.PUSH1[0x2] + Op.PUSH1[0xf] + Op.PUSH1[0x10] + Op.MUL + Op.ADD + Op.SSTORE
        + Op.PUSH1[0x10] + Op.PUSH2[0x100] + Op.EXP + Op.PUSH1[0x10] + Op.PUSH1[0x10]
        + Op.MUL + Op.SSTORE + Op.PUSH1[0x10] + Op.PUSH1[0xff] + Op.EXP
        + Op.PUSH1[0x1] + Op.PUSH1[0x10] + Op.PUSH1[0x10] + Op.MUL + Op.ADD
        + Op.SSTORE + Op.PUSH1[0x10] + Op.PUSH2[0x101] + Op.EXP + Op.PUSH1[0x2]
        + Op.PUSH1[0x10] + Op.PUSH1[0x10] + Op.MUL + Op.ADD + Op.SSTORE
        + Op.PUSH1[0x11] + Op.PUSH2[0x100] + Op.EXP + Op.PUSH1[0x11] + Op.PUSH1[0x10]
        + Op.MUL + Op.SSTORE + Op.PUSH1[0x11] + Op.PUSH1[0xff] + Op.EXP
        + Op.PUSH1[0x1] + Op.PUSH1[0x11] + Op.PUSH1[0x10] + Op.MUL + Op.ADD
        + Op.SSTORE + Op.PUSH1[0x11] + Op.PUSH2[0x101] + Op.EXP + Op.PUSH1[0x2]
        + Op.PUSH1[0x11] + Op.PUSH1[0x10] + Op.MUL + Op.ADD + Op.SSTORE
        + Op.PUSH1[0x12] + Op.PUSH2[0x100] + Op.EXP + Op.PUSH1[0x12] + Op.PUSH1[0x10]
        + Op.MUL + Op.SSTORE + Op.PUSH1[0x12] + Op.PUSH1[0xff] + Op.EXP
        + Op.PUSH1[0x1] + Op.PUSH1[0x12] + Op.PUSH1[0x10] + Op.MUL + Op.ADD
        + Op.SSTORE + Op.PUSH1[0x12] + Op.PUSH2[0x101] + Op.EXP + Op.PUSH1[0x2]
        + Op.PUSH1[0x12] + Op.PUSH1[0x10] + Op.MUL + Op.ADD + Op.SSTORE
        + Op.PUSH1[0x13] + Op.PUSH2[0x100] + Op.EXP + Op.PUSH1[0x13] + Op.PUSH1[0x10]
        + Op.MUL + Op.SSTORE + Op.PUSH1[0x13] + Op.PUSH1[0xff] + Op.EXP
        + Op.PUSH1[0x1] + Op.PUSH1[0x13] + Op.PUSH1[0x10] + Op.MUL + Op.ADD
        + Op.SSTORE + Op.PUSH1[0x13] + Op.PUSH2[0x101] + Op.EXP + Op.PUSH1[0x2]
        + Op.PUSH1[0x13] + Op.PUSH1[0x10] + Op.MUL + Op.ADD + Op.SSTORE
        + Op.PUSH1[0x14] + Op.PUSH2[0x100] + Op.EXP + Op.PUSH1[0x14] + Op.PUSH1[0x10]
        + Op.MUL + Op.SSTORE + Op.PUSH1[0x14] + Op.PUSH1[0xff] + Op.EXP
        + Op.PUSH1[0x1] + Op.PUSH1[0x14] + Op.PUSH1[0x10] + Op.MUL + Op.ADD
        + Op.SSTORE + Op.PUSH1[0x14] + Op.PUSH2[0x101] + Op.EXP + Op.PUSH1[0x2]
        + Op.PUSH1[0x14] + Op.PUSH1[0x10] + Op.MUL + Op.ADD + Op.SSTORE
        + Op.PUSH1[0x15] + Op.PUSH2[0x100] + Op.EXP + Op.PUSH1[0x15] + Op.PUSH1[0x10]
        + Op.MUL + Op.SSTORE + Op.PUSH1[0x15] + Op.PUSH1[0xff] + Op.EXP
        + Op.PUSH1[0x1] + Op.PUSH1[0x15] + Op.PUSH1[0x10] + Op.MUL + Op.ADD
        + Op.SSTORE + Op.PUSH1[0x15] + Op.PUSH2[0x101] + Op.EXP + Op.PUSH1[0x2]
        + Op.PUSH1[0x15] + Op.PUSH1[0x10] + Op.MUL + Op.ADD + Op.SSTORE
        + Op.PUSH1[0x16] + Op.PUSH2[0x100] + Op.EXP + Op.PUSH1[0x16] + Op.PUSH1[0x10]
        + Op.MUL + Op.SSTORE + Op.PUSH1[0x16] + Op.PUSH1[0xff] + Op.EXP
        + Op.PUSH1[0x1] + Op.PUSH1[0x16] + Op.PUSH1[0x10] + Op.MUL + Op.ADD
        + Op.SSTORE + Op.PUSH1[0x16] + Op.PUSH2[0x101] + Op.EXP + Op.PUSH1[0x2]
        + Op.PUSH1[0x16] + Op.PUSH1[0x10] + Op.MUL + Op.ADD + Op.SSTORE
        + Op.PUSH1[0x17] + Op.PUSH2[0x100] + Op.EXP + Op.PUSH1[0x17] + Op.PUSH1[0x10]
        + Op.MUL + Op.SSTORE + Op.PUSH1[0x17] + Op.PUSH1[0xff] + Op.EXP
        + Op.PUSH1[0x1] + Op.PUSH1[0x17] + Op.PUSH1[0x10] + Op.MUL + Op.ADD
        + Op.SSTORE + Op.PUSH1[0x17] + Op.PUSH2[0x101] + Op.EXP + Op.PUSH1[0x2]
        + Op.PUSH1[0x17] + Op.PUSH1[0x10] + Op.MUL + Op.ADD + Op.SSTORE
        + Op.PUSH1[0x18] + Op.PUSH2[0x100] + Op.EXP + Op.PUSH1[0x18] + Op.PUSH1[0x10]
        + Op.MUL + Op.SSTORE + Op.PUSH1[0x18] + Op.PUSH1[0xff] + Op.EXP
        + Op.PUSH1[0x1] + Op.PUSH1[0x18] + Op.PUSH1[0x10] + Op.MUL + Op.ADD
        + Op.SSTORE + Op.PUSH1[0x18] + Op.PUSH2[0x101] + Op.EXP + Op.PUSH1[0x2]
        + Op.PUSH1[0x18] + Op.PUSH1[0x10] + Op.MUL + Op.ADD + Op.SSTORE
        + Op.PUSH1[0x19] + Op.PUSH2[0x100] + Op.EXP + Op.PUSH1[0x19] + Op.PUSH1[0x10]
        + Op.MUL + Op.SSTORE + Op.PUSH1[0x19] + Op.PUSH1[0xff] + Op.EXP
        + Op.PUSH1[0x1] + Op.PUSH1[0x19] + Op.PUSH1[0x10] + Op.MUL + Op.ADD
        + Op.SSTORE + Op.PUSH1[0x19] + Op.PUSH2[0x101] + Op.EXP + Op.PUSH1[0x2]
        + Op.PUSH1[0x19] + Op.PUSH1[0x10] + Op.MUL + Op.ADD + Op.SSTORE
        + Op.PUSH1[0x1a] + Op.PUSH2[0x100] + Op.EXP + Op.PUSH1[0x1a] + Op.PUSH1[0x10]
        + Op.MUL + Op.SSTORE + Op.PUSH1[0x1a] + Op.PUSH1[0xff] + Op.EXP
        + Op.PUSH1[0x1] + Op.PUSH1[0x1a] + Op.PUSH1[0x10] + Op.MUL + Op.ADD
        + Op.SSTORE + Op.PUSH1[0x1a] + Op.PUSH2[0x101] + Op.EXP + Op.PUSH1[0x2]
        + Op.PUSH1[0x1a] + Op.PUSH1[0x10] + Op.MUL + Op.ADD + Op.SSTORE
        + Op.PUSH1[0x1b] + Op.PUSH2[0x100] + Op.EXP + Op.PUSH1[0x1b] + Op.PUSH1[0x10]
        + Op.MUL + Op.SSTORE + Op.PUSH1[0x1b] + Op.PUSH1[0xff] + Op.EXP
        + Op.PUSH1[0x1] + Op.PUSH1[0x1b] + Op.PUSH1[0x10] + Op.MUL + Op.ADD
        + Op.SSTORE + Op.PUSH1[0x1b] + Op.PUSH2[0x101] + Op.EXP + Op.PUSH1[0x2]
        + Op.PUSH1[0x1b] + Op.PUSH1[0x10] + Op.MUL + Op.ADD + Op.SSTORE
        + Op.PUSH1[0x1c] + Op.PUSH2[0x100] + Op.EXP + Op.PUSH1[0x1c] + Op.PUSH1[0x10]
        + Op.MUL + Op.SSTORE + Op.PUSH1[0x1c] + Op.PUSH1[0xff] + Op.EXP
        + Op.PUSH1[0x1] + Op.PUSH1[0x1c] + Op.PUSH1[0x10] + Op.MUL + Op.ADD
        + Op.SSTORE + Op.PUSH1[0x1c] + Op.PUSH2[0x101] + Op.EXP + Op.PUSH1[0x2]
        + Op.PUSH1[0x1c] + Op.PUSH1[0x10] + Op.MUL + Op.ADD + Op.SSTORE
        + Op.PUSH1[0x1d] + Op.PUSH2[0x100] + Op.EXP + Op.PUSH1[0x1d] + Op.PUSH1[0x10]
        + Op.MUL + Op.SSTORE + Op.PUSH1[0x1d] + Op.PUSH1[0xff] + Op.EXP
        + Op.PUSH1[0x1] + Op.PUSH1[0x1d] + Op.PUSH1[0x10] + Op.MUL + Op.ADD
        + Op.SSTORE + Op.PUSH1[0x1d] + Op.PUSH2[0x101] + Op.EXP + Op.PUSH1[0x2]
        + Op.PUSH1[0x1d] + Op.PUSH1[0x10] + Op.MUL + Op.ADD + Op.SSTORE
        + Op.PUSH1[0x1e] + Op.PUSH2[0x100] + Op.EXP + Op.PUSH1[0x1e] + Op.PUSH1[0x10]
        + Op.MUL + Op.SSTORE + Op.PUSH1[0x1e] + Op.PUSH1[0xff] + Op.EXP
        + Op.PUSH1[0x1] + Op.PUSH1[0x1e] + Op.PUSH1[0x10] + Op.MUL + Op.ADD
        + Op.SSTORE + Op.PUSH1[0x1e] + Op.PUSH2[0x101] + Op.EXP + Op.PUSH1[0x2]
        + Op.PUSH1[0x1e] + Op.PUSH1[0x10] + Op.MUL + Op.ADD + Op.SSTORE
        + Op.PUSH1[0x1f] + Op.PUSH2[0x100] + Op.EXP + Op.PUSH1[0x1f] + Op.PUSH1[0x10]
        + Op.MUL + Op.SSTORE + Op.PUSH1[0x1f] + Op.PUSH1[0xff] + Op.EXP
        + Op.PUSH1[0x1] + Op.PUSH1[0x1f] + Op.PUSH1[0x10] + Op.MUL + Op.ADD
        + Op.SSTORE + Op.PUSH1[0x1f] + Op.PUSH2[0x101] + Op.EXP + Op.PUSH1[0x2]
        + Op.PUSH1[0x1f] + Op.PUSH1[0x10] + Op.MUL + Op.ADD + Op.SSTORE
        + Op.PUSH1[0x20] + Op.PUSH2[0x100] + Op.EXP + Op.PUSH1[0x20] + Op.PUSH1[0x10]
        + Op.MUL + Op.SSTORE + Op.PUSH1[0x20] + Op.PUSH1[0xff] + Op.EXP
        + Op.PUSH1[0x1] + Op.PUSH1[0x20] + Op.PUSH1[0x10] + Op.MUL + Op.ADD
        + Op.SSTORE + Op.PUSH1[0x20] + Op.PUSH2[0x101] + Op.EXP + Op.PUSH1[0x2]
        + Op.PUSH1[0x20] + Op.PUSH1[0x10] + Op.MUL + Op.ADD + Op.SSTORE
        + Op.PUSH1[0x21] + Op.PUSH2[0x100] + Op.EXP + Op.PUSH1[0x21] + Op.PUSH1[0x10]
        + Op.MUL + Op.SSTORE + Op.PUSH1[0x21] + Op.PUSH1[0xff] + Op.EXP
        + Op.PUSH1[0x1] + Op.PUSH1[0x21] + Op.PUSH1[0x10] + Op.MUL + Op.ADD
        + Op.SSTORE + Op.PUSH1[0x21] + Op.PUSH2[0x101] + Op.EXP + Op.PUSH1[0x2]
        + Op.PUSH1[0x21] + Op.PUSH1[0x10] + Op.MUL + Op.ADD + Op.SSTORE + Op.STOP
    ),
    )

    tx = Transaction(
        secret_key=Hash(
            "0x40ac0fc28c27e961ee46ec43355a094de205856edbd4654cf2577c2608d4ec1e"
        ),
        to=contract,
        data=bytes.fromhex("693c61390000000000000000000000000000000000000000000000000000000000000000"),
        gas_limit=16777216,
        gas_price=10,
        nonce=0,
        value=1,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)
