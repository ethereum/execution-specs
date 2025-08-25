"""
abstract: Tests [EIP-663: SWAPN, DUPN and EXCHANGE instructions](https://eips.ethereum.org/EIPS/eip-663)
    Tests for the EXCHANGE instruction.
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

from .. import EOF_FORK_NAME
from . import REFERENCE_SPEC_GIT_PATH, REFERENCE_SPEC_VERSION

REFERENCE_SPEC_GIT_PATH = REFERENCE_SPEC_GIT_PATH
REFERENCE_SPEC_VERSION = REFERENCE_SPEC_VERSION

pytestmark = pytest.mark.valid_from(EOF_FORK_NAME)


def test_exchange_all_valid_immediates(eof_state_test: EOFStateTestFiller):
    """Test case for all valid EXCHANGE immediates."""
    n = 256
    s = 34
    values = range(0x3E8, 0x3E8 + s)

    eof_code = Container(
        sections=[
            Section.Code(
                code=sum(Op.PUSH2[v] for v in values)
                + sum(Op.EXCHANGE[x] for x in range(0, n))
                + sum((Op.PUSH1[x] + Op.SSTORE) for x in range(0, s))
                + Op.STOP,
            )
        ],
    )

    # this does the same full-loop exchange
    values_rotated = list(range(0x3E8, 0x3E8 + s))
    for e in range(0, n):
        a = (e >> 4) + 1
        b = (e & 0x0F) + 1 + a
        temp = values_rotated[a]
        values_rotated[a] = values_rotated[b]
        values_rotated[b] = temp

    post = Account(storage=dict(zip(range(0, s), reversed(values_rotated), strict=False)))

    eof_state_test(
        tx_sender_funding_amount=1_000_000_000,
        container=eof_code,
        container_post=post,
    )


@pytest.mark.parametrize(
    "stack_height,x,y",
    [
        # 2 and 3 are the lowest valid values for x and y,
        # which translates to the zero immediate value.
        # (0, 2, 3) is tested in test_all_opcodes_stack_underflow()
        pytest.param(1, 2, 3, id="stack_height=1_n=1_m=1"),
        pytest.param(2, 2, 3, id="stack_height=2_n=1_m=1"),
        pytest.param(17, 2, 18, id="stack_height=17_n=1_m=16"),
        pytest.param(17, 17, 18, id="stack_height=17_n=16_m=1"),
        pytest.param(32, 17, 33, id="stack_height=32_n=16_m=16"),
    ],
)
def test_exchange_stack_underflow(
    eof_test: EOFTestFiller,
    stack_height: int,
    x: int,
    y: int,
):
    """Test case the EXCHANGE causing stack underflow."""
    eof_code = Container(
        sections=[
            Section.Code(
                code=sum(Op.PUSH2[v] for v in range(stack_height))
                + Op.EXCHANGE[x, y]
                + Op.POP * stack_height
                + Op.STOP,
                max_stack_height=stack_height,
            )
        ],
    )

    eof_test(
        container=eof_code,
        expect_exception=EOFException.STACK_UNDERFLOW,
    )


@pytest.mark.parametrize(
    "m_arg,n_arg,extra_stack",
    [pytest.param(0, 0, 3, id="m0_n0_extra3"), pytest.param(2, 3, 7, id="m2_n3_extra7")],
)
def test_exchange_simple(
    m_arg: int,
    n_arg: int,
    extra_stack: int,
    pre: Alloc,
    state_test: StateTestFiller,
):
    """Test case for simple EXCHANGE operations."""
    sender = pre.fund_eoa()
    stack_height = m_arg + n_arg + 2 + extra_stack
    contract_address = pre.deploy_contract(
        code=Container(
            sections=[
                Section.Code(
                    code=sum(Op.PUSH2[v] for v in range(stack_height, 0, -1))
                    + Op.EXCHANGE[m_arg << 4 | n_arg]
                    + sum((Op.PUSH1(v) + Op.SSTORE) for v in range(1, stack_height + 1))
                    + Op.STOP,
                    max_stack_height=stack_height + 1,
                )
            ],
        )
    )

    storage = {v: v for v in range(1, stack_height + 1)}
    first = m_arg + 2  # one based index, plus m=0 means first non-top item
    second = first + n_arg + 1  # n+1 past m
    storage[first], storage[second] = storage[second], storage[first]
    print(storage)
    post = {contract_address: Account(storage=storage)}

    tx = Transaction(to=contract_address, sender=sender, gas_limit=10_000_000)

    state_test(env=Environment(), pre=pre, post=post, tx=tx)
