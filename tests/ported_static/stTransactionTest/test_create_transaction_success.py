"""
test_create_transaction_success

Ported from:
state_tests/stTransactionTest/CreateTransactionSuccessFiller.json
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

REFERENCE_SPEC_GIT_PATH = "N/A"

REFERENCE_SPEC_VERSION = "N/A"


@pytest.mark.ported_from(
    ["state_tests/stTransactionTest/CreateTransactionSuccessFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_create_transaction_success(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """test_create_transaction_success"""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = EOA(
        key=0x45a915e4d060149eb4365960e6a7a45f334393093061116b197e3240065ff2d8
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        difficulty=0x20000,
        base_fee_per_gas=10,
        gas_limit=1000000000000,
    )

    pre[sender] = Account(balance=0x5f5e100)


    tx = Transaction(
        sender=sender,
        to=None,
        data=bytes.fromhex("602280600c6000396000f30060e060020a600035048063f8a8fd6d14601457005b601a6020565b60006000f35b56"),  # noqa: E501
        gas_limit=70000,
        value=100,
        nonce=0,
        gas_price=10,
    )

    post = {
        Address("0x6295ee1b4f6dd65047762f924ecd367c17eabf8f"): Account(
                storage={},
                code=bytes.fromhex("60e060020a600035048063f8a8fd6d14601457005b601a6020565b60006000f35b56"),  # noqa: E501
                balance=100,
                nonce=1,
            ),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
