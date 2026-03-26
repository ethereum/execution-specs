"""
test_execute_call_that_ask_fore_gas_then_trabsaction_has

Ported from:
state_tests/stEIP150Specific/ExecuteCallThatAskForeGasThenTrabsactionHasFiller.json
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
    ["state_tests/stEIP150Specific/ExecuteCallThatAskForeGasThenTrabsactionHasFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_execute_call_that_ask_fore_gas_then_trabsaction_has(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """test_execute_call_that_ask_fore_gas_then_trabsaction_has"""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = EOA(
        key=0xa2333eef5630066b928dea5fd85a239f511b5b067d1441ee7ac290d0122b917b
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

    pre[sender] = Account(balance=0x5f5e100)
    # Source: lll
    # { [[1]] (CALL 600000 <contract:0x1000000000000000000000000000000000000001> 0 0 0 0 0) }
    target = pre.deploy_contract(
        code=Op.SSTORE(key=0x1, value=Op.CALL(gas=0x927c0, address=0xbfdd294028701b119d416c68eff7dd9f7effd249, value=0x0, args_offset=0x0, args_size=0x0, ret_offset=0x0, ret_size=0x0))  # noqa: E501
        + Op.STOP,
        nonce=0,
        address=Address("0x1819cf5bff62f0d379f146b85baaf9bd18239832"),  # noqa: E501
    )
    # Source: lll
    # { [[1]] 12 }
    addr_0x1000000000000000000000000000000000000001 = pre.deploy_contract(
        code=Op.SSTORE(key=0x1, value=0xc) + Op.STOP,
        balance=0x186a0,
        nonce=0,
        address=Address("0xbfdd294028701b119d416c68eff7dd9f7effd249"),  # noqa: E501
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
        addr_0x1000000000000000000000000000000000000001: Account(storage={1: 12}),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
