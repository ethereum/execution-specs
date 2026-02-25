"""
Create2OnDepth1023, 0x0400 indicates 1022 level.

Ported from:
tests/static/state_tests/stCreate2/Create2OnDepth1023Filler.json

contract code:
    push1 0x00
    calldataload
    push1 0x00
    mstore
    push1 0x00
    mload
    push1 0x02
    add
    push1 0x00
    mstore
    push2 0x0400
    push1 0x00
    mload
    eq
    push1 0x43
    jumpi
    push1 0x00
    push1 0x00
    push1 0x20
    push1 0x00
    ... (23 more instructions)

callee code:
    push1 0x00
    calldataload
    push1 0x00
    mstore
    push1 0x00
    push1 0x00
    push1 0x20
    push1 0x00
    push1 0x00
    push20 0xb94f5374fce5edbc8e2a8697c15331677e6ebf0b
    gas
    call
    stop
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
    ["tests/static/state_tests/stCreate2/Create2OnDepth1023Filler.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.valid_until("Prague")
@pytest.mark.pre_alloc_mutable
def test_create2_on_depth1023(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Create2OnDepth1023, 0x0400 indicates 1022 level.."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = Address("0xa94f5374fce5edbc8e2a8697c15331677e6ebf0b")
    contract = Address("0xb94f5374fce5edbc8e2a8697c15331677e6ebf0b")
    callee = Address("0xc94f5374fce5edbc8e2a8697c15331677e6ebf0b")

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=9223372036854775807,
    )

    pre[sender] = Account(
        balance=0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff,
        nonce=0,
    )
    pre[contract] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.PUSH1[0x0] + Op.CALLDATALOAD + Op.PUSH1[0x0] + Op.MSTORE + Op.PUSH1[0x0]
        + Op.MLOAD + Op.PUSH1[0x2] + Op.ADD + Op.PUSH1[0x0] + Op.MSTORE
        + Op.PUSH2[0x400] + Op.PUSH1[0x0] + Op.MLOAD + Op.EQ + Op.PUSH1[0x43]
        + Op.JUMPI + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x20] + Op.PUSH1[0x0]
        + Op.PUSH2[0x400] + Op.PUSH1[0x0] + Op.MLOAD + Op.EQ
        + Op.PUSH20[0xc94f5374fce5edbc8e2a8697c15331677e6ebf0b] + Op.GAS + Op.CALL
        + Op.POP + Op.PUSH1[0x60] + Op.JUMP + Op.JUMPDEST
        + Op.PUSH12[0x6000600060006000f5600155] + Op.PUSH1[0x20] + Op.MSTORE
        + Op.PUSH1[0x0] + Op.PUSH1[0xc] + Op.PUSH1[0x34] + Op.PUSH1[0x0] + Op.CREATE2
        + Op.PUSH1[0x1] + Op.SSTORE + Op.JUMPDEST + Op.STOP
    ),
    )
    pre[callee] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.PUSH1[0x0] + Op.CALLDATALOAD + Op.PUSH1[0x0] + Op.MSTORE + Op.PUSH1[0x0]
        + Op.PUSH1[0x0] + Op.PUSH1[0x20] + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH20[0xb94f5374fce5edbc8e2a8697c15331677e6ebf0b] + Op.GAS + Op.CALL
        + Op.STOP
    ),
    )

    tx = Transaction(
        secret_key=Hash(
            "0x45a915e4d060149eb4365960e6a7a45f334393093061116b197e3240065ff2d8"
        ),
        to=contract,
        data=b"",
        gas_limit=9151314442816847871,
        gas_price=10,
        nonce=0,
        value=0,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)
