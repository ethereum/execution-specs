"""
Test combination of gas refund and EF-prefixed create transaction failure.


Ported from:
state_tests/stCreateTest/CreateTransactionRefundEFFiller.yml
"""

import pytest
from execution_testing import (
    Account,
    Alloc,
    Fork,
    StateTestFiller,
    Transaction,
    compute_create_address,
)
from execution_testing.forks import Amsterdam
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


@pytest.mark.ported_from(
    ["state_tests/stCreateTest/CreateTransactionRefundEFFiller.yml"],
)
@pytest.mark.valid_from("Cancun")
def test_create_transaction_refund_ef(
    state_test: StateTestFiller,
    fork: Fork,
    pre: Alloc,
) -> None:
    """Test combination of gas refund and EF-prefixed create transaction..."""
    sender = pre.fund_eoa(amount=0x5AF3107A4000)

    # Source: yul
    # berlin {
    #   sstore(0,0)
    # }
    contract_0 = pre.deploy_contract(
        code=Op.SSTORE(key=Op.DUP1, value=0x0) + Op.STOP,
        storage={0: 1},
    )

    tx = Transaction(
        sender=sender,
        to=None,
        data=Op.POP(
            Op.CALL(
                gas=0xC350,
                address=contract_0,
                value=Op.DUP1,
                args_offset=Op.DUP1,
                args_size=Op.DUP1,
                ret_offset=Op.DUP1,
                ret_size=0x0,
            )
        )
        + Op.MSTORE8(offset=0x0, value=0xEF)
        + Op.RETURN(offset=0x0, size=0x1),
        gas_limit=2100000 if fork >= Amsterdam else 100000,
    )

    post = {
        contract_0: Account(storage={0: 1}),
        compute_create_address(address=sender, nonce=0): Account.NONEXISTENT,
    }

    state_test(pre=pre, post=post, tx=tx)
