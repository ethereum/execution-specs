"""
abstract: Tests [EIP-663: SWAPN, DUPN and EXCHANGE instructions](https://eips.ethereum.org/EIPS/eip-663)
    Tests for the SWAPN instruction.
"""  # noqa: E501

import pytest

from ethereum_test_tools import (
    Account,
    Environment,
    EOFException,
    EOFTestFiller,
    StateTestFiller,
    TestAddress,
    Transaction,
)
from ethereum_test_tools.eof.v1 import Container, Section
from ethereum_test_tools.eof.v1.constants import MAX_OPERAND_STACK_HEIGHT, NON_RETURNING_SECTION
from ethereum_test_tools.vm.opcode import Opcodes as Op

from .. import EOF_FORK_NAME
from . import REFERENCE_SPEC_GIT_PATH, REFERENCE_SPEC_VERSION

REFERENCE_SPEC_GIT_PATH = REFERENCE_SPEC_GIT_PATH
REFERENCE_SPEC_VERSION = REFERENCE_SPEC_VERSION


@pytest.mark.valid_from(EOF_FORK_NAME)
def test_swapn_all_valid_immediates(
    tx: Transaction,
    state_test: StateTestFiller,
):
    """
    Test case for all valid SWAPN immediates.
    """
    n = 256
    values = range(0x500, 0x500 + 257)

    eof_code = Container(
        sections=[
            Section.Code(
                code=b"".join(Op.PUSH2(v) for v in values)
                + b"".join(Op.SSTORE(x, Op.SWAPN[0xFF - x]) for x in range(0, n))
                + Op.STOP,
                code_inputs=0,
                code_outputs=NON_RETURNING_SECTION,
                max_stack_height=n + 2,
            )
        ],
    )

    pre = {
        TestAddress: Account(balance=1_000_000_000),
        tx.to: Account(code=eof_code),
    }

    values_rotated = list(values[1:]) + [values[0]]
    post = {tx.to: Account(storage=dict(zip(range(0, n), reversed(values_rotated))))}

    state_test(
        env=Environment(),
        pre=pre,
        post=post,
        tx=tx,
    )


@pytest.mark.parametrize(
    "swapn_operand",
    [
        0,
        2**8 - 1,
    ],
)
@pytest.mark.valid_from(EOF_FORK_NAME)
def test_swapn_on_max_stack(
    swapn_operand: int,
    eof_test: EOFTestFiller,
):
    """
    Test case out of bounds DUPN immediate.
    """
    eof_code = Container(
        sections=[
            Section.Code(
                code=b"".join(Op.PUSH2(v) for v in range(0, MAX_OPERAND_STACK_HEIGHT))
                + Op.SWAPN[swapn_operand]
                + Op.STOP,
                code_inputs=0,
                code_outputs=NON_RETURNING_SECTION,
                max_stack_height=MAX_OPERAND_STACK_HEIGHT,
            )
        ],
    )
    eof_test(
        data=eof_code,
    )


@pytest.mark.parametrize(
    "stack_height",
    [
        0,
        1,
        2**8 - 1,
    ],
)
@pytest.mark.valid_from(EOF_FORK_NAME)
def test_swapn_stack_underflow(
    stack_height: int,
    eof_test: EOFTestFiller,
):
    """
    Test case out of bounds DUPN immediate.
    """
    eof_code = Container(
        sections=[
            Section.Code(
                code=b"".join(Op.PUSH2(v) for v in range(0, stack_height))
                + Op.SWAPN[stack_height]
                + Op.STOP,
                code_inputs=0,
                code_outputs=NON_RETURNING_SECTION,
                max_stack_height=MAX_OPERAND_STACK_HEIGHT,
            )
        ],
    )
    eof_test(
        data=eof_code,
        expect_exception=EOFException.STACK_UNDERFLOW,
    )
