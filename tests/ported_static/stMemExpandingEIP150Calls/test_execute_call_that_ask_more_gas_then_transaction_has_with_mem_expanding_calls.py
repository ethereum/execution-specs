"""
test_execute_call_that_ask_more_gas_then_transaction_has_with_mem_expanding_calls

Ported from:
state_tests/stMemExpandingEIP150Calls/ExecuteCallThatAskMoreGasThenTransactionHasWithMemExpandingCallsFiller.json
"""

import pytest
from execution_testing import (
    EOA,
    Account,
    Address,
    Alloc,
    Environment,
    StateTestFiller,
    Transaction,
)
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"

REFERENCE_SPEC_VERSION = "N/A"


@pytest.mark.ported_from(
    ["state_tests/stMemExpandingEIP150Calls/ExecuteCallThatAskMoreGasThenTransactionHasWithMemExpandingCallsFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_execute_call_that_ask_more_gas_then_transaction_has_with_mem_expanding_calls(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """test_execute_call_that_ask_more_gas_then_transaction_has_with_mem_e..."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = EOA(
        key=0x6a3a7e4100e459734759453f3aebb7f5fe9b806baa83232cd5c42fe0a359ca67
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        difficulty=0x20000,
        base_fee_per_gas=10,
        gas_limit=10000000,
    )

    pre[sender] = Account(balance=0x186a000)
    # Source: hex
    # 0x60ff60ff60ff60ff600073<contract:0x1000000000000000000000000000000000000001>620927c0f1600155
    target = pre.deploy_contract(
        code=Op.SSTORE(key=0x1, value=Op.CALL(gas=0x927c0, address=0x73d01f7d28c5a55520cd80d2c3f0938c1834ccff, value=0x0, args_offset=0xff, args_size=0xff, ret_offset=0xff, ret_size=0xff)),  # noqa: E501
        nonce=0,
        address=Address("0xbdbacb5fb8222511832eb176b990cd8ad511c271"),  # noqa: E501
    )
    # Source: hex
    # 0x600c600155
    addr_0x1000000000000000000000000000000000000001 = pre.deploy_contract(
        code=Op.SSTORE(key=0x1, value=0xc),
        balance=0x186a0,
        nonce=0,
        address=Address("0x73d01f7d28c5a55520cd80d2c3f0938c1834ccff"),  # noqa: E501
    )


    tx = Transaction(
        sender=sender,
        to=target,
        data=b'',
        gas_limit=100000,
        nonce=0,
        gas_price=10,
    )

    post = {
        sender: Account(nonce=1),
        target: Account(storage={1: 1}),
        addr_0x1000000000000000000000000000000000000001: Account(storage={1: 12}, balance=0x186a0),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
