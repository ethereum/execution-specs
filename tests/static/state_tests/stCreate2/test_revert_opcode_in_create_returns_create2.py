"""
RevertOpcodeInCreateReturns for CREATE2

Ported from:
tests/static/state_tests/stCreate2/RevertOpcodeInCreateReturnsCreate2Filler.json

contract code:
    push1 0x00
    push1 0x0e
    dup1
    push1 0x17
    push1 0x00
    codecopy
    push1 0x00
    push1 0x00
    create2
    pop
    returndatasize
    push1 0x00
    sstore
    stop
    stop
    invalid
    push3 0x112233
    push1 0x00
    mstore
    push1 0x20
    ... (4 more instructions)
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
    ["tests/static/state_tests/stCreate2/RevertOpcodeInCreateReturnsCreate2Filler.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_revert_opcode_in_create_returns_create2(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """RevertOpcodeInCreateReturns for CREATE2."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = Address("0xa94f5374fce5edbc8e2a8697c15331677e6ebf0b")
    contract = Address("0x0f572e5295c57f15886f9b263e2f6d2d6c7b5ec6")

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=47244640256,
    )

    pre[contract] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.PUSH1[0x0] + Op.PUSH1[0xe] + Op.DUP1 + Op.PUSH1[0x17] + Op.PUSH1[0x0]
        + Op.CODECOPY + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.CREATE2 + Op.POP
        + Op.RETURNDATASIZE + Op.PUSH1[0x0] + Op.SSTORE + Op.STOP + Op.STOP
        + Op.INVALID + Op.PUSH3[0x112233] + Op.PUSH1[0x0] + Op.MSTORE + Op.PUSH1[0x20]
        + Op.PUSH1[0x0] + Op.REVERT + Op.STOP + Op.STOP
    ),
        storage={0x0: 0x1},
    )
    pre[sender] = Account(balance=0x6400000000, nonce=0)

    tx = Transaction(
        secret_key=Hash(
            "0x45a915e4d060149eb4365960e6a7a45f334393093061116b197e3240065ff2d8"
        ),
        to=contract,
        data=b"",
        gas_limit=100000,
        gas_price=10,
        nonce=0,
        value=0,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)
