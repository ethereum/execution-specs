"""
Ported from:
tests/static/state_tests/stStaticCall/static_CallToReturn1Filler.json

contract code:
    push1 0x01
    push1 0x1f
    push1 0x00
    push1 0x00
    push20 0xd0a322c1ea1978a5d1edb863e5a6c9027039bf6c
    push2 0x03e8
    staticcall
    push1 0x00
    sstore
    push1 0x00
    mload
    push1 0x01
    sstore
    stop

callee code:
    push1 0x2a
    push1 0x1f
    mstore8
    push1 0x01
    push1 0x1f
    return
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
    ["tests/static/state_tests/stStaticCall/static_CallToReturn1Filler.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_static_call_to_return1(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test ported from static filler."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = Address("0xebaf50debf10e08302fe4280c32df010463ca297")
    contract = Address("0x60f1c8af50c827c6787a7bc5249e9bdde475a4ba")
    callee = Address("0xd0a322c1ea1978a5d1edb863e5a6c9027039bf6c")

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=10000000,
    )

    pre[contract] = Account(
        balance=0xde0b6b3a7640000,
        nonce=0,
        code=(
        Op.PUSH1[0x1] + Op.PUSH1[0x1f] + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH20[0xd0a322c1ea1978a5d1edb863e5a6c9027039bf6c] + Op.PUSH2[0x3e8]
        + Op.STATICCALL + Op.PUSH1[0x0] + Op.SSTORE + Op.PUSH1[0x0] + Op.MLOAD
        + Op.PUSH1[0x1] + Op.SSTORE + Op.STOP
    ),
    )
    pre[callee] = Account(
        balance=23,
        nonce=0,
        code=(
        Op.PUSH1[0x2a] + Op.PUSH1[0x1f] + Op.MSTORE8 + Op.PUSH1[0x1]
        + Op.PUSH1[0x1f] + Op.RETURN
    ),
    )
    pre[sender] = Account(balance=0xde0b6b3a7640000, nonce=0)

    tx = Transaction(
        secret_key=Hash(
            "0xe04d1ac7ddda0c98397d56a0b501e960d4cd325a39286919ac23c1a07009a869"
        ),
        to=contract,
        data=b"",
        gas_limit=300000,
        gas_price=10,
        nonce=0,
        value=100000,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)
