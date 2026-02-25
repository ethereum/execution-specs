"""
Test combination of gas refund and EF-prefixed CREATE2 failure.


Ported from:
tests/static/state_tests/stCreateTest/CREATE2_RefundEFFiller.yml

callee code:
    push1 0x00
    dup1
    sstore
    stop

contract code:
    push1 0x00
    push1 0x19
    dup1
    push1 0x11
    dup4
    codecopy
    dup2
    dup1
    create2
    push1 0x00
    sstore
    stop
    invalid
    push1 0x00
    dup1
    dup1
    dup1
    dup1
    push3 0x5ef94d
    push2 0xc350
    ... (8 more instructions)
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
    ["tests/static/state_tests/stCreateTest/CREATE2_RefundEFFiller.yml"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_create2_refund_ef(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test combination of gas refund and EF-prefixed CREATE2 failure.
."""
    coinbase = Address("0xa94f5374fce5edbc8e2a8697c15331677e6ebf0b")
    sender = Address("0xa94f5374fce5edbc8e2a8697c15331677e6ebf0b")
    contract = Address("0x000000000000000000000000000000000c5ea705")
    callee = Address("0x00000000000000000000000000000000005ef94d")

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=1000000,
    )

    pre[callee] = Account(
        balance=0,
        nonce=0,
        code=Op.PUSH1[0x0] + Op.DUP1 + Op.SSTORE + Op.STOP,
        storage={0x0: 0x1},
    )
    pre[contract] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.PUSH1[0x0] + Op.PUSH1[0x19] + Op.DUP1 + Op.PUSH1[0x11] + Op.DUP4
        + Op.CODECOPY + Op.DUP2 + Op.DUP1 + Op.CREATE2 + Op.PUSH1[0x0] + Op.SSTORE
        + Op.STOP + Op.INVALID + Op.PUSH1[0x0] + Op.DUP1 + Op.DUP1 + Op.DUP1 + Op.DUP1
        + Op.PUSH3[0x5ef94d] + Op.PUSH2[0xc350] + Op.CALL + Op.POP + Op.PUSH1[0xef]
        + Op.PUSH1[0x0] + Op.MSTORE8 + Op.PUSH1[0x1] + Op.PUSH1[0x0] + Op.RETURN
    ),
    )
    pre[sender] = Account(balance=0x5af3107a4000, nonce=0)

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
