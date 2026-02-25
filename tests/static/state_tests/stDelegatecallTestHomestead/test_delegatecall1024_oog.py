"""
Ported from:
tests/static/state_tests/stDelegatecallTestHomestead/Delegatecall1024OOGFiller.json

contract code:
    push1 0x01
    push1 0x00
    sload
    add
    push1 0x00
    sstore
    push1 0x00
    push1 0x00
    push1 0x00
    push1 0x00
    push20 0x62c5c9278da01e6594d6fede061838cf5e597f2b
    push2 0x0401
    push1 0x00
    sload
    div
    push1 0x01
    sub
    push2 0x2710
    gas
    sub
    ... (13 more instructions)
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
    ["tests/static/state_tests/stDelegatecallTestHomestead/Delegatecall1024OOGFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_delegatecall1024_oog(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test ported from static filler."""
    coinbase = Address("0xb94f5374fce5edbc8e2a8697c15331677e6ebf0b")
    sender = Address("0x4768b5e50b0ebe91ae38d84a47e3179e615f9c40")
    contract = Address("0x62c5c9278da01e6594d6fede061838cf5e597f2b")
    callee = Address("0xd9b97c712ebce43f3c19179bbef44b550f9e8bc0")

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=9223372036854775807,
    )

    pre[sender] = Account(balance=0xffffffffffffffffffffffffffffffff, nonce=0)
    pre[contract] = Account(
        balance=1024,
        nonce=0,
        code=(
        Op.PUSH1[0x1] + Op.PUSH1[0x0] + Op.SLOAD + Op.ADD + Op.PUSH1[0x0]
        + Op.SSTORE + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH20[0x62c5c9278da01e6594d6fede061838cf5e597f2b] + Op.PUSH2[0x401]
        + Op.PUSH1[0x0] + Op.SLOAD + Op.DIV + Op.PUSH1[0x1] + Op.SUB
        + Op.PUSH2[0x2710] + Op.GAS + Op.SUB + Op.MUL + Op.DELEGATECALL
        + Op.PUSH1[0x1] + Op.SSTORE + Op.PUSH2[0x3e8] + Op.PUSH1[0x0] + Op.SLOAD
        + Op.MUL + Op.PUSH1[0x1] + Op.ADD + Op.PUSH1[0x2] + Op.SSTORE + Op.STOP
    ),
    )
    pre[callee] = Account(balance=7000, nonce=0)

    tx = Transaction(
        secret_key=Hash(
            "0xe7c72b378297589acee4e0ba3272841bcfc5e220f86de253f890274cfee9e474"
        ),
        to=contract,
        data=b"",
        gas_limit=15720826,
        gas_price=10,
        nonce=0,
        value=10,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)
