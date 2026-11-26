"""
Test arithmetic opcode results.

The original tests were written by Ori Pomerantz.

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

@manually-enhanced: Do not overwrite. One test per opcode, parametrized on
its operands and expected result. Operands arrive via calldata so every case
of an opcode runs the same contract, whose result slot is pre-set to a
sentinel so that a zero result is still observable. Composite filler
expressions (EQ comparisons, `- 1` / `+ 1` wrappers that made zero results
visible) are split into the plain opcode cases they exercised.
"""

import pytest
from execution_testing import (
    Account,
    Alloc,
    Hash,
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


def neg(value: int) -> int:
    """Return the 256-bit two's complement encoding of `-value`."""
    return -value % 2**256


@pytest.mark.ported_from(
    ["state_tests/VMTests/vmArithmeticTest/addFiller.yml"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "a, b, expected",
    [
        pytest.param(neg(1), neg(1), neg(2), id="neg1_neg1"),
        pytest.param(neg(1), 4, 3, id="neg1_4"),
        pytest.param(neg(1), 1, 0, id="neg1_1"),
        pytest.param(0, 0, 0, id="0_0"),
        pytest.param(1, neg(1), 0, id="1_neg1"),
    ],
)
def test_add(
    state_test: StateTestFiller,
    pre: Alloc,
    a: int,
    b: int,
    expected: int,
) -> None:
    """Store `ADD(a, b)` over a sentinel."""
    contract = pre.deploy_contract(
        code=Op.SSTORE(0, Op.ADD(Op.CALLDATALOAD(0), Op.CALLDATALOAD(32)))
        + Op.STOP,
        storage={0: SENTINEL},
    )
    tx = Transaction(
        sender=pre.fund_eoa(), to=contract, data=Hash(a) + Hash(b)
    )
    post = {contract: Account(storage={0: expected})}
    state_test(pre=pre, post=post, tx=tx)


@pytest.mark.ported_from(
    ["state_tests/VMTests/vmArithmeticTest/addmodFiller.yml"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "a, b, n, expected",
    [
        pytest.param(1, 2, 2, 1, id="1_2_2"),
        pytest.param(neg(1), neg(2), 2, 1, id="neg1_neg2_2"),
        pytest.param(neg(6), 1, 3, 2, id="neg6_1_3"),
        pytest.param(4, 1, neg(3), 5, id="4_1_neg3"),
        pytest.param(neg(1), 0, 5, 0, id="neg1_0_5"),
        pytest.param(neg(1), 1, 5, 1, id="neg1_1_5"),
        pytest.param(neg(1), 2, 5, 2, id="neg1_2_5"),
        pytest.param(neg(1), neg(2), 5, 4, id="neg1_neg2_5"),
        pytest.param(4, 1, 0, 0, id="4_1_0"),
        pytest.param(0, 1, 0, 0, id="0_1_0"),
        pytest.param(1, 0, 0, 0, id="1_0_0"),
        pytest.param(0, 0, 0, 0, id="0_0_0"),
    ],
)
def test_addmod(
    state_test: StateTestFiller,
    pre: Alloc,
    a: int,
    b: int,
    n: int,
    expected: int,
) -> None:
    """Store `ADDMOD(a, b, n)` over a sentinel."""
    contract = pre.deploy_contract(
        code=Op.SSTORE(
            0,
            Op.ADDMOD(
                Op.CALLDATALOAD(0), Op.CALLDATALOAD(32), Op.CALLDATALOAD(64)
            ),
        )
        + Op.STOP,
        storage={0: SENTINEL},
    )
    tx = Transaction(
        sender=pre.fund_eoa(),
        to=contract,
        data=Hash(a) + Hash(b) + Hash(n),
    )
    post = {contract: Account(storage={0: expected})}
    state_test(pre=pre, post=post, tx=tx)


@pytest.mark.ported_from(
    ["state_tests/VMTests/vmArithmeticTest/divFiller.yml"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "a, b, expected",
    [
        pytest.param(
            2,
            0xFEDCBA9876543210FEDCBA9876543210FEDCBA9876543210FEDCBA9876543210,
            0,
            id="2_big",
        ),
        pytest.param(
            0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFBA,
            0x1DAE6076B981DAE6076B981DAE6076B981DAE6076B981DAE6076B981DAE6077,
            137,
            id="boost_bug",
        ),
        pytest.param(5, 2, 2, id="5_2"),
        pytest.param(23, 24, 0, id="23_24"),
        pytest.param(0, 24, 0, id="0_24"),
        pytest.param(1, 1, 1, id="1_1"),
        pytest.param(2, 0, 0, id="2_0"),
        pytest.param(13, 0, 0, id="13_0"),
    ],
)
def test_div(
    state_test: StateTestFiller,
    pre: Alloc,
    a: int,
    b: int,
    expected: int,
) -> None:
    """Store `DIV(a, b)` over a sentinel."""
    contract = pre.deploy_contract(
        code=Op.SSTORE(0, Op.DIV(Op.CALLDATALOAD(0), Op.CALLDATALOAD(32)))
        + Op.STOP,
        storage={0: SENTINEL},
    )
    tx = Transaction(
        sender=pre.fund_eoa(), to=contract, data=Hash(a) + Hash(b)
    )
    post = {contract: Account(storage={0: expected})}
    state_test(pre=pre, post=post, tx=tx)


@pytest.mark.ported_from(
    ["state_tests/VMTests/vmArithmeticTest/expFiller.yml"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "base, exponent, expected",
    [
        pytest.param(2, 2, 4, id="2_2"),
        pytest.param(neg(1), neg(2), 1, id="neg1_neg2"),
        pytest.param(
            0x7FFFFFFF,
            0x7FFFFFFF,
            0xBC8CCCCCCCC888888880000000AAAAAAB00000000FFFFFFFFFFFFFFF7FFFFFFF,
            id="big_big",
        ),
        pytest.param(0, 0x7FFFFFFF, 0, id="0_big"),
        pytest.param(0x7FFFFFFF, 0, 1, id="big_0"),
        pytest.param(257, 1, 257, id="257_1"),
        pytest.param(1, 257, 1, id="1_257"),
        pytest.param(2, 257, 0, id="2_257"),
        pytest.param(0, 0, 1, id="0_0"),
        pytest.param(2, 0x100000000000F, 0, id="2_huge"),
        pytest.param(2, 15, 32768, id="2_15"),
    ],
)
def test_exp(
    state_test: StateTestFiller,
    pre: Alloc,
    base: int,
    exponent: int,
    expected: int,
) -> None:
    """Store `EXP(base, exponent)` over a sentinel."""
    contract = pre.deploy_contract(
        code=Op.SSTORE(0, Op.EXP(Op.CALLDATALOAD(0), Op.CALLDATALOAD(32)))
        + Op.STOP,
        storage={0: SENTINEL},
    )
    tx = Transaction(
        sender=pre.fund_eoa(),
        to=contract,
        data=Hash(base) + Hash(exponent),
    )
    post = {contract: Account(storage={0: expected})}
    state_test(pre=pre, post=post, tx=tx)


@pytest.mark.ported_from(
    [
        "state_tests/VMTests/vmArithmeticTest/modFiller.yml",
        "state_tests/VMTests/vmArithmeticTest/addmodFiller.yml",
        "state_tests/VMTests/vmArithmeticTest/mulmodFiller.yml",
    ],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "a, b, expected",
    [
        pytest.param(2, 3, 2, id="2_3"),
        pytest.param(MAX_UINT, 2, 1, id="max_2"),
        pytest.param(0, MAX_UINT, 0, id="0_max"),
        pytest.param(3, 0, 0, id="3_0"),
        pytest.param(neg(2), 3, 2, id="neg2_3"),
        pytest.param(16, 0, 0, id="16_0"),
        pytest.param(neg(5), 3, 2, id="neg5_3"),
    ],
)
def test_mod(
    state_test: StateTestFiller,
    pre: Alloc,
    a: int,
    b: int,
    expected: int,
) -> None:
    """Store `MOD(a, b)` over a sentinel."""
    contract = pre.deploy_contract(
        code=Op.SSTORE(0, Op.MOD(Op.CALLDATALOAD(0), Op.CALLDATALOAD(32)))
        + Op.STOP,
        storage={0: SENTINEL},
    )
    tx = Transaction(
        sender=pre.fund_eoa(), to=contract, data=Hash(a) + Hash(b)
    )
    post = {contract: Account(storage={0: expected})}
    state_test(pre=pre, post=post, tx=tx)


@pytest.mark.ported_from(
    ["state_tests/VMTests/vmArithmeticTest/mulFiller.yml"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "a, b, expected",
    [
        pytest.param(2, 3, 6, id="2_3"),
        pytest.param(neg(1), neg(1), 1, id="neg1_neg1"),
        pytest.param(0, 23, 0, id="0_23"),
        pytest.param(23, 1, 23, id="23_1"),
        pytest.param(INT_MIN, neg(1), INT_MIN, id="int_min_neg1"),
        pytest.param(INT_MIN, INT_MIN, 0, id="int_min_int_min"),
        pytest.param(INT_MAX, INT_MAX, 1, id="int_max_int_max"),
        pytest.param(
            0x1234567890ABCDEF0FEDCBA0987654321,
            0x1234567890ABCDEF0FEDCBA0987654321,
            0x4B66DC328828BCA88B5309B760EC6BF947034577DB029A3ACEFEA12CD7A44A41,
            id="big_squared",
        ),
        pytest.param(
            0x4B66DC328828BCA88B5309B760EC6BF947034577DB029A3ACEFEA12CD7A44A41,
            0x1234567890ABCDEF0FEDCBA0987654321,
            0x47D0817E4167B1EB4F9FC722B133EF9D7D9A6FB4C2C1C442D000107A5E419561,
            id="big_cubed",
        ),
    ],
)
def test_mul(
    state_test: StateTestFiller,
    pre: Alloc,
    a: int,
    b: int,
    expected: int,
) -> None:
    """Store `MUL(a, b)` over a sentinel."""
    contract = pre.deploy_contract(
        code=Op.SSTORE(0, Op.MUL(Op.CALLDATALOAD(0), Op.CALLDATALOAD(32)))
        + Op.STOP,
        storage={0: SENTINEL},
    )
    tx = Transaction(
        sender=pre.fund_eoa(), to=contract, data=Hash(a) + Hash(b)
    )
    post = {contract: Account(storage={0: expected})}
    state_test(pre=pre, post=post, tx=tx)


@pytest.mark.ported_from(
    ["state_tests/VMTests/vmArithmeticTest/mulmodFiller.yml"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "a, b, n, expected",
    [
        pytest.param(1, 2, 2, 0, id="1_2_2"),
        pytest.param(neg(1), neg(2), 3, 0, id="neg1_neg2_3"),
        pytest.param(neg(5), 1, 3, 2, id="neg5_1_3"),
        pytest.param(5, 1, neg(3), 5, id="5_1_neg3"),
        pytest.param(27, 37, 100, 99, id="27_37_100"),
        pytest.param(INT_MIN, 2, 5, 1, id="int_min_2_5"),
        pytest.param(neg(1), 2, 5, 0, id="neg1_2_5"),
        pytest.param(INT_MAX, 2, 5, 4, id="int_max_2_5"),
        pytest.param(INT_MIN + 1, 2, 5, 3, id="int_min_plus1_2_5"),
        pytest.param(0, 1, 0, 0, id="0_1_0"),
        pytest.param(1, 0, 0, 0, id="1_0_0"),
        pytest.param(0, 0, 0, 0, id="0_0_0"),
        pytest.param(5, 1, 0, 0, id="5_1_0"),
    ],
)
def test_mulmod(
    state_test: StateTestFiller,
    pre: Alloc,
    a: int,
    b: int,
    n: int,
    expected: int,
) -> None:
    """Store `MULMOD(a, b, n)` over a sentinel."""
    contract = pre.deploy_contract(
        code=Op.SSTORE(
            0,
            Op.MULMOD(
                Op.CALLDATALOAD(0), Op.CALLDATALOAD(32), Op.CALLDATALOAD(64)
            ),
        )
        + Op.STOP,
        storage={0: SENTINEL},
    )
    tx = Transaction(
        sender=pre.fund_eoa(),
        to=contract,
        data=Hash(a) + Hash(b) + Hash(n),
    )
    post = {contract: Account(storage={0: expected})}
    state_test(pre=pre, post=post, tx=tx)


@pytest.mark.ported_from(
    ["state_tests/VMTests/vmArithmeticTest/notFiller.yml"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "a, expected",
    [
        pytest.param(
            0x123456789ABCDEF,
            MAX_UINT - 0x123456789ABCDEF,
            id="0x123456789abcdef",
        ),
    ],
)
def test_not(
    state_test: StateTestFiller,
    pre: Alloc,
    a: int,
    expected: int,
) -> None:
    """Store `NOT(a)` over a sentinel."""
    contract = pre.deploy_contract(
        code=Op.SSTORE(0, Op.NOT(Op.CALLDATALOAD(0))) + Op.STOP,
        storage={0: SENTINEL},
    )
    tx = Transaction(sender=pre.fund_eoa(), to=contract, data=Hash(a))
    post = {contract: Account(storage={0: expected})}
    state_test(pre=pre, post=post, tx=tx)


@pytest.mark.ported_from(
    ["state_tests/VMTests/vmArithmeticTest/sdivFiller.yml"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "a, b, expected",
    [
        pytest.param(1, neg(1), neg(1), id="1_neg1"),
        pytest.param(neg(1), 1, neg(1), id="neg1_1"),
        pytest.param(neg(2), neg(4), 0, id="neg2_neg4"),
        pytest.param(4, neg(2), neg(2), id="4_neg2"),
        pytest.param(5, neg(4), neg(1), id="5_neg4"),
        pytest.param(INT_MIN, neg(1), INT_MIN, id="int_min_neg1"),
        pytest.param(INT_MIN, 0, 0, id="int_min_0"),
        pytest.param(neg(1), 25, 0, id="neg1_25"),
        pytest.param(neg(1), neg(1), 1, id="neg1_neg1"),
        pytest.param(neg(3), 0, 0, id="neg3_0"),
        pytest.param(1, 0, 0, id="1_0"),
        pytest.param(neg(9), 5, neg(1), id="neg9_5"),
        pytest.param(neg(INT_MAX), neg(1), INT_MAX, id="neg_int_max_neg1"),
        pytest.param(neg(1), neg(INT_MAX), 0, id="neg1_neg_int_max"),
    ],
)
def test_sdiv(
    state_test: StateTestFiller,
    pre: Alloc,
    a: int,
    b: int,
    expected: int,
) -> None:
    """Store `SDIV(a, b)` over a sentinel."""
    contract = pre.deploy_contract(
        code=Op.SSTORE(0, Op.SDIV(Op.CALLDATALOAD(0), Op.CALLDATALOAD(32)))
        + Op.STOP,
        storage={0: SENTINEL},
    )
    tx = Transaction(
        sender=pre.fund_eoa(), to=contract, data=Hash(a) + Hash(b)
    )
    post = {contract: Account(storage={0: expected})}
    state_test(pre=pre, post=post, tx=tx)


@pytest.mark.ported_from(
    ["state_tests/VMTests/vmArithmeticTest/signextendFiller.yml"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "byte_index, value, expected",
    [
        pytest.param(0x50, 0x126AF4, 0x126AF4, id="invalid_byte"),
        pytest.param(0, 0, 0, id="zero_zero"),
        pytest.param(0, neg(1), neg(1), id="zero_neg1"),
        pytest.param(neg(2), neg(2), neg(2), id="neg2_neg2"),
        pytest.param(neg(1), neg(1), neg(1), id="neg1_neg1"),
        pytest.param(0xF00000000000000001, 0xFF, 0xFF, id="large_ff"),
        pytest.param(neg(1), 0, 0, id="neg1_zero"),
        pytest.param(0, 0x122F6A, 0x6A, id="bit_is_not_set"),
        pytest.param(1, 0x126AF4, 0x6AF4, id="bit_is_not_set_high"),
        pytest.param(
            1,
            0x12FAF4,
            0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFAF4,
            id="bit_is_set_high",
        ),
        pytest.param(
            0x10000000000000001, 0x8000, 0x8000, id="overflow_bytenum"
        ),
        pytest.param(0xF0000000000001, 0xFFFF, 0xFFFF, id="overflow_bytenum2"),
        pytest.param(
            0,
            0x122FF4,
            0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF4,
            id="bit_is_set",
        ),
        pytest.param(31, 1, 1, id="byte31_pos"),
        pytest.param(31, neg(1), neg(1), id="byte31_neg"),
    ],
)
def test_signextend(
    state_test: StateTestFiller,
    pre: Alloc,
    byte_index: int,
    value: int,
    expected: int,
) -> None:
    """Store `SIGNEXTEND(byte_index, value)` over a sentinel."""
    contract = pre.deploy_contract(
        code=Op.SSTORE(
            0, Op.SIGNEXTEND(Op.CALLDATALOAD(0), Op.CALLDATALOAD(32))
        )
        + Op.STOP,
        storage={0: SENTINEL},
    )
    tx = Transaction(
        sender=pre.fund_eoa(),
        to=contract,
        data=Hash(byte_index) + Hash(value),
    )
    post = {contract: Account(storage={0: expected})}
    state_test(pre=pre, post=post, tx=tx)


@pytest.mark.ported_from(
    [
        "state_tests/VMTests/vmArithmeticTest/smodFiller.yml",
        "state_tests/VMTests/vmArithmeticTest/addmodFiller.yml",
        "state_tests/VMTests/vmArithmeticTest/mulmodFiller.yml",
    ],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "a, b, expected",
    [
        pytest.param(2, 3, 2, id="2_3"),
        pytest.param(neg(1), 2, neg(1), id="neg1_2"),
        pytest.param(0, neg(1), 0, id="0_neg1"),
        pytest.param(3, 0, 0, id="3_0"),
        pytest.param(neg(2), 3, neg(2), id="neg2_3"),
        pytest.param(16, 0, 0, id="16_0"),
        pytest.param(neg(5), 3, neg(2), id="neg5_3"),
    ],
)
def test_smod(
    state_test: StateTestFiller,
    pre: Alloc,
    a: int,
    b: int,
    expected: int,
) -> None:
    """Store `SMOD(a, b)` over a sentinel."""
    contract = pre.deploy_contract(
        code=Op.SSTORE(0, Op.SMOD(Op.CALLDATALOAD(0), Op.CALLDATALOAD(32)))
        + Op.STOP,
        storage={0: SENTINEL},
    )
    tx = Transaction(
        sender=pre.fund_eoa(), to=contract, data=Hash(a) + Hash(b)
    )
    post = {contract: Account(storage={0: expected})}
    state_test(pre=pre, post=post, tx=tx)


@pytest.mark.ported_from(
    ["state_tests/VMTests/vmArithmeticTest/subFiller.yml"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "a, b, expected",
    [
        pytest.param(23, 1, 22, id="23_1"),
        pytest.param(2, 3, neg(1), id="2_3"),
        pytest.param(0, 23, neg(23), id="0_23"),
        pytest.param(0, neg(1), 1, id="0_neg1"),
        pytest.param(neg(1), 0, neg(1), id="neg1_0"),
    ],
)
def test_sub(
    state_test: StateTestFiller,
    pre: Alloc,
    a: int,
    b: int,
    expected: int,
) -> None:
    """Store `SUB(a, b)` over a sentinel."""
    contract = pre.deploy_contract(
        code=Op.SSTORE(0, Op.SUB(Op.CALLDATALOAD(0), Op.CALLDATALOAD(32)))
        + Op.STOP,
        storage={0: SENTINEL},
    )
    tx = Transaction(
        sender=pre.fund_eoa(), to=contract, data=Hash(a) + Hash(b)
    )
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
