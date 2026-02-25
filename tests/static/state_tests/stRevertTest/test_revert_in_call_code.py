"""
Ported from:
tests/static/state_tests/stRevertTest/RevertInCallCodeFiller.json

callee code:
    push2 0x2232
    push1 0x00
    mstore
    push1 0x20
    push1 0x00
    revert
    stop

contract code:
    push1 0x40
    push1 0x00
    push1 0x40
    push1 0x00
    push2 0x03e8
    push20 0x26bc42b8191ccb142cb8cbc3490bd3bdce465591
    push2 0xc350
    callcode
    push1 0x00
    sstore
    returndatasize
    push1 0x01
    sstore
    push1 0x20
    push1 0x00
    push1 0x40
    returndatacopy
    push1 0x40
    mload
    push1 0x02
    ... (2 more instructions)
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
    ["tests/static/state_tests/stRevertTest/RevertInCallCodeFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_revert_in_call_code(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test ported from static filler."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = Address("0x7f3f285918d9b5e764174551e10b7539b97bbb27")
    contract = Address("0x5e1d76d7badbad41710e47410dba9226c255d229")
    callee = Address("0x26bc42b8191ccb142cb8cbc3490bd3bdce465591")

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
        code=(
        Op.PUSH2[0x2232] + Op.PUSH1[0x0] + Op.MSTORE + Op.PUSH1[0x20]
        + Op.PUSH1[0x0] + Op.REVERT + Op.STOP
    ),
    )
    pre[contract] = Account(
        balance=1000,
        nonce=0,
        code=(
        Op.PUSH1[0x40] + Op.PUSH1[0x0] + Op.PUSH1[0x40] + Op.PUSH1[0x0]
        + Op.PUSH2[0x3e8] + Op.PUSH20[0x26bc42b8191ccb142cb8cbc3490bd3bdce465591]
        + Op.PUSH2[0xc350] + Op.CALLCODE + Op.PUSH1[0x0] + Op.SSTORE
        + Op.RETURNDATASIZE + Op.PUSH1[0x1] + Op.SSTORE + Op.PUSH1[0x20]
        + Op.PUSH1[0x0] + Op.PUSH1[0x40] + Op.RETURNDATACOPY + Op.PUSH1[0x40]
        + Op.MLOAD + Op.PUSH1[0x2] + Op.SSTORE + Op.STOP
    ),
    )
    pre[sender] = Account(balance=0x5f5e100, nonce=0)

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
