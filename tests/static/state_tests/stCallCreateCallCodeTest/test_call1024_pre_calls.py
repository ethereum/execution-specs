"""
calldepth with subcall

Ported from:
tests/static/state_tests/stCallCreateCallCodeTest/Call1024PreCallsFiller.json

contract code:
    push1 0x00
    push1 0x00
    push1 0x00
    push1 0x00
    push1 0x01
    push20 0xd9b97c712ebce43f3c19179bbef44b550f9e8bc0
    push2 0xffff
    call
    push1 0x02
    sstore
    push1 0x00
    push1 0x00
    push1 0x00
    push1 0x00
    push1 0x01
    push20 0xd9b97c712ebce43f3c19179bbef44b550f9e8bc0
    push2 0xffff
    call
    push1 0x03
    sstore
    ... (17 more instructions)
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
    ["tests/static/state_tests/stCallCreateCallCodeTest/Call1024PreCallsFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.valid_until("Prague")
@pytest.mark.parametrize(
    "tx_gas_limit",
    [
        9214364837600034817,
        11837600034817,
    ],
    ids=['case0', 'case1'],
)
@pytest.mark.pre_alloc_mutable
def test_call1024_pre_calls(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_gas_limit: int,
) -> None:
    """calldepth with subcall."""
    coinbase = Address("0xb94f5374fce5edbc8e2a8697c15331677e6ebf0b")
    sender = Address("0x3f13d7fc49b91cdc388f79f861c0f1a0e708dfbf")
    contract = Address("0x48c20cd83ddbd3908712f4d31c51b3cdaae287ce")
    callee = Address("0xd9b97c712ebce43f3c19179bbef44b550f9e8bc0")

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=9223372036854775807,
    )

    pre[sender] = Account(balance=0xfffffffffffffffffffffffffffffffff, nonce=0)
    pre[contract] = Account(
        balance=2024,
        nonce=0,
        code=(
        Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH1[0x1] + Op.PUSH20[0xd9b97c712ebce43f3c19179bbef44b550f9e8bc0]
        + Op.PUSH2[0xffff] + Op.CALL + Op.PUSH1[0x2] + Op.SSTORE + Op.PUSH1[0x0]
        + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x1]
        + Op.PUSH20[0xd9b97c712ebce43f3c19179bbef44b550f9e8bc0] + Op.PUSH2[0xffff]
        + Op.CALL + Op.PUSH1[0x3] + Op.SSTORE + Op.PUSH1[0x1] + Op.PUSH1[0x0]
        + Op.SLOAD + Op.ADD + Op.PUSH1[0x0] + Op.SSTORE + Op.PUSH1[0x0]
        + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH20[0x48c20cd83ddbd3908712f4d31c51b3cdaae287ce]
        + Op.PUSH6[0xfffffffffff] + Op.CALL + Op.PUSH1[0x1] + Op.SSTORE + Op.STOP
    ),
    )
    pre[callee] = Account(balance=7000, nonce=0)

    tx = Transaction(
        secret_key=Hash(
            "0xcc381c83857b17ca629268ed418e2915a0287b84efe9cf2204c020302e83cda0"
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
