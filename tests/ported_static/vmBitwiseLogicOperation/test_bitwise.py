"""
Test comparison and bitwise logic opcode results.

Ported from:
state_tests/VMTests/vmBitwiseLogicOperation/andFiller.yml
state_tests/VMTests/vmBitwiseLogicOperation/byteFiller.yml
state_tests/VMTests/vmBitwiseLogicOperation/eqFiller.yml
state_tests/VMTests/vmBitwiseLogicOperation/gtFiller.yml
state_tests/VMTests/vmBitwiseLogicOperation/iszeroFiller.yml
state_tests/VMTests/vmBitwiseLogicOperation/ltFiller.yml
state_tests/VMTests/vmBitwiseLogicOperation/notFiller.yml
state_tests/VMTests/vmBitwiseLogicOperation/orFiller.yml
state_tests/VMTests/vmBitwiseLogicOperation/sgtFiller.yml
state_tests/VMTests/vmBitwiseLogicOperation/sltFiller.yml
state_tests/VMTests/vmBitwiseLogicOperation/xorFiller.yml
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
SENTINEL = 0x0BAD
BYTE_SOURCE = 0x8040201008040201
BYTE_INDEXES = (
    0x000102030405060708090A0B0C0D0E0F101112131415161718191A1B1C1D1E1F
)

CASES = [
    # gt
    pytest.param(Op.GT(Op.SUB(0, 2), 0), 1, id="gt-gt_neg2_0"),
    pytest.param(Op.GT(0, Op.SUB(0, 2)), 0, id="gt-gt_0_neg2"),
    pytest.param(Op.GT(MAX_UINT, 0), 1, id="gt-gt_neg1_0"),
    pytest.param(Op.GT(0, MAX_UINT), 0, id="gt-gt_0_neg1"),
    # eq
    pytest.param(Op.EQ(Op.SUB(0, 5), Op.SUB(0, 3)), 0, id="eq-eq_neg5_neg3"),
    pytest.param(Op.EQ(0, 0), 1, id="eq-eq_0_0"),
    pytest.param(Op.EQ(MAX_UINT, MAX_UINT), 1, id="eq-eq_neg1_neg1"),
    # lt
    pytest.param(Op.LT(Op.SUB(0, 2), 0), 0, id="lt-lt_neg2_0"),
    pytest.param(Op.LT(0, Op.SUB(0, 2)), 1, id="lt-lt_0_neg2"),
    pytest.param(Op.LT(MAX_UINT, 0), 0, id="lt-lt_neg1_0"),
    pytest.param(Op.LT(0, MAX_UINT), 1, id="lt-lt_0_neg1"),
    # not
    pytest.param(Op.NOT(0), MAX_UINT, id="not-not_0"),
    pytest.param(Op.NOT(2), MAX_UINT - 2, id="not-not_2"),
    pytest.param(Op.NOT(MAX_UINT), 0, id="not-not_allones"),
    pytest.param(Op.NOT(Op.SUB(0, 2)), 1, id="not-not_neg2"),
    pytest.param(
        Op.NOT(Op.SUB(0, MAX_UINT)), MAX_UINT - 1, id="not-not_neg_2_pow_256"
    ),
    pytest.param(Op.NOT(Op.SUB(0, 0)), MAX_UINT, id="not-not_neg0"),
    # xor
    pytest.param(Op.XOR(2, 2), 0, id="xor-xor_2_2"),
    pytest.param(Op.XOR(2, 1), 3, id="xor-xor_2_1"),
    pytest.param(Op.XOR(3, 1), 2, id="xor-xor_3_1"),
    pytest.param(
        Op.XOR(
            MAX_UINT,
            0x123456789ABCDEF0123456789ABCDEF0123456789ABCDEF0123456789ABCDEF,
        ),
        0xFEDCBA9876543210FEDCBA9876543210FEDCBA9876543210FEDCBA9876543210,
        id="xor-xor_allones_bignum",
    ),
    pytest.param(
        Op.XOR(
            0xEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEE,
            MAX_UINT,
        ),
        0x1111111111111111111111111111111111111111111111111111111111111111,
        id="xor-xor_allones_1110s",
    ),
    pytest.param(
        Op.XOR(
            0xEEEEEEEEEEEEEEEEEEEEEEEEEEEEEFEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEE,
            MAX_UINT,
        ),
        0x1111111111111111111111111111101111111111111111111111111111111111,
        id="xor-xor_allones_eefee",
    ),
    # or
    pytest.param(Op.OR(2, 2), 2, id="or-or_2_2"),
    pytest.param(Op.OR(2, 1), 3, id="or-or_2_1"),
    pytest.param(Op.OR(3, 1), 3, id="or-or_3_1"),
    pytest.param(
        Op.OR(
            MAX_UINT,
            0x123456789ABCDEF0123456789ABCDEF0123456789ABCDEF0123456789ABCDEF,
        ),
        MAX_UINT,
        id="or-or_allones_bignum",
    ),
    pytest.param(
        Op.OR(
            0xEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEE,
            MAX_UINT,
        ),
        MAX_UINT,
        id="or-or_allones_1110s",
    ),
    pytest.param(
        Op.OR(
            0xEEEEEEEEEEEEEEEEEEEEEEEEEEEEEFEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEE,
            MAX_UINT,
        ),
        MAX_UINT,
        id="or-or_allones_eefee",
    ),
    # slt
    pytest.param(Op.SLT(Op.SUB(0, 2), 0), 1, id="slt-slt_neg2_0"),
    pytest.param(Op.SLT(0, Op.SUB(0, 2)), 0, id="slt-slt_0_neg2"),
    pytest.param(Op.SLT(MAX_UINT, 0), 1, id="slt-slt_neg1_0"),
    pytest.param(Op.SLT(0, MAX_UINT), 0, id="slt-slt_0_neg1"),
    # sgt
    pytest.param(Op.SGT(Op.SUB(0, 2), 0), 0, id="sgt-sgt_neg2_0"),
    pytest.param(Op.SGT(0, Op.SUB(0, 2)), 1, id="sgt-sgt_0_neg2"),
    pytest.param(Op.SGT(MAX_UINT, 0), 0, id="sgt-sgt_neg1_0"),
    pytest.param(Op.SGT(0, MAX_UINT), 1, id="sgt-sgt_0_neg1"),
    # iszero
    pytest.param(Op.ISZERO(MAX_UINT), 0, id="iszero-iszero_neg1"),
    pytest.param(Op.ISZERO(0), 1, id="iszero-iszero_0"),
    pytest.param(Op.ISZERO(Op.SUB(0, 2)), 0, id="iszero-iszero_neg2"),
    # and
    pytest.param(Op.AND(2, 2), 2, id="and-and_2_2"),
    pytest.param(Op.AND(2, 1), 0, id="and-and_2_1"),
    pytest.param(Op.AND(3, 1), 1, id="and-and_3_1"),
    pytest.param(
        Op.AND(
            MAX_UINT,
            0x123456789ABCDEF0123456789ABCDEF0123456789ABCDEF0123456789ABCDEF,
        ),
        0x123456789ABCDEF0123456789ABCDEF0123456789ABCDEF0123456789ABCDEF,
        id="and-and_allones_bignum",
    ),
    pytest.param(
        Op.AND(
            0xEEEEEEEEEEEEEEEEEEEEEEEEEEEEEFEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEE,
            MAX_UINT,
        ),
        0xEEEEEEEEEEEEEEEEEEEEEEEEEEEEEFEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEE,
        id="and-and_allones_eefee",
    ),
    # byte
    *[
        pytest.param(
            Op.BYTE(Op.SUB(31, i), BYTE_SOURCE),
            2**i,
            id=f"byte-byte_{31 - i}_big",
        )
        for i in range(8)
    ],
    pytest.param(
        Op.BYTE(Op.SUB(31, 31), BYTE_SOURCE), 0, id="byte-byte_00_big"
    ),
    pytest.param(
        Op.BYTE(Op.SDIV(31, 32), BYTE_SOURCE), 0, id="byte-byte_00_big_2nd"
    ),
]


@pytest.mark.ported_from(
    [
        "state_tests/VMTests/vmBitwiseLogicOperation/andFiller.yml",
        "state_tests/VMTests/vmBitwiseLogicOperation/byteFiller.yml",
        "state_tests/VMTests/vmBitwiseLogicOperation/eqFiller.yml",
        "state_tests/VMTests/vmBitwiseLogicOperation/gtFiller.yml",
        "state_tests/VMTests/vmBitwiseLogicOperation/iszeroFiller.yml",
        "state_tests/VMTests/vmBitwiseLogicOperation/ltFiller.yml",
        "state_tests/VMTests/vmBitwiseLogicOperation/notFiller.yml",
        "state_tests/VMTests/vmBitwiseLogicOperation/orFiller.yml",
        "state_tests/VMTests/vmBitwiseLogicOperation/sgtFiller.yml",
        "state_tests/VMTests/vmBitwiseLogicOperation/sltFiller.yml",
        "state_tests/VMTests/vmBitwiseLogicOperation/xorFiller.yml",
    ],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize("value, expected", CASES)
def test_bitwise(
    state_test: StateTestFiller,
    pre: Alloc,
    value: Bytecode,
    expected: int,
) -> None:
    """Store the result of a comparison or bitwise expression."""
    contract = pre.deploy_contract(
        code=Op.SSTORE(0, value) + Op.STOP, storage={0: SENTINEL}
    )
    tx = Transaction(sender=pre.fund_eoa(), to=contract)
    post = {contract: Account(storage={0: expected})}
    state_test(pre=pre, post=post, tx=tx)


@pytest.mark.ported_from(
    ["state_tests/VMTests/vmBitwiseLogicOperation/byteFiller.yml"],
)
@pytest.mark.valid_from("Cancun")
def test_byte_asm(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Store BYTE 31 of a value plus itself via DUP1."""
    contract = pre.deploy_contract(
        code=Op.SSTORE(key=1, value=Op.ADD(Op.DUP1, Op.BYTE(31, 0x1234523456)))
    )
    tx = Transaction(sender=pre.fund_eoa(), to=contract)
    post = {contract: Account(storage={1: 2 * 0x56})}
    state_test(pre=pre, post=post, tx=tx)


@pytest.mark.ported_from(
    ["state_tests/VMTests/vmBitwiseLogicOperation/byteFiller.yml"],
)
@pytest.mark.valid_from("Cancun")
def test_byte_all(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Store BYTE i of a word whose byte i equals i, for every index."""
    code = sum(
        (Op.SSTORE(i, Op.BYTE(i, BYTE_INDEXES)) for i in range(32)),
        Bytecode(),
    )
    contract = pre.deploy_contract(code=code, storage={0: SENTINEL})
    tx = Transaction(sender=pre.fund_eoa(), to=contract)
    post = {contract: Account(storage={i: i for i in range(32)})}
    state_test(pre=pre, post=post, tx=tx)
