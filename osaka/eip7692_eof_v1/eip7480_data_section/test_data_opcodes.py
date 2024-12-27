"""Execution of DATA* opcodes within EOF V1 containers tests."""

import pytest

from ethereum_test_tools import Account, Alloc, Environment, StateTestFiller, Transaction
from ethereum_test_tools.eof.v1 import Container, Section
from ethereum_test_tools.vm.opcode import Opcodes as Op

from .. import EOF_FORK_NAME

REFERENCE_SPEC_GIT_PATH = "EIPS/eip-7480.md"
REFERENCE_SPEC_VERSION = "3ee1334ef110420685f1c8ed63e80f9e1766c251"

pytestmark = pytest.mark.valid_from(EOF_FORK_NAME)


def create_data_test(offset: int, datasize: int):
    """Generate data load operators test cases based on load offset and data section size."""
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
                ),
                Section.Code(
                    code=(Op.DATALOAD(offset) + Op.PUSH1(1) + Op.SSTORE + Op.RETF),
                    code_inputs=0,
                    code_outputs=0,
                ),
                Section.Code(
                    code=(dataloadn_op + Op.PUSH1(2) + Op.SSTORE + Op.RETF),
                    code_inputs=0,
                    code_outputs=0,
                ),
                Section.Code(
                    code=(Op.DATASIZE + Op.PUSH1(3) + Op.SSTORE + Op.RETF),
                    code_inputs=0,
                    code_outputs=0,
                ),
                Section.Code(
                    code=(Op.DATACOPY(0, offset, 32) + Op.SSTORE(4, Op.MLOAD(0)) + Op.RETF),
                    code_inputs=0,
                    code_outputs=0,
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
        pytest.param(2**16 - 1, 32, id="u16_max"),
        pytest.param(2**16, 32, id="u16_max_plus_1"),
        pytest.param(2**32 - 1, 32, id="u32_max"),
        pytest.param(2**32, 32, id="u32_max_plus_1"),
        pytest.param(2**64 - 1, 32, id="u64_max"),
        pytest.param(2**64, 32, id="u64_max_plus_1"),
    ],
)
def test_data_section_succeed(
    state_test: StateTestFiller,
    pre: Alloc,
    offset: int,
    datasize: int,
):
    """Test simple contracts that are simply expected to succeed on call."""
    env = Environment()

    (container, expected_storage) = create_data_test(offset, datasize)
    callee_contract = pre.deploy_contract(code=container)
    entry_point = pre.deploy_contract(
        code=Op.SSTORE(0, Op.DELEGATECALL(Op.GAS, callee_contract, 0, 0, 0, 0)) + Op.STOP()
    )
    sender = pre.fund_eoa()

    tx = Transaction(
        to=entry_point,
        gas_limit=50000000,
        gas_price=10,
        protected=False,
        data="",
        sender=sender,
    )

    post = {entry_point: Account(storage=expected_storage)}

    state_test(
        env=env,
        pre=pre,
        post=post,
        tx=tx,
    )
