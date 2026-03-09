"""
Test ported from static filler.

Ported from:
tests/static/state_tests/stEIP150Specific
ExecuteCallThatAskForeGasThenTrabsactionHasFiller.json
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
    [
        "tests/static/state_tests/stEIP150Specific/ExecuteCallThatAskForeGasThenTrabsactionHasFiller.json",  # noqa: E501
    ],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_execute_call_that_ask_fore_gas_then_trabsaction_has(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test ported from static filler."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = EOA(
        key=0xA2333EEF5630066B928DEA5FD85A239F511B5B067D1441EE7AC290D0122B917B
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=10000000,
    )

    # Source: LLL
    # { [[1]] (CALL 600000 <contract:0x1000000000000000000000000000000000000001> 0 0 0 0 0) }  # noqa: E501
    contract = pre.deploy_contract(
        code=(
            Op.SSTORE(
                key=0x1,
                value=Op.CALL(
                    gas=0x927C0,
                    address=0xBFDD294028701B119D416C68EFF7DD9F7EFFD249,
                    value=0x0,
                    args_offset=0x0,
                    args_size=0x0,
                    ret_offset=0x0,
                    ret_size=0x0,
                ),
            )
            + Op.STOP
        ),
        nonce=0,
        address=Address("0x1819cf5bff62f0d379f146b85baaf9bd18239832"),  # noqa: E501
    )
    pre[sender] = Account(balance=0x5F5E100)
    callee = pre.deploy_contract(
        code=Op.SSTORE(key=0x1, value=0xC) + Op.STOP,
        balance=0x186A0,
        nonce=0,
        address=Address("0xbfdd294028701b119d416c68eff7dd9f7effd249"),  # noqa: E501
    )

    tx = Transaction(
        sender=sender,
        to=contract,
        gas_limit=100000,
    )

    post = {
        contract: Account(storage={1: 1}),
        callee: Account(storage={1: 12}),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
