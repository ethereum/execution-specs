"""
Execution of CALLF, RETF opcodes within EOF V1 containers tests
"""

import pytest

from ethereum_test_tools import (
    Account,
    Address,
    Environment,
    StateTestFiller,
    TestAddress,
    Transaction,
)
from ethereum_test_tools.eof.v1 import Container, Section
from ethereum_test_tools.eof.v1.constants import MAX_CODE_SECTIONS, NON_RETURNING_SECTION
from ethereum_test_tools.vm.opcode import Opcodes as Op

from .. import EOF_FORK_NAME

REFERENCE_SPEC_GIT_PATH = "EIPS/eip-7480.md"
REFERENCE_SPEC_VERSION = "3ee1334ef110420685f1c8ed63e80f9e1766c251"

pytestmark = pytest.mark.valid_from(EOF_FORK_NAME)

contract_call_within_deep_nested_callf = Container(
    name="contract_call_within_deep_nested_callf",
    sections=[
        Section.Code(
            code=(Op.CALLF[1] + Op.SSTORE(0, 1) + Op.STOP),
            code_inputs=0,
            code_outputs=NON_RETURNING_SECTION,
            max_stack_height=2,
        )
    ]
    + [
        # All sections call next section and on return, store a 1
        # to their call stack height key
        Section.Code(
            code=(Op.CALLF[i] + Op.SSTORE(i - 1, 1) + Op.RETF),
            code_inputs=0,
            code_outputs=0,
            max_stack_height=2,
        )
        for i in range(2, MAX_CODE_SECTIONS)
    ]
    + [
        # Last section makes external contract call
        Section.Code(
            code=(
                Op.EXTCALL(0x200, 0, 0, 0) + Op.SSTORE(MAX_CODE_SECTIONS - 1, Op.ISZERO) + Op.RETF
            ),
            code_inputs=0,
            code_outputs=0,
            max_stack_height=4,
        )
    ],
)

recursive_contract_call_within_deep_nested_callf = Container(
    name="recursive_contract_call_within_deep_nested_callf",
    sections=[
        # All sections call next section and on return, store a 1
        # to their call stack height key
        Section.Code(
            code=(Op.CALLF[i + 1] + Op.PUSH1(1) + Op.PUSH2(i) + Op.SSTORE + Op.STOP),
            code_inputs=0,
            code_outputs=NON_RETURNING_SECTION,
            max_stack_height=2,
        )
        for i in range(MAX_CODE_SECTIONS - 1)
    ]
    + [
        # Last section makes external contract call
        Section.Code(
            code=(
                Op.SSTORE(MAX_CODE_SECTIONS - 1, Op.CALL(Op.GAS, 0x200, 0, 0, 0, 0, 0)) + Op.RETF
            ),
            code_inputs=0,
            code_outputs=0,
            max_stack_height=7,
        )
    ],
)


def create_data_test(offset: int, datasize: int):
    """
    Generates data load operators test cases based on load offset and data section size.
    """
    data = b"".join(i.to_bytes(length=2, byteorder="big") for i in range(1, datasize // 2 + 1))
    assert len(data) == datasize
    overhang = min(32, offset + 32 - datasize)
    answer = data[offset : offset + 32] if overhang <= 0 else data[offset:] + b"\x00" * overhang
    dataloadn_op = Op.DATALOADN[offset] if overhang <= 0 else Op.PUSH32[answer]

    return (
        Container(
            sections=[
                Section.Code(
                    code=(
                        Op.CALLF[1]
                        + Op.CALLF[2]
                        + Op.CALLF[3]
                        + Op.CALLF[4]
                        + Op.SSTORE(0, 1)
                        + Op.STOP
                    ),
                    code_inputs=0,
                    code_outputs=NON_RETURNING_SECTION,
                    max_stack_height=2,
                ),
                Section.Code(
                    code=(Op.PUSH2(offset) + Op.DATALOAD + Op.PUSH1(1) + Op.SSTORE + Op.RETF),
                    code_inputs=0,
                    code_outputs=0,
                    max_stack_height=2,
                ),
                Section.Code(
                    code=(dataloadn_op + Op.PUSH1(2) + Op.SSTORE + Op.RETF),
                    code_inputs=0,
                    code_outputs=0,
                    max_stack_height=2,
                ),
                Section.Code(
                    code=(Op.DATASIZE + Op.PUSH1(3) + Op.SSTORE + Op.RETF),
                    code_inputs=0,
                    code_outputs=0,
                    max_stack_height=2,
                ),
                Section.Code(
                    code=(Op.DATACOPY(0, offset, 32) + Op.SSTORE(4, Op.MLOAD(0)) + Op.RETF),
                    code_inputs=0,
                    code_outputs=0,
                    max_stack_height=3,
                ),
                Section.Data(data),
            ],
        ),
        {0: 1, 1: answer, 2: answer, 3: datasize, 4: answer},
    )


@pytest.mark.parametrize(
    ["offset", "datasize"],
    [
        pytest.param(0, 0, id="empty_zero"),
        pytest.param(0, 2, id="short_zero"),
        pytest.param(0, 32, id="exact_zero"),
        pytest.param(0, 64, id="large_zero"),
        pytest.param(32, 0, id="empty_32"),
        pytest.param(32, 34, id="short_32"),
        pytest.param(32, 64, id="exact_32"),
        pytest.param(32, 96, id="large_32"),
        pytest.param(0x5BFE, 0, id="empty_23k"),
        pytest.param(0x5BFE, 0x5C00, id="short_23k"),
        pytest.param(0x5BE0, 0x5D00, id="exact_23k"),
        pytest.param(0x2345, 0x5C00, id="large_23k"),
    ],
)
def test_data_section_succeed(
    state_test: StateTestFiller,
    offset: int,
    datasize: int,
):
    """
    Test simple contracts that are simply expected to succeed on call.
    """
    env = Environment()

    caller_contract = Op.SSTORE(0, Op.DELEGATECALL(Op.GAS, 0x200, 0, 0, 0, 0)) + Op.STOP()
    (container, expected_storage) = create_data_test(offset, datasize)

    pre = {
        TestAddress: Account(
            balance=1000000000000000000000,
            nonce=1,
        ),
        Address(0x100): Account(
            code=caller_contract,
            nonce=1,
        ),
        Address(0x200): Account(
            code=container,
            nonce=1,
        ),
    }

    tx = Transaction(
        nonce=1,
        to=Address(0x100),
        gas_limit=50000000,
        gas_price=10,
        protected=False,
        data="",
    )

    post = {Address(0x100): Account(storage=expected_storage)}

    state_test(
        env=env,
        pre=pre,
        post=post,
        tx=tx,
    )
