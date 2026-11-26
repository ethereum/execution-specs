"""
Test comparison and bitwise logic opcode results.

The original tests were written by Ori Pomerantz.

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

@manually-enhanced: Do not overwrite. One test per opcode, parametrized on
its operands and expected result. Operands arrive via calldata so every case
of an opcode runs the same contract, whose result slot is pre-set to a
sentinel so that a zero result is still observable. Operands the fillers
computed in-EVM (`(- 0 2)`, `(sdiv 31 32)`), the raw `DUP1`/`ADD` BYTE case
and the BYTE loop over every index are split into plain opcode cases.
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
SENTINEL = 0x0BAD

COUNTING_NIBBLES = (
    0x0123456789ABCDEF0123456789ABCDEF0123456789ABCDEF0123456789ABCDEF
)
E_NIBBLES = 0xEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEE
E_NIBBLES_ONE_F = (
    0xEEEEEEEEEEEEEEEEEEEEEEEEEEEEEFEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEE
)

# Byte `31 - i` (counted from the most significant byte) holds `2**i`.
BYTE_POWERS_OF_TWO = 0x8040201008040201
# Byte `i` (counted from the most significant byte) holds `i`.
BYTE_INDEXES = (
    0x000102030405060708090A0B0C0D0E0F101112131415161718191A1B1C1D1E1F
)


def neg(value: int) -> int:
    """Return the 256-bit two's complement encoding of `-value`."""
    return -value % 2**256


@pytest.mark.ported_from(
    ["state_tests/VMTests/vmBitwiseLogicOperation/andFiller.yml"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "a, b, expected",
    [
        pytest.param(2, 2, 2, id="2_2"),
        pytest.param(2, 1, 0, id="2_1"),
        pytest.param(3, 1, 1, id="3_1"),
        pytest.param(
            MAX_UINT, COUNTING_NIBBLES, COUNTING_NIBBLES, id="allones_bignum"
        ),
        pytest.param(
            E_NIBBLES_ONE_F, MAX_UINT, E_NIBBLES_ONE_F, id="allones_eefee"
        ),
    ],
)
def test_and(
    state_test: StateTestFiller,
    pre: Alloc,
    a: int,
    b: int,
    expected: int,
) -> None:
    """Store `AND(a, b)` over a sentinel."""
    contract = pre.deploy_contract(
        code=Op.SSTORE(0, Op.AND(Op.CALLDATALOAD(0), Op.CALLDATALOAD(32)))
        + Op.STOP,
        storage={0: SENTINEL},
    )
    tx = Transaction(
        sender=pre.fund_eoa(), to=contract, data=Hash(a) + Hash(b)
    )
    post = {contract: Account(storage={0: expected})}
    state_test(pre=pre, post=post, tx=tx)


@pytest.mark.ported_from(
    ["state_tests/VMTests/vmBitwiseLogicOperation/byteFiller.yml"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "index, value, expected",
    [
        *[
            pytest.param(31 - i, BYTE_POWERS_OF_TWO, 2**i, id=f"{31 - i}_big")
            for i in range(8)
        ],
        pytest.param(0, BYTE_POWERS_OF_TWO, 0, id="00_big"),
        pytest.param(31, 0x1234523456, 0x56, id="31_asm"),
        *[
            pytest.param(i, BYTE_INDEXES, i, id=f"{i:02}_indexes")
            for i in range(32)
        ],
    ],
)
def test_byte(
    state_test: StateTestFiller,
    pre: Alloc,
    index: int,
    value: int,
    expected: int,
) -> None:
    """Store `BYTE(index, value)` over a sentinel."""
    contract = pre.deploy_contract(
        code=Op.SSTORE(0, Op.BYTE(Op.CALLDATALOAD(0), Op.CALLDATALOAD(32)))
        + Op.STOP,
        storage={0: SENTINEL},
    )
    tx = Transaction(
        sender=pre.fund_eoa(), to=contract, data=Hash(index) + Hash(value)
    )
    post = {contract: Account(storage={0: expected})}
    state_test(pre=pre, post=post, tx=tx)


@pytest.mark.ported_from(
    ["state_tests/VMTests/vmBitwiseLogicOperation/eqFiller.yml"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "a, b, expected",
    [
        pytest.param(neg(5), neg(3), 0, id="neg5_neg3"),
        pytest.param(0, 0, 1, id="0_0"),
        pytest.param(neg(1), neg(1), 1, id="neg1_neg1"),
    ],
)
def test_eq(
    state_test: StateTestFiller,
    pre: Alloc,
    a: int,
    b: int,
    expected: int,
) -> None:
    """Store `EQ(a, b)` over a sentinel."""
    contract = pre.deploy_contract(
        code=Op.SSTORE(0, Op.EQ(Op.CALLDATALOAD(0), Op.CALLDATALOAD(32)))
        + Op.STOP,
        storage={0: SENTINEL},
    )
    tx = Transaction(
        sender=pre.fund_eoa(), to=contract, data=Hash(a) + Hash(b)
    )
    post = {contract: Account(storage={0: expected})}
    state_test(pre=pre, post=post, tx=tx)


@pytest.mark.ported_from(
    ["state_tests/VMTests/vmBitwiseLogicOperation/gtFiller.yml"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "a, b, expected",
    [
        pytest.param(neg(2), 0, 1, id="neg2_0"),
        pytest.param(0, neg(2), 0, id="0_neg2"),
        pytest.param(neg(1), 0, 1, id="neg1_0"),
        pytest.param(0, neg(1), 0, id="0_neg1"),
    ],
)
def test_gt(
    state_test: StateTestFiller,
    pre: Alloc,
    a: int,
    b: int,
    expected: int,
) -> None:
    """Store the unsigned `GT(a, b)` over a sentinel."""
    contract = pre.deploy_contract(
        code=Op.SSTORE(0, Op.GT(Op.CALLDATALOAD(0), Op.CALLDATALOAD(32)))
        + Op.STOP,
        storage={0: SENTINEL},
    )
    tx = Transaction(
        sender=pre.fund_eoa(), to=contract, data=Hash(a) + Hash(b)
    )
    post = {contract: Account(storage={0: expected})}
    state_test(pre=pre, post=post, tx=tx)


@pytest.mark.ported_from(
    ["state_tests/VMTests/vmBitwiseLogicOperation/iszeroFiller.yml"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "a, expected",
    [
        pytest.param(neg(1), 0, id="neg1"),
        pytest.param(0, 1, id="0"),
        pytest.param(neg(2), 0, id="neg2"),
    ],
)
def test_iszero(
    state_test: StateTestFiller,
    pre: Alloc,
    a: int,
    expected: int,
) -> None:
    """Store `ISZERO(a)` over a sentinel."""
    contract = pre.deploy_contract(
        code=Op.SSTORE(0, Op.ISZERO(Op.CALLDATALOAD(0))) + Op.STOP,
        storage={0: SENTINEL},
    )
    tx = Transaction(sender=pre.fund_eoa(), to=contract, data=Hash(a))
    post = {contract: Account(storage={0: expected})}
    state_test(pre=pre, post=post, tx=tx)


@pytest.mark.ported_from(
    ["state_tests/VMTests/vmBitwiseLogicOperation/ltFiller.yml"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "a, b, expected",
    [
        pytest.param(neg(2), 0, 0, id="neg2_0"),
        pytest.param(0, neg(2), 1, id="0_neg2"),
        pytest.param(neg(1), 0, 0, id="neg1_0"),
        pytest.param(0, neg(1), 1, id="0_neg1"),
    ],
)
def test_lt(
    state_test: StateTestFiller,
    pre: Alloc,
    a: int,
    b: int,
    expected: int,
) -> None:
    """Store the unsigned `LT(a, b)` over a sentinel."""
    contract = pre.deploy_contract(
        code=Op.SSTORE(0, Op.LT(Op.CALLDATALOAD(0), Op.CALLDATALOAD(32)))
        + Op.STOP,
        storage={0: SENTINEL},
    )
    tx = Transaction(
        sender=pre.fund_eoa(), to=contract, data=Hash(a) + Hash(b)
    )
    post = {contract: Account(storage={0: expected})}
    state_test(pre=pre, post=post, tx=tx)


@pytest.mark.ported_from(
    ["state_tests/VMTests/vmBitwiseLogicOperation/notFiller.yml"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "a, expected",
    [
        pytest.param(0, MAX_UINT, id="0"),
        pytest.param(2, MAX_UINT - 2, id="2"),
        pytest.param(MAX_UINT, 0, id="allones"),
        pytest.param(neg(2), 1, id="neg2"),
        pytest.param(1, MAX_UINT - 1, id="1"),
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
    ["state_tests/VMTests/vmBitwiseLogicOperation/orFiller.yml"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "a, b, expected",
    [
        pytest.param(2, 2, 2, id="2_2"),
        pytest.param(2, 1, 3, id="2_1"),
        pytest.param(3, 1, 3, id="3_1"),
        pytest.param(
            MAX_UINT, COUNTING_NIBBLES, MAX_UINT, id="allones_bignum"
        ),
        pytest.param(E_NIBBLES, MAX_UINT, MAX_UINT, id="allones_1110s"),
        pytest.param(E_NIBBLES_ONE_F, MAX_UINT, MAX_UINT, id="allones_eefee"),
    ],
)
def test_or(
    state_test: StateTestFiller,
    pre: Alloc,
    a: int,
    b: int,
    expected: int,
) -> None:
    """Store `OR(a, b)` over a sentinel."""
    contract = pre.deploy_contract(
        code=Op.SSTORE(0, Op.OR(Op.CALLDATALOAD(0), Op.CALLDATALOAD(32)))
        + Op.STOP,
        storage={0: SENTINEL},
    )
    tx = Transaction(
        sender=pre.fund_eoa(), to=contract, data=Hash(a) + Hash(b)
    )
    post = {contract: Account(storage={0: expected})}
    state_test(pre=pre, post=post, tx=tx)


@pytest.mark.ported_from(
    ["state_tests/VMTests/vmBitwiseLogicOperation/sgtFiller.yml"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "a, b, expected",
    [
        pytest.param(neg(2), 0, 0, id="neg2_0"),
        pytest.param(0, neg(2), 1, id="0_neg2"),
        pytest.param(neg(1), 0, 0, id="neg1_0"),
        pytest.param(0, neg(1), 1, id="0_neg1"),
    ],
)
def test_sgt(
    state_test: StateTestFiller,
    pre: Alloc,
    a: int,
    b: int,
    expected: int,
) -> None:
    """Store the signed `SGT(a, b)` over a sentinel."""
    contract = pre.deploy_contract(
        code=Op.SSTORE(0, Op.SGT(Op.CALLDATALOAD(0), Op.CALLDATALOAD(32)))
        + Op.STOP,
        storage={0: SENTINEL},
    )
    tx = Transaction(
        sender=pre.fund_eoa(), to=contract, data=Hash(a) + Hash(b)
    )
    post = {contract: Account(storage={0: expected})}
    state_test(pre=pre, post=post, tx=tx)


@pytest.mark.ported_from(
    ["state_tests/VMTests/vmBitwiseLogicOperation/sltFiller.yml"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "a, b, expected",
    [
        pytest.param(neg(2), 0, 1, id="neg2_0"),
        pytest.param(0, neg(2), 0, id="0_neg2"),
        pytest.param(neg(1), 0, 1, id="neg1_0"),
        pytest.param(0, neg(1), 0, id="0_neg1"),
    ],
)
def test_slt(
    state_test: StateTestFiller,
    pre: Alloc,
    a: int,
    b: int,
    expected: int,
) -> None:
    """Store the signed `SLT(a, b)` over a sentinel."""
    contract = pre.deploy_contract(
        code=Op.SSTORE(0, Op.SLT(Op.CALLDATALOAD(0), Op.CALLDATALOAD(32)))
        + Op.STOP,
        storage={0: SENTINEL},
    )
    tx = Transaction(
        sender=pre.fund_eoa(), to=contract, data=Hash(a) + Hash(b)
    )
    post = {contract: Account(storage={0: expected})}
    state_test(pre=pre, post=post, tx=tx)


@pytest.mark.ported_from(
    ["state_tests/VMTests/vmBitwiseLogicOperation/xorFiller.yml"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "a, b, expected",
    [
        pytest.param(2, 2, 0, id="2_2"),
        pytest.param(2, 1, 3, id="2_1"),
        pytest.param(3, 1, 2, id="3_1"),
        pytest.param(
            MAX_UINT,
            COUNTING_NIBBLES,
            0xFEDCBA9876543210FEDCBA9876543210FEDCBA9876543210FEDCBA9876543210,
            id="allones_bignum",
        ),
        pytest.param(
            E_NIBBLES,
            MAX_UINT,
            0x1111111111111111111111111111111111111111111111111111111111111111,
            id="allones_1110s",
        ),
        pytest.param(
            E_NIBBLES_ONE_F,
            MAX_UINT,
            0x1111111111111111111111111111101111111111111111111111111111111111,
            id="allones_eefee",
        ),
    ],
)
def test_xor(
    state_test: StateTestFiller,
    pre: Alloc,
    a: int,
    b: int,
    expected: int,
) -> None:
    """Store `XOR(a, b)` over a sentinel."""
    contract = pre.deploy_contract(
        code=Op.SSTORE(0, Op.XOR(Op.CALLDATALOAD(0), Op.CALLDATALOAD(32)))
        + Op.STOP,
        storage={0: SENTINEL},
    )
    tx = Transaction(
        sender=pre.fund_eoa(), to=contract, data=Hash(a) + Hash(b)
    )
    post = {contract: Account(storage={0: expected})}
    state_test(pre=pre, post=post, tx=tx)
