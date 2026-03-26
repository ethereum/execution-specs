"""
Test combination of gas refund and EF-prefixed create transaction failure.


Ported from:
state_tests/stCreateTest/CreateTransactionRefundEFFiller.yml
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
    ["state_tests/stCreateTest/CreateTransactionRefundEFFiller.yml"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_create_transaction_refund_ef(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test combination of gas refund and EF-prefixed create transaction f..."""
    contract_0 = Address("0x00000000000000000000000000000000005ef94d")
    sender = EOA(
        key=0x45a915e4d060149eb4365960e6a7a45f334393093061116b197e3240065ff2d8
    )

    env = Environment(
        fee_recipient=sender,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        difficulty=1,
        base_fee_per_gas=10,
        gas_limit=1000000,
    )

    pre[sender] = Account(balance=0x5af3107a4000)
    # Source: yul
    # berlin {
    #   sstore(0,0)
    # }
    contract_0 = pre.deploy_contract(
        code=Op.SSTORE(key=Op.DUP1, value=0x0) + Op.STOP,
        storage={0: 1},
        nonce=0,
        address=Address("0x00000000000000000000000000000000005ef94d"),  # noqa: E501
    )


    tx = Transaction(
        sender=sender,
        to=None,
        data=bytes.fromhex("600080808080625ef94d61c350f15060ef60005360016000f3"),  # noqa: E501
        gas_limit=100000,
        nonce=0,
        gas_price=10,
    )

    post = {
        contract_0: Account(storage={0: 1}),
        Address("0x6295ee1b4f6dd65047762f924ecd367c17eabf8f"): Account.NONEXISTENT,  # noqa: E501
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
