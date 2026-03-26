"""
test_self_balance

Ported from:
state_tests/stSelfBalance/selfBalanceFiller.json
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
    ["state_tests/stSelfBalance/selfBalanceFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_self_balance(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """test_self_balance"""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = EOA(
        key=0x897b12d02d588d8a4fe16ff831cbd4459c6f62f8c845b0ccdd31caf068c84a26
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        difficulty=0x20000,
        base_fee_per_gas=10,
        gas_limit=10000000000,
    )

    # Source: lll
    # { [[ 1 ]] (SELFBALANCE) }
    target = pre.deploy_contract(
        code=Op.SSTORE(key=0x1, value=Op.SELFBALANCE) + Op.STOP,
        balance=500,
        nonce=0,
        address=Address("0xc4686d898faa85a20d23378b84956c9e10295db5"),  # noqa: E501
    )
    pre[sender] = Account(balance=0x3635c9adc5dea00000)


    tx = Transaction(
        sender=sender,
        to=target,
        data=b'',
        gas_limit=100000,
        nonce=0,
        gas_price=10,
    )

    post = {target: Account(storage={1: 500})}

    state_test(env=env, pre=pre, post=post, tx=tx)
