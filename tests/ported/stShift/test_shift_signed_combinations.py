"""
https://github.com/ethereum/tests/issues/564

Ported from:
tests/static/state_tests/stShift/shiftSignedCombinationsFiller.yml

contract code:
    push1 0xff
    push1 0x00
    mstore
    push1 0x80
    push1 0x00
    push1 0x20
    mul
    push2 0x2774
    add
    mstore
    push2 0x8000
    push1 0x01
    push1 0x20
    mul
    push2 0x2774
    add
    mstore
    push4 0x80000000
    push1 0x02
    push1 0x20
    ... (477 more instructions)
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
    ["tests/static/state_tests/stShift/shiftSignedCombinationsFiller.yml"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.valid_until("Prague")
@pytest.mark.pre_alloc_mutable
def test_shift_signed_combinations(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """https://github.com/ethereum/tests/issues/564."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = Address("0xebaf50debf10e08302fe4280c32df010463ca297")
    contract = Address("0x6c08b7236ee4784e5499b9a576902679d8f863d5")

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=100000000,
    )

    pre[contract] = Account(
        balance=0xde0b6b3a7640000,
        nonce=0,
        code=(
        Op.PUSH1[0xff] + Op.PUSH1[0x0] + Op.MSTORE + Op.PUSH1[0x80] + Op.PUSH1[0x0]
        + Op.PUSH1[0x20] + Op.MUL + Op.PUSH2[0x2774] + Op.ADD + Op.MSTORE
        + Op.PUSH2[0x8000] + Op.PUSH1[0x1] + Op.PUSH1[0x20] + Op.MUL
        + Op.PUSH2[0x2774] + Op.ADD + Op.MSTORE + Op.PUSH4[0x80000000] + Op.PUSH1[0x2]
        + Op.PUSH1[0x20] + Op.MUL + Op.PUSH2[0x2774] + Op.ADD + Op.MSTORE
        + Op.PUSH8[0x8000000000000000] + Op.PUSH1[0x3] + Op.PUSH1[0x20] + Op.MUL
        + Op.PUSH2[0x2774] + Op.ADD + Op.MSTORE
        + Op.PUSH16[0x80000000000000000000000000000000] + Op.PUSH1[0x4]
        + Op.PUSH1[0x20] + Op.MUL + Op.PUSH2[0x2774] + Op.ADD + Op.MSTORE
        + Op.PUSH32[0x8000000000000000000000000000000000000000000000000000000000000000]
        + Op.PUSH1[0x5] + Op.PUSH1[0x20] + Op.MUL + Op.PUSH2[0x2774] + Op.ADD
        + Op.MSTORE + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x20] + Op.MUL
        + Op.PUSH2[0x4e84] + Op.ADD + Op.MSTORE + Op.PUSH1[0x1] + Op.PUSH1[0x1]
        + Op.PUSH1[0x20] + Op.MUL + Op.PUSH2[0x4e84] + Op.ADD + Op.MSTORE
        + Op.PUSH1[0x2] + Op.PUSH1[0x2] + Op.PUSH1[0x20] + Op.MUL + Op.PUSH2[0x4e84]
        + Op.ADD + Op.MSTORE + Op.PUSH1[0x5] + Op.PUSH1[0x3] + Op.PUSH1[0x20] + Op.MUL
        + Op.PUSH2[0x2774] + Op.ADD + Op.MSTORE + Op.PUSH1[0xfe] + Op.PUSH1[0x4]
        + Op.PUSH1[0x20] + Op.MUL + Op.PUSH2[0x4e84] + Op.ADD + Op.MSTORE
        + Op.PUSH1[0xff] + Op.PUSH1[0x5] + Op.PUSH1[0x20] + Op.MUL + Op.PUSH2[0x4e84]
        + Op.ADD + Op.MSTORE + Op.PUSH2[0x100] + Op.PUSH1[0x6] + Op.PUSH1[0x20]
        + Op.MUL + Op.PUSH2[0x4e84] + Op.ADD + Op.MSTORE + Op.PUSH2[0x101]
        + Op.PUSH1[0x7] + Op.PUSH1[0x20] + Op.MUL + Op.PUSH2[0x4e84] + Op.ADD
        + Op.MSTORE
        + Op.PUSH32[0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff]
        + Op.PUSH1[0x8] + Op.PUSH1[0x20] + Op.MUL + Op.PUSH2[0x4e84] + Op.ADD
        + Op.MSTORE
        + Op.PUSH32[0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffe]
        + Op.PUSH1[0x9] + Op.PUSH1[0x20] + Op.MUL + Op.PUSH2[0x4e84] + Op.ADD
        + Op.MSTORE
        + Op.PUSH32[0x8000000000000000000000000000000000000000000000000000000000000000]
        + Op.PUSH1[0xa] + Op.PUSH1[0x20] + Op.MUL + Op.PUSH2[0x4e84] + Op.ADD
        + Op.MSTORE
        + Op.PUSH32[0xa000000000000000000000000000000000000000000000000000000000000000]
        + Op.PUSH1[0xb] + Op.PUSH1[0x20] + Op.MUL + Op.PUSH2[0x4e84] + Op.ADD
        + Op.MSTORE
        + Op.PUSH32[0x5555555555555555555555555555555555555555555555555555555555555555]
        + Op.PUSH1[0xc] + Op.PUSH1[0x20] + Op.MUL + Op.PUSH2[0x4e84] + Op.ADD
        + Op.MSTORE
        + Op.PUSH32[0xaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa]
        + Op.PUSH1[0xd] + Op.PUSH1[0x20] + Op.MUL + Op.PUSH2[0x4e84] + Op.ADD
        + Op.MSTORE + Op.PUSH1[0x0] + Op.PUSH1[0x20] + Op.MSTORE + Op.JUMPDEST
        + Op.PUSH1[0x6] + Op.PUSH1[0x20] + Op.MLOAD + Op.LT + Op.ISZERO
        + Op.PUSH2[0x40d] + Op.JUMPI + Op.PUSH1[0x0] + Op.PUSH1[0x40] + Op.MSTORE
        + Op.JUMPDEST + Op.PUSH1[0xe] + Op.PUSH1[0x40] + Op.MLOAD + Op.LT + Op.ISZERO
        + Op.PUSH2[0x3ff] + Op.JUMPI + Op.PUSH1[0x0] + Op.MLOAD + Op.PUSH1[0x1]
        + Op.ADD + Op.PUSH1[0x0] + Op.MSTORE + Op.PUSH4[0x1000001d] + Op.PUSH1[0x0]
        + Op.MLOAD + Op.SSTORE + Op.PUSH1[0x0] + Op.MLOAD + Op.PUSH1[0x1] + Op.ADD
        + Op.PUSH1[0x0] + Op.MSTORE + Op.PUSH1[0x0] + Op.PUSH1[0x20] + Op.MLOAD
        + Op.PUSH1[0x20] + Op.MUL + Op.PUSH2[0x2774] + Op.ADD + Op.MLOAD + Op.EQ
        + Op.PUSH2[0x24c] + Op.JUMPI + Op.PUSH1[0x20] + Op.MLOAD + Op.PUSH1[0x20]
        + Op.MUL + Op.PUSH2[0x2774] + Op.ADD + Op.MLOAD + Op.PUSH1[0x0] + Op.MLOAD
        + Op.SSTORE + Op.PUSH2[0x253] + Op.JUMP + Op.JUMPDEST + Op.PUSH1[0x80]
        + Op.PUSH1[0x0] + Op.MLOAD + Op.SSTORE + Op.JUMPDEST + Op.PUSH1[0x0]
        + Op.MLOAD + Op.PUSH1[0x1] + Op.ADD + Op.PUSH1[0x0] + Op.MSTORE
        + Op.PUSH1[0x0] + Op.PUSH1[0x40] + Op.MLOAD + Op.PUSH1[0x20] + Op.MUL
        + Op.PUSH2[0x4e84] + Op.ADD + Op.MLOAD + Op.EQ + Op.PUSH2[0x282] + Op.JUMPI
        + Op.PUSH1[0x40] + Op.MLOAD + Op.PUSH1[0x20] + Op.MUL + Op.PUSH2[0x4e84]
        + Op.ADD + Op.MLOAD + Op.PUSH1[0x0] + Op.MLOAD + Op.SSTORE + Op.PUSH2[0x289]
        + Op.JUMP + Op.JUMPDEST + Op.PUSH1[0x80] + Op.PUSH1[0x0] + Op.MLOAD
        + Op.SSTORE + Op.JUMPDEST + Op.PUSH1[0x0] + Op.MLOAD + Op.PUSH1[0x1] + Op.ADD
        + Op.PUSH1[0x0] + Op.MSTORE + Op.PUSH1[0x40] + Op.MLOAD + Op.PUSH1[0x20]
        + Op.MUL + Op.PUSH2[0x4e84] + Op.ADD + Op.MLOAD + Op.PUSH1[0x20] + Op.MLOAD
        + Op.PUSH1[0x20] + Op.MUL + Op.PUSH2[0x2774] + Op.ADD + Op.MLOAD + Op.SAR
        + Op.PUSH1[0x0] + Op.MLOAD + Op.SSTORE + Op.PUSH1[0x0] + Op.MLOAD
        + Op.PUSH1[0x1] + Op.ADD + Op.PUSH1[0x0] + Op.MSTORE + Op.PUSH4[0x1000001b]
        + Op.PUSH1[0x0] + Op.MLOAD + Op.SSTORE + Op.PUSH1[0x0] + Op.MLOAD
        + Op.PUSH1[0x1] + Op.ADD + Op.PUSH1[0x0] + Op.MSTORE + Op.PUSH1[0x0]
        + Op.PUSH1[0x20] + Op.MLOAD + Op.PUSH1[0x20] + Op.MUL + Op.PUSH2[0x2774]
        + Op.ADD + Op.MLOAD + Op.EQ + Op.PUSH2[0x2ee] + Op.JUMPI + Op.PUSH1[0x20]
        + Op.MLOAD + Op.PUSH1[0x20] + Op.MUL + Op.PUSH2[0x2774] + Op.ADD + Op.MLOAD
        + Op.PUSH1[0x0] + Op.MLOAD + Op.SSTORE + Op.PUSH2[0x2f5] + Op.JUMP
        + Op.JUMPDEST + Op.PUSH1[0x80] + Op.PUSH1[0x0] + Op.MLOAD + Op.SSTORE
        + Op.JUMPDEST + Op.PUSH1[0x0] + Op.MLOAD + Op.PUSH1[0x1] + Op.ADD
        + Op.PUSH1[0x0] + Op.MSTORE + Op.PUSH1[0x0] + Op.PUSH1[0x40] + Op.MLOAD
        + Op.PUSH1[0x20] + Op.MUL + Op.PUSH2[0x4e84] + Op.ADD + Op.MLOAD + Op.EQ
        + Op.PUSH2[0x324] + Op.JUMPI + Op.PUSH1[0x40] + Op.MLOAD + Op.PUSH1[0x20]
        + Op.MUL + Op.PUSH2[0x4e84] + Op.ADD + Op.MLOAD + Op.PUSH1[0x0] + Op.MLOAD
        + Op.SSTORE + Op.PUSH2[0x32b] + Op.JUMP + Op.JUMPDEST + Op.PUSH1[0x80]
        + Op.PUSH1[0x0] + Op.MLOAD + Op.SSTORE + Op.JUMPDEST + Op.PUSH1[0x0]
        + Op.MLOAD + Op.PUSH1[0x1] + Op.ADD + Op.PUSH1[0x0] + Op.MSTORE
        + Op.PUSH1[0x40] + Op.MLOAD + Op.PUSH1[0x20] + Op.MUL + Op.PUSH2[0x4e84]
        + Op.ADD + Op.MLOAD + Op.PUSH1[0x20] + Op.MLOAD + Op.PUSH1[0x20] + Op.MUL
        + Op.PUSH2[0x2774] + Op.ADD + Op.MLOAD + Op.SHL + Op.PUSH1[0x0] + Op.MLOAD
        + Op.SSTORE + Op.PUSH1[0x0] + Op.MLOAD + Op.PUSH1[0x1] + Op.ADD
        + Op.PUSH1[0x0] + Op.MSTORE + Op.PUSH4[0x1000001c] + Op.PUSH1[0x0] + Op.MLOAD
        + Op.SSTORE + Op.PUSH1[0x0] + Op.MLOAD + Op.PUSH1[0x1] + Op.ADD
        + Op.PUSH1[0x0] + Op.MSTORE + Op.PUSH1[0x0] + Op.PUSH1[0x20] + Op.MLOAD
        + Op.PUSH1[0x20] + Op.MUL + Op.PUSH2[0x2774] + Op.ADD + Op.MLOAD + Op.EQ
        + Op.PUSH2[0x390] + Op.JUMPI + Op.PUSH1[0x20] + Op.MLOAD + Op.PUSH1[0x20]
        + Op.MUL + Op.PUSH2[0x2774] + Op.ADD + Op.MLOAD + Op.PUSH1[0x0] + Op.MLOAD
        + Op.SSTORE + Op.PUSH2[0x397] + Op.JUMP + Op.JUMPDEST + Op.PUSH1[0x80]
        + Op.PUSH1[0x0] + Op.MLOAD + Op.SSTORE + Op.JUMPDEST + Op.PUSH1[0x0]
        + Op.MLOAD + Op.PUSH1[0x1] + Op.ADD + Op.PUSH1[0x0] + Op.MSTORE
        + Op.PUSH1[0x0] + Op.PUSH1[0x40] + Op.MLOAD + Op.PUSH1[0x20] + Op.MUL
        + Op.PUSH2[0x4e84] + Op.ADD + Op.MLOAD + Op.EQ + Op.PUSH2[0x3c6] + Op.JUMPI
        + Op.PUSH1[0x40] + Op.MLOAD + Op.PUSH1[0x20] + Op.MUL + Op.PUSH2[0x4e84]
        + Op.ADD + Op.MLOAD + Op.PUSH1[0x0] + Op.MLOAD + Op.SSTORE + Op.PUSH2[0x3cd]
        + Op.JUMP + Op.JUMPDEST + Op.PUSH1[0x80] + Op.PUSH1[0x0] + Op.MLOAD
        + Op.SSTORE + Op.JUMPDEST + Op.PUSH1[0x0] + Op.MLOAD + Op.PUSH1[0x1] + Op.ADD
        + Op.PUSH1[0x0] + Op.MSTORE + Op.PUSH1[0x40] + Op.MLOAD + Op.PUSH1[0x20]
        + Op.MUL + Op.PUSH2[0x4e84] + Op.ADD + Op.MLOAD + Op.PUSH1[0x20] + Op.MLOAD
        + Op.PUSH1[0x20] + Op.MUL + Op.PUSH2[0x2774] + Op.ADD + Op.MLOAD + Op.SHR
        + Op.PUSH1[0x0] + Op.MLOAD + Op.SSTORE + Op.PUSH1[0x40] + Op.MLOAD
        + Op.PUSH1[0x1] + Op.ADD + Op.PUSH1[0x40] + Op.MSTORE + Op.PUSH2[0x200]
        + Op.JUMP + Op.JUMPDEST + Op.PUSH1[0x20] + Op.MLOAD + Op.PUSH1[0x1] + Op.ADD
        + Op.PUSH1[0x20] + Op.MSTORE + Op.PUSH2[0x1ef] + Op.JUMP + Op.JUMPDEST
        + Op.STOP + Op.STOP
    ),
    )
    pre[sender] = Account(balance=0xde0b6b3a7640000, nonce=0)

    tx = Transaction(
        secret_key=Hash(
            "0xe04d1ac7ddda0c98397d56a0b501e960d4cd325a39286919ac23c1a07009a869"
        ),
        to=contract,
        data=b"",
        gas_limit=80000000,
        gas_price=10,
        nonce=0,
        value=1,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)
