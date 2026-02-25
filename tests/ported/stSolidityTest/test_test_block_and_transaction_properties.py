"""
Ported from:
tests/static/state_tests/stSolidityTest/TestBlockAndTransactionPropertiesFiller.json

contract code:
    push1 0x60
    push1 0x40
    mstore
    push1 0x00
    calldataload
    push29 0x0100000000000000000000000000000000000000000000000000000000
    swap1
    div
    dup1
    push4 0xc0406226
    eq
    push2 0x44
    jumpi
    dup1
    push4 0xe97384dc
    eq
    push2 0x69
    jumpi
    push2 0x42
    jump
    ... (229 more instructions)
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
    ["tests/static/state_tests/stSolidityTest/TestBlockAndTransactionPropertiesFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_test_block_and_transaction_properties(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test ported from static filler."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = Address("0x7f3f285918d9b5e764174551e10b7539b97bbb27")
    contract = Address("0xad24d212286ab785efe98ab6f5a3ecde73054ee5")

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=9223372036854775807,
    )

    pre[sender] = Account(balance=0x5f5e100, nonce=0)
    pre[contract] = Account(
        balance=0x186a0,
        nonce=0,
        code=(
        Op.PUSH1[0x60] + Op.PUSH1[0x40] + Op.MSTORE + Op.PUSH1[0x0]
        + Op.CALLDATALOAD
        + Op.PUSH29[0x100000000000000000000000000000000000000000000000000000000]
        + Op.SWAP1 + Op.DIV + Op.DUP1 + Op.PUSH4[0xc0406226] + Op.EQ + Op.PUSH2[0x44]
        + Op.JUMPI + Op.DUP1 + Op.PUSH4[0xe97384dc] + Op.EQ + Op.PUSH2[0x69]
        + Op.JUMPI + Op.PUSH2[0x42] + Op.JUMP + Op.JUMPDEST + Op.STOP + Op.JUMPDEST
        + Op.PUSH2[0x51] + Op.PUSH1[0x4] + Op.DUP1 + Op.POP + Op.POP + Op.PUSH2[0x8e]
        + Op.JUMP + Op.JUMPDEST + Op.PUSH1[0x40] + Op.MLOAD + Op.DUP1 + Op.DUP3
        + Op.ISZERO + Op.ISZERO + Op.DUP2 + Op.MSTORE + Op.PUSH1[0x20] + Op.ADD
        + Op.SWAP2 + Op.POP + Op.POP + Op.PUSH1[0x40] + Op.MLOAD + Op.DUP1 + Op.SWAP2
        + Op.SUB + Op.SWAP1 + Op.RETURN + Op.JUMPDEST + Op.PUSH2[0x76] + Op.PUSH1[0x4]
        + Op.DUP1 + Op.POP + Op.POP + Op.PUSH2[0xc9] + Op.JUMP + Op.JUMPDEST
        + Op.PUSH1[0x40] + Op.MLOAD + Op.DUP1 + Op.DUP3 + Op.ISZERO + Op.ISZERO
        + Op.DUP2 + Op.MSTORE + Op.PUSH1[0x20] + Op.ADD + Op.SWAP2 + Op.POP + Op.POP
        + Op.PUSH1[0x40] + Op.MLOAD + Op.DUP1 + Op.SWAP2 + Op.SUB + Op.SWAP1
        + Op.RETURN + Op.JUMPDEST + Op.PUSH1[0x0] + Op.PUSH2[0x98] + Op.PUSH2[0xc9]
        + Op.JUMP + Op.JUMPDEST + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH2[0x100]
        + Op.EXP + Op.DUP2 + Op.SLOAD + Op.DUP2 + Op.PUSH1[0xff] + Op.MUL + Op.NOT
        + Op.AND + Op.SWAP1 + Op.DUP4 + Op.MUL + Op.OR + Op.SWAP1 + Op.SSTORE + Op.POP
        + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.SWAP1 + Op.SLOAD + Op.SWAP1
        + Op.PUSH2[0x100] + Op.EXP + Op.SWAP1 + Op.DIV + Op.PUSH1[0xff] + Op.AND
        + Op.SWAP1 + Op.POP + Op.PUSH2[0xc6] + Op.JUMP + Op.JUMPDEST + Op.SWAP1
        + Op.JUMP + Op.JUMPDEST + Op.PUSH1[0x0] + Op.PUSH1[0x1] + Op.SWAP1 + Op.POP
        + Op.DUP1 + Op.POP + Op.PUSH20[0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba]
        + Op.COINBASE + Op.PUSH20[0xffffffffffffffffffffffffffffffffffffffff] + Op.AND
        + Op.EQ + Op.ISZERO + Op.ISZERO + Op.PUSH2[0x10d] + Op.JUMPI + Op.PUSH1[0x0]
        + Op.SWAP1 + Op.POP + Op.PUSH2[0x1f7] + Op.JUMP + Op.JUMPDEST
        + Op.PUSH4[0x2b8feb0] + Op.PREVRANDAO + Op.EQ + Op.ISZERO + Op.ISZERO
        + Op.PUSH2[0x123] + Op.JUMPI + Op.PUSH1[0x0] + Op.SWAP1 + Op.POP
        + Op.PUSH2[0x1f7] + Op.JUMP + Op.JUMPDEST + Op.PUSH8[0x7fffffffffffffff]
        + Op.GASLIMIT + Op.EQ + Op.ISZERO + Op.ISZERO + Op.PUSH2[0x13d] + Op.JUMPI
        + Op.PUSH1[0x0] + Op.SWAP1 + Op.POP + Op.PUSH2[0x1f7] + Op.JUMP + Op.JUMPDEST
        + Op.PUSH1[0x78] + Op.NUMBER + Op.EQ + Op.ISZERO + Op.ISZERO + Op.PUSH2[0x150]
        + Op.JUMPI + Op.PUSH1[0x0] + Op.SWAP1 + Op.POP + Op.PUSH2[0x1f7] + Op.JUMP
        + Op.JUMPDEST + Op.PUSH1[0x78] + Op.BLOCKHASH + Op.POP + Op.TIMESTAMP + Op.POP
        + Op.GAS + Op.POP + Op.PUSH20[0x7f3f285918d9b5e764174551e10b7539b97bbb27]
        + Op.CALLER + Op.PUSH20[0xffffffffffffffffffffffffffffffffffffffff] + Op.AND
        + Op.EQ + Op.ISZERO + Op.ISZERO + Op.PUSH2[0x194] + Op.JUMPI + Op.PUSH1[0x0]
        + Op.SWAP1 + Op.POP + Op.PUSH2[0x1f7] + Op.JUMP + Op.JUMPDEST + Op.PUSH1[0x64]
        + Op.CALLVALUE + Op.EQ + Op.ISZERO + Op.ISZERO + Op.PUSH2[0x1a7] + Op.JUMPI
        + Op.PUSH1[0x0] + Op.SWAP1 + Op.POP + Op.PUSH2[0x1f7] + Op.JUMP + Op.JUMPDEST
        + Op.PUSH1[0x1] + Op.GASPRICE + Op.EQ + Op.ISZERO + Op.ISZERO
        + Op.PUSH2[0x1ba] + Op.JUMPI + Op.PUSH1[0x0] + Op.SWAP1 + Op.POP
        + Op.PUSH2[0x1f7] + Op.JUMP + Op.JUMPDEST
        + Op.PUSH20[0x7f3f285918d9b5e764174551e10b7539b97bbb27] + Op.ORIGIN
        + Op.PUSH20[0xffffffffffffffffffffffffffffffffffffffff] + Op.AND + Op.EQ
        + Op.ISZERO + Op.ISZERO + Op.PUSH2[0x1f6] + Op.JUMPI + Op.PUSH1[0x0]
        + Op.SWAP1 + Op.POP + Op.PUSH2[0x1f7] + Op.JUMP + Op.JUMPDEST + Op.JUMPDEST
        + Op.SWAP1 + Op.JUMP
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
        value=100,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)
