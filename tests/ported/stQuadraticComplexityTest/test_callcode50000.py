"""
Ported from:
tests/static/state_tests/stQuadraticComplexityTest/Callcode50000Filler.json

contract code:
    jumpdest
    push2 0xc350
    push1 0x80
    mload
    lt
    iszero
    push1 0x3f
    jumpi
    push1 0x00
    push1 0x00
    push2 0xc350
    push1 0x00
    push1 0x01
    push20 0xd9b97c712ebce43f3c19179bbef44b550f9e8bc0
    push2 0x0640
    callcode
    push1 0x00
    sstore
    push1 0x01
    push1 0x80
    ... (12 more instructions)
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
    ["tests/static/state_tests/stQuadraticComplexityTest/Callcode50000Filler.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.valid_until("Prague")
@pytest.mark.parametrize(
    "tx_gas_limit",
    [
        150000,
        250000000,
    ],
    ids=['case0', 'case1'],
)
@pytest.mark.pre_alloc_mutable
def test_callcode50000(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_gas_limit: int,
) -> None:
    """Test ported from static filler."""
    coinbase = Address("0xb94f5374fce5edbc8e2a8697c15331677e6ebf0b")
    sender = Address("0x4768b5e50b0ebe91ae38d84a47e3179e615f9c40")
    contract = Address("0x7fc89545bed7af26b6ef809b53e9a93fd0718468")
    callee = Address("0xd9b97c712ebce43f3c19179bbef44b550f9e8bc0")

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=8600000000,
    )

    pre[sender] = Account(balance=0xffffffffffffffffffffffffffffffff, nonce=0)
    pre[contract] = Account(
        balance=0xfffffffffffff,
        nonce=0,
        code=(
        Op.JUMPDEST + Op.PUSH2[0xc350] + Op.PUSH1[0x80] + Op.MLOAD + Op.LT
        + Op.ISZERO + Op.PUSH1[0x3f] + Op.JUMPI + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH2[0xc350] + Op.PUSH1[0x0] + Op.PUSH1[0x1]
        + Op.PUSH20[0xd9b97c712ebce43f3c19179bbef44b550f9e8bc0] + Op.PUSH2[0x640]
        + Op.CALLCODE + Op.PUSH1[0x0] + Op.SSTORE + Op.PUSH1[0x1] + Op.PUSH1[0x80]
        + Op.MLOAD + Op.ADD + Op.PUSH1[0x80] + Op.MSTORE + Op.PUSH1[0x0] + Op.JUMP
        + Op.JUMPDEST + Op.PUSH1[0x80] + Op.MLOAD + Op.PUSH1[0x1] + Op.SSTORE
        + Op.STOP
    ),
    )
    pre[callee] = Account(balance=7000, nonce=0)

    tx = Transaction(
        secret_key=Hash(
            "0xe7c72b378297589acee4e0ba3272841bcfc5e220f86de253f890274cfee9e474"
        ),
        to=contract,
        data=b"",
        gas_limit=tx_gas_limit,
        gas_price=10,
        nonce=0,
        value=10,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)
