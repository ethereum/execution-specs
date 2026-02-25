"""
Ported from:
tests/static/state_tests/stSystemOperationsTest/suicideSendEtherPostDeathFiller.json

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
    push4 0x35f46994
    eq
    push2 0x44
    jumpi
    dup1
    push4 0x4d536fe3
    eq
    push2 0x51
    jumpi
    push2 0x42
    jump
    ... (122 more instructions)
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
    ["tests/static/state_tests/stSystemOperationsTest/suicideSendEtherPostDeathFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_suicide_send_ether_post_death(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test ported from static filler."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = Address("0x2e3d0156d2b99a6eacba540c55f423c8f5a33143")
    contract = Address("0xa997455dca526734f5607f7c452de0cfb9af19f4")

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=10000000,
    )

    pre[sender] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[contract] = Account(
        balance=0xde0b6b3a7640000,
        nonce=0,
        code=(
        Op.PUSH1[0x60] + Op.PUSH1[0x40] + Op.MSTORE + Op.PUSH1[0x0]
        + Op.CALLDATALOAD
        + Op.PUSH29[0x100000000000000000000000000000000000000000000000000000000]
        + Op.SWAP1 + Op.DIV + Op.DUP1 + Op.PUSH4[0x35f46994] + Op.EQ + Op.PUSH2[0x44]
        + Op.JUMPI + Op.DUP1 + Op.PUSH4[0x4d536fe3] + Op.EQ + Op.PUSH2[0x51]
        + Op.JUMPI + Op.PUSH2[0x42] + Op.JUMP + Op.JUMPDEST + Op.STOP + Op.JUMPDEST
        + Op.PUSH2[0x4f] + Op.PUSH1[0x4] + Op.POP + Op.PUSH2[0x72] + Op.JUMP
        + Op.JUMPDEST + Op.STOP + Op.JUMPDEST + Op.PUSH2[0x5c] + Op.PUSH1[0x4]
        + Op.POP + Op.PUSH2[0x8d] + Op.JUMP + Op.JUMPDEST + Op.PUSH1[0x40] + Op.MLOAD
        + Op.DUP1 + Op.DUP3 + Op.DUP2 + Op.MSTORE + Op.PUSH1[0x20] + Op.ADD + Op.SWAP2
        + Op.POP + Op.POP + Op.PUSH1[0x40] + Op.MLOAD + Op.DUP1 + Op.SWAP2 + Op.SUB
        + Op.SWAP1 + Op.RETURN + Op.JUMPDEST + Op.ADDRESS
        + Op.PUSH20[0xffffffffffffffffffffffffffffffffffffffff] + Op.AND
        + Op.SELFDESTRUCT + Op.JUMPDEST + Op.JUMP + Op.JUMPDEST + Op.PUSH1[0x0]
        + Op.PUSH1[0x0] + Op.ADDRESS
        + Op.PUSH20[0xffffffffffffffffffffffffffffffffffffffff] + Op.AND
        + Op.PUSH4[0x35f46994] + Op.PUSH1[0x40] + Op.MLOAD + Op.DUP2
        + Op.PUSH29[0x100000000000000000000000000000000000000000000000000000000]
        + Op.MUL + Op.DUP2 + Op.MSTORE + Op.PUSH1[0x4] + Op.ADD + Op.DUP1 + Op.SWAP1
        + Op.POP + Op.PUSH1[0x0] + Op.PUSH1[0x40] + Op.MLOAD + Op.DUP1 + Op.DUP4
        + Op.SUB + Op.DUP2 + Op.PUSH1[0x0] + Op.DUP8 + Op.PUSH2[0x61da] + Op.GAS
        + Op.SUB + Op.CALL + Op.ISZERO + Op.PUSH2[0x2] + Op.JUMPI + Op.POP + Op.POP
        + Op.POP + Op.ADDRESS + Op.PUSH20[0xffffffffffffffffffffffffffffffffffffffff]
        + Op.AND + Op.BALANCE + Op.SWAP1 + Op.POP + Op.CALLER
        + Op.PUSH20[0xffffffffffffffffffffffffffffffffffffffff] + Op.AND
        + Op.PUSH1[0x0] + Op.DUP3 + Op.PUSH1[0x40] + Op.MLOAD + Op.DUP1 + Op.SWAP1
        + Op.POP + Op.PUSH1[0x0] + Op.PUSH1[0x40] + Op.MLOAD + Op.DUP1 + Op.DUP4
        + Op.SUB + Op.DUP2 + Op.DUP6 + Op.DUP9 + Op.DUP9 + Op.CALL + Op.SWAP4 + Op.POP
        + Op.POP + Op.POP + Op.POP + Op.POP + Op.DUP1 + Op.SWAP2 + Op.POP
        + Op.PUSH2[0x147] + Op.JUMP + Op.JUMPDEST + Op.POP + Op.SWAP1 + Op.JUMP
    ),
    )

    tx = Transaction(
        secret_key=Hash(
            "0xb1f4cbc3a50042184425a6f9e996d0910f7ba879457ce5dac5c71e498ad3c005"
        ),
        to=contract,
        data=bytes.fromhex("4d536fe3"),
        gas_limit=3000000,
        gas_price=10,
        nonce=0,
        value=100000,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)
