"""
Measure the gas cost of the PUSH0 instruction.

Ported from:
state_tests/Shanghai/stEIP3855_push0/push0GasFiller.yml

@manually-enhanced: Do not overwrite. PUSH0 gas via CodeGasMeasure.
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
    ["state_tests/Shanghai/stEIP3855_push0/push0GasFiller.yml"],
)
@pytest.mark.valid_from("Shanghai")
def test_push0_gas(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """Measure PUSH0's gas cost against the fork-derived expectation."""
    sender = pre.fund_eoa()

    push0_code = Op.PUSH0
    target = pre.deploy_contract(
        code=CodeGasMeasure(
            code=push0_code,
            extra_stack_items=1,
            sstore_key=0x1,
        ),
    )

    tx = Transaction(
        sender=sender,
        to=target,
    )

    post = {target: Account(storage={0x1: push0_code.gas_cost(fork)})}

    state_test(pre=pre, post=post, tx=tx)
