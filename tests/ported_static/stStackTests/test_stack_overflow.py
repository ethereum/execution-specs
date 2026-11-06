"""
Test filling the stack to its limit, and one past it, in creation code.

Ported from:
state_tests/stStackTests/stackOverflowFiller.json
state_tests/stStackTests/stackOverflowM1Filler.json
state_tests/stStackTests/stackOverflowDUPFiller.json
state_tests/stStackTests/stackOverflowM1DUPFiller.json
state_tests/stStackTests/stackOverflowPUSHFiller.json
state_tests/stStackTests/stackOverflowM1PUSHFiller.json
state_tests/stStackTests/stackOverflowSWAPFiller.json
state_tests/stStackTests/stacksanitySWAPFiller.json
"""

import pytest
from execution_testing import (
    Account,
    Alloc,
    Bytecode,
    Fork,
    StateTestFiller,
    Transaction,
    compute_create_address,
)
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"

TX_VALUE = 1

SINGLE_PUSH_OPCODES = [
    Op.ADDRESS,
    Op.ORIGIN,
    Op.CALLER,
    Op.CALLVALUE,
    Op.CALLDATASIZE,
    Op.CODESIZE,
    Op.GASPRICE,
    Op.COINBASE,
    Op.TIMESTAMP,
    Op.NUMBER,
    Op.PREVRANDAO,
    Op.GASLIMIT,
    Op.PC,
    Op.MSIZE,
    Op.GAS,
]
PUSH_OPCODES = [getattr(Op, f"PUSH{n}") for n in range(1, 33)]
DUP_OPCODES = [getattr(Op, f"DUP{n}") for n in range(1, 17)]


def fill_stack(opcode: Op, height: int) -> Bytecode:
    """Return code that grows the stack to `height` items via `opcode`."""
    if opcode in PUSH_OPCODES:
        return opcode[0] * height
    if opcode in DUP_OPCODES:
        depth = DUP_OPCODES.index(opcode) + 1
        prefix = sum((Op.PUSH1[n] for n in range(1, depth + 1)), Bytecode())
        return prefix + opcode * (height - depth)
    return opcode * height


@pytest.mark.ported_from(
    [
        "state_tests/stStackTests/stackOverflowFiller.json",
        "state_tests/stStackTests/stackOverflowM1Filler.json",
        "state_tests/stStackTests/stackOverflowDUPFiller.json",
        "state_tests/stStackTests/stackOverflowM1DUPFiller.json",
        "state_tests/stStackTests/stackOverflowPUSHFiller.json",
        "state_tests/stStackTests/stackOverflowM1PUSHFiller.json",
    ],
)
@pytest.mark.valid_from("Frontier")
@pytest.mark.parametrize(
    "overflow", [pytest.param(False, id="at_limit"), True]
)
@pytest.mark.parametrize(
    "opcode",
    [
        pytest.param(op, id=str(op).lower())
        for op in SINGLE_PUSH_OPCODES + PUSH_OPCODES + DUP_OPCODES
    ],
)
def test_stack_overflow(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    opcode: Op,
    overflow: bool,
) -> None:
    """Create a contract whose init code fills the stack via `opcode`."""
    height = fork.max_stack_height() + int(overflow)
    sender = pre.fund_eoa()

    tx = Transaction(
        sender=sender,
        to=None,
        data=fill_stack(opcode, height),
        value=TX_VALUE,
        protected=fork.supports_protected_txs(),
    )

    created = compute_create_address(address=sender, nonce=0)
    post = {
        created: Account.NONEXISTENT if overflow else Account(balance=TX_VALUE)
    }

    state_test(pre=pre, post=post, tx=tx)


@pytest.mark.ported_from(
    [
        "state_tests/stStackTests/stackOverflowSWAPFiller.json",
        "state_tests/stStackTests/stacksanitySWAPFiller.json",
    ],
)
@pytest.mark.valid_from("Frontier")
def test_stack_full_swap(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """Create a contract whose init code swaps on a full stack."""
    sender = pre.fund_eoa()

    tx = Transaction(
        sender=sender,
        to=None,
        data=Op.PUSH1[0] * fork.max_stack_height() + Op.SWAP1,
        value=TX_VALUE,
        protected=fork.supports_protected_txs(),
    )

    post = {
        compute_create_address(address=sender, nonce=0): Account(
            balance=TX_VALUE
        ),
    }

    state_test(pre=pre, post=post, tx=tx)
