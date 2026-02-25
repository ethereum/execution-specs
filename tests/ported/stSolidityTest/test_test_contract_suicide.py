"""
Ported from:
tests/static/state_tests/stSolidityTest/TestContractSuicideFiller.json

contract code:
    push29 0x0100000000000000000000000000000000000000000000000000000000
    push1 0x00
    calldataload
    div
    push4 0xa60eedda
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
    ... (195 more instructions)
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
    ["tests/static/state_tests/stSolidityTest/TestContractSuicideFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_test_contract_suicide(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test ported from static filler."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = Address("0x7f3f285918d9b5e764174551e10b7539b97bbb27")
    contract = Address("0xfe34831df57f026afbfffd7e7b51b4adbfe135e1")

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
        + Op.PUSH1[0x0] + Op.CALLDATALOAD + Op.DIV + Op.PUSH4[0xa60eedda] + Op.DUP2
        + Op.EQ + Op.PUSH2[0x39] + Op.JUMPI + Op.DUP1 + Op.PUSH4[0xc0406226] + Op.EQ
        + Op.PUSH2[0x4b] + Op.JUMPI + Op.STOP + Op.JUMPDEST + Op.PUSH2[0x41]
        + Op.PUSH2[0x5d] + Op.JUMP + Op.JUMPDEST + Op.DUP1 + Op.PUSH1[0x0] + Op.MSTORE
        + Op.PUSH1[0x20] + Op.PUSH1[0x0] + Op.RETURN + Op.JUMPDEST + Op.PUSH2[0x53]
        + Op.PUSH2[0x15a] + Op.JUMP + Op.JUMPDEST + Op.DUP1 + Op.PUSH1[0x0]
        + Op.MSTORE + Op.PUSH1[0x20] + Op.PUSH1[0x0] + Op.RETURN + Op.JUMPDEST
        + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x81] + Op.PUSH2[0x18a]
        + Op.PUSH1[0x0] + Op.CODECOPY + Op.PUSH1[0x81] + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.CREATE + Op.SWAP1 + Op.POP
        + Op.PUSH20[0xffffffffffffffffffffffffffffffffffffffff] + Op.DUP2 + Op.AND
        + Op.PUSH3[0xf55d9d] + Op.PUSH1[0x0] + Op.DUP1
        + Op.PUSH31[0xf55d9d00000000000000000000000000000000000000000000000000000000]
        + Op.DUP3 + Op.MSTORE + Op.PUSH1[0x4] + Op.COINBASE
        + Op.PUSH20[0xffffffffffffffffffffffffffffffffffffffff] + Op.AND + Op.DUP2
        + Op.MSTORE + Op.PUSH1[0x20] + Op.ADD + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.DUP7 + Op.PUSH1[0x32] + Op.GAS + Op.SUB + Op.CALL + Op.PUSH2[0xe0]
        + Op.JUMPI + Op.STOP + Op.JUMPDEST + Op.POP + Op.POP
        + Op.PUSH20[0xffffffffffffffffffffffffffffffffffffffff] + Op.DUP2 + Op.AND
        + Op.PUSH4[0xb9c3d0a5] + Op.PUSH1[0x20] + Op.PUSH1[0x0]
        + Op.PUSH32[0xb9c3d0a500000000000000000000000000000000000000000000000000000000]
        + Op.DUP2 + Op.MSTORE + Op.PUSH1[0x4] + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.DUP7 + Op.PUSH1[0x32] + Op.GAS + Op.SUB + Op.CALL + Op.PUSH2[0x137]
        + Op.JUMPI + Op.STOP + Op.JUMPDEST + Op.POP + Op.POP + Op.PUSH1[0x0]
        + Op.MLOAD + Op.PUSH1[0xe1] + Op.EQ + Op.PUSH2[0x148] + Op.JUMPI
        + Op.PUSH2[0x151] + Op.JUMP + Op.JUMPDEST + Op.PUSH1[0x1] + Op.SWAP2 + Op.POP
        + Op.PUSH2[0x156] + Op.JUMP + Op.JUMPDEST + Op.PUSH1[0x0] + Op.SWAP2 + Op.POP
        + Op.JUMPDEST + Op.POP + Op.SWAP1 + Op.JUMP + Op.JUMPDEST + Op.PUSH1[0x0]
        + Op.PUSH2[0x164] + Op.PUSH2[0x5d] + Op.JUMP + Op.JUMPDEST + Op.PUSH1[0x0]
        + Op.PUSH1[0x0] + Op.PUSH2[0x100] + Op.EXP + Op.DUP2 + Op.SLOAD + Op.DUP2
        + Op.PUSH1[0xff] + Op.MUL + Op.NOT + Op.AND + Op.SWAP1 + Op.DUP4 + Op.MUL
        + Op.OR + Op.SWAP1 + Op.SSTORE + Op.POP + Op.PUSH1[0xff] + Op.PUSH1[0x1]
        + Op.PUSH1[0x0] + Op.SLOAD + Op.DIV + Op.AND + Op.SWAP1 + Op.POP + Op.SWAP1
        + Op.JUMP + Op.STOP + Op.PUSH1[0x75] + Op.DUP1 + Op.PUSH1[0xc] + Op.PUSH1[0x0]
        + Op.CODECOPY + Op.PUSH1[0x0] + Op.RETURN + Op.STOP
        + Op.PUSH29[0x100000000000000000000000000000000000000000000000000000000]
        + Op.PUSH1[0x0] + Op.CALLDATALOAD + Op.DIV + Op.PUSH3[0xf55d9d] + Op.DUP2
        + Op.EQ + Op.PUSH1[0x36] + Op.JUMPI + Op.DUP1 + Op.PUSH4[0xb9c3d0a5] + Op.EQ
        + Op.PUSH1[0x45] + Op.JUMPI + Op.STOP + Op.JUMPDEST + Op.PUSH1[0x3f]
        + Op.PUSH1[0x4] + Op.CALLDATALOAD + Op.PUSH1[0x5a] + Op.JUMP + Op.JUMPDEST
        + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.RETURN + Op.JUMPDEST + Op.PUSH1[0x4b]
        + Op.PUSH1[0x55] + Op.JUMP + Op.JUMPDEST + Op.DUP1 + Op.PUSH1[0x0] + Op.MSTORE
        + Op.PUSH1[0x20] + Op.PUSH1[0x0] + Op.RETURN + Op.JUMPDEST + Op.PUSH1[0xe1]
        + Op.SWAP1 + Op.JUMP + Op.JUMPDEST + Op.DUP1
        + Op.PUSH20[0xffffffffffffffffffffffffffffffffffffffff] + Op.AND
        + Op.SELFDESTRUCT + Op.POP + Op.JUMP
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
