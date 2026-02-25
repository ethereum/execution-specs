"""
Ported from:
tests/static/state_tests/stMemExpandingEIP150Calls/ExecuteCallThatAskMoreGasThenTransactionHasWithMemExpandingCallsFiller.json

callee code:
    push1 0x0c
    push1 0x01
    sstore

contract code:
    push1 0xff
    push1 0xff
    push1 0xff
    push1 0xff
    push1 0x00
    push20 0x73d01f7d28c5a55520cd80d2c3f0938c1834ccff
    push3 0x0927c0
    call
    push1 0x01
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
    ["tests/static/state_tests/stMemExpandingEIP150Calls/ExecuteCallThatAskMoreGasThenTransactionHasWithMemExpandingCallsFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_execute_call_that_ask_more_gas_then_transaction_has_with_mem_expanding_calls(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test ported from static filler."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = Address("0xc47e84e3d3b68b50c9a630067216938478842d46")
    contract = Address("0xbdbacb5fb8222511832eb176b990cd8ad511c271")
    callee = Address("0x73d01f7d28c5a55520cd80d2c3f0938c1834ccff")

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=10000000,
    )

    pre[callee] = Account(balance=0x186a0, nonce=0, code=Op.PUSH1[0xc] + Op.PUSH1[0x1] + Op.SSTORE)
    pre[contract] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.PUSH1[0xff] + Op.PUSH1[0xff] + Op.PUSH1[0xff] + Op.PUSH1[0xff]
        + Op.PUSH1[0x0] + Op.PUSH20[0x73d01f7d28c5a55520cd80d2c3f0938c1834ccff]
        + Op.PUSH3[0x927c0] + Op.CALL + Op.PUSH1[0x1] + Op.SSTORE
    ),
    )
    pre[sender] = Account(balance=0x186a000, nonce=0)

    tx = Transaction(
        secret_key=Hash(
            "0x6a3a7e4100e459734759453f3aebb7f5fe9b806baa83232cd5c42fe0a359ca67"
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
