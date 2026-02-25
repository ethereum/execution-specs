"""
Ported from:
tests/static/state_tests/stSolidityTest/TestKeywordsFiller.json

contract code:
    push29 0x0100000000000000000000000000000000000000000000000000000000
    push1 0x00
    calldataload
    div
    push4 0x380e4396
    dup2
    eq
    push1 0x37
    jumpi
    dup1
    push4 0xc0406226
    eq
    push1 0x47
    jumpi
    stop
    jumpdest
    push1 0x3d
    push1 0x84
    jump
    jumpdest
    ... (136 more instructions)
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
    ["tests/static/state_tests/stSolidityTest/TestKeywordsFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_test_keywords(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test ported from static filler."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = Address("0x7f3f285918d9b5e764174551e10b7539b97bbb27")
    contract = Address("0xe7dcb339943a6db535ffe618ec32d1e4e5a50f37")

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=100000000,
    )

    pre[sender] = Account(balance=0x5f5e100, nonce=0)
    pre[contract] = Account(
        balance=0x186a0,
        nonce=0,
        code=(
        Op.PUSH29[0x100000000000000000000000000000000000000000000000000000000]
        + Op.PUSH1[0x0] + Op.CALLDATALOAD + Op.DIV + Op.PUSH4[0x380e4396] + Op.DUP2
        + Op.EQ + Op.PUSH1[0x37] + Op.JUMPI + Op.DUP1 + Op.PUSH4[0xc0406226] + Op.EQ
        + Op.PUSH1[0x47] + Op.JUMPI + Op.STOP + Op.JUMPDEST + Op.PUSH1[0x3d]
        + Op.PUSH1[0x84] + Op.JUMP + Op.JUMPDEST + Op.DUP1 + Op.PUSH1[0x0] + Op.MSTORE
        + Op.PUSH1[0x20] + Op.PUSH1[0x0] + Op.RETURN + Op.JUMPDEST + Op.PUSH1[0x4d]
        + Op.PUSH1[0x57] + Op.JUMP + Op.JUMPDEST + Op.DUP1 + Op.PUSH1[0x0] + Op.MSTORE
        + Op.PUSH1[0x20] + Op.PUSH1[0x0] + Op.RETURN + Op.JUMPDEST + Op.PUSH1[0x0]
        + Op.PUSH1[0x5f] + Op.PUSH1[0x84] + Op.JUMP + Op.JUMPDEST + Op.PUSH1[0x0]
        + Op.PUSH1[0x0] + Op.PUSH2[0x100] + Op.EXP + Op.DUP2 + Op.SLOAD + Op.DUP2
        + Op.PUSH1[0xff] + Op.MUL + Op.NOT + Op.AND + Op.SWAP1 + Op.DUP4 + Op.MUL
        + Op.OR + Op.SWAP1 + Op.SSTORE + Op.POP + Op.PUSH1[0xff] + Op.PUSH1[0x1]
        + Op.PUSH1[0x0] + Op.SLOAD + Op.DIV + Op.AND + Op.SWAP1 + Op.POP + Op.SWAP1
        + Op.JUMP + Op.JUMPDEST + Op.PUSH1[0x0] + Op.DUP1 + Op.DUP2 + Op.PUSH1[0x1]
        + Op.ISZERO + Op.PUSH1[0xcd] + Op.JUMPI + Op.JUMPDEST + Op.PUSH1[0xa]
        + Op.DUP3 + Op.SLT + Op.ISZERO + Op.PUSH1[0xa1] + Op.JUMPI + Op.PUSH1[0x1]
        + Op.SWAP1 + Op.SWAP2 + Op.ADD + Op.SWAP1 + Op.PUSH1[0x8f] + Op.JUMP
        + Op.JUMPDEST + Op.DUP2 + Op.PUSH1[0xa] + Op.EQ + Op.PUSH1[0xac] + Op.JUMPI
        + Op.PUSH1[0xc9] + Op.JUMP + Op.JUMPDEST + Op.POP + Op.PUSH1[0xa]
        + Op.JUMPDEST + Op.PUSH1[0x0] + Op.DUP2 + Op.PUSH1[0xff] + Op.AND + Op.GT
        + Op.ISZERO + Op.PUSH1[0xc8] + Op.JUMPI + Op.PUSH1[0x1] + Op.SWAP2 + Op.DUP3
        + Op.SWAP1 + Op.SUB + Op.SWAP2 + Op.SWAP1 + Op.SUB + Op.PUSH1[0xb0] + Op.JUMP
        + Op.JUMPDEST + Op.JUMPDEST + Op.PUSH1[0xd5] + Op.JUMP + Op.JUMPDEST
        + Op.PUSH1[0x0] + Op.SWAP3 + Op.POP + Op.PUSH1[0xed] + Op.JUMP + Op.JUMPDEST
        + Op.DUP2 + Op.PUSH1[0x0] + Op.EQ + Op.PUSH1[0xe0] + Op.JUMPI + Op.PUSH1[0xe8]
        + Op.JUMP + Op.JUMPDEST + Op.PUSH1[0x1] + Op.SWAP3 + Op.POP + Op.PUSH1[0xed]
        + Op.JUMP + Op.JUMPDEST + Op.PUSH1[0x0] + Op.SWAP3 + Op.POP + Op.JUMPDEST
        + Op.POP + Op.POP + Op.SWAP1 + Op.JUMP
    ),
    )

    tx = Transaction(
        secret_key=Hash(
            "0xa2333eef5630066b928dea5fd85a239f511b5b067d1441ee7ac290d0122b917b"
        ),
        to=contract,
        data=bytes.fromhex("c0406226"),
        gas_limit=350000,
        gas_price=10,
        nonce=0,
        value=1,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)
