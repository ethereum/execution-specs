"""
Ported from:
tests/static/state_tests/stLogTests/log0_emptyMemFiller.json

contract code:
    push1 0x00
    push1 0x00
    push1 0x00
    push1 0x00
    push1 0x17
    push20 0xc2a943e837808399d9c1b946c6188739d4d4475e
    push2 0x03e8
    call
    push1 0x00
    sstore
    stop

callee code:
    push1 0x00
    push1 0x00
    log0
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
    ["tests/static/state_tests/stLogTests/log0_emptyMemFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_log0_empty_mem(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test ported from static filler."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = Address("0xebaf50debf10e08302fe4280c32df010463ca297")
    contract = Address("0x1e5597b6168fe79952cb2de7af91c3449bc95bd4")
    callee = Address("0xc2a943e837808399d9c1b946c6188739d4d4475e")

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=1000000,
    )

    pre[contract] = Account(
        balance=0xde0b6b3a7640000,
        nonce=0,
        code=(
        Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH1[0x17] + Op.PUSH20[0xc2a943e837808399d9c1b946c6188739d4d4475e]
        + Op.PUSH2[0x3e8] + Op.CALL + Op.PUSH1[0x0] + Op.SSTORE + Op.STOP
    ),
    )
    pre[callee] = Account(
        balance=0xde0b6b3a7640000,
        nonce=0,
        code=Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.LOG0 + Op.STOP,
    )
    pre[sender] = Account(balance=0xde0b6b3a7640000, nonce=0)

    tx = Transaction(
        secret_key=Hash(
            "0xe04d1ac7ddda0c98397d56a0b501e960d4cd325a39286919ac23c1a07009a869"
        ),
        to=contract,
        data=b"",
        gas_limit=210000,
        gas_price=10,
        nonce=0,
        value=100000,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)
