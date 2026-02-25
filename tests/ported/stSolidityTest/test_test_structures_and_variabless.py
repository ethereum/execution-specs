"""
Ported from:
tests/static/state_tests/stSolidityTest/TestStructuresAndVariablessFiller.json

contract code:
    push29 0x0100000000000000000000000000000000000000000000000000000000
    push1 0x00
    calldataload
    div
    push4 0x2a9afb83
    dup2
    eq
    push2 0x39
    jumpi
    dup1
    push4 0xc0406226
    eq
    push2 0x4b
    jumpi
    stop
    jumpdest
    push2 0x41
    push2 0x5d
    jump
    jumpdest
    ... (219 more instructions)
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
    ["tests/static/state_tests/stSolidityTest/TestStructuresAndVariablessFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_test_structures_and_variabless(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test ported from static filler."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = Address("0xd96ed4431b417993ab4f4d4a656959d13c66e1dc")
    contract = Address("0x53d3dbdfd3ae109712a4771f7f37a6b1cda7b864")

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=9223372036854775807,
    )

    pre[contract] = Account(
        balance=0x186a0,
        nonce=0,
        code=(
        Op.PUSH29[0x100000000000000000000000000000000000000000000000000000000]
        + Op.PUSH1[0x0] + Op.CALLDATALOAD + Op.DIV + Op.PUSH4[0x2a9afb83] + Op.DUP2
        + Op.EQ + Op.PUSH2[0x39] + Op.JUMPI + Op.DUP1 + Op.PUSH4[0xc0406226] + Op.EQ
        + Op.PUSH2[0x4b] + Op.JUMPI + Op.STOP + Op.JUMPDEST + Op.PUSH2[0x41]
        + Op.PUSH2[0x5d] + Op.JUMP + Op.JUMPDEST + Op.DUP1 + Op.PUSH1[0x0] + Op.MSTORE
        + Op.PUSH1[0x20] + Op.PUSH1[0x0] + Op.RETURN + Op.JUMPDEST + Op.PUSH2[0x53]
        + Op.PUSH2[0x16c] + Op.JUMP + Op.JUMPDEST + Op.DUP1 + Op.PUSH1[0x0]
        + Op.MSTORE + Op.PUSH1[0x20] + Op.PUSH1[0x0] + Op.RETURN + Op.JUMPDEST
        + Op.PUSH1[0x1] + Op.PUSH1[0xff] + Op.DUP2 + Op.SLOAD + Op.EQ + Op.ISZERO
        + Op.PUSH2[0x6e] + Op.JUMPI + Op.PUSH2[0x76] + Op.JUMP + Op.JUMPDEST + Op.POP
        + Op.PUSH1[0x0] + Op.PUSH2[0x169] + Op.JUMP + Op.JUMPDEST + Op.PUSH1[0x1]
        + Op.SLOAD + Op.PUSH1[0x3] + Op.SLOAD + Op.EQ + Op.ISZERO + Op.PUSH2[0x87]
        + Op.JUMPI + Op.PUSH2[0x8f] + Op.JUMP + Op.JUMPDEST + Op.POP + Op.PUSH1[0x0]
        + Op.PUSH2[0x169] + Op.JUMP + Op.JUMPDEST
        + Op.PUSH20[0xd96ed4431b417993ab4f4d4a656959d13c66e1dc]
        + Op.PUSH20[0xffffffffffffffffffffffffffffffffffffffff] + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.SLOAD + Op.DIV + Op.DUP2 + Op.AND + Op.AND + Op.EQ
        + Op.ISZERO + Op.PUSH2[0xcd] + Op.JUMPI + Op.PUSH2[0xd5] + Op.JUMP
        + Op.JUMPDEST + Op.POP + Op.PUSH1[0x0] + Op.PUSH2[0x169] + Op.JUMP
        + Op.JUMPDEST
        + Op.PUSH32[0x676c6f62616c2064617461203332206c656e67746820737472696e6700000000]
        + Op.PUSH1[0x4] + Op.SLOAD + Op.EQ + Op.ISZERO + Op.PUSH2[0x104] + Op.JUMPI
        + Op.PUSH2[0x10c] + Op.JUMP + Op.JUMPDEST + Op.POP + Op.PUSH1[0x0]
        + Op.PUSH2[0x169] + Op.JUMP + Op.JUMPDEST + Op.PUSH1[0x5] + Op.PUSH1[0x0]
        + Op.DUP1 + Op.DUP2 + Op.MSTORE + Op.PUSH1[0x20] + Op.ADD + Op.SWAP1 + Op.DUP2
        + Op.MSTORE + Op.PUSH1[0x20] + Op.ADD + Op.PUSH1[0x0] + Op.SHA3
        + Op.PUSH1[0x0] + Op.SWAP1 + Op.SLOAD + Op.SWAP1 + Op.PUSH2[0x100] + Op.EXP
        + Op.SWAP1 + Op.DIV + Op.PUSH20[0xffffffffffffffffffffffffffffffffffffffff]
        + Op.AND + Op.PUSH20[0xd96ed4431b417993ab4f4d4a656959d13c66e1dc] + Op.EQ
        + Op.ISZERO + Op.PUSH2[0x160] + Op.JUMPI + Op.PUSH2[0x168] + Op.JUMP
        + Op.JUMPDEST + Op.POP + Op.PUSH1[0x0] + Op.PUSH2[0x169] + Op.JUMP
        + Op.JUMPDEST + Op.JUMPDEST + Op.SWAP1 + Op.JUMP + Op.JUMPDEST + Op.PUSH1[0x0]
        + Op.PUSH1[0xff] + Op.DUP1 + Op.PUSH1[0x1] + Op.SSTORE + Op.POP
        + Op.PUSH20[0xd96ed4431b417993ab4f4d4a656959d13c66e1dc] + Op.PUSH1[0x2]
        + Op.DUP1 + Op.SLOAD + Op.PUSH20[0xffffffffffffffffffffffffffffffffffffffff]
        + Op.NOT + Op.AND + Op.DUP3 + Op.OR + Op.SWAP1 + Op.SSTORE + Op.POP
        + Op.PUSH1[0xff] + Op.DUP1 + Op.PUSH1[0x3] + Op.SSTORE + Op.POP
        + Op.PUSH32[0x676c6f62616c2064617461203332206c656e67746820737472696e6700000000]
        + Op.DUP1 + Op.PUSH1[0x4] + Op.SSTORE + Op.POP
        + Op.PUSH20[0xd96ed4431b417993ab4f4d4a656959d13c66e1dc] + Op.PUSH1[0x5]
        + Op.PUSH1[0x0] + Op.DUP1 + Op.DUP2 + Op.MSTORE + Op.PUSH1[0x20] + Op.ADD
        + Op.SWAP1 + Op.DUP2 + Op.MSTORE + Op.PUSH1[0x20] + Op.ADD + Op.PUSH1[0x0]
        + Op.SHA3 + Op.PUSH1[0x0] + Op.PUSH2[0x100] + Op.EXP + Op.DUP2 + Op.SLOAD
        + Op.DUP2 + Op.PUSH20[0xffffffffffffffffffffffffffffffffffffffff] + Op.MUL
        + Op.NOT + Op.AND + Op.SWAP1 + Op.DUP4 + Op.MUL + Op.OR + Op.SWAP1 + Op.SSTORE
        + Op.POP + Op.PUSH2[0x22f] + Op.PUSH2[0x5d] + Op.JUMP + Op.JUMPDEST
        + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH2[0x100] + Op.EXP + Op.DUP2
        + Op.SLOAD + Op.DUP2 + Op.PUSH1[0xff] + Op.MUL + Op.NOT + Op.AND + Op.SWAP1
        + Op.DUP4 + Op.MUL + Op.OR + Op.SWAP1 + Op.SSTORE + Op.POP + Op.PUSH1[0xff]
        + Op.PUSH1[0x1] + Op.PUSH1[0x0] + Op.SLOAD + Op.DIV + Op.AND + Op.SWAP1
        + Op.POP + Op.SWAP1 + Op.JUMP
    ),
    )
    pre[sender] = Account(balance=0x2540be400, nonce=0)

    tx = Transaction(
        secret_key=Hash(
            "0x6f0117d3e9c684c7d6e1e6b79dc3880da2bebe77c765b171c062fdffd38a673f"
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
