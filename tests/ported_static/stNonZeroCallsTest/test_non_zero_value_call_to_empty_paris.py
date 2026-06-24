"""
Test_non_zero_value_call_to_empty_paris.

Ported from:
state_tests/stNonZeroCallsTest/NonZeroValue_CALL_ToEmpty_ParisFiller.json

@manually-enhanced: Do not overwrite. CALL gas via CodeGasMeasure.
"""

import pytest
from execution_testing import (
    Account,
    Alloc,
    CodeGasMeasure,
    Fork,
    StateTestFiller,
    Transaction,
)
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


@pytest.mark.ported_from(
    [
        "state_tests/stNonZeroCallsTest/NonZeroValue_CALL_ToEmpty_ParisFiller.json"
    ],
)
@pytest.mark.valid_from("Berlin")
def test_non_zero_value_call_to_empty_paris(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """Measure CALL gas with value to a cold, existing account."""
    contract_balance = 100
    call_value = 1

    call_target = pre.fund_eoa(amount=10)
    call_code = Op.CALL(
        gas=0xEA60,
        address=call_target,
        value=call_value,
        address_warm=False,
        value_transfer=True,
        account_new=False,
    )
    contract_0 = pre.deploy_contract(
        code=CodeGasMeasure(
            code=call_code,
            extra_stack_items=1,
            sstore_key=0x64,
        ),
        balance=contract_balance,
    )

    tx = Transaction(
        sender=pre.fund_eoa(),
        to=contract_0,
        state_gas_reservoir=0,
    )

    post = {
        contract_0: Account(
            storage={
                0x64: call_code.gas_cost(fork) - fork.gas_costs().CALL_STIPEND
            },
        ),
        call_target: Account(balance=10 + call_value),
    }

    state_test(pre=pre, post=post, tx=tx)
