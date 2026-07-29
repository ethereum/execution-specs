"""
Measure the gas cost of PUSH0 and of PUSH1 0x00: each case asserts its own
fork-derived cost, which together demonstrate PUSH0 is the cheaper encoding.

Ported from:
state_tests/Shanghai/stEIP3855_push0/push0Gas2Filler.yml

@manually-enhanced: Do not overwrite. Opcode gas via CodeGasMeasure.
"""

import pytest
from execution_testing import (
    Account,
    Alloc,
    Bytecode,
    CodeGasMeasure,
    Fork,
    StateTestFiller,
    Transaction,
)
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


@pytest.mark.ported_from(
    ["state_tests/Shanghai/stEIP3855_push0/push0Gas2Filler.yml"],
)
@pytest.mark.valid_from("Shanghai")
@pytest.mark.parametrize(
    "opcode",
    [Op.PUSH0, Op.PUSH1[0x00]],
    ids=["use_push0", "use_push1_00"],
)
def test_push0_gas2(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    opcode: Bytecode,
) -> None:
    """Measure the parametrized push encoding's exact gas cost."""
    sender = pre.fund_eoa()

    measured = pre.deploy_contract(
        code=CodeGasMeasure(
            code=opcode,
            extra_stack_items=1,
            sstore_key=0x0,
        ),
    )

    tx = Transaction(
        sender=sender,
        to=measured,
    )

    post = {measured: Account(storage={0x0: opcode.gas_cost(fork)})}

    state_test(pre=pre, post=post, tx=tx)
