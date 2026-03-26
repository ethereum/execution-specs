"""
test_callcode_emptycontract

Ported from:
state_tests/stCallCodes/callcodeEmptycontractFiller.json
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
    ["state_tests/stCallCodes/callcodeEmptycontractFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_callcode_emptycontract(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """test_callcode_emptycontract"""
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

    # Source: lll
    # { [[ 0 ]] (CALLCODE 50000 0x945304eb96065b2a98b57a48a06ae28d285a71b5 1000 0 64 0 64 )}
    target = pre.deploy_contract(
        code=Op.SSTORE(key=0x0, value=Op.CALLCODE(gas=0xc350, address=0x945304eb96065b2a98b57a48a06ae28d285a71b5, value=0x3e8, args_offset=0x0, args_size=0x40, ret_offset=0x0, ret_size=0x40))  # noqa: E501
        + Op.STOP,
        balance=1000,
        nonce=0,
        address=Address("0x594f6a1a002fc9949ac40616cc146845680302e1"),  # noqa: E501
    )
    pre[sender] = Account(balance=0x5f5e100)


    tx = Transaction(
        sender=sender,
        to=target,
        data=b'',
        gas_limit=1050440,
        nonce=0,
        gas_price=10,
    )

    post = {target: Account(storage={0: 1})}

    state_test(env=env, pre=pre, post=post, tx=tx)
