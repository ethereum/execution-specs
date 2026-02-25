"""
Ported from:
tests/static/state_tests/stQuadraticComplexityTest/Call1MB1024CalldepthFiller.json

contract code:
    push1 0x01
    push1 0x00
    sload
    add
    push1 0x00
    sstore
    push2 0x0400
    push1 0x00
    sload
    lt
    push1 0x1b
    jumpi
    push1 0x01
    push1 0x02
    sstore
    push1 0x47
    jump
    jumpdest
    push1 0x00
    push1 0x00
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
    ["tests/static/state_tests/stQuadraticComplexityTest/Call1MB1024CalldepthFiller.json"],
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
def test_call1_mb1024_calldepth(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_gas_limit: int,
) -> None:
    """Test ported from static filler."""
    coinbase = Address("0xb94f5374fce5edbc8e2a8697c15331677e6ebf0b")
    sender = Address("0x4768b5e50b0ebe91ae38d84a47e3179e615f9c40")
    contract = Address("0x9d15232f6851f9f3a88f88a3b358ed1579977a5a")
    callee = Address("0x2ab8257767339461506c0c67824cf17bc77b52ca")

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=882500000000,
    )

    pre[callee] = Account(balance=0xfffffffffffff, nonce=0)
    pre[sender] = Account(balance=0xffffffffffffffffffffffffffffffff, nonce=0)
    pre[contract] = Account(
        balance=0xfffffffffffff,
        nonce=0,
        code=(
        Op.PUSH1[0x1] + Op.PUSH1[0x0] + Op.SLOAD + Op.ADD + Op.PUSH1[0x0]
        + Op.SSTORE + Op.PUSH2[0x400] + Op.PUSH1[0x0] + Op.SLOAD + Op.LT
        + Op.PUSH1[0x1b] + Op.JUMPI + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.SSTORE
        + Op.PUSH1[0x47] + Op.JUMP + Op.JUMPDEST + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH3[0xf4240] + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH20[0x9d15232f6851f9f3a88f88a3b358ed1579977a5a] + Op.PUSH3[0xf55c8]
        + Op.GAS + Op.SUB + Op.CALL + Op.PUSH1[0x1] + Op.SSTORE + Op.JUMPDEST
        + Op.STOP
    ),
    )

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
