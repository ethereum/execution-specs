"""
Ported from:
tests/static/state_tests/stRevertTest/RevertInDelegateCallFiller.json

contract code:
    push1 0x40
    push1 0x00
    push1 0x40
    push1 0x00
    push20 0xc3ecfe24c185ad3c946ebff4624131e8af5220a2
    push2 0xc350
    delegatecall
    push1 0x00
    sstore
    returndatasize
    push1 0x01
    sstore
    push1 0x20
    push1 0x00
    push1 0x3f
    returndatacopy
    push1 0x3f
    mload
    push1 0x02
    sstore
    ... (1 more instructions)

callee code:
    push1 0x0a
    push1 0x20
    mstore
    push1 0x20
    push1 0x20
    revert
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
    ["tests/static/state_tests/stRevertTest/RevertInDelegateCallFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_revert_in_delegate_call(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test ported from static filler."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = Address("0x7f3f285918d9b5e764174551e10b7539b97bbb27")
    contract = Address("0x23ea33dc3aa11f5a1da3643bb13956382b9b6767")
    callee = Address("0xc3ecfe24c185ad3c946ebff4624131e8af5220a2")

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=1000000,
    )

    pre[contract] = Account(
        balance=1000,
        nonce=0,
        code=(
        Op.PUSH1[0x40] + Op.PUSH1[0x0] + Op.PUSH1[0x40] + Op.PUSH1[0x0]
        + Op.PUSH20[0xc3ecfe24c185ad3c946ebff4624131e8af5220a2] + Op.PUSH2[0xc350]
        + Op.DELEGATECALL + Op.PUSH1[0x0] + Op.SSTORE + Op.RETURNDATASIZE
        + Op.PUSH1[0x1] + Op.SSTORE + Op.PUSH1[0x20] + Op.PUSH1[0x0] + Op.PUSH1[0x3f]
        + Op.RETURNDATACOPY + Op.PUSH1[0x3f] + Op.MLOAD + Op.PUSH1[0x2] + Op.SSTORE
        + Op.STOP
    ),
    )
    pre[sender] = Account(balance=0x5f5e100, nonce=0)
    pre[callee] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.PUSH1[0xa] + Op.PUSH1[0x20] + Op.MSTORE + Op.PUSH1[0x20] + Op.PUSH1[0x20]
        + Op.REVERT + Op.STOP
    ),
    )

    tx = Transaction(
        secret_key=Hash(
            "0xa2333eef5630066b928dea5fd85a239f511b5b067d1441ee7ac290d0122b917b"
        ),
        to=contract,
        data=b"",
        gas_limit=105044,
        gas_price=10,
        nonce=0,
        value=0,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)
