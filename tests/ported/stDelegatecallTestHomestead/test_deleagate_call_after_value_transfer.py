"""
Ported from:
tests/static/state_tests/stDelegatecallTestHomestead/deleagateCallAfterValueTransferFiller.json

callee code:
    callvalue
    push1 0x00
    sstore
    caller
    push1 0x01
    sstore
    push1 0x00
    calldataload
    push1 0x02
    sstore
    stop

contract code:
    push1 0x01
    push1 0x00
    mstore
    push1 0x40
    push1 0x00
    push1 0x40
    push1 0x00
    push20 0x0346aa231cb52f55ddf201dc19ca469cc73e6495
    push3 0x0186a0
    delegatecall
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
    ["tests/static/state_tests/stDelegatecallTestHomestead/deleagateCallAfterValueTransferFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_deleagate_call_after_value_transfer(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test ported from static filler."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = Address("0x6fda566d1950d7e0a4dac1de87109b2ca7d12da4")
    contract = Address("0xdd657898b318b3d967472eaa82bb75c4141b6735")
    callee = Address("0x0346aa231cb52f55ddf201dc19ca469cc73e6495")

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
        Op.CALLVALUE + Op.PUSH1[0x0] + Op.SSTORE + Op.CALLER + Op.PUSH1[0x1]
        + Op.SSTORE + Op.PUSH1[0x0] + Op.CALLDATALOAD + Op.PUSH1[0x2] + Op.SSTORE
        + Op.STOP
    ),
    )
    pre[sender] = Account(balance=0x2386f26fc10000, nonce=0)
    pre[contract] = Account(
        balance=0x10c8e0,
        nonce=0,
        code=(
        Op.PUSH1[0x1] + Op.PUSH1[0x0] + Op.MSTORE + Op.PUSH1[0x40] + Op.PUSH1[0x0]
        + Op.PUSH1[0x40] + Op.PUSH1[0x0]
        + Op.PUSH20[0x346aa231cb52f55ddf201dc19ca469cc73e6495] + Op.PUSH3[0x186a0]
        + Op.DELEGATECALL + Op.STOP
    ),
    )

    tx = Transaction(
        secret_key=Hash(
            "0x3722faab4d25b944622d559ea4bcf38b4bcf3caf07a6d2c6fd99321c1a66c974"
        ),
        to=contract,
        data=b"",
        gas_limit=453081,
        gas_price=10,
        nonce=0,
        value=0,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)
