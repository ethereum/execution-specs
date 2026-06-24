"""
Test_non_zero_value_delegatecall_to_one_storage_key_paris.

Ported from:
state_tests/stNonZeroCallsTest/NonZeroValue_DELEGATECALL_ToOneStorageKey_ParisFiller.json

@manually-enhanced: Do not overwrite. DELEGATECALL gas via CodeGasMeasure.
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
        "state_tests/stNonZeroCallsTest/NonZeroValue_DELEGATECALL_ToOneStorageKey_ParisFiller.json"
    ],
)
@pytest.mark.valid_from("Berlin")
def test_non_zero_value_delegatecall_to_one_storage_key_paris(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """Measure DELEGATECALL gas to a cold account with storage."""
    call_target = pre.deploy_contract(code=b"", balance=10, storage={0x0: 0x1})
    call_code = Op.DELEGATECALL(
        gas=0xEA60,
        address=call_target,
        address_warm=False,
    )
    contract_0 = pre.deploy_contract(
        code=CodeGasMeasure(
            code=call_code,
            extra_stack_items=1,
            sstore_key=0x64,
        ),
    )

    tx = Transaction(
        sender=pre.fund_eoa(),
        to=contract_0,
        state_gas_reservoir=0,
    )

    post = {
        contract_0: Account(
            storage={0x64: call_code.gas_cost(fork)},
        ),
        call_target: Account(storage={0x0: 0x1}, balance=10),
    }

    state_test(pre=pre, post=post, tx=tx)
