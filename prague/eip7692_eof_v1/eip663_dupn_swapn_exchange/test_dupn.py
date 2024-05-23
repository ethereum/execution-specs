"""
abstract: Tests [EIP-663: SWAPN, DUPN and EXCHANGE instructions](https://eips.ethereum.org/EIPS/eip-663)
    Tests for the DUPN instruction.
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

from ..eip3540_eof_v1.spec import EOF_FORK_NAME
from . import REFERENCE_SPEC_GIT_PATH, REFERENCE_SPEC_VERSION

REFERENCE_SPEC_GIT_PATH = REFERENCE_SPEC_GIT_PATH
REFERENCE_SPEC_VERSION = REFERENCE_SPEC_VERSION


@pytest.mark.valid_from(EOF_FORK_NAME)
def test_dupn_all_valid_immediates(
    tx: Transaction,
    state_test: StateTestFiller,
):
    """
    Test case for all valid DUPN immediates.
    """
    n = 2**8
    values = range(0xD00, 0xD00 + n)

    eof_code = Container(
        sections=[
            Section.Code(
                code=b"".join(Op.PUSH2(v) for v in values)
                + b"".join(Op.SSTORE(x, Op.DUPN[x]) for x in range(0, n))
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

    post = {tx.to: Account(storage=dict(zip(range(0, n), reversed(values))))}

    state_test(
        env=Environment(),
        pre=pre,
        post=post,
        tx=tx,
    )


@pytest.mark.parametrize(
    "stack_height,max_stack_height",
    [
        [0, 0],
        [0, 1],
        [1, 1],
        [1, 2],
        [2**8 - 1, 2**8 - 1],
        [2**8 - 1, 2**8],
    ],
)
@pytest.mark.valid_from(EOF_FORK_NAME)
def test_dupn_stack_underflow(
    stack_height: int,
    max_stack_height: int,
    eof_test: EOFTestFiller,
):
    """
    Test case out of bounds DUPN immediate.
    """
    eof_code = Container(
        sections=[
            Section.Code(
                code=b"".join(Op.PUSH2(v) for v in range(0, stack_height))
                + Op.DUPN[stack_height]
                + Op.STOP,
                code_inputs=0,
                code_outputs=NON_RETURNING_SECTION,
                max_stack_height=max_stack_height,
            )
        ],
    )
    eof_test(
        data=eof_code,
        expect_exception=EOFException.STACK_UNDERFLOW,
    )


@pytest.mark.parametrize(
    "dupn_operand,max_stack_height,expect_exception",
    [
        [0, MAX_OPERAND_STACK_HEIGHT, EOFException.INVALID_MAX_STACK_HEIGHT],
        [0, MAX_OPERAND_STACK_HEIGHT + 1, EOFException.MAX_STACK_HEIGHT_ABOVE_LIMIT],
        [2**8 - 1, MAX_OPERAND_STACK_HEIGHT, EOFException.INVALID_MAX_STACK_HEIGHT],
        [2**8 - 1, MAX_OPERAND_STACK_HEIGHT + 1, EOFException.MAX_STACK_HEIGHT_ABOVE_LIMIT],
    ],
)
@pytest.mark.valid_from(EOF_FORK_NAME)
def test_dupn_stack_overflow(
    dupn_operand: int,
    max_stack_height: int,
    expect_exception: EOFException,
    eof_test: EOFTestFiller,
):
    """
    Test case where DUPN produces an stack overflow.
    """
    eof_code = Container(
        sections=[
            Section.Code(
                code=b"".join(Op.PUSH2(v) for v in range(0, MAX_OPERAND_STACK_HEIGHT))
                + Op.DUPN[dupn_operand]
                + Op.STOP,
                code_inputs=0,
                code_outputs=NON_RETURNING_SECTION,
                max_stack_height=max_stack_height,
            )
        ],
    )
    eof_test(
        data=eof_code,
        expect_exception=expect_exception,
    )
