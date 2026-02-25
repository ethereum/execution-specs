"""
Ported from:
tests/static/state_tests/stMemExpandingEIP150Calls/DelegateCallOnEIPWithMemExpandingCallsFiller.json

contract code:
    gas
    push1 0x08
    sstore
    push1 0xff
    push1 0xff
    push1 0xff
    push1 0xff
    push20 0xa1f6e75a455896613053d45331763a07f4718969
    push3 0x0927c0
    delegatecall
    push1 0x09
    sstore

callee code:
    push1 0x12
    push1 0x00
    sstore
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
    ["tests/static/state_tests/stMemExpandingEIP150Calls/DelegateCallOnEIPWithMemExpandingCallsFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_delegate_call_on_eip_with_mem_expanding_calls(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test ported from static filler."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = Address("0x823066fb511f07f5e49cbd8ca9874e4bc6ee9e65")
    contract = Address("0x3fc906a124d4054023be5dd8666ce29aa3712ccb")
    callee = Address("0xa1f6e75a455896613053d45331763a07f4718969")

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
        Op.GAS + Op.PUSH1[0x8] + Op.SSTORE + Op.PUSH1[0xff] + Op.PUSH1[0xff]
        + Op.PUSH1[0xff] + Op.PUSH1[0xff]
        + Op.PUSH20[0xa1f6e75a455896613053d45331763a07f4718969] + Op.PUSH3[0x927c0]
        + Op.DELEGATECALL + Op.PUSH1[0x9] + Op.SSTORE
    ),
    )
    pre[sender] = Account(balance=0xe8d4a51000, nonce=0)
    pre[callee] = Account(balance=0, nonce=0, code=Op.PUSH1[0x12] + Op.PUSH1[0x0] + Op.SSTORE)

    tx = Transaction(
        secret_key=Hash(
            "0x8d19f2b0d2f5689c1771fbca70476ca6e877a81ee15c3733de87fae38e5abcef"
        ),
        to=contract,
        data=b"",
        gas_limit=600000,
        gas_price=10,
        nonce=0,
        value=0,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)
