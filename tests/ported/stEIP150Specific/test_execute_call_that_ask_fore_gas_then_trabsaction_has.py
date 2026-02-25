"""
Ported from:
tests/static/state_tests/stEIP150Specific/ExecuteCallThatAskForeGasThenTrabsactionHasFiller.json

contract code:
    push1 0x00
    push1 0x00
    push1 0x00
    push1 0x00
    push1 0x00
    push20 0xbfdd294028701b119d416c68eff7dd9f7effd249
    push3 0x0927c0
    call
    push1 0x01
    sstore
    stop

callee code:
    push1 0x0c
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
    ["tests/static/state_tests/stEIP150Specific/ExecuteCallThatAskForeGasThenTrabsactionHasFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_execute_call_that_ask_fore_gas_then_trabsaction_has(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test ported from static filler."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = Address("0x7f3f285918d9b5e764174551e10b7539b97bbb27")
    contract = Address("0x1819cf5bff62f0d379f146b85baaf9bd18239832")
    callee = Address("0xbfdd294028701b119d416c68eff7dd9f7effd249")

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=10000000,
    )

    pre[contract] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH1[0x0] + Op.PUSH20[0xbfdd294028701b119d416c68eff7dd9f7effd249]
        + Op.PUSH3[0x927c0] + Op.CALL + Op.PUSH1[0x1] + Op.SSTORE + Op.STOP
    ),
    )
    pre[sender] = Account(balance=0x5f5e100, nonce=0)
    pre[callee] = Account(
        balance=0x186a0,
        nonce=0,
        code=Op.PUSH1[0xc] + Op.PUSH1[0x1] + Op.SSTORE + Op.STOP,
    )

    tx = Transaction(
        secret_key=Hash(
            "0xa2333eef5630066b928dea5fd85a239f511b5b067d1441ee7ac290d0122b917b"
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
