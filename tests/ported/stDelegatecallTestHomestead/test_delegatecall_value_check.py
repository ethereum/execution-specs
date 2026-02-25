"""
Ported from:
tests/static/state_tests/stDelegatecallTestHomestead/delegatecallValueCheckFiller.json

contract code:
    push1 0x02
    push1 0x00
    push1 0x40
    push1 0x00
    push20 0x5d25ad2a26f849e9400d6b65244f26f4eea11adf
    push3 0x07a120
    delegatecall
    push1 0x00
    sstore
    stop

callee code:
    callvalue
    push1 0x01
    sstore
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
    ["tests/static/state_tests/stDelegatecallTestHomestead/delegatecallValueCheckFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_delegatecall_value_check(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test ported from static filler."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = Address("0xebaf50debf10e08302fe4280c32df010463ca297")
    contract = Address("0x55bb8a8658b848ebbbb73cbf6ac9d59d715aec58")
    callee = Address("0x5d25ad2a26f849e9400d6b65244f26f4eea11adf")

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=30000000,
    )

    pre[contract] = Account(
        balance=0xde0b6b3a7640000,
        nonce=0,
        code=(
        Op.PUSH1[0x2] + Op.PUSH1[0x0] + Op.PUSH1[0x40] + Op.PUSH1[0x0]
        + Op.PUSH20[0x5d25ad2a26f849e9400d6b65244f26f4eea11adf] + Op.PUSH3[0x7a120]
        + Op.DELEGATECALL + Op.PUSH1[0x0] + Op.SSTORE + Op.STOP
    ),
    )
    pre[callee] = Account(
        balance=23,
        nonce=0,
        code=Op.CALLVALUE + Op.PUSH1[0x1] + Op.SSTORE + Op.STOP,
    )
    pre[sender] = Account(balance=0xde0b6b3a7640000, nonce=0)

    tx = Transaction(
        secret_key=Hash(
            "0xe04d1ac7ddda0c98397d56a0b501e960d4cd325a39286919ac23c1a07009a869"
        ),
        to=contract,
        data=b"",
        gas_limit=3000000,
        gas_price=10,
        nonce=0,
        value=23,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)
