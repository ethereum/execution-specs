"""
abstract: Tests [EIP-663: SWAPN, DUPN and EXCHANGE instructions](https://eips.ethereum.org/EIPS/eip-663)
    Tests for the DUPN instruction.
"""  # noqa: E501

import pytest

from ethereum_test_tools import (
    Account,
    Alloc,
    Environment,
    EOFException,
    EOFStateTestFiller,
    EOFTestFiller,
    StateTestFiller,
    Transaction,
)
from ethereum_test_tools.vm.opcode import Opcodes as Op
from ethereum_test_types.eof.v1 import Container, Section
from ethereum_test_types.eof.v1.constants import MAX_STACK_INCREASE_LIMIT

from .. import EOF_FORK_NAME
from . import REFERENCE_SPEC_GIT_PATH, REFERENCE_SPEC_VERSION

REFERENCE_SPEC_GIT_PATH = REFERENCE_SPEC_GIT_PATH
REFERENCE_SPEC_VERSION = REFERENCE_SPEC_VERSION

pytestmark = pytest.mark.valid_from(EOF_FORK_NAME)


def test_dupn_all_valid_immediates(eof_state_test: EOFStateTestFiller):
    """Test case for all valid DUPN immediates."""
    n = 2**8
    values = range(0xD00, 0xD00 + n)

    eof_code = Container(
        sections=[
            Section.Code(
                code=sum(Op.PUSH2[v] for v in values)
                + sum(Op.SSTORE(x, Op.DUPN[x]) for x in range(0, n))
                + Op.STOP,
            )
        ],
    )

    post = Account(storage=dict(zip(range(0, n), reversed(values), strict=False)))

    eof_state_test(
        tx_sender_funding_amount=1_000_000_000,
        container=eof_code,
        container_post=post,
    )


@pytest.mark.parametrize(
    "stack_height,max_stack_height",
    [
        # [0, 0] is tested in test_all_opcodes_stack_underflow()
        [0, 1],
        [1, 1],
        [1, 2],
        [2**8 - 1, 2**8 - 1],
        [2**8 - 1, 2**8],
    ],
)
def test_dupn_stack_underflow(
    stack_height: int,
    max_stack_height: int,
    eof_test: EOFTestFiller,
):
    """Test case out of bounds DUPN immediate."""
    eof_code = Container(
        sections=[
            Section.Code(
                code=sum(Op.PUSH2[v] for v in range(0, stack_height))
                + Op.DUPN[stack_height]
                + Op.STOP,
                max_stack_height=max_stack_height,
            )
        ],
    )
    eof_test(
        container=eof_code,
        expect_exception=EOFException.STACK_UNDERFLOW,
    )


@pytest.mark.parametrize(
    "dupn_operand,max_stack_height,expect_exception",
    [
        [0, MAX_STACK_INCREASE_LIMIT, EOFException.INVALID_MAX_STACK_INCREASE],
        [0, MAX_STACK_INCREASE_LIMIT + 1, EOFException.MAX_STACK_INCREASE_ABOVE_LIMIT],
        [2**8 - 1, MAX_STACK_INCREASE_LIMIT, EOFException.INVALID_MAX_STACK_INCREASE],
        [2**8 - 1, MAX_STACK_INCREASE_LIMIT + 1, EOFException.MAX_STACK_INCREASE_ABOVE_LIMIT],
    ],
)
def test_dupn_stack_overflow(
    dupn_operand: int,
    max_stack_height: int,
    expect_exception: EOFException,
    eof_test: EOFTestFiller,
):
    """Test case where DUPN produces an stack overflow."""
    eof_code = Container(
        sections=[
            Section.Code(
                code=sum(Op.PUSH2[v] for v in range(0, MAX_STACK_INCREASE_LIMIT))
                + Op.DUPN[dupn_operand]
                + Op.STOP,
                max_stack_height=max_stack_height,
            )
        ],
    )
    eof_test(
        container=eof_code,
        expect_exception=expect_exception,
    )


@pytest.mark.parametrize(
    "dupn_arg,stack_height", [pytest.param(5, 9, id="5_of_9"), pytest.param(12, 30, id="12_of_30")]
)
def test_dupn_simple(
    stack_height: int,
    dupn_arg: int,
    pre: Alloc,
    state_test: StateTestFiller,
):
    """Test case for simple DUPN operations."""
    sender = pre.fund_eoa()
    contract_address = pre.deploy_contract(
        code=Container(
            sections=[
                Section.Code(
                    code=sum(Op.PUSH2[v] for v in range(stack_height, 0, -1))
                    + Op.DUPN[dupn_arg]
                    + sum((Op.PUSH1(v) + Op.SSTORE) for v in range(0, stack_height + 1))
                    + Op.STOP,
                    max_stack_height=stack_height + 2,
                )
            ],
        )
    )

    storage = {v: v for v in range(1, stack_height + 1)}
    storage[0] = dupn_arg + 1
    print(storage)
    post = {contract_address: Account(storage=storage)}

    tx = Transaction(to=contract_address, sender=sender, gas_limit=10_000_000)

    state_test(env=Environment(), pre=pre, post=post, tx=tx)
