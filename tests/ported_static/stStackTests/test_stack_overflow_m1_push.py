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
        Op.PUSH1,
        Op.PUSH2,
        Op.PUSH3,
        Op.PUSH4,
        Op.PUSH5,
        Op.PUSH6,
        Op.PUSH7,
        Op.PUSH8,
        Op.PUSH9,
        Op.PUSH10,
        Op.PUSH11,
        Op.PUSH12,
        Op.PUSH13,
        Op.PUSH14,
        Op.PUSH15,
        Op.PUSH16,
        Op.PUSH17,
        Op.PUSH18,
        Op.PUSH19,
        Op.PUSH20,
        Op.PUSH21,
        Op.PUSH22,
        Op.PUSH23,
        Op.PUSH24,
        Op.PUSH25,
        Op.PUSH26,
        Op.PUSH27,
        Op.PUSH28,
        Op.PUSH29,
        Op.PUSH30,
        Op.PUSH31,
        Op.PUSH32,
    ],
)
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
