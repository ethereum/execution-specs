"""
Test_stack_overflow_m1_push.

Ported from:
state_tests/stStackTests/stackOverflowM1PUSHFiller.json

@manually-enhanced: Do not overwrite. This test has been manually reviewed and
enhanced.
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
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


@pytest.mark.ported_from(
    ["state_tests/stStackTests/stackOverflowM1PUSHFiller.json"],
)
@pytest.mark.parametrize(
    "opcode",
    [
        # pytest.param(Op.PUSH1, id="d"), Not in baseline
        pytest.param(Op.PUSH2, id="d0"),
        pytest.param(Op.PUSH3, id="d1"),
        pytest.param(Op.PUSH4, id="d2"),
        pytest.param(Op.PUSH5, id="d3"),
        pytest.param(Op.PUSH6, id="d4"),
        pytest.param(Op.PUSH7, id="d5"),
        pytest.param(Op.PUSH8, id="d6"),
        pytest.param(Op.PUSH9, id="d7"),
        pytest.param(Op.PUSH10, id="d8"),
        pytest.param(Op.PUSH11, id="d9"),
        pytest.param(Op.PUSH12, id="d10"),
        pytest.param(Op.PUSH13, id="d11"),
        pytest.param(Op.PUSH14, id="d12"),
        pytest.param(Op.PUSH15, id="d13"),
        pytest.param(Op.PUSH16, id="d14"),
        pytest.param(Op.PUSH17, id="d15"),
        pytest.param(Op.PUSH18, id="d16"),
        pytest.param(Op.PUSH19, id="d17"),
        pytest.param(Op.PUSH20, id="d18"),
        pytest.param(Op.PUSH21, id="d19"),
        pytest.param(Op.PUSH22, id="d20"),
        pytest.param(Op.PUSH23, id="d21"),
        pytest.param(Op.PUSH24, id="d22"),
        pytest.param(Op.PUSH25, id="d23"),
        pytest.param(Op.PUSH26, id="d24"),
        pytest.param(Op.PUSH27, id="d25"),
        pytest.param(Op.PUSH28, id="d26"),
        pytest.param(Op.PUSH29, id="d27"),
        pytest.param(Op.PUSH30, id="d28"),
        pytest.param(Op.PUSH31, id="d29"),
        pytest.param(Op.PUSH32, id="d30"),
    ],
)
@pytest.mark.pre_alloc_mutable
def test_stack_overflow_m1_push(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    opcode: Op,
) -> None:
    """
    Test pushing to the stack with all PUSH* opcodes until almost a stack
    overflow occurs.
    """
    max_stack_height = fork.max_stack_height()
    initcode = opcode[0x0] * max_stack_height
    value = 1
    sender = pre.fund_eoa()
    tx = Transaction(
        sender=sender,
        to=None,
        data=initcode,
        gas_limit=6_000_000,
        value=value,
        protected=fork.supports_protected_txs(),
    )

    post = {
        compute_create_address(address=sender, nonce=0): Account(
            balance=value
        ),
    }

    state_test(pre=pre, post=post, tx=tx)
