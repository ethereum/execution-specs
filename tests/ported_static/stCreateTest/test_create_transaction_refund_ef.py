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
    Bytes,
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
    """Test combination of gas refund and EF-prefixed create transaction..."""
    contract_0 = Address(0x00000000000000000000000000000000005EF94D)
    sender = EOA(
        key=0x45A915E4D060149EB4365960E6A7A45F334393093061116B197E3240065FF2D8
    )

    env = Environment(
        fee_recipient=sender,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=1000000,
    )

    pre[sender] = Account(balance=0x5AF3107A4000)
    # Source: yul
    # berlin {
    #   sstore(0,0)
    # }
    contract_0 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=Op.DUP1, value=0x0) + Op.STOP,
        storage={0: 1},
        nonce=0,
        address=Address(0x00000000000000000000000000000000005EF94D),  # noqa: E501
    )

    tx = Transaction(
        sender=sender,
        to=None,
        data=Bytes("600080808080625ef94d61c350f15060ef60005360016000f3"),
        gas_limit=100000,
    )

    post = {
        contract_0: Account(storage={0: 1}),
        Address(
            "0x6295ee1b4f6dd65047762f924ecd367c17eabf8f"
        ): Account.NONEXISTENT,
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
