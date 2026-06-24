"""
Test_non_zero_value_call.

Ported from:
state_tests/stNonZeroCallsTest/NonZeroValue_CALLFiller.json

@manually-enhanced: Do not overwrite. Dynamic CALL gas + addresses.
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
    ["state_tests/stNonZeroCallsTest/NonZeroValue_CALLFiller.json"],
)
@pytest.mark.valid_from("Berlin")
def test_non_zero_value_call(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """Test_non_zero_value_call."""
    sender = pre.fund_eoa()
    contract_balance = 100
    call_value = 1

    call_target = pre.nonexistent_account()
    # Source: lll
    # { [0](GAS) [[1]] (CALL 60000 <call_target> 1 0 0 0 0) [[100]] (SUB @0 (GAS)) }  # noqa: E501
    call_code = Op.CALL(
        gas=0xEA60,
        address=call_target,
        value=call_value,
        address_warm=False,
        value_transfer=True,
        account_new=True,
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
        sender=sender,
        to=contract_0,
        state_gas_reservoir=0,
    )

    post = {
        contract_0: Account(
            storage={
                0x64: call_code.gas_cost(fork) - fork.gas_costs().CALL_STIPEND
            },
            balance=contract_balance - call_value,
        ),
        call_target: Account(balance=call_value),
    }

    state_test(pre=pre, post=post, tx=tx)
