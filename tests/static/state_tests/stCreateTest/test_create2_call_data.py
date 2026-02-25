"""
Test if calldata is empty in initcode context.


Ported from:
tests/static/state_tests/stCreateTest/CREATE2_CallDataFiller.yml

contract code:
    push1 0x00
    push1 0x10
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
    calldataload
    push1 0x00
    sstore
    push1 0x40
    push1 0x00
    dup1
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
    ["tests/static/state_tests/stCreateTest/CREATE2_CallDataFiller.yml"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_create2_call_data(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test if calldata is empty in initcode context.
."""
    coinbase = Address("0xa94f5374fce5edbc8e2a8697c15331677e6ebf0b")
    sender = Address("0xa94f5374fce5edbc8e2a8697c15331677e6ebf0b")
    contract = Address("0x000000000000000000000000000000000c5ea705")

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=1000000,
    )

    pre[contract] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.PUSH1[0x0] + Op.PUSH1[0x10] + Op.DUP1 + Op.PUSH1[0x11] + Op.DUP4
        + Op.CODECOPY + Op.DUP2 + Op.DUP1 + Op.CREATE2 + Op.PUSH1[0x0] + Op.SSTORE
        + Op.STOP + Op.INVALID + Op.PUSH1[0x0] + Op.CALLDATALOAD + Op.PUSH1[0x0]
        + Op.SSTORE + Op.PUSH1[0x40] + Op.PUSH1[0x0] + Op.DUP1 + Op.CALLDATACOPY
        + Op.MSIZE + Op.PUSH1[0x0] + Op.RETURN
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
