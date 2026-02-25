"""
Ported from:
tests/static/state_tests/stQuadraticComplexityTest/Call50000_sha256Filler.json

contract code:
    jumpdest
    push2 0xc350
    push1 0x80
    mload
    lt
    iszero
    push1 0x2d
    jumpi
    push1 0x00
    push1 0x00
    push2 0xc350
    push1 0x00
    push1 0x01
    push1 0x02
    push3 0x013178
    call
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
    ["tests/static/state_tests/stQuadraticComplexityTest/Call50000_sha256Filler.json"],
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
def test_call50000_sha256(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_gas_limit: int,
) -> None:
    """Test ported from static filler."""
    coinbase = Address("0xb94f5374fce5edbc8e2a8697c15331677e6ebf0b")
    sender = Address("0xa94f5374fce5edbc8e2a8697c15331677e6ebf0b")
    contract = Address("0xbbbf5374fce5edbc8e2a8697c15331677e6ebf0b")

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=3925000000,
    )

    pre[sender] = Account(balance=0xffffffffffffffffffffffffffffffff, nonce=0)
    pre[contract] = Account(
        balance=0xfffffffffffff,
        nonce=0,
        code=(
        Op.JUMPDEST + Op.PUSH2[0xc350] + Op.PUSH1[0x80] + Op.MLOAD + Op.LT
        + Op.ISZERO + Op.PUSH1[0x2d] + Op.JUMPI + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH2[0xc350] + Op.PUSH1[0x0] + Op.PUSH1[0x1] + Op.PUSH1[0x2]
        + Op.PUSH3[0x13178] + Op.CALL + Op.PUSH1[0x0] + Op.SSTORE + Op.PUSH1[0x1]
        + Op.PUSH1[0x80] + Op.MLOAD + Op.ADD + Op.PUSH1[0x80] + Op.MSTORE
        + Op.PUSH1[0x0] + Op.JUMP + Op.JUMPDEST + Op.PUSH1[0x80] + Op.MLOAD
        + Op.PUSH1[0x1] + Op.SSTORE + Op.STOP
    ),
    )

    tx = Transaction(
        secret_key=Hash(
            "0x45a915e4d060149eb4365960e6a7a45f334393093061116b197e3240065ff2d8"
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
