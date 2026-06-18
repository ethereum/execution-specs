"""
Test_static_make_money.

Ported from:
state_tests/stStaticCall/static_makeMoneyFiller.json

@manually-enhanced: Do not overwrite.
"""

import pytest
from execution_testing import Account, Alloc, StateTestFiller, Transaction
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


@pytest.mark.ported_from(
    ["state_tests/stStaticCall/static_makeMoneyFiller.json"],
)
@pytest.mark.valid_from("Cancun")
def test_static_make_money(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test_static_make_money."""
    sender = pre.fund_eoa()

    contracts_starting_balance = 1

    subcall_contract = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x1, value=0x1)
        + Op.SSTORE(key=0x2, value=Op.ORIGIN),
        balance=contracts_starting_balance,
    )
    entry_contract = pre.deploy_contract(  # noqa: F841
        code=Op.MSTORE(
            offset=0x0,
            value=0x601080600C6000396000F20060003554156009570060203560003555,
        )
        + Op.STATICCALL(
            gas=2**256 - 20,
            address=subcall_contract,
        )
        + Op.STOP,
        balance=contracts_starting_balance,
    )

    tx_value = 1
    tx = Transaction(sender=sender, to=entry_contract, value=tx_value)

    post = {
        entry_contract: Account(
            balance=contracts_starting_balance + tx_value,
        ),
        subcall_contract: Account(
            balance=contracts_starting_balance,
            storage={
                1: 0,
                2: 0,
            },
        ),
    }

    state_test(pre=pre, post=post, tx=tx)
