"""
Ori Pomerantz qbzzt1@gmail.com

Ported from:
tests/static/state_tests/VMTests/vmArithmeticTest/twoOpsFiller.yml

contract code:
    push1 0x03
    push1 0x01
    push1 0x02
    add
    add
    push7 0x11000100010000
    sstore
    push1 0x01
    push1 0x01
    push1 0x02
    add
    add
    push7 0x11000100010001
    sstore
    push1 0x03
    push1 0x01
    push1 0x02
    mul
    add
    push7 0x11000100020000
    ... (8045 more instructions)
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
    ["tests/static/state_tests/VMTests/vmArithmeticTest/twoOpsFiller.yml"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_two_ops(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Ori Pomerantz qbzzt1@gmail.com."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = Address("0x56724d001b4f2a2888a81971a64aad37cd43f881")
    contract = Address("0xe262558822902632416f26edbf70ccac609cd2ce")

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
        balance=0,
        nonce=1,
        code=(
        Op.PUSH1[0x3] + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.ADD + Op.ADD
        + Op.PUSH7[0x11000100010000] + Op.SSTORE + Op.PUSH1[0x1] + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.ADD + Op.ADD + Op.PUSH7[0x11000100010001] + Op.SSTORE
        + Op.PUSH1[0x3] + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.MUL + Op.ADD
        + Op.PUSH7[0x11000100020000] + Op.SSTORE + Op.PUSH1[0x1] + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.MUL + Op.ADD + Op.PUSH7[0x11000100020001] + Op.SSTORE
        + Op.PUSH1[0x3] + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.SUB + Op.ADD
        + Op.PUSH7[0x11000100030000] + Op.SSTORE + Op.PUSH1[0x1] + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.SUB + Op.ADD + Op.PUSH7[0x11000100030001] + Op.SSTORE
        + Op.PUSH1[0x3] + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.DIV + Op.ADD
        + Op.PUSH7[0x11000100040000] + Op.SSTORE + Op.PUSH1[0x1] + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.DIV + Op.ADD + Op.PUSH7[0x11000100040001] + Op.SSTORE
        + Op.PUSH1[0x3] + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.SDIV + Op.ADD
        + Op.PUSH7[0x11000100050000] + Op.SSTORE + Op.PUSH1[0x1] + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.SDIV + Op.ADD + Op.PUSH7[0x11000100050001] + Op.SSTORE
        + Op.PUSH1[0x3] + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.MOD + Op.ADD
        + Op.PUSH7[0x11000100060000] + Op.SSTORE + Op.PUSH1[0x1] + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.MOD + Op.ADD + Op.PUSH7[0x11000100060001] + Op.SSTORE
        + Op.PUSH1[0x3] + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.SMOD + Op.ADD
        + Op.PUSH7[0x11000100070000] + Op.SSTORE + Op.PUSH1[0x1] + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.SMOD + Op.ADD + Op.PUSH7[0x11000100070001] + Op.SSTORE
        + Op.PUSH1[0x3] + Op.PUSH1[0x3] + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.ADDMOD
        + Op.ADD + Op.PUSH7[0x11000100080000] + Op.SSTORE + Op.PUSH1[0x1]
        + Op.PUSH1[0x3] + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.ADDMOD + Op.ADD
        + Op.PUSH7[0x11000100080001] + Op.SSTORE + Op.PUSH1[0x3] + Op.PUSH1[0x3]
        + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.MULMOD + Op.ADD
        + Op.PUSH7[0x11000100090000] + Op.SSTORE + Op.PUSH1[0x1] + Op.PUSH1[0x3]
        + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.MULMOD + Op.ADD
        + Op.PUSH7[0x11000100090001] + Op.SSTORE + Op.PUSH1[0x3] + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.EXP + Op.ADD + Op.PUSH7[0x110001000a0000] + Op.SSTORE
        + Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.EXP + Op.ADD
        + Op.PUSH7[0x110001000a0001] + Op.SSTORE + Op.PUSH1[0x3] + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.LT + Op.ADD + Op.PUSH7[0x11000100100000] + Op.SSTORE
        + Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.LT + Op.ADD
        + Op.PUSH7[0x11000100100001] + Op.SSTORE + Op.PUSH1[0x3] + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.GT + Op.ADD + Op.PUSH7[0x11000100110000] + Op.SSTORE
        + Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.GT + Op.ADD
        + Op.PUSH7[0x11000100110001] + Op.SSTORE + Op.PUSH1[0x3] + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.SLT + Op.ADD + Op.PUSH7[0x11000100120000] + Op.SSTORE
        + Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.SLT + Op.ADD
        + Op.PUSH7[0x11000100120001] + Op.SSTORE + Op.PUSH1[0x3] + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.SGT + Op.ADD + Op.PUSH7[0x11000100130000] + Op.SSTORE
        + Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.SGT + Op.ADD
        + Op.PUSH7[0x11000100130001] + Op.SSTORE + Op.PUSH1[0x3] + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.EQ + Op.ADD + Op.PUSH7[0x11000100140000] + Op.SSTORE
        + Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.EQ + Op.ADD
        + Op.PUSH7[0x11000100140001] + Op.SSTORE + Op.PUSH1[0x3] + Op.PUSH1[0x2]
        + Op.ISZERO + Op.ADD + Op.PUSH7[0x11000100150000] + Op.SSTORE + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.ISZERO + Op.ADD + Op.PUSH7[0x11000100150001] + Op.SSTORE
        + Op.PUSH1[0x3] + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.AND + Op.ADD
        + Op.PUSH7[0x11000100160000] + Op.SSTORE + Op.PUSH1[0x1] + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.AND + Op.ADD + Op.PUSH7[0x11000100160001] + Op.SSTORE
        + Op.PUSH1[0x3] + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.OR + Op.ADD
        + Op.PUSH7[0x11000100170000] + Op.SSTORE + Op.PUSH1[0x1] + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.OR + Op.ADD + Op.PUSH7[0x11000100170001] + Op.SSTORE
        + Op.PUSH1[0x3] + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.XOR + Op.ADD
        + Op.PUSH7[0x11000100180000] + Op.SSTORE + Op.PUSH1[0x1] + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.XOR + Op.ADD + Op.PUSH7[0x11000100180001] + Op.SSTORE
        + Op.PUSH1[0x3] + Op.PUSH1[0x2] + Op.NOT + Op.ADD + Op.PUSH7[0x11000100190000]
        + Op.SSTORE + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.NOT + Op.ADD
        + Op.PUSH7[0x11000100190001] + Op.SSTORE + Op.PUSH1[0x3] + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.BYTE + Op.ADD + Op.PUSH7[0x110001001a0000] + Op.SSTORE
        + Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.BYTE + Op.ADD
        + Op.PUSH7[0x110001001a0001] + Op.SSTORE + Op.PUSH1[0x3] + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.SHL + Op.ADD + Op.PUSH7[0x110001001b0000] + Op.SSTORE
        + Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.SHL + Op.ADD
        + Op.PUSH7[0x110001001b0001] + Op.SSTORE + Op.PUSH1[0x3] + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.SHR + Op.ADD + Op.PUSH7[0x110001001c0000] + Op.SSTORE
        + Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.SHR + Op.ADD
        + Op.PUSH7[0x110001001c0001] + Op.SSTORE + Op.PUSH1[0x3] + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.SAR + Op.ADD + Op.PUSH7[0x110001001d0000] + Op.SSTORE
        + Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.SAR + Op.ADD
        + Op.PUSH7[0x110001001d0001] + Op.SSTORE + Op.PUSH1[0x3] + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.ADD + Op.MUL + Op.PUSH7[0x11000200010000] + Op.SSTORE
        + Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.ADD + Op.MUL
        + Op.PUSH7[0x11000200010001] + Op.SSTORE + Op.PUSH1[0x3] + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.MUL + Op.MUL + Op.PUSH7[0x11000200020000] + Op.SSTORE
        + Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.MUL + Op.MUL
        + Op.PUSH7[0x11000200020001] + Op.SSTORE + Op.PUSH1[0x3] + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.SUB + Op.MUL + Op.PUSH7[0x11000200030000] + Op.SSTORE
        + Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.SUB + Op.MUL
        + Op.PUSH7[0x11000200030001] + Op.SSTORE + Op.PUSH1[0x3] + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.DIV + Op.MUL + Op.PUSH7[0x11000200040000] + Op.SSTORE
        + Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.DIV + Op.MUL
        + Op.PUSH7[0x11000200040001] + Op.SSTORE + Op.PUSH1[0x3] + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.SDIV + Op.MUL + Op.PUSH7[0x11000200050000] + Op.SSTORE
        + Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.SDIV + Op.MUL
        + Op.PUSH7[0x11000200050001] + Op.SSTORE + Op.PUSH1[0x3] + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.MOD + Op.MUL + Op.PUSH7[0x11000200060000] + Op.SSTORE
        + Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.MOD + Op.MUL
        + Op.PUSH7[0x11000200060001] + Op.SSTORE + Op.PUSH1[0x3] + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.SMOD + Op.MUL + Op.PUSH7[0x11000200070000] + Op.SSTORE
        + Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.SMOD + Op.MUL
        + Op.PUSH7[0x11000200070001] + Op.SSTORE + Op.PUSH1[0x3] + Op.PUSH1[0x3]
        + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.ADDMOD + Op.MUL
        + Op.PUSH7[0x11000200080000] + Op.SSTORE + Op.PUSH1[0x1] + Op.PUSH1[0x3]
        + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.ADDMOD + Op.MUL
        + Op.PUSH7[0x11000200080001] + Op.SSTORE + Op.PUSH1[0x3] + Op.PUSH1[0x3]
        + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.MULMOD + Op.MUL
        + Op.PUSH7[0x11000200090000] + Op.SSTORE + Op.PUSH1[0x1] + Op.PUSH1[0x3]
        + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.MULMOD + Op.MUL
        + Op.PUSH7[0x11000200090001] + Op.SSTORE + Op.PUSH1[0x3] + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.EXP + Op.MUL + Op.PUSH7[0x110002000a0000] + Op.SSTORE
        + Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.EXP + Op.MUL
        + Op.PUSH7[0x110002000a0001] + Op.SSTORE + Op.PUSH1[0x3] + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.LT + Op.MUL + Op.PUSH7[0x11000200100000] + Op.SSTORE
        + Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.LT + Op.MUL
        + Op.PUSH7[0x11000200100001] + Op.SSTORE + Op.PUSH1[0x3] + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.GT + Op.MUL + Op.PUSH7[0x11000200110000] + Op.SSTORE
        + Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.GT + Op.MUL
        + Op.PUSH7[0x11000200110001] + Op.SSTORE + Op.PUSH1[0x3] + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.SLT + Op.MUL + Op.PUSH7[0x11000200120000] + Op.SSTORE
        + Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.SLT + Op.MUL
        + Op.PUSH7[0x11000200120001] + Op.SSTORE + Op.PUSH1[0x3] + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.SGT + Op.MUL + Op.PUSH7[0x11000200130000] + Op.SSTORE
        + Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.SGT + Op.MUL
        + Op.PUSH7[0x11000200130001] + Op.SSTORE + Op.PUSH1[0x3] + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.EQ + Op.MUL + Op.PUSH7[0x11000200140000] + Op.SSTORE
        + Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.EQ + Op.MUL
        + Op.PUSH7[0x11000200140001] + Op.SSTORE + Op.PUSH1[0x3] + Op.PUSH1[0x2]
        + Op.ISZERO + Op.MUL + Op.PUSH7[0x11000200150000] + Op.SSTORE + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.ISZERO + Op.MUL + Op.PUSH7[0x11000200150001] + Op.SSTORE
        + Op.PUSH1[0x3] + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.AND + Op.MUL
        + Op.PUSH7[0x11000200160000] + Op.SSTORE + Op.PUSH1[0x1] + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.AND + Op.MUL + Op.PUSH7[0x11000200160001] + Op.SSTORE
        + Op.PUSH1[0x3] + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.OR + Op.MUL
        + Op.PUSH7[0x11000200170000] + Op.SSTORE + Op.PUSH1[0x1] + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.OR + Op.MUL + Op.PUSH7[0x11000200170001] + Op.SSTORE
        + Op.PUSH1[0x3] + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.XOR + Op.MUL
        + Op.PUSH7[0x11000200180000] + Op.SSTORE + Op.PUSH1[0x1] + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.XOR + Op.MUL + Op.PUSH7[0x11000200180001] + Op.SSTORE
        + Op.PUSH1[0x3] + Op.PUSH1[0x2] + Op.NOT + Op.MUL + Op.PUSH7[0x11000200190000]
        + Op.SSTORE + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.NOT + Op.MUL
        + Op.PUSH7[0x11000200190001] + Op.SSTORE + Op.PUSH1[0x3] + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.BYTE + Op.MUL + Op.PUSH7[0x110002001a0000] + Op.SSTORE
        + Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.BYTE + Op.MUL
        + Op.PUSH7[0x110002001a0001] + Op.SSTORE + Op.PUSH1[0x3] + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.SHL + Op.MUL + Op.PUSH7[0x110002001b0000] + Op.SSTORE
        + Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.SHL + Op.MUL
        + Op.PUSH7[0x110002001b0001] + Op.SSTORE + Op.PUSH1[0x3] + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.SHR + Op.MUL + Op.PUSH7[0x110002001c0000] + Op.SSTORE
        + Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.SHR + Op.MUL
        + Op.PUSH7[0x110002001c0001] + Op.SSTORE + Op.PUSH1[0x3] + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.SAR + Op.MUL + Op.PUSH7[0x110002001d0000] + Op.SSTORE
        + Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.SAR + Op.MUL
        + Op.PUSH7[0x110002001d0001] + Op.SSTORE + Op.PUSH1[0x3] + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.ADD + Op.SUB + Op.PUSH7[0x11000300010000] + Op.SSTORE
        + Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.ADD + Op.SUB
        + Op.PUSH7[0x11000300010001] + Op.SSTORE + Op.PUSH1[0x3] + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.MUL + Op.SUB + Op.PUSH7[0x11000300020000] + Op.SSTORE
        + Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.MUL + Op.SUB
        + Op.PUSH7[0x11000300020001] + Op.SSTORE + Op.PUSH1[0x3] + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.SUB + Op.SUB + Op.PUSH7[0x11000300030000] + Op.SSTORE
        + Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.SUB + Op.SUB
        + Op.PUSH7[0x11000300030001] + Op.SSTORE + Op.PUSH1[0x3] + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.DIV + Op.SUB + Op.PUSH7[0x11000300040000] + Op.SSTORE
        + Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.DIV + Op.SUB
        + Op.PUSH7[0x11000300040001] + Op.SSTORE + Op.PUSH1[0x3] + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.SDIV + Op.SUB + Op.PUSH7[0x11000300050000] + Op.SSTORE
        + Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.SDIV + Op.SUB
        + Op.PUSH7[0x11000300050001] + Op.SSTORE + Op.PUSH1[0x3] + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.MOD + Op.SUB + Op.PUSH7[0x11000300060000] + Op.SSTORE
        + Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.MOD + Op.SUB
        + Op.PUSH7[0x11000300060001] + Op.SSTORE + Op.PUSH1[0x3] + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.SMOD + Op.SUB + Op.PUSH7[0x11000300070000] + Op.SSTORE
        + Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.SMOD + Op.SUB
        + Op.PUSH7[0x11000300070001] + Op.SSTORE + Op.PUSH1[0x3] + Op.PUSH1[0x3]
        + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.ADDMOD + Op.SUB
        + Op.PUSH7[0x11000300080000] + Op.SSTORE + Op.PUSH1[0x1] + Op.PUSH1[0x3]
        + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.ADDMOD + Op.SUB
        + Op.PUSH7[0x11000300080001] + Op.SSTORE + Op.PUSH1[0x3] + Op.PUSH1[0x3]
        + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.MULMOD + Op.SUB
        + Op.PUSH7[0x11000300090000] + Op.SSTORE + Op.PUSH1[0x1] + Op.PUSH1[0x3]
        + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.MULMOD + Op.SUB
        + Op.PUSH7[0x11000300090001] + Op.SSTORE + Op.PUSH1[0x3] + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.EXP + Op.SUB + Op.PUSH7[0x110003000a0000] + Op.SSTORE
        + Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.EXP + Op.SUB
        + Op.PUSH7[0x110003000a0001] + Op.SSTORE + Op.PUSH1[0x3] + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.LT + Op.SUB + Op.PUSH7[0x11000300100000] + Op.SSTORE
        + Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.LT + Op.SUB
        + Op.PUSH7[0x11000300100001] + Op.SSTORE + Op.PUSH1[0x3] + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.GT + Op.SUB + Op.PUSH7[0x11000300110000] + Op.SSTORE
        + Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.GT + Op.SUB
        + Op.PUSH7[0x11000300110001] + Op.SSTORE + Op.PUSH1[0x3] + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.SLT + Op.SUB + Op.PUSH7[0x11000300120000] + Op.SSTORE
        + Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.SLT + Op.SUB
        + Op.PUSH7[0x11000300120001] + Op.SSTORE + Op.PUSH1[0x3] + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.SGT + Op.SUB + Op.PUSH7[0x11000300130000] + Op.SSTORE
        + Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.SGT + Op.SUB
        + Op.PUSH7[0x11000300130001] + Op.SSTORE + Op.PUSH1[0x3] + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.EQ + Op.SUB + Op.PUSH7[0x11000300140000] + Op.SSTORE
        + Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.EQ + Op.SUB
        + Op.PUSH7[0x11000300140001] + Op.SSTORE + Op.PUSH1[0x3] + Op.PUSH1[0x2]
        + Op.ISZERO + Op.SUB + Op.PUSH7[0x11000300150000] + Op.SSTORE + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.ISZERO + Op.SUB + Op.PUSH7[0x11000300150001] + Op.SSTORE
        + Op.PUSH1[0x3] + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.AND + Op.SUB
        + Op.PUSH7[0x11000300160000] + Op.SSTORE + Op.PUSH1[0x1] + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.AND + Op.SUB + Op.PUSH7[0x11000300160001] + Op.SSTORE
        + Op.PUSH1[0x3] + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.OR + Op.SUB
        + Op.PUSH7[0x11000300170000] + Op.SSTORE + Op.PUSH1[0x1] + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.OR + Op.SUB + Op.PUSH7[0x11000300170001] + Op.SSTORE
        + Op.PUSH1[0x3] + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.XOR + Op.SUB
        + Op.PUSH7[0x11000300180000] + Op.SSTORE + Op.PUSH1[0x1] + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.XOR + Op.SUB + Op.PUSH7[0x11000300180001] + Op.SSTORE
        + Op.PUSH1[0x3] + Op.PUSH1[0x2] + Op.NOT + Op.SUB + Op.PUSH7[0x11000300190000]
        + Op.SSTORE + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.NOT + Op.SUB
        + Op.PUSH7[0x11000300190001] + Op.SSTORE + Op.PUSH1[0x3] + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.BYTE + Op.SUB + Op.PUSH7[0x110003001a0000] + Op.SSTORE
        + Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.BYTE + Op.SUB
        + Op.PUSH7[0x110003001a0001] + Op.SSTORE + Op.PUSH1[0x3] + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.SHL + Op.SUB + Op.PUSH7[0x110003001b0000] + Op.SSTORE
        + Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.SHL + Op.SUB
        + Op.PUSH7[0x110003001b0001] + Op.SSTORE + Op.PUSH1[0x3] + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.SHR + Op.SUB + Op.PUSH7[0x110003001c0000] + Op.SSTORE
        + Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.SHR + Op.SUB
        + Op.PUSH7[0x110003001c0001] + Op.SSTORE + Op.PUSH1[0x3] + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.SAR + Op.SUB + Op.PUSH7[0x110003001d0000] + Op.SSTORE
        + Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.SAR + Op.SUB
        + Op.PUSH7[0x110003001d0001] + Op.SSTORE + Op.PUSH1[0x3] + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.ADD + Op.DIV + Op.PUSH7[0x11000400010000] + Op.SSTORE
        + Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.ADD + Op.DIV
        + Op.PUSH7[0x11000400010001] + Op.SSTORE + Op.PUSH1[0x3] + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.MUL + Op.DIV + Op.PUSH7[0x11000400020000] + Op.SSTORE
        + Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.MUL + Op.DIV
        + Op.PUSH7[0x11000400020001] + Op.SSTORE + Op.PUSH1[0x3] + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.SUB + Op.DIV + Op.PUSH7[0x11000400030000] + Op.SSTORE
        + Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.SUB + Op.DIV
        + Op.PUSH7[0x11000400030001] + Op.SSTORE + Op.PUSH1[0x3] + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.DIV + Op.DIV + Op.PUSH7[0x11000400040000] + Op.SSTORE
        + Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.DIV + Op.DIV
        + Op.PUSH7[0x11000400040001] + Op.SSTORE + Op.PUSH1[0x3] + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.SDIV + Op.DIV + Op.PUSH7[0x11000400050000] + Op.SSTORE
        + Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.SDIV + Op.DIV
        + Op.PUSH7[0x11000400050001] + Op.SSTORE + Op.PUSH1[0x3] + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.MOD + Op.DIV + Op.PUSH7[0x11000400060000] + Op.SSTORE
        + Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.MOD + Op.DIV
        + Op.PUSH7[0x11000400060001] + Op.SSTORE + Op.PUSH1[0x3] + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.SMOD + Op.DIV + Op.PUSH7[0x11000400070000] + Op.SSTORE
        + Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.SMOD + Op.DIV
        + Op.PUSH7[0x11000400070001] + Op.SSTORE + Op.PUSH1[0x3] + Op.PUSH1[0x3]
        + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.ADDMOD + Op.DIV
        + Op.PUSH7[0x11000400080000] + Op.SSTORE + Op.PUSH1[0x1] + Op.PUSH1[0x3]
        + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.ADDMOD + Op.DIV
        + Op.PUSH7[0x11000400080001] + Op.SSTORE + Op.PUSH1[0x3] + Op.PUSH1[0x3]
        + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.MULMOD + Op.DIV
        + Op.PUSH7[0x11000400090000] + Op.SSTORE + Op.PUSH1[0x1] + Op.PUSH1[0x3]
        + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.MULMOD + Op.DIV
        + Op.PUSH7[0x11000400090001] + Op.SSTORE + Op.PUSH1[0x3] + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.EXP + Op.DIV + Op.PUSH7[0x110004000a0000] + Op.SSTORE
        + Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.EXP + Op.DIV
        + Op.PUSH7[0x110004000a0001] + Op.SSTORE + Op.PUSH1[0x3] + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.LT + Op.DIV + Op.PUSH7[0x11000400100000] + Op.SSTORE
        + Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.LT + Op.DIV
        + Op.PUSH7[0x11000400100001] + Op.SSTORE + Op.PUSH1[0x3] + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.GT + Op.DIV + Op.PUSH7[0x11000400110000] + Op.SSTORE
        + Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.GT + Op.DIV
        + Op.PUSH7[0x11000400110001] + Op.SSTORE + Op.PUSH1[0x3] + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.SLT + Op.DIV + Op.PUSH7[0x11000400120000] + Op.SSTORE
        + Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.SLT + Op.DIV
        + Op.PUSH7[0x11000400120001] + Op.SSTORE + Op.PUSH1[0x3] + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.SGT + Op.DIV + Op.PUSH7[0x11000400130000] + Op.SSTORE
        + Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.SGT + Op.DIV
        + Op.PUSH7[0x11000400130001] + Op.SSTORE + Op.PUSH1[0x3] + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.EQ + Op.DIV + Op.PUSH7[0x11000400140000] + Op.SSTORE
        + Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.EQ + Op.DIV
        + Op.PUSH7[0x11000400140001] + Op.SSTORE + Op.PUSH1[0x3] + Op.PUSH1[0x2]
        + Op.ISZERO + Op.DIV + Op.PUSH7[0x11000400150000] + Op.SSTORE + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.ISZERO + Op.DIV + Op.PUSH7[0x11000400150001] + Op.SSTORE
        + Op.PUSH1[0x3] + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.AND + Op.DIV
        + Op.PUSH7[0x11000400160000] + Op.SSTORE + Op.PUSH1[0x1] + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.AND + Op.DIV + Op.PUSH7[0x11000400160001] + Op.SSTORE
        + Op.PUSH1[0x3] + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.OR + Op.DIV
        + Op.PUSH7[0x11000400170000] + Op.SSTORE + Op.PUSH1[0x1] + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.OR + Op.DIV + Op.PUSH7[0x11000400170001] + Op.SSTORE
        + Op.PUSH1[0x3] + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.XOR + Op.DIV
        + Op.PUSH7[0x11000400180000] + Op.SSTORE + Op.PUSH1[0x1] + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.XOR + Op.DIV + Op.PUSH7[0x11000400180001] + Op.SSTORE
        + Op.PUSH1[0x3] + Op.PUSH1[0x2] + Op.NOT + Op.DIV + Op.PUSH7[0x11000400190000]
        + Op.SSTORE + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.NOT + Op.DIV
        + Op.PUSH7[0x11000400190001] + Op.SSTORE + Op.PUSH1[0x3] + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.BYTE + Op.DIV + Op.PUSH7[0x110004001a0000] + Op.SSTORE
        + Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.BYTE + Op.DIV
        + Op.PUSH7[0x110004001a0001] + Op.SSTORE + Op.PUSH1[0x3] + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.SHL + Op.DIV + Op.PUSH7[0x110004001b0000] + Op.SSTORE
        + Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.SHL + Op.DIV
        + Op.PUSH7[0x110004001b0001] + Op.SSTORE + Op.PUSH1[0x3] + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.SHR + Op.DIV + Op.PUSH7[0x110004001c0000] + Op.SSTORE
        + Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.SHR + Op.DIV
        + Op.PUSH7[0x110004001c0001] + Op.SSTORE + Op.PUSH1[0x3] + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.SAR + Op.DIV + Op.PUSH7[0x110004001d0000] + Op.SSTORE
        + Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.SAR + Op.DIV
        + Op.PUSH7[0x110004001d0001] + Op.SSTORE + Op.PUSH1[0x3] + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.ADD + Op.SDIV + Op.PUSH7[0x11000500010000] + Op.SSTORE
        + Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.ADD + Op.SDIV
        + Op.PUSH7[0x11000500010001] + Op.SSTORE + Op.PUSH1[0x3] + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.MUL + Op.SDIV + Op.PUSH7[0x11000500020000] + Op.SSTORE
        + Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.MUL + Op.SDIV
        + Op.PUSH7[0x11000500020001] + Op.SSTORE + Op.PUSH1[0x3] + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.SUB + Op.SDIV + Op.PUSH7[0x11000500030000] + Op.SSTORE
        + Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.SUB + Op.SDIV
        + Op.PUSH7[0x11000500030001] + Op.SSTORE + Op.PUSH1[0x3] + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.DIV + Op.SDIV + Op.PUSH7[0x11000500040000] + Op.SSTORE
        + Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.DIV + Op.SDIV
        + Op.PUSH7[0x11000500040001] + Op.SSTORE + Op.PUSH1[0x3] + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.SDIV + Op.SDIV + Op.PUSH7[0x11000500050000] + Op.SSTORE
        + Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.SDIV + Op.SDIV
        + Op.PUSH7[0x11000500050001] + Op.SSTORE + Op.PUSH1[0x3] + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.MOD + Op.SDIV + Op.PUSH7[0x11000500060000] + Op.SSTORE
        + Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.MOD + Op.SDIV
        + Op.PUSH7[0x11000500060001] + Op.SSTORE + Op.PUSH1[0x3] + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.SMOD + Op.SDIV + Op.PUSH7[0x11000500070000] + Op.SSTORE
        + Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.SMOD + Op.SDIV
        + Op.PUSH7[0x11000500070001] + Op.SSTORE + Op.PUSH1[0x3] + Op.PUSH1[0x3]
        + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.ADDMOD + Op.SDIV
        + Op.PUSH7[0x11000500080000] + Op.SSTORE + Op.PUSH1[0x1] + Op.PUSH1[0x3]
        + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.ADDMOD + Op.SDIV
        + Op.PUSH7[0x11000500080001] + Op.SSTORE + Op.PUSH1[0x3] + Op.PUSH1[0x3]
        + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.MULMOD + Op.SDIV
        + Op.PUSH7[0x11000500090000] + Op.SSTORE + Op.PUSH1[0x1] + Op.PUSH1[0x3]
        + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.MULMOD + Op.SDIV
        + Op.PUSH7[0x11000500090001] + Op.SSTORE + Op.PUSH1[0x3] + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.EXP + Op.SDIV + Op.PUSH7[0x110005000a0000] + Op.SSTORE
        + Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.EXP + Op.SDIV
        + Op.PUSH7[0x110005000a0001] + Op.SSTORE + Op.PUSH1[0x3] + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.LT + Op.SDIV + Op.PUSH7[0x11000500100000] + Op.SSTORE
        + Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.LT + Op.SDIV
        + Op.PUSH7[0x11000500100001] + Op.SSTORE + Op.PUSH1[0x3] + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.GT + Op.SDIV + Op.PUSH7[0x11000500110000] + Op.SSTORE
        + Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.GT + Op.SDIV
        + Op.PUSH7[0x11000500110001] + Op.SSTORE + Op.PUSH1[0x3] + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.SLT + Op.SDIV + Op.PUSH7[0x11000500120000] + Op.SSTORE
        + Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.SLT + Op.SDIV
        + Op.PUSH7[0x11000500120001] + Op.SSTORE + Op.PUSH1[0x3] + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.SGT + Op.SDIV + Op.PUSH7[0x11000500130000] + Op.SSTORE
        + Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.SGT + Op.SDIV
        + Op.PUSH7[0x11000500130001] + Op.SSTORE + Op.PUSH1[0x3] + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.EQ + Op.SDIV + Op.PUSH7[0x11000500140000] + Op.SSTORE
        + Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.EQ + Op.SDIV
        + Op.PUSH7[0x11000500140001] + Op.SSTORE + Op.PUSH1[0x3] + Op.PUSH1[0x2]
        + Op.ISZERO + Op.SDIV + Op.PUSH7[0x11000500150000] + Op.SSTORE + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.ISZERO + Op.SDIV + Op.PUSH7[0x11000500150001] + Op.SSTORE
        + Op.PUSH1[0x3] + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.AND + Op.SDIV
        + Op.PUSH7[0x11000500160000] + Op.SSTORE + Op.PUSH1[0x1] + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.AND + Op.SDIV + Op.PUSH7[0x11000500160001] + Op.SSTORE
        + Op.PUSH1[0x3] + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.OR + Op.SDIV
        + Op.PUSH7[0x11000500170000] + Op.SSTORE + Op.PUSH1[0x1] + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.OR + Op.SDIV + Op.PUSH7[0x11000500170001] + Op.SSTORE
        + Op.PUSH1[0x3] + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.XOR + Op.SDIV
        + Op.PUSH7[0x11000500180000] + Op.SSTORE + Op.PUSH1[0x1] + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.XOR + Op.SDIV + Op.PUSH7[0x11000500180001] + Op.SSTORE
        + Op.PUSH1[0x3] + Op.PUSH1[0x2] + Op.NOT + Op.SDIV
        + Op.PUSH7[0x11000500190000] + Op.SSTORE + Op.PUSH1[0x1] + Op.PUSH1[0x2]
        + Op.NOT + Op.SDIV + Op.PUSH7[0x11000500190001] + Op.SSTORE + Op.PUSH1[0x3]
        + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.BYTE + Op.SDIV
        + Op.PUSH7[0x110005001a0000] + Op.SSTORE + Op.PUSH1[0x1] + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.BYTE + Op.SDIV + Op.PUSH7[0x110005001a0001] + Op.SSTORE
        + Op.PUSH1[0x3] + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.SHL + Op.SDIV
        + Op.PUSH7[0x110005001b0000] + Op.SSTORE + Op.PUSH1[0x1] + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.SHL + Op.SDIV + Op.PUSH7[0x110005001b0001] + Op.SSTORE
        + Op.PUSH1[0x3] + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.SHR + Op.SDIV
        + Op.PUSH7[0x110005001c0000] + Op.SSTORE + Op.PUSH1[0x1] + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.SHR + Op.SDIV + Op.PUSH7[0x110005001c0001] + Op.SSTORE
        + Op.PUSH1[0x3] + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.SAR + Op.SDIV
        + Op.PUSH7[0x110005001d0000] + Op.SSTORE + Op.PUSH1[0x1] + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.SAR + Op.SDIV + Op.PUSH7[0x110005001d0001] + Op.SSTORE
        + Op.PUSH1[0x3] + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.ADD + Op.MOD
        + Op.PUSH7[0x11000600010000] + Op.SSTORE + Op.PUSH1[0x1] + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.ADD + Op.MOD + Op.PUSH7[0x11000600010001] + Op.SSTORE
        + Op.PUSH1[0x3] + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.MUL + Op.MOD
        + Op.PUSH7[0x11000600020000] + Op.SSTORE + Op.PUSH1[0x1] + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.MUL + Op.MOD + Op.PUSH7[0x11000600020001] + Op.SSTORE
        + Op.PUSH1[0x3] + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.SUB + Op.MOD
        + Op.PUSH7[0x11000600030000] + Op.SSTORE + Op.PUSH1[0x1] + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.SUB + Op.MOD + Op.PUSH7[0x11000600030001] + Op.SSTORE
        + Op.PUSH1[0x3] + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.DIV + Op.MOD
        + Op.PUSH7[0x11000600040000] + Op.SSTORE + Op.PUSH1[0x1] + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.DIV + Op.MOD + Op.PUSH7[0x11000600040001] + Op.SSTORE
        + Op.PUSH1[0x3] + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.SDIV + Op.MOD
        + Op.PUSH7[0x11000600050000] + Op.SSTORE + Op.PUSH1[0x1] + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.SDIV + Op.MOD + Op.PUSH7[0x11000600050001] + Op.SSTORE
        + Op.PUSH1[0x3] + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.MOD + Op.MOD
        + Op.PUSH7[0x11000600060000] + Op.SSTORE + Op.PUSH1[0x1] + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.MOD + Op.MOD + Op.PUSH7[0x11000600060001] + Op.SSTORE
        + Op.PUSH1[0x3] + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.SMOD + Op.MOD
        + Op.PUSH7[0x11000600070000] + Op.SSTORE + Op.PUSH1[0x1] + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.SMOD + Op.MOD + Op.PUSH7[0x11000600070001] + Op.SSTORE
        + Op.PUSH1[0x3] + Op.PUSH1[0x3] + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.ADDMOD
        + Op.MOD + Op.PUSH7[0x11000600080000] + Op.SSTORE + Op.PUSH1[0x1]
        + Op.PUSH1[0x3] + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.ADDMOD + Op.MOD
        + Op.PUSH7[0x11000600080001] + Op.SSTORE + Op.PUSH1[0x3] + Op.PUSH1[0x3]
        + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.MULMOD + Op.MOD
        + Op.PUSH7[0x11000600090000] + Op.SSTORE + Op.PUSH1[0x1] + Op.PUSH1[0x3]
        + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.MULMOD + Op.MOD
        + Op.PUSH7[0x11000600090001] + Op.SSTORE + Op.PUSH1[0x3] + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.EXP + Op.MOD + Op.PUSH7[0x110006000a0000] + Op.SSTORE
        + Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.EXP + Op.MOD
        + Op.PUSH7[0x110006000a0001] + Op.SSTORE + Op.PUSH1[0x3] + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.LT + Op.MOD + Op.PUSH7[0x11000600100000] + Op.SSTORE
        + Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.LT + Op.MOD
        + Op.PUSH7[0x11000600100001] + Op.SSTORE + Op.PUSH1[0x3] + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.GT + Op.MOD + Op.PUSH7[0x11000600110000] + Op.SSTORE
        + Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.GT + Op.MOD
        + Op.PUSH7[0x11000600110001] + Op.SSTORE + Op.PUSH1[0x3] + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.SLT + Op.MOD + Op.PUSH7[0x11000600120000] + Op.SSTORE
        + Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.SLT + Op.MOD
        + Op.PUSH7[0x11000600120001] + Op.SSTORE + Op.PUSH1[0x3] + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.SGT + Op.MOD + Op.PUSH7[0x11000600130000] + Op.SSTORE
        + Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.SGT + Op.MOD
        + Op.PUSH7[0x11000600130001] + Op.SSTORE + Op.PUSH1[0x3] + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.EQ + Op.MOD + Op.PUSH7[0x11000600140000] + Op.SSTORE
        + Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.EQ + Op.MOD
        + Op.PUSH7[0x11000600140001] + Op.SSTORE + Op.PUSH1[0x3] + Op.PUSH1[0x2]
        + Op.ISZERO + Op.MOD + Op.PUSH7[0x11000600150000] + Op.SSTORE + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.ISZERO + Op.MOD + Op.PUSH7[0x11000600150001] + Op.SSTORE
        + Op.PUSH1[0x3] + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.AND + Op.MOD
        + Op.PUSH7[0x11000600160000] + Op.SSTORE + Op.PUSH1[0x1] + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.AND + Op.MOD + Op.PUSH7[0x11000600160001] + Op.SSTORE
        + Op.PUSH1[0x3] + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.OR + Op.MOD
        + Op.PUSH7[0x11000600170000] + Op.SSTORE + Op.PUSH1[0x1] + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.OR + Op.MOD + Op.PUSH7[0x11000600170001] + Op.SSTORE
        + Op.PUSH1[0x3] + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.XOR + Op.MOD
        + Op.PUSH7[0x11000600180000] + Op.SSTORE + Op.PUSH1[0x1] + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.XOR + Op.MOD + Op.PUSH7[0x11000600180001] + Op.SSTORE
        + Op.PUSH1[0x3] + Op.PUSH1[0x2] + Op.NOT + Op.MOD + Op.PUSH7[0x11000600190000]
        + Op.SSTORE + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.NOT + Op.MOD
        + Op.PUSH7[0x11000600190001] + Op.SSTORE + Op.PUSH1[0x3] + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.BYTE + Op.MOD + Op.PUSH7[0x110006001a0000] + Op.SSTORE
        + Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.BYTE + Op.MOD
        + Op.PUSH7[0x110006001a0001] + Op.SSTORE + Op.PUSH1[0x3] + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.SHL + Op.MOD + Op.PUSH7[0x110006001b0000] + Op.SSTORE
        + Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.SHL + Op.MOD
        + Op.PUSH7[0x110006001b0001] + Op.SSTORE + Op.PUSH1[0x3] + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.SHR + Op.MOD + Op.PUSH7[0x110006001c0000] + Op.SSTORE
        + Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.SHR + Op.MOD
        + Op.PUSH7[0x110006001c0001] + Op.SSTORE + Op.PUSH1[0x3] + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.SAR + Op.MOD + Op.PUSH7[0x110006001d0000] + Op.SSTORE
        + Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.SAR + Op.MOD
        + Op.PUSH7[0x110006001d0001] + Op.SSTORE + Op.PUSH1[0x3] + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.ADD + Op.SMOD + Op.PUSH7[0x11000700010000] + Op.SSTORE
        + Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.ADD + Op.SMOD
        + Op.PUSH7[0x11000700010001] + Op.SSTORE + Op.PUSH1[0x3] + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.MUL + Op.SMOD + Op.PUSH7[0x11000700020000] + Op.SSTORE
        + Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.MUL + Op.SMOD
        + Op.PUSH7[0x11000700020001] + Op.SSTORE + Op.PUSH1[0x3] + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.SUB + Op.SMOD + Op.PUSH7[0x11000700030000] + Op.SSTORE
        + Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.SUB + Op.SMOD
        + Op.PUSH7[0x11000700030001] + Op.SSTORE + Op.PUSH1[0x3] + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.DIV + Op.SMOD + Op.PUSH7[0x11000700040000] + Op.SSTORE
        + Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.DIV + Op.SMOD
        + Op.PUSH7[0x11000700040001] + Op.SSTORE + Op.PUSH1[0x3] + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.SDIV + Op.SMOD + Op.PUSH7[0x11000700050000] + Op.SSTORE
        + Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.SDIV + Op.SMOD
        + Op.PUSH7[0x11000700050001] + Op.SSTORE + Op.PUSH1[0x3] + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.MOD + Op.SMOD + Op.PUSH7[0x11000700060000] + Op.SSTORE
        + Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.MOD + Op.SMOD
        + Op.PUSH7[0x11000700060001] + Op.SSTORE + Op.PUSH1[0x3] + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.SMOD + Op.SMOD + Op.PUSH7[0x11000700070000] + Op.SSTORE
        + Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.SMOD + Op.SMOD
        + Op.PUSH7[0x11000700070001] + Op.SSTORE + Op.PUSH1[0x3] + Op.PUSH1[0x3]
        + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.ADDMOD + Op.SMOD
        + Op.PUSH7[0x11000700080000] + Op.SSTORE + Op.PUSH1[0x1] + Op.PUSH1[0x3]
        + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.ADDMOD + Op.SMOD
        + Op.PUSH7[0x11000700080001] + Op.SSTORE + Op.PUSH1[0x3] + Op.PUSH1[0x3]
        + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.MULMOD + Op.SMOD
        + Op.PUSH7[0x11000700090000] + Op.SSTORE + Op.PUSH1[0x1] + Op.PUSH1[0x3]
        + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.MULMOD + Op.SMOD
        + Op.PUSH7[0x11000700090001] + Op.SSTORE + Op.PUSH1[0x3] + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.EXP + Op.SMOD + Op.PUSH7[0x110007000a0000] + Op.SSTORE
        + Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.EXP + Op.SMOD
        + Op.PUSH7[0x110007000a0001] + Op.SSTORE + Op.PUSH1[0x3] + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.LT + Op.SMOD + Op.PUSH7[0x11000700100000] + Op.SSTORE
        + Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.LT + Op.SMOD
        + Op.PUSH7[0x11000700100001] + Op.SSTORE + Op.PUSH1[0x3] + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.GT + Op.SMOD + Op.PUSH7[0x11000700110000] + Op.SSTORE
        + Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.GT + Op.SMOD
        + Op.PUSH7[0x11000700110001] + Op.SSTORE + Op.PUSH1[0x3] + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.SLT + Op.SMOD + Op.PUSH7[0x11000700120000] + Op.SSTORE
        + Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.SLT + Op.SMOD
        + Op.PUSH7[0x11000700120001] + Op.SSTORE + Op.PUSH1[0x3] + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.SGT + Op.SMOD + Op.PUSH7[0x11000700130000] + Op.SSTORE
        + Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.SGT + Op.SMOD
        + Op.PUSH7[0x11000700130001] + Op.SSTORE + Op.PUSH1[0x3] + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.EQ + Op.SMOD + Op.PUSH7[0x11000700140000] + Op.SSTORE
        + Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.EQ + Op.SMOD
        + Op.PUSH7[0x11000700140001] + Op.SSTORE + Op.PUSH1[0x3] + Op.PUSH1[0x2]
        + Op.ISZERO + Op.SMOD + Op.PUSH7[0x11000700150000] + Op.SSTORE + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.ISZERO + Op.SMOD + Op.PUSH7[0x11000700150001] + Op.SSTORE
        + Op.PUSH1[0x3] + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.AND + Op.SMOD
        + Op.PUSH7[0x11000700160000] + Op.SSTORE + Op.PUSH1[0x1] + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.AND + Op.SMOD + Op.PUSH7[0x11000700160001] + Op.SSTORE
        + Op.PUSH1[0x3] + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.OR + Op.SMOD
        + Op.PUSH7[0x11000700170000] + Op.SSTORE + Op.PUSH1[0x1] + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.OR + Op.SMOD + Op.PUSH7[0x11000700170001] + Op.SSTORE
        + Op.PUSH1[0x3] + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.XOR + Op.SMOD
        + Op.PUSH7[0x11000700180000] + Op.SSTORE + Op.PUSH1[0x1] + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.XOR + Op.SMOD + Op.PUSH7[0x11000700180001] + Op.SSTORE
        + Op.PUSH1[0x3] + Op.PUSH1[0x2] + Op.NOT + Op.SMOD
        + Op.PUSH7[0x11000700190000] + Op.SSTORE + Op.PUSH1[0x1] + Op.PUSH1[0x2]
        + Op.NOT + Op.SMOD + Op.PUSH7[0x11000700190001] + Op.SSTORE + Op.PUSH1[0x3]
        + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.BYTE + Op.SMOD
        + Op.PUSH7[0x110007001a0000] + Op.SSTORE + Op.PUSH1[0x1] + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.BYTE + Op.SMOD + Op.PUSH7[0x110007001a0001] + Op.SSTORE
        + Op.PUSH1[0x3] + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.SHL + Op.SMOD
        + Op.PUSH7[0x110007001b0000] + Op.SSTORE + Op.PUSH1[0x1] + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.SHL + Op.SMOD + Op.PUSH7[0x110007001b0001] + Op.SSTORE
        + Op.PUSH1[0x3] + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.SHR + Op.SMOD
        + Op.PUSH7[0x110007001c0000] + Op.SSTORE + Op.PUSH1[0x1] + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.SHR + Op.SMOD + Op.PUSH7[0x110007001c0001] + Op.SSTORE
        + Op.PUSH1[0x3] + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.SAR + Op.SMOD
        + Op.PUSH7[0x110007001d0000] + Op.SSTORE + Op.PUSH1[0x1] + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.SAR + Op.SMOD + Op.PUSH7[0x110007001d0001] + Op.SSTORE
        + Op.PUSH1[0x2] + Op.PUSH1[0x3] + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.ADD
        + Op.ADDMOD + Op.PUSH7[0x11000800010000] + Op.SSTORE + Op.PUSH1[0x2]
        + Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.ADD + Op.ADDMOD
        + Op.PUSH7[0x11000800010001] + Op.SSTORE + Op.PUSH1[0x2] + Op.PUSH1[0x3]
        + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.MUL + Op.ADDMOD
        + Op.PUSH7[0x11000800020000] + Op.SSTORE + Op.PUSH1[0x2] + Op.PUSH1[0x1]
        + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.MUL + Op.ADDMOD
        + Op.PUSH7[0x11000800020001] + Op.SSTORE + Op.PUSH1[0x2] + Op.PUSH1[0x3]
        + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.SUB + Op.ADDMOD
        + Op.PUSH7[0x11000800030000] + Op.SSTORE + Op.PUSH1[0x2] + Op.PUSH1[0x1]
        + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.SUB + Op.ADDMOD
        + Op.PUSH7[0x11000800030001] + Op.SSTORE + Op.PUSH1[0x2] + Op.PUSH1[0x3]
        + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.DIV + Op.ADDMOD
        + Op.PUSH7[0x11000800040000] + Op.SSTORE + Op.PUSH1[0x2] + Op.PUSH1[0x1]
        + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.DIV + Op.ADDMOD
        + Op.PUSH7[0x11000800040001] + Op.SSTORE + Op.PUSH1[0x2] + Op.PUSH1[0x3]
        + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.SDIV + Op.ADDMOD
        + Op.PUSH7[0x11000800050000] + Op.SSTORE + Op.PUSH1[0x2] + Op.PUSH1[0x1]
        + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.SDIV + Op.ADDMOD
        + Op.PUSH7[0x11000800050001] + Op.SSTORE + Op.PUSH1[0x2] + Op.PUSH1[0x3]
        + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.MOD + Op.ADDMOD
        + Op.PUSH7[0x11000800060000] + Op.SSTORE + Op.PUSH1[0x2] + Op.PUSH1[0x1]
        + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.MOD + Op.ADDMOD
        + Op.PUSH7[0x11000800060001] + Op.SSTORE + Op.PUSH1[0x2] + Op.PUSH1[0x3]
        + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.SMOD + Op.ADDMOD
        + Op.PUSH7[0x11000800070000] + Op.SSTORE + Op.PUSH1[0x2] + Op.PUSH1[0x1]
        + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.SMOD + Op.ADDMOD
        + Op.PUSH7[0x11000800070001] + Op.SSTORE + Op.PUSH1[0x2] + Op.PUSH1[0x3]
        + Op.PUSH1[0x3] + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.ADDMOD + Op.ADDMOD
        + Op.PUSH7[0x11000800080000] + Op.SSTORE + Op.PUSH1[0x2] + Op.PUSH1[0x1]
        + Op.PUSH1[0x3] + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.ADDMOD + Op.ADDMOD
        + Op.PUSH7[0x11000800080001] + Op.SSTORE + Op.PUSH1[0x2] + Op.PUSH1[0x3]
        + Op.PUSH1[0x3] + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.MULMOD + Op.ADDMOD
        + Op.PUSH7[0x11000800090000] + Op.SSTORE + Op.PUSH1[0x2] + Op.PUSH1[0x1]
        + Op.PUSH1[0x3] + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.MULMOD + Op.ADDMOD
        + Op.PUSH7[0x11000800090001] + Op.SSTORE + Op.PUSH1[0x2] + Op.PUSH1[0x3]
        + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.EXP + Op.ADDMOD
        + Op.PUSH7[0x110008000a0000] + Op.SSTORE + Op.PUSH1[0x2] + Op.PUSH1[0x1]
        + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.EXP + Op.ADDMOD
        + Op.PUSH7[0x110008000a0001] + Op.SSTORE + Op.PUSH1[0x2] + Op.PUSH1[0x3]
        + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.LT + Op.ADDMOD
        + Op.PUSH7[0x11000800100000] + Op.SSTORE + Op.PUSH1[0x2] + Op.PUSH1[0x1]
        + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.LT + Op.ADDMOD
        + Op.PUSH7[0x11000800100001] + Op.SSTORE + Op.PUSH1[0x2] + Op.PUSH1[0x3]
        + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.GT + Op.ADDMOD
        + Op.PUSH7[0x11000800110000] + Op.SSTORE + Op.PUSH1[0x2] + Op.PUSH1[0x1]
        + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.GT + Op.ADDMOD
        + Op.PUSH7[0x11000800110001] + Op.SSTORE + Op.PUSH1[0x2] + Op.PUSH1[0x3]
        + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.SLT + Op.ADDMOD
        + Op.PUSH7[0x11000800120000] + Op.SSTORE + Op.PUSH1[0x2] + Op.PUSH1[0x1]
        + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.SLT + Op.ADDMOD
        + Op.PUSH7[0x11000800120001] + Op.SSTORE + Op.PUSH1[0x2] + Op.PUSH1[0x3]
        + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.SGT + Op.ADDMOD
        + Op.PUSH7[0x11000800130000] + Op.SSTORE + Op.PUSH1[0x2] + Op.PUSH1[0x1]
        + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.SGT + Op.ADDMOD
        + Op.PUSH7[0x11000800130001] + Op.SSTORE + Op.PUSH1[0x2] + Op.PUSH1[0x3]
        + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.EQ + Op.ADDMOD
        + Op.PUSH7[0x11000800140000] + Op.SSTORE + Op.PUSH1[0x2] + Op.PUSH1[0x1]
        + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.EQ + Op.ADDMOD
        + Op.PUSH7[0x11000800140001] + Op.SSTORE + Op.PUSH1[0x2] + Op.PUSH1[0x3]
        + Op.PUSH1[0x2] + Op.ISZERO + Op.ADDMOD + Op.PUSH7[0x11000800150000]
        + Op.SSTORE + Op.PUSH1[0x2] + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.ISZERO
        + Op.ADDMOD + Op.PUSH7[0x11000800150001] + Op.SSTORE + Op.PUSH1[0x2]
        + Op.PUSH1[0x3] + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.AND + Op.ADDMOD
        + Op.PUSH7[0x11000800160000] + Op.SSTORE + Op.PUSH1[0x2] + Op.PUSH1[0x1]
        + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.AND + Op.ADDMOD
        + Op.PUSH7[0x11000800160001] + Op.SSTORE + Op.PUSH1[0x2] + Op.PUSH1[0x3]
        + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.OR + Op.ADDMOD
        + Op.PUSH7[0x11000800170000] + Op.SSTORE + Op.PUSH1[0x2] + Op.PUSH1[0x1]
        + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.OR + Op.ADDMOD
        + Op.PUSH7[0x11000800170001] + Op.SSTORE + Op.PUSH1[0x2] + Op.PUSH1[0x3]
        + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.XOR + Op.ADDMOD
        + Op.PUSH7[0x11000800180000] + Op.SSTORE + Op.PUSH1[0x2] + Op.PUSH1[0x1]
        + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.XOR + Op.ADDMOD
        + Op.PUSH7[0x11000800180001] + Op.SSTORE + Op.PUSH1[0x2] + Op.PUSH1[0x3]
        + Op.PUSH1[0x2] + Op.NOT + Op.ADDMOD + Op.PUSH7[0x11000800190000] + Op.SSTORE
        + Op.PUSH1[0x2] + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.NOT + Op.ADDMOD
        + Op.PUSH7[0x11000800190001] + Op.SSTORE + Op.PUSH1[0x2] + Op.PUSH1[0x3]
        + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.BYTE + Op.ADDMOD
        + Op.PUSH7[0x110008001a0000] + Op.SSTORE + Op.PUSH1[0x2] + Op.PUSH1[0x1]
        + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.BYTE + Op.ADDMOD
        + Op.PUSH7[0x110008001a0001] + Op.SSTORE + Op.PUSH1[0x2] + Op.PUSH1[0x3]
        + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.SHL + Op.ADDMOD
        + Op.PUSH7[0x110008001b0000] + Op.SSTORE + Op.PUSH1[0x2] + Op.PUSH1[0x1]
        + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.SHL + Op.ADDMOD
        + Op.PUSH7[0x110008001b0001] + Op.SSTORE + Op.PUSH1[0x2] + Op.PUSH1[0x3]
        + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.SHR + Op.ADDMOD
        + Op.PUSH7[0x110008001c0000] + Op.SSTORE + Op.PUSH1[0x2] + Op.PUSH1[0x1]
        + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.SHR + Op.ADDMOD
        + Op.PUSH7[0x110008001c0001] + Op.SSTORE + Op.PUSH1[0x2] + Op.PUSH1[0x3]
        + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.SAR + Op.ADDMOD
        + Op.PUSH7[0x110008001d0000] + Op.SSTORE + Op.PUSH1[0x2] + Op.PUSH1[0x1]
        + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.SAR + Op.ADDMOD
        + Op.PUSH7[0x110008001d0001] + Op.SSTORE + Op.PUSH1[0x2] + Op.PUSH1[0x3]
        + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.ADD + Op.MULMOD
        + Op.PUSH7[0x11000900010000] + Op.SSTORE + Op.PUSH1[0x2] + Op.PUSH1[0x1]
        + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.ADD + Op.MULMOD
        + Op.PUSH7[0x11000900010001] + Op.SSTORE + Op.PUSH1[0x2] + Op.PUSH1[0x3]
        + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.MUL + Op.MULMOD
        + Op.PUSH7[0x11000900020000] + Op.SSTORE + Op.PUSH1[0x2] + Op.PUSH1[0x1]
        + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.MUL + Op.MULMOD
        + Op.PUSH7[0x11000900020001] + Op.SSTORE + Op.PUSH1[0x2] + Op.PUSH1[0x3]
        + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.SUB + Op.MULMOD
        + Op.PUSH7[0x11000900030000] + Op.SSTORE + Op.PUSH1[0x2] + Op.PUSH1[0x1]
        + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.SUB + Op.MULMOD
        + Op.PUSH7[0x11000900030001] + Op.SSTORE + Op.PUSH1[0x2] + Op.PUSH1[0x3]
        + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.DIV + Op.MULMOD
        + Op.PUSH7[0x11000900040000] + Op.SSTORE + Op.PUSH1[0x2] + Op.PUSH1[0x1]
        + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.DIV + Op.MULMOD
        + Op.PUSH7[0x11000900040001] + Op.SSTORE + Op.PUSH1[0x2] + Op.PUSH1[0x3]
        + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.SDIV + Op.MULMOD
        + Op.PUSH7[0x11000900050000] + Op.SSTORE + Op.PUSH1[0x2] + Op.PUSH1[0x1]
        + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.SDIV + Op.MULMOD
        + Op.PUSH7[0x11000900050001] + Op.SSTORE + Op.PUSH1[0x2] + Op.PUSH1[0x3]
        + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.MOD + Op.MULMOD
        + Op.PUSH7[0x11000900060000] + Op.SSTORE + Op.PUSH1[0x2] + Op.PUSH1[0x1]
        + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.MOD + Op.MULMOD
        + Op.PUSH7[0x11000900060001] + Op.SSTORE + Op.PUSH1[0x2] + Op.PUSH1[0x3]
        + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.SMOD + Op.MULMOD
        + Op.PUSH7[0x11000900070000] + Op.SSTORE + Op.PUSH1[0x2] + Op.PUSH1[0x1]
        + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.SMOD + Op.MULMOD
        + Op.PUSH7[0x11000900070001] + Op.SSTORE + Op.PUSH1[0x2] + Op.PUSH1[0x3]
        + Op.PUSH1[0x3] + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.ADDMOD + Op.MULMOD
        + Op.PUSH7[0x11000900080000] + Op.SSTORE + Op.PUSH1[0x2] + Op.PUSH1[0x1]
        + Op.PUSH1[0x3] + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.ADDMOD + Op.MULMOD
        + Op.PUSH7[0x11000900080001] + Op.SSTORE + Op.PUSH1[0x2] + Op.PUSH1[0x3]
        + Op.PUSH1[0x3] + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.MULMOD + Op.MULMOD
        + Op.PUSH7[0x11000900090000] + Op.SSTORE + Op.PUSH1[0x2] + Op.PUSH1[0x1]
        + Op.PUSH1[0x3] + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.MULMOD + Op.MULMOD
        + Op.PUSH7[0x11000900090001] + Op.SSTORE + Op.PUSH1[0x2] + Op.PUSH1[0x3]
        + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.EXP + Op.MULMOD
        + Op.PUSH7[0x110009000a0000] + Op.SSTORE + Op.PUSH1[0x2] + Op.PUSH1[0x1]
        + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.EXP + Op.MULMOD
        + Op.PUSH7[0x110009000a0001] + Op.SSTORE + Op.PUSH1[0x2] + Op.PUSH1[0x3]
        + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.LT + Op.MULMOD
        + Op.PUSH7[0x11000900100000] + Op.SSTORE + Op.PUSH1[0x2] + Op.PUSH1[0x1]
        + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.LT + Op.MULMOD
        + Op.PUSH7[0x11000900100001] + Op.SSTORE + Op.PUSH1[0x2] + Op.PUSH1[0x3]
        + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.GT + Op.MULMOD
        + Op.PUSH7[0x11000900110000] + Op.SSTORE + Op.PUSH1[0x2] + Op.PUSH1[0x1]
        + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.GT + Op.MULMOD
        + Op.PUSH7[0x11000900110001] + Op.SSTORE + Op.PUSH1[0x2] + Op.PUSH1[0x3]
        + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.SLT + Op.MULMOD
        + Op.PUSH7[0x11000900120000] + Op.SSTORE + Op.PUSH1[0x2] + Op.PUSH1[0x1]
        + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.SLT + Op.MULMOD
        + Op.PUSH7[0x11000900120001] + Op.SSTORE + Op.PUSH1[0x2] + Op.PUSH1[0x3]
        + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.SGT + Op.MULMOD
        + Op.PUSH7[0x11000900130000] + Op.SSTORE + Op.PUSH1[0x2] + Op.PUSH1[0x1]
        + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.SGT + Op.MULMOD
        + Op.PUSH7[0x11000900130001] + Op.SSTORE + Op.PUSH1[0x2] + Op.PUSH1[0x3]
        + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.EQ + Op.MULMOD
        + Op.PUSH7[0x11000900140000] + Op.SSTORE + Op.PUSH1[0x2] + Op.PUSH1[0x1]
        + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.EQ + Op.MULMOD
        + Op.PUSH7[0x11000900140001] + Op.SSTORE + Op.PUSH1[0x2] + Op.PUSH1[0x3]
        + Op.PUSH1[0x2] + Op.ISZERO + Op.MULMOD + Op.PUSH7[0x11000900150000]
        + Op.SSTORE + Op.PUSH1[0x2] + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.ISZERO
        + Op.MULMOD + Op.PUSH7[0x11000900150001] + Op.SSTORE + Op.PUSH1[0x2]
        + Op.PUSH1[0x3] + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.AND + Op.MULMOD
        + Op.PUSH7[0x11000900160000] + Op.SSTORE + Op.PUSH1[0x2] + Op.PUSH1[0x1]
        + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.AND + Op.MULMOD
        + Op.PUSH7[0x11000900160001] + Op.SSTORE + Op.PUSH1[0x2] + Op.PUSH1[0x3]
        + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.OR + Op.MULMOD
        + Op.PUSH7[0x11000900170000] + Op.SSTORE + Op.PUSH1[0x2] + Op.PUSH1[0x1]
        + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.OR + Op.MULMOD
        + Op.PUSH7[0x11000900170001] + Op.SSTORE + Op.PUSH1[0x2] + Op.PUSH1[0x3]
        + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.XOR + Op.MULMOD
        + Op.PUSH7[0x11000900180000] + Op.SSTORE + Op.PUSH1[0x2] + Op.PUSH1[0x1]
        + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.XOR + Op.MULMOD
        + Op.PUSH7[0x11000900180001] + Op.SSTORE + Op.PUSH1[0x2] + Op.PUSH1[0x3]
        + Op.PUSH1[0x2] + Op.NOT + Op.MULMOD + Op.PUSH7[0x11000900190000] + Op.SSTORE
        + Op.PUSH1[0x2] + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.NOT + Op.MULMOD
        + Op.PUSH7[0x11000900190001] + Op.SSTORE + Op.PUSH1[0x2] + Op.PUSH1[0x3]
        + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.BYTE + Op.MULMOD
        + Op.PUSH7[0x110009001a0000] + Op.SSTORE + Op.PUSH1[0x2] + Op.PUSH1[0x1]
        + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.BYTE + Op.MULMOD
        + Op.PUSH7[0x110009001a0001] + Op.SSTORE + Op.PUSH1[0x2] + Op.PUSH1[0x3]
        + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.SHL + Op.MULMOD
        + Op.PUSH7[0x110009001b0000] + Op.SSTORE + Op.PUSH1[0x2] + Op.PUSH1[0x1]
        + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.SHL + Op.MULMOD
        + Op.PUSH7[0x110009001b0001] + Op.SSTORE + Op.PUSH1[0x2] + Op.PUSH1[0x3]
        + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.SHR + Op.MULMOD
        + Op.PUSH7[0x110009001c0000] + Op.SSTORE + Op.PUSH1[0x2] + Op.PUSH1[0x1]
        + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.SHR + Op.MULMOD
        + Op.PUSH7[0x110009001c0001] + Op.SSTORE + Op.PUSH1[0x2] + Op.PUSH1[0x3]
        + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.SAR + Op.MULMOD
        + Op.PUSH7[0x110009001d0000] + Op.SSTORE + Op.PUSH1[0x2] + Op.PUSH1[0x1]
        + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.SAR + Op.MULMOD
        + Op.PUSH7[0x110009001d0001] + Op.SSTORE + Op.PUSH1[0x3] + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.ADD + Op.EXP + Op.PUSH7[0x11000a00010000] + Op.SSTORE
        + Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.ADD + Op.EXP
        + Op.PUSH7[0x11000a00010001] + Op.SSTORE + Op.PUSH1[0x3] + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.MUL + Op.EXP + Op.PUSH7[0x11000a00020000] + Op.SSTORE
        + Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.MUL + Op.EXP
        + Op.PUSH7[0x11000a00020001] + Op.SSTORE + Op.PUSH1[0x3] + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.SUB + Op.EXP + Op.PUSH7[0x11000a00030000] + Op.SSTORE
        + Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.SUB + Op.EXP
        + Op.PUSH7[0x11000a00030001] + Op.SSTORE + Op.PUSH1[0x3] + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.DIV + Op.EXP + Op.PUSH7[0x11000a00040000] + Op.SSTORE
        + Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.DIV + Op.EXP
        + Op.PUSH7[0x11000a00040001] + Op.SSTORE + Op.PUSH1[0x3] + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.SDIV + Op.EXP + Op.PUSH7[0x11000a00050000] + Op.SSTORE
        + Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.SDIV + Op.EXP
        + Op.PUSH7[0x11000a00050001] + Op.SSTORE + Op.PUSH1[0x3] + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.MOD + Op.EXP + Op.PUSH7[0x11000a00060000] + Op.SSTORE
        + Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.MOD + Op.EXP
        + Op.PUSH7[0x11000a00060001] + Op.SSTORE + Op.PUSH1[0x3] + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.SMOD + Op.EXP + Op.PUSH7[0x11000a00070000] + Op.SSTORE
        + Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.SMOD + Op.EXP
        + Op.PUSH7[0x11000a00070001] + Op.SSTORE + Op.PUSH1[0x3] + Op.PUSH1[0x3]
        + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.ADDMOD + Op.EXP
        + Op.PUSH7[0x11000a00080000] + Op.SSTORE + Op.PUSH1[0x1] + Op.PUSH1[0x3]
        + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.ADDMOD + Op.EXP
        + Op.PUSH7[0x11000a00080001] + Op.SSTORE + Op.PUSH1[0x3] + Op.PUSH1[0x3]
        + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.MULMOD + Op.EXP
        + Op.PUSH7[0x11000a00090000] + Op.SSTORE + Op.PUSH1[0x1] + Op.PUSH1[0x3]
        + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.MULMOD + Op.EXP
        + Op.PUSH7[0x11000a00090001] + Op.SSTORE + Op.PUSH1[0x3] + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.EXP + Op.EXP + Op.PUSH7[0x11000a000a0000] + Op.SSTORE
        + Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.EXP + Op.EXP
        + Op.PUSH7[0x11000a000a0001] + Op.SSTORE + Op.PUSH1[0x3] + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.LT + Op.EXP + Op.PUSH7[0x11000a00100000] + Op.SSTORE
        + Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.LT + Op.EXP
        + Op.PUSH7[0x11000a00100001] + Op.SSTORE + Op.PUSH1[0x3] + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.GT + Op.EXP + Op.PUSH7[0x11000a00110000] + Op.SSTORE
        + Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.GT + Op.EXP
        + Op.PUSH7[0x11000a00110001] + Op.SSTORE + Op.PUSH1[0x3] + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.SLT + Op.EXP + Op.PUSH7[0x11000a00120000] + Op.SSTORE
        + Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.SLT + Op.EXP
        + Op.PUSH7[0x11000a00120001] + Op.SSTORE + Op.PUSH1[0x3] + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.SGT + Op.EXP + Op.PUSH7[0x11000a00130000] + Op.SSTORE
        + Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.SGT + Op.EXP
        + Op.PUSH7[0x11000a00130001] + Op.SSTORE + Op.PUSH1[0x3] + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.EQ + Op.EXP + Op.PUSH7[0x11000a00140000] + Op.SSTORE
        + Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.EQ + Op.EXP
        + Op.PUSH7[0x11000a00140001] + Op.SSTORE + Op.PUSH1[0x3] + Op.PUSH1[0x2]
        + Op.ISZERO + Op.EXP + Op.PUSH7[0x11000a00150000] + Op.SSTORE + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.ISZERO + Op.EXP + Op.PUSH7[0x11000a00150001] + Op.SSTORE
        + Op.PUSH1[0x3] + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.AND + Op.EXP
        + Op.PUSH7[0x11000a00160000] + Op.SSTORE + Op.PUSH1[0x1] + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.AND + Op.EXP + Op.PUSH7[0x11000a00160001] + Op.SSTORE
        + Op.PUSH1[0x3] + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.OR + Op.EXP
        + Op.PUSH7[0x11000a00170000] + Op.SSTORE + Op.PUSH1[0x1] + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.OR + Op.EXP + Op.PUSH7[0x11000a00170001] + Op.SSTORE
        + Op.PUSH1[0x3] + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.XOR + Op.EXP
        + Op.PUSH7[0x11000a00180000] + Op.SSTORE + Op.PUSH1[0x1] + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.XOR + Op.EXP + Op.PUSH7[0x11000a00180001] + Op.SSTORE
        + Op.PUSH1[0x3] + Op.PUSH1[0x2] + Op.NOT + Op.EXP + Op.PUSH7[0x11000a00190000]
        + Op.SSTORE + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.NOT + Op.EXP
        + Op.PUSH7[0x11000a00190001] + Op.SSTORE + Op.PUSH1[0x3] + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.BYTE + Op.EXP + Op.PUSH7[0x11000a001a0000] + Op.SSTORE
        + Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.BYTE + Op.EXP
        + Op.PUSH7[0x11000a001a0001] + Op.SSTORE + Op.PUSH1[0x3] + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.SHL + Op.EXP + Op.PUSH7[0x11000a001b0000] + Op.SSTORE
        + Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.SHL + Op.EXP
        + Op.PUSH7[0x11000a001b0001] + Op.SSTORE + Op.PUSH1[0x3] + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.SHR + Op.EXP + Op.PUSH7[0x11000a001c0000] + Op.SSTORE
        + Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.SHR + Op.EXP
        + Op.PUSH7[0x11000a001c0001] + Op.SSTORE + Op.PUSH1[0x3] + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.SAR + Op.EXP + Op.PUSH7[0x11000a001d0000] + Op.SSTORE
        + Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.SAR + Op.EXP
        + Op.PUSH7[0x11000a001d0001] + Op.SSTORE + Op.PUSH1[0x3] + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.ADD + Op.LT + Op.PUSH7[0x11001000010000] + Op.SSTORE
        + Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.ADD + Op.LT
        + Op.PUSH7[0x11001000010001] + Op.SSTORE + Op.PUSH1[0x3] + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.MUL + Op.LT + Op.PUSH7[0x11001000020000] + Op.SSTORE
        + Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.MUL + Op.LT
        + Op.PUSH7[0x11001000020001] + Op.SSTORE + Op.PUSH1[0x3] + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.SUB + Op.LT + Op.PUSH7[0x11001000030000] + Op.SSTORE
        + Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.SUB + Op.LT
        + Op.PUSH7[0x11001000030001] + Op.SSTORE + Op.PUSH1[0x3] + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.DIV + Op.LT + Op.PUSH7[0x11001000040000] + Op.SSTORE
        + Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.DIV + Op.LT
        + Op.PUSH7[0x11001000040001] + Op.SSTORE + Op.PUSH1[0x3] + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.SDIV + Op.LT + Op.PUSH7[0x11001000050000] + Op.SSTORE
        + Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.SDIV + Op.LT
        + Op.PUSH7[0x11001000050001] + Op.SSTORE + Op.PUSH1[0x3] + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.MOD + Op.LT + Op.PUSH7[0x11001000060000] + Op.SSTORE
        + Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.MOD + Op.LT
        + Op.PUSH7[0x11001000060001] + Op.SSTORE + Op.PUSH1[0x3] + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.SMOD + Op.LT + Op.PUSH7[0x11001000070000] + Op.SSTORE
        + Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.SMOD + Op.LT
        + Op.PUSH7[0x11001000070001] + Op.SSTORE + Op.PUSH1[0x3] + Op.PUSH1[0x3]
        + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.ADDMOD + Op.LT
        + Op.PUSH7[0x11001000080000] + Op.SSTORE + Op.PUSH1[0x1] + Op.PUSH1[0x3]
        + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.ADDMOD + Op.LT
        + Op.PUSH7[0x11001000080001] + Op.SSTORE + Op.PUSH1[0x3] + Op.PUSH1[0x3]
        + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.MULMOD + Op.LT
        + Op.PUSH7[0x11001000090000] + Op.SSTORE + Op.PUSH1[0x1] + Op.PUSH1[0x3]
        + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.MULMOD + Op.LT
        + Op.PUSH7[0x11001000090001] + Op.SSTORE + Op.PUSH1[0x3] + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.EXP + Op.LT + Op.PUSH7[0x110010000a0000] + Op.SSTORE
        + Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.EXP + Op.LT
        + Op.PUSH7[0x110010000a0001] + Op.SSTORE + Op.PUSH1[0x3] + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.LT + Op.LT + Op.PUSH7[0x11001000100000] + Op.SSTORE
        + Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.LT + Op.LT
        + Op.PUSH7[0x11001000100001] + Op.SSTORE + Op.PUSH1[0x3] + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.GT + Op.LT + Op.PUSH7[0x11001000110000] + Op.SSTORE
        + Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.GT + Op.LT
        + Op.PUSH7[0x11001000110001] + Op.SSTORE + Op.PUSH1[0x3] + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.SLT + Op.LT + Op.PUSH7[0x11001000120000] + Op.SSTORE
        + Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.SLT + Op.LT
        + Op.PUSH7[0x11001000120001] + Op.SSTORE + Op.PUSH1[0x3] + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.SGT + Op.LT + Op.PUSH7[0x11001000130000] + Op.SSTORE
        + Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.SGT + Op.LT
        + Op.PUSH7[0x11001000130001] + Op.SSTORE + Op.PUSH1[0x3] + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.EQ + Op.LT + Op.PUSH7[0x11001000140000] + Op.SSTORE
        + Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.EQ + Op.LT
        + Op.PUSH7[0x11001000140001] + Op.SSTORE + Op.PUSH1[0x3] + Op.PUSH1[0x2]
        + Op.ISZERO + Op.LT + Op.PUSH7[0x11001000150000] + Op.SSTORE + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.ISZERO + Op.LT + Op.PUSH7[0x11001000150001] + Op.SSTORE
        + Op.PUSH1[0x3] + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.AND + Op.LT
        + Op.PUSH7[0x11001000160000] + Op.SSTORE + Op.PUSH1[0x1] + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.AND + Op.LT + Op.PUSH7[0x11001000160001] + Op.SSTORE
        + Op.PUSH1[0x3] + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.OR + Op.LT
        + Op.PUSH7[0x11001000170000] + Op.SSTORE + Op.PUSH1[0x1] + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.OR + Op.LT + Op.PUSH7[0x11001000170001] + Op.SSTORE
        + Op.PUSH1[0x3] + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.XOR + Op.LT
        + Op.PUSH7[0x11001000180000] + Op.SSTORE + Op.PUSH1[0x1] + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.XOR + Op.LT + Op.PUSH7[0x11001000180001] + Op.SSTORE
        + Op.PUSH1[0x3] + Op.PUSH1[0x2] + Op.NOT + Op.LT + Op.PUSH7[0x11001000190000]
        + Op.SSTORE + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.NOT + Op.LT
        + Op.PUSH7[0x11001000190001] + Op.SSTORE + Op.PUSH1[0x3] + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.BYTE + Op.LT + Op.PUSH7[0x110010001a0000] + Op.SSTORE
        + Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.BYTE + Op.LT
        + Op.PUSH7[0x110010001a0001] + Op.SSTORE + Op.PUSH1[0x3] + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.SHL + Op.LT + Op.PUSH7[0x110010001b0000] + Op.SSTORE
        + Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.SHL + Op.LT
        + Op.PUSH7[0x110010001b0001] + Op.SSTORE + Op.PUSH1[0x3] + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.SHR + Op.LT + Op.PUSH7[0x110010001c0000] + Op.SSTORE
        + Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.SHR + Op.LT
        + Op.PUSH7[0x110010001c0001] + Op.SSTORE + Op.PUSH1[0x3] + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.SAR + Op.LT + Op.PUSH7[0x110010001d0000] + Op.SSTORE
        + Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.SAR + Op.LT
        + Op.PUSH7[0x110010001d0001] + Op.SSTORE + Op.PUSH1[0x3] + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.ADD + Op.GT + Op.PUSH7[0x11001100010000] + Op.SSTORE
        + Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.ADD + Op.GT
        + Op.PUSH7[0x11001100010001] + Op.SSTORE + Op.PUSH1[0x3] + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.MUL + Op.GT + Op.PUSH7[0x11001100020000] + Op.SSTORE
        + Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.MUL + Op.GT
        + Op.PUSH7[0x11001100020001] + Op.SSTORE + Op.PUSH1[0x3] + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.SUB + Op.GT + Op.PUSH7[0x11001100030000] + Op.SSTORE
        + Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.SUB + Op.GT
        + Op.PUSH7[0x11001100030001] + Op.SSTORE + Op.PUSH1[0x3] + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.DIV + Op.GT + Op.PUSH7[0x11001100040000] + Op.SSTORE
        + Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.DIV + Op.GT
        + Op.PUSH7[0x11001100040001] + Op.SSTORE + Op.PUSH1[0x3] + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.SDIV + Op.GT + Op.PUSH7[0x11001100050000] + Op.SSTORE
        + Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.SDIV + Op.GT
        + Op.PUSH7[0x11001100050001] + Op.SSTORE + Op.PUSH1[0x3] + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.MOD + Op.GT + Op.PUSH7[0x11001100060000] + Op.SSTORE
        + Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.MOD + Op.GT
        + Op.PUSH7[0x11001100060001] + Op.SSTORE + Op.PUSH1[0x3] + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.SMOD + Op.GT + Op.PUSH7[0x11001100070000] + Op.SSTORE
        + Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.SMOD + Op.GT
        + Op.PUSH7[0x11001100070001] + Op.SSTORE + Op.PUSH1[0x3] + Op.PUSH1[0x3]
        + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.ADDMOD + Op.GT
        + Op.PUSH7[0x11001100080000] + Op.SSTORE + Op.PUSH1[0x1] + Op.PUSH1[0x3]
        + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.ADDMOD + Op.GT
        + Op.PUSH7[0x11001100080001] + Op.SSTORE + Op.PUSH1[0x3] + Op.PUSH1[0x3]
        + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.MULMOD + Op.GT
        + Op.PUSH7[0x11001100090000] + Op.SSTORE + Op.PUSH1[0x1] + Op.PUSH1[0x3]
        + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.MULMOD + Op.GT
        + Op.PUSH7[0x11001100090001] + Op.SSTORE + Op.PUSH1[0x3] + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.EXP + Op.GT + Op.PUSH7[0x110011000a0000] + Op.SSTORE
        + Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.EXP + Op.GT
        + Op.PUSH7[0x110011000a0001] + Op.SSTORE + Op.PUSH1[0x3] + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.LT + Op.GT + Op.PUSH7[0x11001100100000] + Op.SSTORE
        + Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.LT + Op.GT
        + Op.PUSH7[0x11001100100001] + Op.SSTORE + Op.PUSH1[0x3] + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.GT + Op.GT + Op.PUSH7[0x11001100110000] + Op.SSTORE
        + Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.GT + Op.GT
        + Op.PUSH7[0x11001100110001] + Op.SSTORE + Op.PUSH1[0x3] + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.SLT + Op.GT + Op.PUSH7[0x11001100120000] + Op.SSTORE
        + Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.SLT + Op.GT
        + Op.PUSH7[0x11001100120001] + Op.SSTORE + Op.PUSH1[0x3] + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.SGT + Op.GT + Op.PUSH7[0x11001100130000] + Op.SSTORE
        + Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.SGT + Op.GT
        + Op.PUSH7[0x11001100130001] + Op.SSTORE + Op.PUSH1[0x3] + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.EQ + Op.GT + Op.PUSH7[0x11001100140000] + Op.SSTORE
        + Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.EQ + Op.GT
        + Op.PUSH7[0x11001100140001] + Op.SSTORE + Op.PUSH1[0x3] + Op.PUSH1[0x2]
        + Op.ISZERO + Op.GT + Op.PUSH7[0x11001100150000] + Op.SSTORE + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.ISZERO + Op.GT + Op.PUSH7[0x11001100150001] + Op.SSTORE
        + Op.PUSH1[0x3] + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.AND + Op.GT
        + Op.PUSH7[0x11001100160000] + Op.SSTORE + Op.PUSH1[0x1] + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.AND + Op.GT + Op.PUSH7[0x11001100160001] + Op.SSTORE
        + Op.PUSH1[0x3] + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.OR + Op.GT
        + Op.PUSH7[0x11001100170000] + Op.SSTORE + Op.PUSH1[0x1] + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.OR + Op.GT + Op.PUSH7[0x11001100170001] + Op.SSTORE
        + Op.PUSH1[0x3] + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.XOR + Op.GT
        + Op.PUSH7[0x11001100180000] + Op.SSTORE + Op.PUSH1[0x1] + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.XOR + Op.GT + Op.PUSH7[0x11001100180001] + Op.SSTORE
        + Op.PUSH1[0x3] + Op.PUSH1[0x2] + Op.NOT + Op.GT + Op.PUSH7[0x11001100190000]
        + Op.SSTORE + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.NOT + Op.GT
        + Op.PUSH7[0x11001100190001] + Op.SSTORE + Op.PUSH1[0x3] + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.BYTE + Op.GT + Op.PUSH7[0x110011001a0000] + Op.SSTORE
        + Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.BYTE + Op.GT
        + Op.PUSH7[0x110011001a0001] + Op.SSTORE + Op.PUSH1[0x3] + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.SHL + Op.GT + Op.PUSH7[0x110011001b0000] + Op.SSTORE
        + Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.SHL + Op.GT
        + Op.PUSH7[0x110011001b0001] + Op.SSTORE + Op.PUSH1[0x3] + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.SHR + Op.GT + Op.PUSH7[0x110011001c0000] + Op.SSTORE
        + Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.SHR + Op.GT
        + Op.PUSH7[0x110011001c0001] + Op.SSTORE + Op.PUSH1[0x3] + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.SAR + Op.GT + Op.PUSH7[0x110011001d0000] + Op.SSTORE
        + Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.SAR + Op.GT
        + Op.PUSH7[0x110011001d0001] + Op.SSTORE + Op.PUSH1[0x3] + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.ADD + Op.SLT + Op.PUSH7[0x11001200010000] + Op.SSTORE
        + Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.ADD + Op.SLT
        + Op.PUSH7[0x11001200010001] + Op.SSTORE + Op.PUSH1[0x3] + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.MUL + Op.SLT + Op.PUSH7[0x11001200020000] + Op.SSTORE
        + Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.MUL + Op.SLT
        + Op.PUSH7[0x11001200020001] + Op.SSTORE + Op.PUSH1[0x3] + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.SUB + Op.SLT + Op.PUSH7[0x11001200030000] + Op.SSTORE
        + Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.SUB + Op.SLT
        + Op.PUSH7[0x11001200030001] + Op.SSTORE + Op.PUSH1[0x3] + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.DIV + Op.SLT + Op.PUSH7[0x11001200040000] + Op.SSTORE
        + Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.DIV + Op.SLT
        + Op.PUSH7[0x11001200040001] + Op.SSTORE + Op.PUSH1[0x3] + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.SDIV + Op.SLT + Op.PUSH7[0x11001200050000] + Op.SSTORE
        + Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.SDIV + Op.SLT
        + Op.PUSH7[0x11001200050001] + Op.SSTORE + Op.PUSH1[0x3] + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.MOD + Op.SLT + Op.PUSH7[0x11001200060000] + Op.SSTORE
        + Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.MOD + Op.SLT
        + Op.PUSH7[0x11001200060001] + Op.SSTORE + Op.PUSH1[0x3] + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.SMOD + Op.SLT + Op.PUSH7[0x11001200070000] + Op.SSTORE
        + Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.SMOD + Op.SLT
        + Op.PUSH7[0x11001200070001] + Op.SSTORE + Op.PUSH1[0x3] + Op.PUSH1[0x3]
        + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.ADDMOD + Op.SLT
        + Op.PUSH7[0x11001200080000] + Op.SSTORE + Op.PUSH1[0x1] + Op.PUSH1[0x3]
        + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.ADDMOD + Op.SLT
        + Op.PUSH7[0x11001200080001] + Op.SSTORE + Op.PUSH1[0x3] + Op.PUSH1[0x3]
        + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.MULMOD + Op.SLT
        + Op.PUSH7[0x11001200090000] + Op.SSTORE + Op.PUSH1[0x1] + Op.PUSH1[0x3]
        + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.MULMOD + Op.SLT
        + Op.PUSH7[0x11001200090001] + Op.SSTORE + Op.PUSH1[0x3] + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.EXP + Op.SLT + Op.PUSH7[0x110012000a0000] + Op.SSTORE
        + Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.EXP + Op.SLT
        + Op.PUSH7[0x110012000a0001] + Op.SSTORE + Op.PUSH1[0x3] + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.LT + Op.SLT + Op.PUSH7[0x11001200100000] + Op.SSTORE
        + Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.LT + Op.SLT
        + Op.PUSH7[0x11001200100001] + Op.SSTORE + Op.PUSH1[0x3] + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.GT + Op.SLT + Op.PUSH7[0x11001200110000] + Op.SSTORE
        + Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.GT + Op.SLT
        + Op.PUSH7[0x11001200110001] + Op.SSTORE + Op.PUSH1[0x3] + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.SLT + Op.SLT + Op.PUSH7[0x11001200120000] + Op.SSTORE
        + Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.SLT + Op.SLT
        + Op.PUSH7[0x11001200120001] + Op.SSTORE + Op.PUSH1[0x3] + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.SGT + Op.SLT + Op.PUSH7[0x11001200130000] + Op.SSTORE
        + Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.SGT + Op.SLT
        + Op.PUSH7[0x11001200130001] + Op.SSTORE + Op.PUSH1[0x3] + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.EQ + Op.SLT + Op.PUSH7[0x11001200140000] + Op.SSTORE
        + Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.EQ + Op.SLT
        + Op.PUSH7[0x11001200140001] + Op.SSTORE + Op.PUSH1[0x3] + Op.PUSH1[0x2]
        + Op.ISZERO + Op.SLT + Op.PUSH7[0x11001200150000] + Op.SSTORE + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.ISZERO + Op.SLT + Op.PUSH7[0x11001200150001] + Op.SSTORE
        + Op.PUSH1[0x3] + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.AND + Op.SLT
        + Op.PUSH7[0x11001200160000] + Op.SSTORE + Op.PUSH1[0x1] + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.AND + Op.SLT + Op.PUSH7[0x11001200160001] + Op.SSTORE
        + Op.PUSH1[0x3] + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.OR + Op.SLT
        + Op.PUSH7[0x11001200170000] + Op.SSTORE + Op.PUSH1[0x1] + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.OR + Op.SLT + Op.PUSH7[0x11001200170001] + Op.SSTORE
        + Op.PUSH1[0x3] + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.XOR + Op.SLT
        + Op.PUSH7[0x11001200180000] + Op.SSTORE + Op.PUSH1[0x1] + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.XOR + Op.SLT + Op.PUSH7[0x11001200180001] + Op.SSTORE
        + Op.PUSH1[0x3] + Op.PUSH1[0x2] + Op.NOT + Op.SLT + Op.PUSH7[0x11001200190000]
        + Op.SSTORE + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.NOT + Op.SLT
        + Op.PUSH7[0x11001200190001] + Op.SSTORE + Op.PUSH1[0x3] + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.BYTE + Op.SLT + Op.PUSH7[0x110012001a0000] + Op.SSTORE
        + Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.BYTE + Op.SLT
        + Op.PUSH7[0x110012001a0001] + Op.SSTORE + Op.PUSH1[0x3] + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.SHL + Op.SLT + Op.PUSH7[0x110012001b0000] + Op.SSTORE
        + Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.SHL + Op.SLT
        + Op.PUSH7[0x110012001b0001] + Op.SSTORE + Op.PUSH1[0x3] + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.SHR + Op.SLT + Op.PUSH7[0x110012001c0000] + Op.SSTORE
        + Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.SHR + Op.SLT
        + Op.PUSH7[0x110012001c0001] + Op.SSTORE + Op.PUSH1[0x3] + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.SAR + Op.SLT + Op.PUSH7[0x110012001d0000] + Op.SSTORE
        + Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.SAR + Op.SLT
        + Op.PUSH7[0x110012001d0001] + Op.SSTORE + Op.PUSH1[0x3] + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.ADD + Op.SGT + Op.PUSH7[0x11001300010000] + Op.SSTORE
        + Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.ADD + Op.SGT
        + Op.PUSH7[0x11001300010001] + Op.SSTORE + Op.PUSH1[0x3] + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.MUL + Op.SGT + Op.PUSH7[0x11001300020000] + Op.SSTORE
        + Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.MUL + Op.SGT
        + Op.PUSH7[0x11001300020001] + Op.SSTORE + Op.PUSH1[0x3] + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.SUB + Op.SGT + Op.PUSH7[0x11001300030000] + Op.SSTORE
        + Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.SUB + Op.SGT
        + Op.PUSH7[0x11001300030001] + Op.SSTORE + Op.PUSH1[0x3] + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.DIV + Op.SGT + Op.PUSH7[0x11001300040000] + Op.SSTORE
        + Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.DIV + Op.SGT
        + Op.PUSH7[0x11001300040001] + Op.SSTORE + Op.PUSH1[0x3] + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.SDIV + Op.SGT + Op.PUSH7[0x11001300050000] + Op.SSTORE
        + Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.SDIV + Op.SGT
        + Op.PUSH7[0x11001300050001] + Op.SSTORE + Op.PUSH1[0x3] + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.MOD + Op.SGT + Op.PUSH7[0x11001300060000] + Op.SSTORE
        + Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.MOD + Op.SGT
        + Op.PUSH7[0x11001300060001] + Op.SSTORE + Op.PUSH1[0x3] + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.SMOD + Op.SGT + Op.PUSH7[0x11001300070000] + Op.SSTORE
        + Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.SMOD + Op.SGT
        + Op.PUSH7[0x11001300070001] + Op.SSTORE + Op.PUSH1[0x3] + Op.PUSH1[0x3]
        + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.ADDMOD + Op.SGT
        + Op.PUSH7[0x11001300080000] + Op.SSTORE + Op.PUSH1[0x1] + Op.PUSH1[0x3]
        + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.ADDMOD + Op.SGT
        + Op.PUSH7[0x11001300080001] + Op.SSTORE + Op.PUSH1[0x3] + Op.PUSH1[0x3]
        + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.MULMOD + Op.SGT
        + Op.PUSH7[0x11001300090000] + Op.SSTORE + Op.PUSH1[0x1] + Op.PUSH1[0x3]
        + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.MULMOD + Op.SGT
        + Op.PUSH7[0x11001300090001] + Op.SSTORE + Op.PUSH1[0x3] + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.EXP + Op.SGT + Op.PUSH7[0x110013000a0000] + Op.SSTORE
        + Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.EXP + Op.SGT
        + Op.PUSH7[0x110013000a0001] + Op.SSTORE + Op.PUSH1[0x3] + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.LT + Op.SGT + Op.PUSH7[0x11001300100000] + Op.SSTORE
        + Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.LT + Op.SGT
        + Op.PUSH7[0x11001300100001] + Op.SSTORE + Op.PUSH1[0x3] + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.GT + Op.SGT + Op.PUSH7[0x11001300110000] + Op.SSTORE
        + Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.GT + Op.SGT
        + Op.PUSH7[0x11001300110001] + Op.SSTORE + Op.PUSH1[0x3] + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.SLT + Op.SGT + Op.PUSH7[0x11001300120000] + Op.SSTORE
        + Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.SLT + Op.SGT
        + Op.PUSH7[0x11001300120001] + Op.SSTORE + Op.PUSH1[0x3] + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.SGT + Op.SGT + Op.PUSH7[0x11001300130000] + Op.SSTORE
        + Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.SGT + Op.SGT
        + Op.PUSH7[0x11001300130001] + Op.SSTORE + Op.PUSH1[0x3] + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.EQ + Op.SGT + Op.PUSH7[0x11001300140000] + Op.SSTORE
        + Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.EQ + Op.SGT
        + Op.PUSH7[0x11001300140001] + Op.SSTORE + Op.PUSH1[0x3] + Op.PUSH1[0x2]
        + Op.ISZERO + Op.SGT + Op.PUSH7[0x11001300150000] + Op.SSTORE + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.ISZERO + Op.SGT + Op.PUSH7[0x11001300150001] + Op.SSTORE
        + Op.PUSH1[0x3] + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.AND + Op.SGT
        + Op.PUSH7[0x11001300160000] + Op.SSTORE + Op.PUSH1[0x1] + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.AND + Op.SGT + Op.PUSH7[0x11001300160001] + Op.SSTORE
        + Op.PUSH1[0x3] + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.OR + Op.SGT
        + Op.PUSH7[0x11001300170000] + Op.SSTORE + Op.PUSH1[0x1] + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.OR + Op.SGT + Op.PUSH7[0x11001300170001] + Op.SSTORE
        + Op.PUSH1[0x3] + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.XOR + Op.SGT
        + Op.PUSH7[0x11001300180000] + Op.SSTORE + Op.PUSH1[0x1] + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.XOR + Op.SGT + Op.PUSH7[0x11001300180001] + Op.SSTORE
        + Op.PUSH1[0x3] + Op.PUSH1[0x2] + Op.NOT + Op.SGT + Op.PUSH7[0x11001300190000]
        + Op.SSTORE + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.NOT + Op.SGT
        + Op.PUSH7[0x11001300190001] + Op.SSTORE + Op.PUSH1[0x3] + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.BYTE + Op.SGT + Op.PUSH7[0x110013001a0000] + Op.SSTORE
        + Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.BYTE + Op.SGT
        + Op.PUSH7[0x110013001a0001] + Op.SSTORE + Op.PUSH1[0x3] + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.SHL + Op.SGT + Op.PUSH7[0x110013001b0000] + Op.SSTORE
        + Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.SHL + Op.SGT
        + Op.PUSH7[0x110013001b0001] + Op.SSTORE + Op.PUSH1[0x3] + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.SHR + Op.SGT + Op.PUSH7[0x110013001c0000] + Op.SSTORE
        + Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.SHR + Op.SGT
        + Op.PUSH7[0x110013001c0001] + Op.SSTORE + Op.PUSH1[0x3] + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.SAR + Op.SGT + Op.PUSH7[0x110013001d0000] + Op.SSTORE
        + Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.SAR + Op.SGT
        + Op.PUSH7[0x110013001d0001] + Op.SSTORE + Op.PUSH1[0x3] + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.ADD + Op.EQ + Op.PUSH7[0x11001400010000] + Op.SSTORE
        + Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.ADD + Op.EQ
        + Op.PUSH7[0x11001400010001] + Op.SSTORE + Op.PUSH1[0x3] + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.MUL + Op.EQ + Op.PUSH7[0x11001400020000] + Op.SSTORE
        + Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.MUL + Op.EQ
        + Op.PUSH7[0x11001400020001] + Op.SSTORE + Op.PUSH1[0x3] + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.SUB + Op.EQ + Op.PUSH7[0x11001400030000] + Op.SSTORE
        + Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.SUB + Op.EQ
        + Op.PUSH7[0x11001400030001] + Op.SSTORE + Op.PUSH1[0x3] + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.DIV + Op.EQ + Op.PUSH7[0x11001400040000] + Op.SSTORE
        + Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.DIV + Op.EQ
        + Op.PUSH7[0x11001400040001] + Op.SSTORE + Op.PUSH1[0x3] + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.SDIV + Op.EQ + Op.PUSH7[0x11001400050000] + Op.SSTORE
        + Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.SDIV + Op.EQ
        + Op.PUSH7[0x11001400050001] + Op.SSTORE + Op.PUSH1[0x3] + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.MOD + Op.EQ + Op.PUSH7[0x11001400060000] + Op.SSTORE
        + Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.MOD + Op.EQ
        + Op.PUSH7[0x11001400060001] + Op.SSTORE + Op.PUSH1[0x3] + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.SMOD + Op.EQ + Op.PUSH7[0x11001400070000] + Op.SSTORE
        + Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.SMOD + Op.EQ
        + Op.PUSH7[0x11001400070001] + Op.SSTORE + Op.PUSH1[0x3] + Op.PUSH1[0x3]
        + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.ADDMOD + Op.EQ
        + Op.PUSH7[0x11001400080000] + Op.SSTORE + Op.PUSH1[0x1] + Op.PUSH1[0x3]
        + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.ADDMOD + Op.EQ
        + Op.PUSH7[0x11001400080001] + Op.SSTORE + Op.PUSH1[0x3] + Op.PUSH1[0x3]
        + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.MULMOD + Op.EQ
        + Op.PUSH7[0x11001400090000] + Op.SSTORE + Op.PUSH1[0x1] + Op.PUSH1[0x3]
        + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.MULMOD + Op.EQ
        + Op.PUSH7[0x11001400090001] + Op.SSTORE + Op.PUSH1[0x3] + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.EXP + Op.EQ + Op.PUSH7[0x110014000a0000] + Op.SSTORE
        + Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.EXP + Op.EQ
        + Op.PUSH7[0x110014000a0001] + Op.SSTORE + Op.PUSH1[0x3] + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.LT + Op.EQ + Op.PUSH7[0x11001400100000] + Op.SSTORE
        + Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.LT + Op.EQ
        + Op.PUSH7[0x11001400100001] + Op.SSTORE + Op.PUSH1[0x3] + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.GT + Op.EQ + Op.PUSH7[0x11001400110000] + Op.SSTORE
        + Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.GT + Op.EQ
        + Op.PUSH7[0x11001400110001] + Op.SSTORE + Op.PUSH1[0x3] + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.SLT + Op.EQ + Op.PUSH7[0x11001400120000] + Op.SSTORE
        + Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.SLT + Op.EQ
        + Op.PUSH7[0x11001400120001] + Op.SSTORE + Op.PUSH1[0x3] + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.SGT + Op.EQ + Op.PUSH7[0x11001400130000] + Op.SSTORE
        + Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.SGT + Op.EQ
        + Op.PUSH7[0x11001400130001] + Op.SSTORE + Op.PUSH1[0x3] + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.EQ + Op.EQ + Op.PUSH7[0x11001400140000] + Op.SSTORE
        + Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.EQ + Op.EQ
        + Op.PUSH7[0x11001400140001] + Op.SSTORE + Op.PUSH1[0x3] + Op.PUSH1[0x2]
        + Op.ISZERO + Op.EQ + Op.PUSH7[0x11001400150000] + Op.SSTORE + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.ISZERO + Op.EQ + Op.PUSH7[0x11001400150001] + Op.SSTORE
        + Op.PUSH1[0x3] + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.AND + Op.EQ
        + Op.PUSH7[0x11001400160000] + Op.SSTORE + Op.PUSH1[0x1] + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.AND + Op.EQ + Op.PUSH7[0x11001400160001] + Op.SSTORE
        + Op.PUSH1[0x3] + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.OR + Op.EQ
        + Op.PUSH7[0x11001400170000] + Op.SSTORE + Op.PUSH1[0x1] + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.OR + Op.EQ + Op.PUSH7[0x11001400170001] + Op.SSTORE
        + Op.PUSH1[0x3] + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.XOR + Op.EQ
        + Op.PUSH7[0x11001400180000] + Op.SSTORE + Op.PUSH1[0x1] + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.XOR + Op.EQ + Op.PUSH7[0x11001400180001] + Op.SSTORE
        + Op.PUSH1[0x3] + Op.PUSH1[0x2] + Op.NOT + Op.EQ + Op.PUSH7[0x11001400190000]
        + Op.SSTORE + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.NOT + Op.EQ
        + Op.PUSH7[0x11001400190001] + Op.SSTORE + Op.PUSH1[0x3] + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.BYTE + Op.EQ + Op.PUSH7[0x110014001a0000] + Op.SSTORE
        + Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.BYTE + Op.EQ
        + Op.PUSH7[0x110014001a0001] + Op.SSTORE + Op.PUSH1[0x3] + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.SHL + Op.EQ + Op.PUSH7[0x110014001b0000] + Op.SSTORE
        + Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.SHL + Op.EQ
        + Op.PUSH7[0x110014001b0001] + Op.SSTORE + Op.PUSH1[0x3] + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.SHR + Op.EQ + Op.PUSH7[0x110014001c0000] + Op.SSTORE
        + Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.SHR + Op.EQ
        + Op.PUSH7[0x110014001c0001] + Op.SSTORE + Op.PUSH1[0x3] + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.SAR + Op.EQ + Op.PUSH7[0x110014001d0000] + Op.SSTORE
        + Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.SAR + Op.EQ
        + Op.PUSH7[0x110014001d0001] + Op.SSTORE + Op.PUSH1[0x1] + Op.PUSH1[0x2]
        + Op.ADD + Op.ISZERO + Op.PUSH7[0x11001500010000] + Op.SSTORE + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.ADD + Op.ISZERO + Op.PUSH7[0x11001500010001] + Op.SSTORE
        + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.MUL + Op.ISZERO
        + Op.PUSH7[0x11001500020000] + Op.SSTORE + Op.PUSH1[0x1] + Op.PUSH1[0x2]
        + Op.MUL + Op.ISZERO + Op.PUSH7[0x11001500020001] + Op.SSTORE + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.SUB + Op.ISZERO + Op.PUSH7[0x11001500030000] + Op.SSTORE
        + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.SUB + Op.ISZERO
        + Op.PUSH7[0x11001500030001] + Op.SSTORE + Op.PUSH1[0x1] + Op.PUSH1[0x2]
        + Op.DIV + Op.ISZERO + Op.PUSH7[0x11001500040000] + Op.SSTORE + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.DIV + Op.ISZERO + Op.PUSH7[0x11001500040001] + Op.SSTORE
        + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.SDIV + Op.ISZERO
        + Op.PUSH7[0x11001500050000] + Op.SSTORE + Op.PUSH1[0x1] + Op.PUSH1[0x2]
        + Op.SDIV + Op.ISZERO + Op.PUSH7[0x11001500050001] + Op.SSTORE + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.MOD + Op.ISZERO + Op.PUSH7[0x11001500060000] + Op.SSTORE
        + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.MOD + Op.ISZERO
        + Op.PUSH7[0x11001500060001] + Op.SSTORE + Op.PUSH1[0x1] + Op.PUSH1[0x2]
        + Op.SMOD + Op.ISZERO + Op.PUSH7[0x11001500070000] + Op.SSTORE + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.SMOD + Op.ISZERO + Op.PUSH7[0x11001500070001] + Op.SSTORE
        + Op.PUSH1[0x3] + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.ADDMOD + Op.ISZERO
        + Op.PUSH7[0x11001500080000] + Op.SSTORE + Op.PUSH1[0x3] + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.ADDMOD + Op.ISZERO + Op.PUSH7[0x11001500080001]
        + Op.SSTORE + Op.PUSH1[0x3] + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.MULMOD
        + Op.ISZERO + Op.PUSH7[0x11001500090000] + Op.SSTORE + Op.PUSH1[0x3]
        + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.MULMOD + Op.ISZERO
        + Op.PUSH7[0x11001500090001] + Op.SSTORE + Op.PUSH1[0x1] + Op.PUSH1[0x2]
        + Op.EXP + Op.ISZERO + Op.PUSH7[0x110015000a0000] + Op.SSTORE + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.EXP + Op.ISZERO + Op.PUSH7[0x110015000a0001] + Op.SSTORE
        + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.LT + Op.ISZERO
        + Op.PUSH7[0x11001500100000] + Op.SSTORE + Op.PUSH1[0x1] + Op.PUSH1[0x2]
        + Op.LT + Op.ISZERO + Op.PUSH7[0x11001500100001] + Op.SSTORE + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.GT + Op.ISZERO + Op.PUSH7[0x11001500110000] + Op.SSTORE
        + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.GT + Op.ISZERO
        + Op.PUSH7[0x11001500110001] + Op.SSTORE + Op.PUSH1[0x1] + Op.PUSH1[0x2]
        + Op.SLT + Op.ISZERO + Op.PUSH7[0x11001500120000] + Op.SSTORE + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.SLT + Op.ISZERO + Op.PUSH7[0x11001500120001] + Op.SSTORE
        + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.SGT + Op.ISZERO
        + Op.PUSH7[0x11001500130000] + Op.SSTORE + Op.PUSH1[0x1] + Op.PUSH1[0x2]
        + Op.SGT + Op.ISZERO + Op.PUSH7[0x11001500130001] + Op.SSTORE + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.EQ + Op.ISZERO + Op.PUSH7[0x11001500140000] + Op.SSTORE
        + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.EQ + Op.ISZERO
        + Op.PUSH7[0x11001500140001] + Op.SSTORE + Op.PUSH1[0x2] + Op.ISZERO
        + Op.ISZERO + Op.PUSH7[0x11001500150000] + Op.SSTORE + Op.PUSH1[0x2]
        + Op.ISZERO + Op.ISZERO + Op.PUSH7[0x11001500150001] + Op.SSTORE
        + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.AND + Op.ISZERO
        + Op.PUSH7[0x11001500160000] + Op.SSTORE + Op.PUSH1[0x1] + Op.PUSH1[0x2]
        + Op.AND + Op.ISZERO + Op.PUSH7[0x11001500160001] + Op.SSTORE + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.OR + Op.ISZERO + Op.PUSH7[0x11001500170000] + Op.SSTORE
        + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.OR + Op.ISZERO
        + Op.PUSH7[0x11001500170001] + Op.SSTORE + Op.PUSH1[0x1] + Op.PUSH1[0x2]
        + Op.XOR + Op.ISZERO + Op.PUSH7[0x11001500180000] + Op.SSTORE + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.XOR + Op.ISZERO + Op.PUSH7[0x11001500180001] + Op.SSTORE
        + Op.PUSH1[0x2] + Op.NOT + Op.ISZERO + Op.PUSH7[0x11001500190000] + Op.SSTORE
        + Op.PUSH1[0x2] + Op.NOT + Op.ISZERO + Op.PUSH7[0x11001500190001] + Op.SSTORE
        + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.BYTE + Op.ISZERO
        + Op.PUSH7[0x110015001a0000] + Op.SSTORE + Op.PUSH1[0x1] + Op.PUSH1[0x2]
        + Op.BYTE + Op.ISZERO + Op.PUSH7[0x110015001a0001] + Op.SSTORE + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.SHL + Op.ISZERO + Op.PUSH7[0x110015001b0000] + Op.SSTORE
        + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.SHL + Op.ISZERO
        + Op.PUSH7[0x110015001b0001] + Op.SSTORE + Op.PUSH1[0x1] + Op.PUSH1[0x2]
        + Op.SHR + Op.ISZERO + Op.PUSH7[0x110015001c0000] + Op.SSTORE + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.SHR + Op.ISZERO + Op.PUSH7[0x110015001c0001] + Op.SSTORE
        + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.SAR + Op.ISZERO
        + Op.PUSH7[0x110015001d0000] + Op.SSTORE + Op.PUSH1[0x1] + Op.PUSH1[0x2]
        + Op.SAR + Op.ISZERO + Op.PUSH7[0x110015001d0001] + Op.SSTORE + Op.PUSH1[0x3]
        + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.ADD + Op.AND + Op.PUSH7[0x11001600010000]
        + Op.SSTORE + Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.ADD + Op.AND
        + Op.PUSH7[0x11001600010001] + Op.SSTORE + Op.PUSH1[0x3] + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.MUL + Op.AND + Op.PUSH7[0x11001600020000] + Op.SSTORE
        + Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.MUL + Op.AND
        + Op.PUSH7[0x11001600020001] + Op.SSTORE + Op.PUSH1[0x3] + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.SUB + Op.AND + Op.PUSH7[0x11001600030000] + Op.SSTORE
        + Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.SUB + Op.AND
        + Op.PUSH7[0x11001600030001] + Op.SSTORE + Op.PUSH1[0x3] + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.DIV + Op.AND + Op.PUSH7[0x11001600040000] + Op.SSTORE
        + Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.DIV + Op.AND
        + Op.PUSH7[0x11001600040001] + Op.SSTORE + Op.PUSH1[0x3] + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.SDIV + Op.AND + Op.PUSH7[0x11001600050000] + Op.SSTORE
        + Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.SDIV + Op.AND
        + Op.PUSH7[0x11001600050001] + Op.SSTORE + Op.PUSH1[0x3] + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.MOD + Op.AND + Op.PUSH7[0x11001600060000] + Op.SSTORE
        + Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.MOD + Op.AND
        + Op.PUSH7[0x11001600060001] + Op.SSTORE + Op.PUSH1[0x3] + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.SMOD + Op.AND + Op.PUSH7[0x11001600070000] + Op.SSTORE
        + Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.SMOD + Op.AND
        + Op.PUSH7[0x11001600070001] + Op.SSTORE + Op.PUSH1[0x3] + Op.PUSH1[0x3]
        + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.ADDMOD + Op.AND
        + Op.PUSH7[0x11001600080000] + Op.SSTORE + Op.PUSH1[0x1] + Op.PUSH1[0x3]
        + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.ADDMOD + Op.AND
        + Op.PUSH7[0x11001600080001] + Op.SSTORE + Op.PUSH1[0x3] + Op.PUSH1[0x3]
        + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.MULMOD + Op.AND
        + Op.PUSH7[0x11001600090000] + Op.SSTORE + Op.PUSH1[0x1] + Op.PUSH1[0x3]
        + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.MULMOD + Op.AND
        + Op.PUSH7[0x11001600090001] + Op.SSTORE + Op.PUSH1[0x3] + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.EXP + Op.AND + Op.PUSH7[0x110016000a0000] + Op.SSTORE
        + Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.EXP + Op.AND
        + Op.PUSH7[0x110016000a0001] + Op.SSTORE + Op.PUSH1[0x3] + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.LT + Op.AND + Op.PUSH7[0x11001600100000] + Op.SSTORE
        + Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.LT + Op.AND
        + Op.PUSH7[0x11001600100001] + Op.SSTORE + Op.PUSH1[0x3] + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.GT + Op.AND + Op.PUSH7[0x11001600110000] + Op.SSTORE
        + Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.GT + Op.AND
        + Op.PUSH7[0x11001600110001] + Op.SSTORE + Op.PUSH1[0x3] + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.SLT + Op.AND + Op.PUSH7[0x11001600120000] + Op.SSTORE
        + Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.SLT + Op.AND
        + Op.PUSH7[0x11001600120001] + Op.SSTORE + Op.PUSH1[0x3] + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.SGT + Op.AND + Op.PUSH7[0x11001600130000] + Op.SSTORE
        + Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.SGT + Op.AND
        + Op.PUSH7[0x11001600130001] + Op.SSTORE + Op.PUSH1[0x3] + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.EQ + Op.AND + Op.PUSH7[0x11001600140000] + Op.SSTORE
        + Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.EQ + Op.AND
        + Op.PUSH7[0x11001600140001] + Op.SSTORE + Op.PUSH1[0x3] + Op.PUSH1[0x2]
        + Op.ISZERO + Op.AND + Op.PUSH7[0x11001600150000] + Op.SSTORE + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.ISZERO + Op.AND + Op.PUSH7[0x11001600150001] + Op.SSTORE
        + Op.PUSH1[0x3] + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.AND + Op.AND
        + Op.PUSH7[0x11001600160000] + Op.SSTORE + Op.PUSH1[0x1] + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.AND + Op.AND + Op.PUSH7[0x11001600160001] + Op.SSTORE
        + Op.PUSH1[0x3] + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.OR + Op.AND
        + Op.PUSH7[0x11001600170000] + Op.SSTORE + Op.PUSH1[0x1] + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.OR + Op.AND + Op.PUSH7[0x11001600170001] + Op.SSTORE
        + Op.PUSH1[0x3] + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.XOR + Op.AND
        + Op.PUSH7[0x11001600180000] + Op.SSTORE + Op.PUSH1[0x1] + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.XOR + Op.AND + Op.PUSH7[0x11001600180001] + Op.SSTORE
        + Op.PUSH1[0x3] + Op.PUSH1[0x2] + Op.NOT + Op.AND + Op.PUSH7[0x11001600190000]
        + Op.SSTORE + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.NOT + Op.AND
        + Op.PUSH7[0x11001600190001] + Op.SSTORE + Op.PUSH1[0x3] + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.BYTE + Op.AND + Op.PUSH7[0x110016001a0000] + Op.SSTORE
        + Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.BYTE + Op.AND
        + Op.PUSH7[0x110016001a0001] + Op.SSTORE + Op.PUSH1[0x3] + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.SHL + Op.AND + Op.PUSH7[0x110016001b0000] + Op.SSTORE
        + Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.SHL + Op.AND
        + Op.PUSH7[0x110016001b0001] + Op.SSTORE + Op.PUSH1[0x3] + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.SHR + Op.AND + Op.PUSH7[0x110016001c0000] + Op.SSTORE
        + Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.SHR + Op.AND
        + Op.PUSH7[0x110016001c0001] + Op.SSTORE + Op.PUSH1[0x3] + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.SAR + Op.AND + Op.PUSH7[0x110016001d0000] + Op.SSTORE
        + Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.SAR + Op.AND
        + Op.PUSH7[0x110016001d0001] + Op.SSTORE + Op.PUSH1[0x3] + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.ADD + Op.OR + Op.PUSH7[0x11001700010000] + Op.SSTORE
        + Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.ADD + Op.OR
        + Op.PUSH7[0x11001700010001] + Op.SSTORE + Op.PUSH1[0x3] + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.MUL + Op.OR + Op.PUSH7[0x11001700020000] + Op.SSTORE
        + Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.MUL + Op.OR
        + Op.PUSH7[0x11001700020001] + Op.SSTORE + Op.PUSH1[0x3] + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.SUB + Op.OR + Op.PUSH7[0x11001700030000] + Op.SSTORE
        + Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.SUB + Op.OR
        + Op.PUSH7[0x11001700030001] + Op.SSTORE + Op.PUSH1[0x3] + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.DIV + Op.OR + Op.PUSH7[0x11001700040000] + Op.SSTORE
        + Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.DIV + Op.OR
        + Op.PUSH7[0x11001700040001] + Op.SSTORE + Op.PUSH1[0x3] + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.SDIV + Op.OR + Op.PUSH7[0x11001700050000] + Op.SSTORE
        + Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.SDIV + Op.OR
        + Op.PUSH7[0x11001700050001] + Op.SSTORE + Op.PUSH1[0x3] + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.MOD + Op.OR + Op.PUSH7[0x11001700060000] + Op.SSTORE
        + Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.MOD + Op.OR
        + Op.PUSH7[0x11001700060001] + Op.SSTORE + Op.PUSH1[0x3] + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.SMOD + Op.OR + Op.PUSH7[0x11001700070000] + Op.SSTORE
        + Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.SMOD + Op.OR
        + Op.PUSH7[0x11001700070001] + Op.SSTORE + Op.PUSH1[0x3] + Op.PUSH1[0x3]
        + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.ADDMOD + Op.OR
        + Op.PUSH7[0x11001700080000] + Op.SSTORE + Op.PUSH1[0x1] + Op.PUSH1[0x3]
        + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.ADDMOD + Op.OR
        + Op.PUSH7[0x11001700080001] + Op.SSTORE + Op.PUSH1[0x3] + Op.PUSH1[0x3]
        + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.MULMOD + Op.OR
        + Op.PUSH7[0x11001700090000] + Op.SSTORE + Op.PUSH1[0x1] + Op.PUSH1[0x3]
        + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.MULMOD + Op.OR
        + Op.PUSH7[0x11001700090001] + Op.SSTORE + Op.PUSH1[0x3] + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.EXP + Op.OR + Op.PUSH7[0x110017000a0000] + Op.SSTORE
        + Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.EXP + Op.OR
        + Op.PUSH7[0x110017000a0001] + Op.SSTORE + Op.PUSH1[0x3] + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.LT + Op.OR + Op.PUSH7[0x11001700100000] + Op.SSTORE
        + Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.LT + Op.OR
        + Op.PUSH7[0x11001700100001] + Op.SSTORE + Op.PUSH1[0x3] + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.GT + Op.OR + Op.PUSH7[0x11001700110000] + Op.SSTORE
        + Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.GT + Op.OR
        + Op.PUSH7[0x11001700110001] + Op.SSTORE + Op.PUSH1[0x3] + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.SLT + Op.OR + Op.PUSH7[0x11001700120000] + Op.SSTORE
        + Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.SLT + Op.OR
        + Op.PUSH7[0x11001700120001] + Op.SSTORE + Op.PUSH1[0x3] + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.SGT + Op.OR + Op.PUSH7[0x11001700130000] + Op.SSTORE
        + Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.SGT + Op.OR
        + Op.PUSH7[0x11001700130001] + Op.SSTORE + Op.PUSH1[0x3] + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.EQ + Op.OR + Op.PUSH7[0x11001700140000] + Op.SSTORE
        + Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.EQ + Op.OR
        + Op.PUSH7[0x11001700140001] + Op.SSTORE + Op.PUSH1[0x3] + Op.PUSH1[0x2]
        + Op.ISZERO + Op.OR + Op.PUSH7[0x11001700150000] + Op.SSTORE + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.ISZERO + Op.OR + Op.PUSH7[0x11001700150001] + Op.SSTORE
        + Op.PUSH1[0x3] + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.AND + Op.OR
        + Op.PUSH7[0x11001700160000] + Op.SSTORE + Op.PUSH1[0x1] + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.AND + Op.OR + Op.PUSH7[0x11001700160001] + Op.SSTORE
        + Op.PUSH1[0x3] + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.OR + Op.OR
        + Op.PUSH7[0x11001700170000] + Op.SSTORE + Op.PUSH1[0x1] + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.OR + Op.OR + Op.PUSH7[0x11001700170001] + Op.SSTORE
        + Op.PUSH1[0x3] + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.XOR + Op.OR
        + Op.PUSH7[0x11001700180000] + Op.SSTORE + Op.PUSH1[0x1] + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.XOR + Op.OR + Op.PUSH7[0x11001700180001] + Op.SSTORE
        + Op.PUSH1[0x3] + Op.PUSH1[0x2] + Op.NOT + Op.OR + Op.PUSH7[0x11001700190000]
        + Op.SSTORE + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.NOT + Op.OR
        + Op.PUSH7[0x11001700190001] + Op.SSTORE + Op.PUSH1[0x3] + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.BYTE + Op.OR + Op.PUSH7[0x110017001a0000] + Op.SSTORE
        + Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.BYTE + Op.OR
        + Op.PUSH7[0x110017001a0001] + Op.SSTORE + Op.PUSH1[0x3] + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.SHL + Op.OR + Op.PUSH7[0x110017001b0000] + Op.SSTORE
        + Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.SHL + Op.OR
        + Op.PUSH7[0x110017001b0001] + Op.SSTORE + Op.PUSH1[0x3] + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.SHR + Op.OR + Op.PUSH7[0x110017001c0000] + Op.SSTORE
        + Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.SHR + Op.OR
        + Op.PUSH7[0x110017001c0001] + Op.SSTORE + Op.PUSH1[0x3] + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.SAR + Op.OR + Op.PUSH7[0x110017001d0000] + Op.SSTORE
        + Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.SAR + Op.OR
        + Op.PUSH7[0x110017001d0001] + Op.SSTORE + Op.PUSH1[0x3] + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.ADD + Op.XOR + Op.PUSH7[0x11001800010000] + Op.SSTORE
        + Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.ADD + Op.XOR
        + Op.PUSH7[0x11001800010001] + Op.SSTORE + Op.PUSH1[0x3] + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.MUL + Op.XOR + Op.PUSH7[0x11001800020000] + Op.SSTORE
        + Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.MUL + Op.XOR
        + Op.PUSH7[0x11001800020001] + Op.SSTORE + Op.PUSH1[0x3] + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.SUB + Op.XOR + Op.PUSH7[0x11001800030000] + Op.SSTORE
        + Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.SUB + Op.XOR
        + Op.PUSH7[0x11001800030001] + Op.SSTORE + Op.PUSH1[0x3] + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.DIV + Op.XOR + Op.PUSH7[0x11001800040000] + Op.SSTORE
        + Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.DIV + Op.XOR
        + Op.PUSH7[0x11001800040001] + Op.SSTORE + Op.PUSH1[0x3] + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.SDIV + Op.XOR + Op.PUSH7[0x11001800050000] + Op.SSTORE
        + Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.SDIV + Op.XOR
        + Op.PUSH7[0x11001800050001] + Op.SSTORE + Op.PUSH1[0x3] + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.MOD + Op.XOR + Op.PUSH7[0x11001800060000] + Op.SSTORE
        + Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.MOD + Op.XOR
        + Op.PUSH7[0x11001800060001] + Op.SSTORE + Op.PUSH1[0x3] + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.SMOD + Op.XOR + Op.PUSH7[0x11001800070000] + Op.SSTORE
        + Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.SMOD + Op.XOR
        + Op.PUSH7[0x11001800070001] + Op.SSTORE + Op.PUSH1[0x3] + Op.PUSH1[0x3]
        + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.ADDMOD + Op.XOR
        + Op.PUSH7[0x11001800080000] + Op.SSTORE + Op.PUSH1[0x1] + Op.PUSH1[0x3]
        + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.ADDMOD + Op.XOR
        + Op.PUSH7[0x11001800080001] + Op.SSTORE + Op.PUSH1[0x3] + Op.PUSH1[0x3]
        + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.MULMOD + Op.XOR
        + Op.PUSH7[0x11001800090000] + Op.SSTORE + Op.PUSH1[0x1] + Op.PUSH1[0x3]
        + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.MULMOD + Op.XOR
        + Op.PUSH7[0x11001800090001] + Op.SSTORE + Op.PUSH1[0x3] + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.EXP + Op.XOR + Op.PUSH7[0x110018000a0000] + Op.SSTORE
        + Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.EXP + Op.XOR
        + Op.PUSH7[0x110018000a0001] + Op.SSTORE + Op.PUSH1[0x3] + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.LT + Op.XOR + Op.PUSH7[0x11001800100000] + Op.SSTORE
        + Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.LT + Op.XOR
        + Op.PUSH7[0x11001800100001] + Op.SSTORE + Op.PUSH1[0x3] + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.GT + Op.XOR + Op.PUSH7[0x11001800110000] + Op.SSTORE
        + Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.GT + Op.XOR
        + Op.PUSH7[0x11001800110001] + Op.SSTORE + Op.PUSH1[0x3] + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.SLT + Op.XOR + Op.PUSH7[0x11001800120000] + Op.SSTORE
        + Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.SLT + Op.XOR
        + Op.PUSH7[0x11001800120001] + Op.SSTORE + Op.PUSH1[0x3] + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.SGT + Op.XOR + Op.PUSH7[0x11001800130000] + Op.SSTORE
        + Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.SGT + Op.XOR
        + Op.PUSH7[0x11001800130001] + Op.SSTORE + Op.PUSH1[0x3] + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.EQ + Op.XOR + Op.PUSH7[0x11001800140000] + Op.SSTORE
        + Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.EQ + Op.XOR
        + Op.PUSH7[0x11001800140001] + Op.SSTORE + Op.PUSH1[0x3] + Op.PUSH1[0x2]
        + Op.ISZERO + Op.XOR + Op.PUSH7[0x11001800150000] + Op.SSTORE + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.ISZERO + Op.XOR + Op.PUSH7[0x11001800150001] + Op.SSTORE
        + Op.PUSH1[0x3] + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.AND + Op.XOR
        + Op.PUSH7[0x11001800160000] + Op.SSTORE + Op.PUSH1[0x1] + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.AND + Op.XOR + Op.PUSH7[0x11001800160001] + Op.SSTORE
        + Op.PUSH1[0x3] + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.OR + Op.XOR
        + Op.PUSH7[0x11001800170000] + Op.SSTORE + Op.PUSH1[0x1] + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.OR + Op.XOR + Op.PUSH7[0x11001800170001] + Op.SSTORE
        + Op.PUSH1[0x3] + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.XOR + Op.XOR
        + Op.PUSH7[0x11001800180000] + Op.SSTORE + Op.PUSH1[0x1] + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.XOR + Op.XOR + Op.PUSH7[0x11001800180001] + Op.SSTORE
        + Op.PUSH1[0x3] + Op.PUSH1[0x2] + Op.NOT + Op.XOR + Op.PUSH7[0x11001800190000]
        + Op.SSTORE + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.NOT + Op.XOR
        + Op.PUSH7[0x11001800190001] + Op.SSTORE + Op.PUSH1[0x3] + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.BYTE + Op.XOR + Op.PUSH7[0x110018001a0000] + Op.SSTORE
        + Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.BYTE + Op.XOR
        + Op.PUSH7[0x110018001a0001] + Op.SSTORE + Op.PUSH1[0x3] + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.SHL + Op.XOR + Op.PUSH7[0x110018001b0000] + Op.SSTORE
        + Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.SHL + Op.XOR
        + Op.PUSH7[0x110018001b0001] + Op.SSTORE + Op.PUSH1[0x3] + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.SHR + Op.XOR + Op.PUSH7[0x110018001c0000] + Op.SSTORE
        + Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.SHR + Op.XOR
        + Op.PUSH7[0x110018001c0001] + Op.SSTORE + Op.PUSH1[0x3] + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.SAR + Op.XOR + Op.PUSH7[0x110018001d0000] + Op.SSTORE
        + Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.SAR + Op.XOR
        + Op.PUSH7[0x110018001d0001] + Op.SSTORE + Op.PUSH1[0x1] + Op.PUSH1[0x2]
        + Op.ADD + Op.NOT + Op.PUSH7[0x11001900010000] + Op.SSTORE + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.ADD + Op.NOT + Op.PUSH7[0x11001900010001] + Op.SSTORE
        + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.MUL + Op.NOT + Op.PUSH7[0x11001900020000]
        + Op.SSTORE + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.MUL + Op.NOT
        + Op.PUSH7[0x11001900020001] + Op.SSTORE + Op.PUSH1[0x1] + Op.PUSH1[0x2]
        + Op.SUB + Op.NOT + Op.PUSH7[0x11001900030000] + Op.SSTORE + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.SUB + Op.NOT + Op.PUSH7[0x11001900030001] + Op.SSTORE
        + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.DIV + Op.NOT + Op.PUSH7[0x11001900040000]
        + Op.SSTORE + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.DIV + Op.NOT
        + Op.PUSH7[0x11001900040001] + Op.SSTORE + Op.PUSH1[0x1] + Op.PUSH1[0x2]
        + Op.SDIV + Op.NOT + Op.PUSH7[0x11001900050000] + Op.SSTORE + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.SDIV + Op.NOT + Op.PUSH7[0x11001900050001] + Op.SSTORE
        + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.MOD + Op.NOT + Op.PUSH7[0x11001900060000]
        + Op.SSTORE + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.MOD + Op.NOT
        + Op.PUSH7[0x11001900060001] + Op.SSTORE + Op.PUSH1[0x1] + Op.PUSH1[0x2]
        + Op.SMOD + Op.NOT + Op.PUSH7[0x11001900070000] + Op.SSTORE + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.SMOD + Op.NOT + Op.PUSH7[0x11001900070001] + Op.SSTORE
        + Op.PUSH1[0x3] + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.ADDMOD + Op.NOT
        + Op.PUSH7[0x11001900080000] + Op.SSTORE + Op.PUSH1[0x3] + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.ADDMOD + Op.NOT + Op.PUSH7[0x11001900080001] + Op.SSTORE
        + Op.PUSH1[0x3] + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.MULMOD + Op.NOT
        + Op.PUSH7[0x11001900090000] + Op.SSTORE + Op.PUSH1[0x3] + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.MULMOD + Op.NOT + Op.PUSH7[0x11001900090001] + Op.SSTORE
        + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.EXP + Op.NOT + Op.PUSH7[0x110019000a0000]
        + Op.SSTORE + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.EXP + Op.NOT
        + Op.PUSH7[0x110019000a0001] + Op.SSTORE + Op.PUSH1[0x1] + Op.PUSH1[0x2]
        + Op.LT + Op.NOT + Op.PUSH7[0x11001900100000] + Op.SSTORE + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.LT + Op.NOT + Op.PUSH7[0x11001900100001] + Op.SSTORE
        + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.GT + Op.NOT + Op.PUSH7[0x11001900110000]
        + Op.SSTORE + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.GT + Op.NOT
        + Op.PUSH7[0x11001900110001] + Op.SSTORE + Op.PUSH1[0x1] + Op.PUSH1[0x2]
        + Op.SLT + Op.NOT + Op.PUSH7[0x11001900120000] + Op.SSTORE + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.SLT + Op.NOT + Op.PUSH7[0x11001900120001] + Op.SSTORE
        + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.SGT + Op.NOT + Op.PUSH7[0x11001900130000]
        + Op.SSTORE + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.SGT + Op.NOT
        + Op.PUSH7[0x11001900130001] + Op.SSTORE + Op.PUSH1[0x1] + Op.PUSH1[0x2]
        + Op.EQ + Op.NOT + Op.PUSH7[0x11001900140000] + Op.SSTORE + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.EQ + Op.NOT + Op.PUSH7[0x11001900140001] + Op.SSTORE
        + Op.PUSH1[0x2] + Op.ISZERO + Op.NOT + Op.PUSH7[0x11001900150000] + Op.SSTORE
        + Op.PUSH1[0x2] + Op.ISZERO + Op.NOT + Op.PUSH7[0x11001900150001] + Op.SSTORE
        + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.AND + Op.NOT + Op.PUSH7[0x11001900160000]
        + Op.SSTORE + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.AND + Op.NOT
        + Op.PUSH7[0x11001900160001] + Op.SSTORE + Op.PUSH1[0x1] + Op.PUSH1[0x2]
        + Op.OR + Op.NOT + Op.PUSH7[0x11001900170000] + Op.SSTORE + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.OR + Op.NOT + Op.PUSH7[0x11001900170001] + Op.SSTORE
        + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.XOR + Op.NOT + Op.PUSH7[0x11001900180000]
        + Op.SSTORE + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.XOR + Op.NOT
        + Op.PUSH7[0x11001900180001] + Op.SSTORE + Op.PUSH1[0x2] + Op.NOT + Op.NOT
        + Op.PUSH7[0x11001900190000] + Op.SSTORE + Op.PUSH1[0x2] + Op.NOT + Op.NOT
        + Op.PUSH7[0x11001900190001] + Op.SSTORE + Op.PUSH1[0x1] + Op.PUSH1[0x2]
        + Op.BYTE + Op.NOT + Op.PUSH7[0x110019001a0000] + Op.SSTORE + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.BYTE + Op.NOT + Op.PUSH7[0x110019001a0001] + Op.SSTORE
        + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.SHL + Op.NOT + Op.PUSH7[0x110019001b0000]
        + Op.SSTORE + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.SHL + Op.NOT
        + Op.PUSH7[0x110019001b0001] + Op.SSTORE + Op.PUSH1[0x1] + Op.PUSH1[0x2]
        + Op.SHR + Op.NOT + Op.PUSH7[0x110019001c0000] + Op.SSTORE + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.SHR + Op.NOT + Op.PUSH7[0x110019001c0001] + Op.SSTORE
        + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.SAR + Op.NOT + Op.PUSH7[0x110019001d0000]
        + Op.SSTORE + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.SAR + Op.NOT
        + Op.PUSH7[0x110019001d0001] + Op.SSTORE + Op.PUSH1[0x3] + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.ADD + Op.BYTE + Op.PUSH7[0x11001a00010000] + Op.SSTORE
        + Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.ADD + Op.BYTE
        + Op.PUSH7[0x11001a00010001] + Op.SSTORE + Op.PUSH1[0x3] + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.MUL + Op.BYTE + Op.PUSH7[0x11001a00020000] + Op.SSTORE
        + Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.MUL + Op.BYTE
        + Op.PUSH7[0x11001a00020001] + Op.SSTORE + Op.PUSH1[0x3] + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.SUB + Op.BYTE + Op.PUSH7[0x11001a00030000] + Op.SSTORE
        + Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.SUB + Op.BYTE
        + Op.PUSH7[0x11001a00030001] + Op.SSTORE + Op.PUSH1[0x3] + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.DIV + Op.BYTE + Op.PUSH7[0x11001a00040000] + Op.SSTORE
        + Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.DIV + Op.BYTE
        + Op.PUSH7[0x11001a00040001] + Op.SSTORE + Op.PUSH1[0x3] + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.SDIV + Op.BYTE + Op.PUSH7[0x11001a00050000] + Op.SSTORE
        + Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.SDIV + Op.BYTE
        + Op.PUSH7[0x11001a00050001] + Op.SSTORE + Op.PUSH1[0x3] + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.MOD + Op.BYTE + Op.PUSH7[0x11001a00060000] + Op.SSTORE
        + Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.MOD + Op.BYTE
        + Op.PUSH7[0x11001a00060001] + Op.SSTORE + Op.PUSH1[0x3] + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.SMOD + Op.BYTE + Op.PUSH7[0x11001a00070000] + Op.SSTORE
        + Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.SMOD + Op.BYTE
        + Op.PUSH7[0x11001a00070001] + Op.SSTORE + Op.PUSH1[0x3] + Op.PUSH1[0x3]
        + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.ADDMOD + Op.BYTE
        + Op.PUSH7[0x11001a00080000] + Op.SSTORE + Op.PUSH1[0x1] + Op.PUSH1[0x3]
        + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.ADDMOD + Op.BYTE
        + Op.PUSH7[0x11001a00080001] + Op.SSTORE + Op.PUSH1[0x3] + Op.PUSH1[0x3]
        + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.MULMOD + Op.BYTE
        + Op.PUSH7[0x11001a00090000] + Op.SSTORE + Op.PUSH1[0x1] + Op.PUSH1[0x3]
        + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.MULMOD + Op.BYTE
        + Op.PUSH7[0x11001a00090001] + Op.SSTORE + Op.PUSH1[0x3] + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.EXP + Op.BYTE + Op.PUSH7[0x11001a000a0000] + Op.SSTORE
        + Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.EXP + Op.BYTE
        + Op.PUSH7[0x11001a000a0001] + Op.SSTORE + Op.PUSH1[0x3] + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.LT + Op.BYTE + Op.PUSH7[0x11001a00100000] + Op.SSTORE
        + Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.LT + Op.BYTE
        + Op.PUSH7[0x11001a00100001] + Op.SSTORE + Op.PUSH1[0x3] + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.GT + Op.BYTE + Op.PUSH7[0x11001a00110000] + Op.SSTORE
        + Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.GT + Op.BYTE
        + Op.PUSH7[0x11001a00110001] + Op.SSTORE + Op.PUSH1[0x3] + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.SLT + Op.BYTE + Op.PUSH7[0x11001a00120000] + Op.SSTORE
        + Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.SLT + Op.BYTE
        + Op.PUSH7[0x11001a00120001] + Op.SSTORE + Op.PUSH1[0x3] + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.SGT + Op.BYTE + Op.PUSH7[0x11001a00130000] + Op.SSTORE
        + Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.SGT + Op.BYTE
        + Op.PUSH7[0x11001a00130001] + Op.SSTORE + Op.PUSH1[0x3] + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.EQ + Op.BYTE + Op.PUSH7[0x11001a00140000] + Op.SSTORE
        + Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.EQ + Op.BYTE
        + Op.PUSH7[0x11001a00140001] + Op.SSTORE + Op.PUSH1[0x3] + Op.PUSH1[0x2]
        + Op.ISZERO + Op.BYTE + Op.PUSH7[0x11001a00150000] + Op.SSTORE + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.ISZERO + Op.BYTE + Op.PUSH7[0x11001a00150001] + Op.SSTORE
        + Op.PUSH1[0x3] + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.AND + Op.BYTE
        + Op.PUSH7[0x11001a00160000] + Op.SSTORE + Op.PUSH1[0x1] + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.AND + Op.BYTE + Op.PUSH7[0x11001a00160001] + Op.SSTORE
        + Op.PUSH1[0x3] + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.OR + Op.BYTE
        + Op.PUSH7[0x11001a00170000] + Op.SSTORE + Op.PUSH1[0x1] + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.OR + Op.BYTE + Op.PUSH7[0x11001a00170001] + Op.SSTORE
        + Op.PUSH1[0x3] + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.XOR + Op.BYTE
        + Op.PUSH7[0x11001a00180000] + Op.SSTORE + Op.PUSH1[0x1] + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.XOR + Op.BYTE + Op.PUSH7[0x11001a00180001] + Op.SSTORE
        + Op.PUSH1[0x3] + Op.PUSH1[0x2] + Op.NOT + Op.BYTE
        + Op.PUSH7[0x11001a00190000] + Op.SSTORE + Op.PUSH1[0x1] + Op.PUSH1[0x2]
        + Op.NOT + Op.BYTE + Op.PUSH7[0x11001a00190001] + Op.SSTORE + Op.PUSH1[0x3]
        + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.BYTE + Op.BYTE
        + Op.PUSH7[0x11001a001a0000] + Op.SSTORE + Op.PUSH1[0x1] + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.BYTE + Op.BYTE + Op.PUSH7[0x11001a001a0001] + Op.SSTORE
        + Op.PUSH1[0x3] + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.SHL + Op.BYTE
        + Op.PUSH7[0x11001a001b0000] + Op.SSTORE + Op.PUSH1[0x1] + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.SHL + Op.BYTE + Op.PUSH7[0x11001a001b0001] + Op.SSTORE
        + Op.PUSH1[0x3] + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.SHR + Op.BYTE
        + Op.PUSH7[0x11001a001c0000] + Op.SSTORE + Op.PUSH1[0x1] + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.SHR + Op.BYTE + Op.PUSH7[0x11001a001c0001] + Op.SSTORE
        + Op.PUSH1[0x3] + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.SAR + Op.BYTE
        + Op.PUSH7[0x11001a001d0000] + Op.SSTORE + Op.PUSH1[0x1] + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.SAR + Op.BYTE + Op.PUSH7[0x11001a001d0001] + Op.SSTORE
        + Op.PUSH1[0x3] + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.ADD + Op.SHL
        + Op.PUSH7[0x11001b00010000] + Op.SSTORE + Op.PUSH1[0x1] + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.ADD + Op.SHL + Op.PUSH7[0x11001b00010001] + Op.SSTORE
        + Op.PUSH1[0x3] + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.MUL + Op.SHL
        + Op.PUSH7[0x11001b00020000] + Op.SSTORE + Op.PUSH1[0x1] + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.MUL + Op.SHL + Op.PUSH7[0x11001b00020001] + Op.SSTORE
        + Op.PUSH1[0x3] + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.SUB + Op.SHL
        + Op.PUSH7[0x11001b00030000] + Op.SSTORE + Op.PUSH1[0x1] + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.SUB + Op.SHL + Op.PUSH7[0x11001b00030001] + Op.SSTORE
        + Op.PUSH1[0x3] + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.DIV + Op.SHL
        + Op.PUSH7[0x11001b00040000] + Op.SSTORE + Op.PUSH1[0x1] + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.DIV + Op.SHL + Op.PUSH7[0x11001b00040001] + Op.SSTORE
        + Op.PUSH1[0x3] + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.SDIV + Op.SHL
        + Op.PUSH7[0x11001b00050000] + Op.SSTORE + Op.PUSH1[0x1] + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.SDIV + Op.SHL + Op.PUSH7[0x11001b00050001] + Op.SSTORE
        + Op.PUSH1[0x3] + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.MOD + Op.SHL
        + Op.PUSH7[0x11001b00060000] + Op.SSTORE + Op.PUSH1[0x1] + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.MOD + Op.SHL + Op.PUSH7[0x11001b00060001] + Op.SSTORE
        + Op.PUSH1[0x3] + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.SMOD + Op.SHL
        + Op.PUSH7[0x11001b00070000] + Op.SSTORE + Op.PUSH1[0x1] + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.SMOD + Op.SHL + Op.PUSH7[0x11001b00070001] + Op.SSTORE
        + Op.PUSH1[0x3] + Op.PUSH1[0x3] + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.ADDMOD
        + Op.SHL + Op.PUSH7[0x11001b00080000] + Op.SSTORE + Op.PUSH1[0x1]
        + Op.PUSH1[0x3] + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.ADDMOD + Op.SHL
        + Op.PUSH7[0x11001b00080001] + Op.SSTORE + Op.PUSH1[0x3] + Op.PUSH1[0x3]
        + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.MULMOD + Op.SHL
        + Op.PUSH7[0x11001b00090000] + Op.SSTORE + Op.PUSH1[0x1] + Op.PUSH1[0x3]
        + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.MULMOD + Op.SHL
        + Op.PUSH7[0x11001b00090001] + Op.SSTORE + Op.PUSH1[0x3] + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.EXP + Op.SHL + Op.PUSH7[0x11001b000a0000] + Op.SSTORE
        + Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.EXP + Op.SHL
        + Op.PUSH7[0x11001b000a0001] + Op.SSTORE + Op.PUSH1[0x3] + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.LT + Op.SHL + Op.PUSH7[0x11001b00100000] + Op.SSTORE
        + Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.LT + Op.SHL
        + Op.PUSH7[0x11001b00100001] + Op.SSTORE + Op.PUSH1[0x3] + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.GT + Op.SHL + Op.PUSH7[0x11001b00110000] + Op.SSTORE
        + Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.GT + Op.SHL
        + Op.PUSH7[0x11001b00110001] + Op.SSTORE + Op.PUSH1[0x3] + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.SLT + Op.SHL + Op.PUSH7[0x11001b00120000] + Op.SSTORE
        + Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.SLT + Op.SHL
        + Op.PUSH7[0x11001b00120001] + Op.SSTORE + Op.PUSH1[0x3] + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.SGT + Op.SHL + Op.PUSH7[0x11001b00130000] + Op.SSTORE
        + Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.SGT + Op.SHL
        + Op.PUSH7[0x11001b00130001] + Op.SSTORE + Op.PUSH1[0x3] + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.EQ + Op.SHL + Op.PUSH7[0x11001b00140000] + Op.SSTORE
        + Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.EQ + Op.SHL
        + Op.PUSH7[0x11001b00140001] + Op.SSTORE + Op.PUSH1[0x3] + Op.PUSH1[0x2]
        + Op.ISZERO + Op.SHL + Op.PUSH7[0x11001b00150000] + Op.SSTORE + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.ISZERO + Op.SHL + Op.PUSH7[0x11001b00150001] + Op.SSTORE
        + Op.PUSH1[0x3] + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.AND + Op.SHL
        + Op.PUSH7[0x11001b00160000] + Op.SSTORE + Op.PUSH1[0x1] + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.AND + Op.SHL + Op.PUSH7[0x11001b00160001] + Op.SSTORE
        + Op.PUSH1[0x3] + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.OR + Op.SHL
        + Op.PUSH7[0x11001b00170000] + Op.SSTORE + Op.PUSH1[0x1] + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.OR + Op.SHL + Op.PUSH7[0x11001b00170001] + Op.SSTORE
        + Op.PUSH1[0x3] + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.XOR + Op.SHL
        + Op.PUSH7[0x11001b00180000] + Op.SSTORE + Op.PUSH1[0x1] + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.XOR + Op.SHL + Op.PUSH7[0x11001b00180001] + Op.SSTORE
        + Op.PUSH1[0x3] + Op.PUSH1[0x2] + Op.NOT + Op.SHL + Op.PUSH7[0x11001b00190000]
        + Op.SSTORE + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.NOT + Op.SHL
        + Op.PUSH7[0x11001b00190001] + Op.SSTORE + Op.PUSH1[0x3] + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.BYTE + Op.SHL + Op.PUSH7[0x11001b001a0000] + Op.SSTORE
        + Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.BYTE + Op.SHL
        + Op.PUSH7[0x11001b001a0001] + Op.SSTORE + Op.PUSH1[0x3] + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.SHL + Op.SHL + Op.PUSH7[0x11001b001b0000] + Op.SSTORE
        + Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.SHL + Op.SHL
        + Op.PUSH7[0x11001b001b0001] + Op.SSTORE + Op.PUSH1[0x3] + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.SHR + Op.SHL + Op.PUSH7[0x11001b001c0000] + Op.SSTORE
        + Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.SHR + Op.SHL
        + Op.PUSH7[0x11001b001c0001] + Op.SSTORE + Op.PUSH1[0x3] + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.SAR + Op.SHL + Op.PUSH7[0x11001b001d0000] + Op.SSTORE
        + Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.SAR + Op.SHL
        + Op.PUSH7[0x11001b001d0001] + Op.SSTORE + Op.PUSH1[0x3] + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.ADD + Op.SHR + Op.PUSH7[0x11001c00010000] + Op.SSTORE
        + Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.ADD + Op.SHR
        + Op.PUSH7[0x11001c00010001] + Op.SSTORE + Op.PUSH1[0x3] + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.MUL + Op.SHR + Op.PUSH7[0x11001c00020000] + Op.SSTORE
        + Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.MUL + Op.SHR
        + Op.PUSH7[0x11001c00020001] + Op.SSTORE + Op.PUSH1[0x3] + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.SUB + Op.SHR + Op.PUSH7[0x11001c00030000] + Op.SSTORE
        + Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.SUB + Op.SHR
        + Op.PUSH7[0x11001c00030001] + Op.SSTORE + Op.PUSH1[0x3] + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.DIV + Op.SHR + Op.PUSH7[0x11001c00040000] + Op.SSTORE
        + Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.DIV + Op.SHR
        + Op.PUSH7[0x11001c00040001] + Op.SSTORE + Op.PUSH1[0x3] + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.SDIV + Op.SHR + Op.PUSH7[0x11001c00050000] + Op.SSTORE
        + Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.SDIV + Op.SHR
        + Op.PUSH7[0x11001c00050001] + Op.SSTORE + Op.PUSH1[0x3] + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.MOD + Op.SHR + Op.PUSH7[0x11001c00060000] + Op.SSTORE
        + Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.MOD + Op.SHR
        + Op.PUSH7[0x11001c00060001] + Op.SSTORE + Op.PUSH1[0x3] + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.SMOD + Op.SHR + Op.PUSH7[0x11001c00070000] + Op.SSTORE
        + Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.SMOD + Op.SHR
        + Op.PUSH7[0x11001c00070001] + Op.SSTORE + Op.PUSH1[0x3] + Op.PUSH1[0x3]
        + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.ADDMOD + Op.SHR
        + Op.PUSH7[0x11001c00080000] + Op.SSTORE + Op.PUSH1[0x1] + Op.PUSH1[0x3]
        + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.ADDMOD + Op.SHR
        + Op.PUSH7[0x11001c00080001] + Op.SSTORE + Op.PUSH1[0x3] + Op.PUSH1[0x3]
        + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.MULMOD + Op.SHR
        + Op.PUSH7[0x11001c00090000] + Op.SSTORE + Op.PUSH1[0x1] + Op.PUSH1[0x3]
        + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.MULMOD + Op.SHR
        + Op.PUSH7[0x11001c00090001] + Op.SSTORE + Op.PUSH1[0x3] + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.EXP + Op.SHR + Op.PUSH7[0x11001c000a0000] + Op.SSTORE
        + Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.EXP + Op.SHR
        + Op.PUSH7[0x11001c000a0001] + Op.SSTORE + Op.PUSH1[0x3] + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.LT + Op.SHR + Op.PUSH7[0x11001c00100000] + Op.SSTORE
        + Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.LT + Op.SHR
        + Op.PUSH7[0x11001c00100001] + Op.SSTORE + Op.PUSH1[0x3] + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.GT + Op.SHR + Op.PUSH7[0x11001c00110000] + Op.SSTORE
        + Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.GT + Op.SHR
        + Op.PUSH7[0x11001c00110001] + Op.SSTORE + Op.PUSH1[0x3] + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.SLT + Op.SHR + Op.PUSH7[0x11001c00120000] + Op.SSTORE
        + Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.SLT + Op.SHR
        + Op.PUSH7[0x11001c00120001] + Op.SSTORE + Op.PUSH1[0x3] + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.SGT + Op.SHR + Op.PUSH7[0x11001c00130000] + Op.SSTORE
        + Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.SGT + Op.SHR
        + Op.PUSH7[0x11001c00130001] + Op.SSTORE + Op.PUSH1[0x3] + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.EQ + Op.SHR + Op.PUSH7[0x11001c00140000] + Op.SSTORE
        + Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.EQ + Op.SHR
        + Op.PUSH7[0x11001c00140001] + Op.SSTORE + Op.PUSH1[0x3] + Op.PUSH1[0x2]
        + Op.ISZERO + Op.SHR + Op.PUSH7[0x11001c00150000] + Op.SSTORE + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.ISZERO + Op.SHR + Op.PUSH7[0x11001c00150001] + Op.SSTORE
        + Op.PUSH1[0x3] + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.AND + Op.SHR
        + Op.PUSH7[0x11001c00160000] + Op.SSTORE + Op.PUSH1[0x1] + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.AND + Op.SHR + Op.PUSH7[0x11001c00160001] + Op.SSTORE
        + Op.PUSH1[0x3] + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.OR + Op.SHR
        + Op.PUSH7[0x11001c00170000] + Op.SSTORE + Op.PUSH1[0x1] + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.OR + Op.SHR + Op.PUSH7[0x11001c00170001] + Op.SSTORE
        + Op.PUSH1[0x3] + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.XOR + Op.SHR
        + Op.PUSH7[0x11001c00180000] + Op.SSTORE + Op.PUSH1[0x1] + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.XOR + Op.SHR + Op.PUSH7[0x11001c00180001] + Op.SSTORE
        + Op.PUSH1[0x3] + Op.PUSH1[0x2] + Op.NOT + Op.SHR + Op.PUSH7[0x11001c00190000]
        + Op.SSTORE + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.NOT + Op.SHR
        + Op.PUSH7[0x11001c00190001] + Op.SSTORE + Op.PUSH1[0x3] + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.BYTE + Op.SHR + Op.PUSH7[0x11001c001a0000] + Op.SSTORE
        + Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.BYTE + Op.SHR
        + Op.PUSH7[0x11001c001a0001] + Op.SSTORE + Op.PUSH1[0x3] + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.SHL + Op.SHR + Op.PUSH7[0x11001c001b0000] + Op.SSTORE
        + Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.SHL + Op.SHR
        + Op.PUSH7[0x11001c001b0001] + Op.SSTORE + Op.PUSH1[0x3] + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.SHR + Op.SHR + Op.PUSH7[0x11001c001c0000] + Op.SSTORE
        + Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.SHR + Op.SHR
        + Op.PUSH7[0x11001c001c0001] + Op.SSTORE + Op.PUSH1[0x3] + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.SAR + Op.SHR + Op.PUSH7[0x11001c001d0000] + Op.SSTORE
        + Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.SAR + Op.SHR
        + Op.PUSH7[0x11001c001d0001] + Op.SSTORE + Op.PUSH1[0x3] + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.ADD + Op.SAR + Op.PUSH7[0x11001d00010000] + Op.SSTORE
        + Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.ADD + Op.SAR
        + Op.PUSH7[0x11001d00010001] + Op.SSTORE + Op.PUSH1[0x3] + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.MUL + Op.SAR + Op.PUSH7[0x11001d00020000] + Op.SSTORE
        + Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.MUL + Op.SAR
        + Op.PUSH7[0x11001d00020001] + Op.SSTORE + Op.PUSH1[0x3] + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.SUB + Op.SAR + Op.PUSH7[0x11001d00030000] + Op.SSTORE
        + Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.SUB + Op.SAR
        + Op.PUSH7[0x11001d00030001] + Op.SSTORE + Op.PUSH1[0x3] + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.DIV + Op.SAR + Op.PUSH7[0x11001d00040000] + Op.SSTORE
        + Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.DIV + Op.SAR
        + Op.PUSH7[0x11001d00040001] + Op.SSTORE + Op.PUSH1[0x3] + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.SDIV + Op.SAR + Op.PUSH7[0x11001d00050000] + Op.SSTORE
        + Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.SDIV + Op.SAR
        + Op.PUSH7[0x11001d00050001] + Op.SSTORE + Op.PUSH1[0x3] + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.MOD + Op.SAR + Op.PUSH7[0x11001d00060000] + Op.SSTORE
        + Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.MOD + Op.SAR
        + Op.PUSH7[0x11001d00060001] + Op.SSTORE + Op.PUSH1[0x3] + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.SMOD + Op.SAR + Op.PUSH7[0x11001d00070000] + Op.SSTORE
        + Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.SMOD + Op.SAR
        + Op.PUSH7[0x11001d00070001] + Op.SSTORE + Op.PUSH1[0x3] + Op.PUSH1[0x3]
        + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.ADDMOD + Op.SAR
        + Op.PUSH7[0x11001d00080000] + Op.SSTORE + Op.PUSH1[0x1] + Op.PUSH1[0x3]
        + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.ADDMOD + Op.SAR
        + Op.PUSH7[0x11001d00080001] + Op.SSTORE + Op.PUSH1[0x3] + Op.PUSH1[0x3]
        + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.MULMOD + Op.SAR
        + Op.PUSH7[0x11001d00090000] + Op.SSTORE + Op.PUSH1[0x1] + Op.PUSH1[0x3]
        + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.MULMOD + Op.SAR
        + Op.PUSH7[0x11001d00090001] + Op.SSTORE + Op.PUSH1[0x3] + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.EXP + Op.SAR + Op.PUSH7[0x11001d000a0000] + Op.SSTORE
        + Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.EXP + Op.SAR
        + Op.PUSH7[0x11001d000a0001] + Op.SSTORE + Op.PUSH1[0x3] + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.LT + Op.SAR + Op.PUSH7[0x11001d00100000] + Op.SSTORE
        + Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.LT + Op.SAR
        + Op.PUSH7[0x11001d00100001] + Op.SSTORE + Op.PUSH1[0x3] + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.GT + Op.SAR + Op.PUSH7[0x11001d00110000] + Op.SSTORE
        + Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.GT + Op.SAR
        + Op.PUSH7[0x11001d00110001] + Op.SSTORE + Op.PUSH1[0x3] + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.SLT + Op.SAR + Op.PUSH7[0x11001d00120000] + Op.SSTORE
        + Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.SLT + Op.SAR
        + Op.PUSH7[0x11001d00120001] + Op.SSTORE + Op.PUSH1[0x3] + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.SGT + Op.SAR + Op.PUSH7[0x11001d00130000] + Op.SSTORE
        + Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.SGT + Op.SAR
        + Op.PUSH7[0x11001d00130001] + Op.SSTORE + Op.PUSH1[0x3] + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.EQ + Op.SAR + Op.PUSH7[0x11001d00140000] + Op.SSTORE
        + Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.EQ + Op.SAR
        + Op.PUSH7[0x11001d00140001] + Op.SSTORE + Op.PUSH1[0x3] + Op.PUSH1[0x2]
        + Op.ISZERO + Op.SAR + Op.PUSH7[0x11001d00150000] + Op.SSTORE + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.ISZERO + Op.SAR + Op.PUSH7[0x11001d00150001] + Op.SSTORE
        + Op.PUSH1[0x3] + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.AND + Op.SAR
        + Op.PUSH7[0x11001d00160000] + Op.SSTORE + Op.PUSH1[0x1] + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.AND + Op.SAR + Op.PUSH7[0x11001d00160001] + Op.SSTORE
        + Op.PUSH1[0x3] + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.OR + Op.SAR
        + Op.PUSH7[0x11001d00170000] + Op.SSTORE + Op.PUSH1[0x1] + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.OR + Op.SAR + Op.PUSH7[0x11001d00170001] + Op.SSTORE
        + Op.PUSH1[0x3] + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.XOR + Op.SAR
        + Op.PUSH7[0x11001d00180000] + Op.SSTORE + Op.PUSH1[0x1] + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.XOR + Op.SAR + Op.PUSH7[0x11001d00180001] + Op.SSTORE
        + Op.PUSH1[0x3] + Op.PUSH1[0x2] + Op.NOT + Op.SAR + Op.PUSH7[0x11001d00190000]
        + Op.SSTORE + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.NOT + Op.SAR
        + Op.PUSH7[0x11001d00190001] + Op.SSTORE + Op.PUSH1[0x3] + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.BYTE + Op.SAR + Op.PUSH7[0x11001d001a0000] + Op.SSTORE
        + Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.BYTE + Op.SAR
        + Op.PUSH7[0x11001d001a0001] + Op.SSTORE + Op.PUSH1[0x3] + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.SHL + Op.SAR + Op.PUSH7[0x11001d001b0000] + Op.SSTORE
        + Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.SHL + Op.SAR
        + Op.PUSH7[0x11001d001b0001] + Op.SSTORE + Op.PUSH1[0x3] + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.SHR + Op.SAR + Op.PUSH7[0x11001d001c0000] + Op.SSTORE
        + Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.SHR + Op.SAR
        + Op.PUSH7[0x11001d001c0001] + Op.SSTORE + Op.PUSH1[0x3] + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.SAR + Op.SAR + Op.PUSH7[0x11001d001d0000] + Op.SSTORE
        + Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.SAR + Op.SAR
        + Op.PUSH7[0x11001d001d0001] + Op.SSTORE + Op.STOP
    ),
    )

    tx = Transaction(
        secret_key=Hash(
            "0x40ac0fc28c27e961ee46ec43355a094de205856edbd4654cf2577c2608d4ec1e"
        ),
        to=contract,
        data=bytes.fromhex("00"),
        gas_limit=16777216,
        gas_price=10,
        nonce=0,
        value=1,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)
