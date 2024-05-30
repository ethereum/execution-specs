"""
abstract: Tests [EIP-663: SWAPN, DUPN and EXCHANGE instructions](https://eips.ethereum.org/EIPS/eip-663)
    Tests for the EXCHANGE instruction.
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
from ethereum_test_tools.eof.v1.constants import NON_RETURNING_SECTION
from ethereum_test_tools.vm.opcode import Opcodes as Op

from .. import EOF_FORK_NAME
from . import REFERENCE_SPEC_GIT_PATH, REFERENCE_SPEC_VERSION

REFERENCE_SPEC_GIT_PATH = REFERENCE_SPEC_GIT_PATH
REFERENCE_SPEC_VERSION = REFERENCE_SPEC_VERSION


@pytest.mark.valid_from(EOF_FORK_NAME)
def test_exchange_all_valid_immediates(
    tx: Transaction,
    state_test: StateTestFiller,
):
    """
    Test case for all valid EXCHANGE immediates.
    """
    n = 256
    s = 34
    values = range(0x3E8, 0x3E8 + s)

    eof_code = Container(
        sections=[
            Section.Code(
                code=b"".join(Op.PUSH2(v) for v in values)
                + b"".join(Op.EXCHANGE(x) for x in range(0, n))
                + b"".join((Op.PUSH1(x) + Op.SSTORE) for x in range(0, s))
                + Op.STOP,
                code_inputs=0,
                code_outputs=NON_RETURNING_SECTION,
                max_stack_height=s + 1,
            )
        ],
    )

    pre = {
        TestAddress: Account(balance=1_000_000_000),
        tx.to: Account(code=eof_code),
    }

    # this does the same full-loop exchange
    values_rotated = list(range(0x3E8, 0x3E8 + s))
    for e in range(0, n):
        a = (e >> 4) + 1
        b = (e & 0x0F) + 1 + a
        temp = values_rotated[a]
        values_rotated[a] = values_rotated[b]
        values_rotated[b] = temp

    post = {tx.to: Account(storage=dict(zip(range(0, s), reversed(values_rotated))))}

    state_test(
        env=Environment(),
        pre=pre,
        post=post,
        tx=tx,
    )


@pytest.mark.parametrize(
    "stack_height,x,y",
    [
        # 2 and 3 are the lowest valid values for x and y, which translates to a
        # zero immediate value.
        pytest.param(0, 2, 3, id="stack_height=0_n=1_m=1"),
        pytest.param(1, 2, 3, id="stack_height=1_n=1_m=1"),
        pytest.param(2, 2, 3, id="stack_height=2_n=1_m=1"),
        pytest.param(17, 2, 18, id="stack_height=17_n=1_m=16"),
        pytest.param(17, 17, 18, id="stack_height=17_n=16_m=1"),
        pytest.param(32, 17, 33, id="stack_height=32_n=16_m=16"),
    ],
)
@pytest.mark.valid_from(EOF_FORK_NAME)
def test_exchange_all_invalid_immediates(
    eof_test: EOFTestFiller,
    stack_height: int,
    x: int,
    y: int,
):
    """
    Test case for all invalid EXCHANGE immediates.
    """
    eof_code = Container(
        sections=[
            Section.Code(
                code=b"".join(Op.PUSH2(v) for v in range(stack_height))
                + Op.EXCHANGE[x, y]
                + Op.POP * stack_height
                + Op.STOP,
                code_inputs=0,
                code_outputs=NON_RETURNING_SECTION,
                max_stack_height=stack_height,
            )
        ],
    )

    eof_test(
        data=eof_code,
        expect_exception=EOFException.STACK_UNDERFLOW,
    )
