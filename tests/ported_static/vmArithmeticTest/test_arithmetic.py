"""
Test arithmetic opcode results.

Ported from:
state_tests/VMTests/vmArithmeticTest/addFiller.yml
state_tests/VMTests/vmArithmeticTest/addmodFiller.yml
state_tests/VMTests/vmArithmeticTest/divFiller.yml
state_tests/VMTests/vmArithmeticTest/expFiller.yml
state_tests/VMTests/vmArithmeticTest/modFiller.yml
state_tests/VMTests/vmArithmeticTest/mulFiller.yml
state_tests/VMTests/vmArithmeticTest/mulmodFiller.yml
state_tests/VMTests/vmArithmeticTest/sdivFiller.yml
state_tests/VMTests/vmArithmeticTest/signextendFiller.yml
state_tests/VMTests/vmArithmeticTest/smodFiller.yml
state_tests/VMTests/vmArithmeticTest/subFiller.yml
state_tests/VMTests/vmArithmeticTest/notFiller.yml
"""

import pytest
from execution_testing import (
    Account,
    Alloc,
    Bytecode,
    StateTestFiller,
    Transaction,
)
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"

MAX_UINT = 2**256 - 1
INT_MIN = 2**255
INT_MAX = 2**255 - 1
SENTINEL = 0x0BAD

CASES = [
    # add
    pytest.param(
        Op.ADD(MAX_UINT, MAX_UINT), MAX_UINT - 1, id="add-add_neg1_neg1"
    ),
    pytest.param(Op.ADD(MAX_UINT, 4), 3, id="add-add_neg1_4"),
    pytest.param(Op.ADD(MAX_UINT, 1), 0, id="add-add_neg1_1"),
    pytest.param(Op.ADD(0, 0), 0, id="add-add_0_0"),
    pytest.param(Op.ADD(1, MAX_UINT), 0, id="add-add_1_neg1"),
    # addmod
    pytest.param(Op.ADDMOD(1, 2, 2), 1, id="addmod-addmod_1_2_2"),
    pytest.param(
        Op.ADDMOD(Op.SUB(0, 1), Op.SUB(0, 2), 2),
        1,
        id="addmod-addmod_neg1_neg2_2",
    ),
    pytest.param(
        Op.ADDMOD(Op.SUB(0, 6), 1, 3), 2, id="addmod-addmod_neg6_1_3"
    ),
    pytest.param(
        Op.EQ(Op.SMOD(Op.SUB(0, 5), 3), Op.ADDMOD(Op.SUB(0, 6), 1, 3)),
        0,
        id="addmod-addmod_eq_smod",
    ),
    pytest.param(
        Op.EQ(Op.MOD(Op.SUB(0, 5), 3), Op.ADDMOD(Op.SUB(0, 6), 1, 3)),
        1,
        id="addmod-addmod_eq_mod",
    ),
    pytest.param(
        Op.ADDMOD(4, 1, Op.SUB(0, 3)), 5, id="addmod-addmod_4_1_neg3"
    ),
    pytest.param(
        Op.EQ(Op.ADDMOD(4, 1, Op.SUB(0, 3)), 2),
        0,
        id="addmod-addmod_4_1_neg3_eq",
    ),
    pytest.param(
        Op.ADDMOD(Op.SUB(0, 1), 0, 5), 0, id="addmod-addmod_neg1_0_5"
    ),
    pytest.param(
        Op.ADDMOD(Op.SUB(0, 1), 1, 5), 1, id="addmod-addmod_neg1_1_5"
    ),
    pytest.param(
        Op.ADDMOD(Op.SUB(0, 1), 2, 5), 2, id="addmod-addmod_neg1_2_5"
    ),
    pytest.param(
        Op.ADDMOD(Op.SUB(0, 1), Op.SUB(0, 2), 5),
        4,
        id="addmod-addmod_neg1_neg2_5",
    ),
    pytest.param(Op.ADDMOD(MAX_UINT, 1, 5), 1, id="addmod-addmod_2_160_1_5"),
    pytest.param(Op.ADDMOD(4, 1, 0), 0, id="addmod-addmod_4_1_0"),
    pytest.param(Op.ADDMOD(0, 1, 0), 0, id="addmod-addmod_0_1_0"),
    pytest.param(Op.ADDMOD(1, 0, 0), 0, id="addmod-addmod_1_0_0"),
    pytest.param(
        Op.SUB(Op.ADDMOD(0, 0, 0), 1), MAX_UINT, id="addmod-addmod_0_0_0_min_1"
    ),
    # div
    pytest.param(
        Op.DIV(
            2,
            0xFEDCBA9876543210FEDCBA9876543210FEDCBA9876543210FEDCBA9876543210,
        ),
        0,
        id="div-div_2_big",
    ),
    pytest.param(
        Op.DIV(
            0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFBA,
            0x1DAE6076B981DAE6076B981DAE6076B981DAE6076B981DAE6076B981DAE6077,
        ),
        137,
        id="div-div_boost_bug",
    ),
    pytest.param(Op.DIV(5, 2), 2, id="div-div_5_2"),
    pytest.param(Op.DIV(0x17, 0x18), 0, id="div-div_23_24"),
    pytest.param(Op.DIV(0, 0x18), 0, id="div-div_0_24"),
    pytest.param(Op.DIV(1, 1), 1, id="div-div_1_0"),
    pytest.param(Op.DIV(2, 0), 0, id="div-div_2_0"),
    pytest.param(Op.ADD(Op.DIV(0xD, 0), 7), 7, id="div-div_0_add"),
    # exp
    pytest.param(Op.EXP(2, 2), 4, id="exp-exp_2_2"),
    pytest.param(Op.EXP(MAX_UINT, MAX_UINT - 1), 1, id="exp-exp_neg1_neg2"),
    pytest.param(
        Op.EXP(0x7FFFFFFF, 0x7FFFFFFF),
        0xBC8CCCCCCCC888888880000000AAAAAAB00000000FFFFFFFFFFFFFFF7FFFFFFF,
        id="exp-exp_big_big",
    ),
    pytest.param(Op.EXP(0, 0x7FFFFFFF), 0, id="exp-exp_0_big"),
    pytest.param(Op.EXP(0x7FFFFFFF, 0), 1, id="exp-exp_big_0"),
    pytest.param(Op.EXP(0x101, 1), 257, id="exp-exp_257_1"),
    pytest.param(Op.EXP(1, 0x101), 1, id="exp-exp_1_257"),
    pytest.param(Op.EXP(2, 0x101), 0, id="exp-exp_2_257"),
    pytest.param(Op.EXP(0, 0), 1, id="exp-exp_0_0"),
    pytest.param(Op.EXP(2, 0x100000000000F), 0, id="exp-exp_2_big"),
    pytest.param(Op.EXP(2, 0xF), 32768, id="exp-exp_2_15"),
    # mod
    pytest.param(Op.MOD(2, 3), 2, id="mod-mod_2_3"),
    pytest.param(Op.MOD(MAX_UINT, 2), 1, id="mod-mod_neg1_2"),
    pytest.param(Op.MOD(0, MAX_UINT), 0, id="mod-mod_0_neg1"),
    pytest.param(Op.MOD(3, 0), 0, id="mod-mod_3_0"),
    pytest.param(Op.MOD(Op.SUB(0, 2), 3), 2, id="mod-mod_neg2_3"),
    pytest.param(Op.SUB(Op.MOD(0x10, 0), 1), MAX_UINT, id="mod-mod_16_0"),
    # mul
    pytest.param(Op.MUL(2, 3), 6, id="mul-mul_2_3"),
    pytest.param(Op.MUL(MAX_UINT, MAX_UINT), 1, id="mul-mul_neg1_neg1"),
    pytest.param(Op.MUL(0, 0x17), 0, id="mul-mul_0_23"),
    pytest.param(Op.MUL(0x17, 1), 23, id="mul-mul_23_1"),
    pytest.param(
        Op.MUL(INT_MIN, MAX_UINT), INT_MIN, id="mul-mul_2pow255_neg1"
    ),
    pytest.param(Op.MUL(INT_MIN, INT_MIN), 0, id="mul-mul_2pow255_2pow255"),
    pytest.param(
        Op.MUL(INT_MAX, INT_MAX), 1, id="mul-mul_2pow255min1_2pow255min1"
    ),
    pytest.param(
        Op.MUL(
            Op.MUL(
                0x1234567890ABCDEF0FEDCBA0987654321,
                0x1234567890ABCDEF0FEDCBA0987654321,
            ),
            0x1234567890ABCDEF0FEDCBA0987654321,
        ),
        0x47D0817E4167B1EB4F9FC722B133EF9D7D9A6FB4C2C1C442D000107A5E419561,
        id="mul-big_pow_3",
    ),
    # mulmod
    pytest.param(Op.MULMOD(1, 2, 2), 0, id="mulmod-mm_1_2_2"),
    pytest.param(
        Op.MULMOD(Op.SUB(0, 1), Op.SUB(0, 2), 3), 0, id="mulmod-mm_neg1_neg2_3"
    ),
    pytest.param(Op.MULMOD(Op.SUB(0, 5), 1, 3), 2, id="mulmod-mm_neg5_1_3"),
    pytest.param(Op.MULMOD(5, 1, Op.SUB(0, 3)), 5, id="mulmod-mm_5_1_neg3"),
    pytest.param(Op.MULMOD(0x1B, 0x25, 0x64), 99, id="mulmod-mm_27_37_100"),
    pytest.param(Op.MULMOD(INT_MIN, 2, 5), 1, id="mulmod-mm_2pow255_2_5"),
    pytest.param(Op.MULMOD(Op.SUB(0, 1), 2, 5), 0, id="mulmod-mm_neg1_2_5"),
    pytest.param(
        Op.MULMOD(Op.SUB(INT_MIN, 1), 2, 5), 4, id="mulmod-mm_2pow255min1_2_5"
    ),
    pytest.param(
        Op.MULMOD(Op.ADD(INT_MIN, 1), 2, 5), 3, id="mulmod-mm_2pow255plus1_2_5"
    ),
    pytest.param(
        Op.EQ(Op.SMOD(Op.SUB(0, 5), 3), Op.MULMOD(Op.SUB(0, 5), 1, 3)),
        0,
        id="mulmod-mulmod_vs_smod",
    ),
    pytest.param(
        Op.EQ(Op.MOD(Op.SUB(0, 5), 3), Op.MULMOD(Op.SUB(0, 5), 1, 3)),
        1,
        id="mulmod-mulmod_vs_mod",
    ),
    pytest.param(
        Op.EQ(Op.MULMOD(5, 1, Op.SUB(0, 3)), 2),
        0,
        id="mulmod-mulmod_pos_pos_neg",
    ),
    pytest.param(Op.MULMOD(0, 1, 0), 0, id="mulmod-mm_0_1_0"),
    pytest.param(Op.MULMOD(1, 0, 0), 0, id="mulmod-mm_1_0_0"),
    pytest.param(
        Op.SUB(1, Op.MULMOD(0, 0, 0)), 1, id="mulmod-one_minus_mm_0_0_0"
    ),
    pytest.param(Op.MULMOD(5, 1, 0), 0, id="mulmod-mm_5_1_0"),
    # sdiv
    pytest.param(
        Op.SDIV(Op.SUB(0, MAX_UINT), MAX_UINT), MAX_UINT, id="sdiv-sdiv_1_neg1"
    ),
    pytest.param(
        Op.SDIV(MAX_UINT, Op.SUB(0, MAX_UINT)), MAX_UINT, id="sdiv-sdiv_neg1_1"
    ),
    pytest.param(
        Op.SDIV(Op.SUB(0, 2), Op.SUB(0, 4)), 0, id="sdiv-sdiv_neg2_neg4"
    ),
    pytest.param(
        Op.SDIV(4, Op.SUB(0, 2)), MAX_UINT - 1, id="sdiv-sdiv_4_neg2"
    ),
    pytest.param(Op.SDIV(5, Op.SUB(0, 4)), MAX_UINT, id="sdiv-sdiv_5_neg4"),
    pytest.param(
        Op.SDIV(Op.SUB(0, INT_MIN), Op.SUB(0, 1)),
        INT_MIN,
        id="sdiv-sdiv_2pow255_neg1",
    ),
    pytest.param(Op.SDIV(Op.SUB(0, INT_MIN), 0), 0, id="sdiv-sdiv_2pow255_0"),
    pytest.param(Op.SDIV(Op.SUB(0, 1), 0x19), 0, id="sdiv-sdiv_neg1_25"),
    pytest.param(
        Op.SDIV(Op.SUB(0, 1), Op.SUB(0, 1)), 1, id="sdiv-sdiv_neg1_neg1"
    ),
    pytest.param(
        Op.SDIV(Op.SUB(0, 1), 1), MAX_UINT, id="sdiv-sdiv_neg1_1_2nd"
    ),
    pytest.param(
        Op.SDIV(Op.SUB(0, 3), Op.SUB(0, 0)), 0, id="sdiv-sdiv_neg3_0"
    ),
    pytest.param(Op.SDIV(Op.SUB(0, MAX_UINT), 0), 0, id="sdiv-sdiv_1_0"),
    pytest.param(
        Op.ADD(Op.SDIV(Op.SUB(0, MAX_UINT), 0), 1), 1, id="sdiv-sdiv_1_0_add1"
    ),
    pytest.param(Op.SDIV(Op.SUB(0, 9), 5), MAX_UINT, id="sdiv-sdiv_neg9_5"),
    pytest.param(
        Op.SDIV(Op.SUB(0, Op.SUB(INT_MIN, 1)), Op.SUB(0, 1)),
        INT_MAX,
        id="sdiv-sdiv_minint_neg1",
    ),
    pytest.param(
        Op.SDIV(MAX_UINT, Op.SUB(0, INT_MAX)), 0, id="sdiv-sdiv_neg1_minint"
    ),
    # signextend
    pytest.param(
        Op.SIGNEXTEND(0x50, 0x126AF4), 0x126AF4, id="signextend-invalid_byte"
    ),
    pytest.param(Op.SIGNEXTEND(0, 0), 0, id="signextend-zero_zero"),
    pytest.param(
        Op.SIGNEXTEND(0, MAX_UINT), MAX_UINT, id="signextend-zero_neg1"
    ),
    pytest.param(
        Op.SIGNEXTEND(MAX_UINT - 1, MAX_UINT - 1),
        MAX_UINT - 1,
        id="signextend-neg2_neg2",
    ),
    pytest.param(
        Op.SIGNEXTEND(MAX_UINT, MAX_UINT), MAX_UINT, id="signextend-neg1_neg1"
    ),
    pytest.param(
        Op.SIGNEXTEND(0xF00000000000000001, 0xFF),
        255,
        id="signextend-large_ff",
    ),
    pytest.param(Op.SIGNEXTEND(MAX_UINT, 0), 0, id="signextend-neg1_zero"),
    pytest.param(
        Op.SIGNEXTEND(0, 0x122F6A), 106, id="signextend-bit_is_not_set"
    ),
    pytest.param(
        Op.SIGNEXTEND(1, 0x126AF4), 27380, id="signextend-bit_is_not_set_high"
    ),
    pytest.param(
        Op.SIGNEXTEND(1, 0x12FAF4),
        0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFAF4,
        id="signextend-bit_is_set_high",
    ),
    pytest.param(
        Op.SIGNEXTEND(0x10000000000000001, 0x8000),
        32768,
        id="signextend-overflow_bytenum",
    ),
    pytest.param(
        Op.SIGNEXTEND(0xF0000000000001, 0xFFFF),
        65535,
        id="signextend-overflow_bytenum2",
    ),
    pytest.param(
        Op.SIGNEXTEND(0, 0x122FF4),
        0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF4,
        id="signextend-bit_is_set",
    ),
    pytest.param(Op.SIGNEXTEND(0x1F, 1), 1, id="signextend-byte31_pos"),
    pytest.param(
        Op.SIGNEXTEND(0x1F, Op.SUB(0, 1)), MAX_UINT, id="signextend-byte31_neg"
    ),
    # smod
    pytest.param(Op.SMOD(2, 3), 2, id="smod-smod_2_3"),
    pytest.param(Op.SMOD(MAX_UINT, 2), MAX_UINT, id="smod-smod_neg1_2"),
    pytest.param(Op.SMOD(0, MAX_UINT), 0, id="smod-smod_0_neg1"),
    pytest.param(Op.SMOD(3, 0), 0, id="smod-smod_3_0"),
    pytest.param(
        Op.SMOD(Op.SUB(0, 2), 3), MAX_UINT - 1, id="smod-smod_neg2_3"
    ),
    pytest.param(Op.SUB(Op.SMOD(0x10, 0), 1), MAX_UINT, id="smod-smod_16_0"),
    # sub
    pytest.param(Op.SUB(0x17, 1), 22, id="sub-sub_23_1"),
    pytest.param(Op.SUB(2, 3), MAX_UINT, id="sub-sub_2_3"),
    pytest.param(
        Op.SUB(0, 0x17),
        0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFE9,
        id="sub-sub_0_23",
    ),
    pytest.param(Op.SUB(0, MAX_UINT), 1, id="sub-sub_0_neg1"),
    pytest.param(Op.SUB(MAX_UINT, 0), MAX_UINT, id="sub-sub_neg1_0"),
    # not
    pytest.param(
        Op.NOT(0x123456789ABCDEF), MAX_UINT - 0x123456789ABCDEF, id="not-not"
    ),
]

PORTED_FROM = [
    "state_tests/VMTests/vmArithmeticTest/addFiller.yml",
    "state_tests/VMTests/vmArithmeticTest/addmodFiller.yml",
    "state_tests/VMTests/vmArithmeticTest/divFiller.yml",
    "state_tests/VMTests/vmArithmeticTest/expFiller.yml",
    "state_tests/VMTests/vmArithmeticTest/modFiller.yml",
    "state_tests/VMTests/vmArithmeticTest/mulFiller.yml",
    "state_tests/VMTests/vmArithmeticTest/mulmodFiller.yml",
    "state_tests/VMTests/vmArithmeticTest/sdivFiller.yml",
    "state_tests/VMTests/vmArithmeticTest/signextendFiller.yml",
    "state_tests/VMTests/vmArithmeticTest/smodFiller.yml",
    "state_tests/VMTests/vmArithmeticTest/subFiller.yml",
    "state_tests/VMTests/vmArithmeticTest/notFiller.yml",
]


@pytest.mark.ported_from(PORTED_FROM)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize("value, expected", CASES)
def test_arithmetic(
    state_test: StateTestFiller,
    pre: Alloc,
    value: Bytecode,
    expected: int,
) -> None:
    """Store the result of an arithmetic expression over a sentinel."""
    contract = pre.deploy_contract(
        code=Op.SSTORE(0, value) + Op.STOP, storage={0: SENTINEL}
    )
    tx = Transaction(sender=pre.fund_eoa(), to=contract)
    post = {contract: Account(storage={0: expected})}
    state_test(pre=pre, post=post, tx=tx)


@pytest.mark.ported_from(
    ["state_tests/VMTests/vmArithmeticTest/mulFiller.yml"],
)
@pytest.mark.valid_from("Cancun")
def test_mul_stack_underflow(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Revert a storage write when MUL underflows the stack."""
    contract = pre.deploy_contract(
        code=Op.SSTORE(0, 1) + Op.PUSH1[1] + Op.MUL + Op.STOP,
        storage={0: SENTINEL},
    )
    tx = Transaction(sender=pre.fund_eoa(), to=contract)
    post = {contract: Account(storage={0: SENTINEL})}
    state_test(pre=pre, post=post, tx=tx)
