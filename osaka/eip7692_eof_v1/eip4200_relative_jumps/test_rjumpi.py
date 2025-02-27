"""EOF JUMPF tests covering stack and code validation rules."""

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
from ethereum_test_tools.eof.v1 import Container, Section
from ethereum_test_tools.eof.v1.constants import MAX_BYTECODE_SIZE
from ethereum_test_tools.vm.opcode import Opcodes as Op

from .. import EOF_FORK_NAME
from .helpers import (
    JumpDirection,
    slot_code_worked,
    slot_conditional_result,
    value_calldata_false,
    value_calldata_true,
    value_code_worked,
)

REFERENCE_SPEC_GIT_PATH = "EIPS/eip-4200.md"
REFERENCE_SPEC_VERSION = "17d4a8d12d2b5e0f2985c866376c16c8c6df7cba"

pytestmark = pytest.mark.valid_from(EOF_FORK_NAME)

RJUMP_LEN = len(Op.RJUMP[0])
RJUMPI_LEN = len(Op.RJUMPI[0])


@pytest.mark.parametrize(
    "calldata",
    [pytest.param(b"\x00", id="False"), pytest.param(b"\x01", id="True")],
)
def test_rjumpi_condition_forwards(
    state_test: StateTestFiller,
    pre: Alloc,
    calldata: bytes,
):
    """Test RJUMPI contract switching based on external input (forwards)."""
    env = Environment()
    sender = pre.fund_eoa(10**18)
    contract_address = pre.deploy_contract(
        code=Container.Code(
            Op.PUSH1(0)
            + Op.CALLDATALOAD
            + Op.RJUMPI[6]
            + Op.SSTORE(slot_conditional_result, value_calldata_false)
            + Op.STOP
            + Op.SSTORE(slot_conditional_result, value_calldata_true)
            + Op.STOP,
        )
    )
    tx = Transaction(
        to=contract_address,
        gas_limit=10_000_000,
        data=calldata,
        sender=sender,
    )
    post = {
        contract_address: Account(
            storage={
                slot_conditional_result: value_calldata_false
                if calldata == b"\0"
                else value_calldata_true
            }
        )
    }
    state_test(env=env, tx=tx, pre=pre, post=post)


@pytest.mark.parametrize(
    "calldata",
    [pytest.param(b"\x00", id="False"), pytest.param(b"\x01", id="True")],
)
def test_rjumpi_condition_backwards(
    state_test: StateTestFiller,
    pre: Alloc,
    calldata: bytes,
):
    """Test RJUMPI contract switching based on external input."""
    env = Environment()
    sender = pre.fund_eoa(10**18)
    contract_address = pre.deploy_contract(
        code=Container.Code(
            Op.PUSH1(1)
            + Op.RJUMPI[6]
            + Op.SSTORE(slot_conditional_result, value_calldata_true)
            + Op.STOP
            + Op.PUSH0
            + Op.CALLDATALOAD
            + Op.RJUMPI[-11]
            + Op.SSTORE(slot_conditional_result, value_calldata_false)
            + Op.STOP,
        )
    )
    tx = Transaction(
        to=contract_address,
        gas_limit=10_000_000,
        data=calldata,
        sender=sender,
    )
    post = {
        contract_address: Account(
            storage={
                slot_conditional_result: value_calldata_false
                if calldata == b"\0"
                else value_calldata_true
            }
        )
    }
    state_test(env=env, tx=tx, pre=pre, post=post)


@pytest.mark.parametrize(
    "calldata",
    [pytest.param(b"\x00", id="False"), pytest.param(b"\x01", id="True")],
)
def test_rjumpi_condition_zero(
    state_test: StateTestFiller,
    pre: Alloc,
    calldata: bytes,
):
    """Test RJUMPI contract switching based on external input (condition zero)."""
    env = Environment()
    sender = pre.fund_eoa(10**18)
    contract_address = pre.deploy_contract(
        code=Container(
            sections=[
                Section.Code(
                    code=Op.PUSH0
                    + Op.CALLDATALOAD
                    + Op.RJUMPI[0]
                    + Op.SSTORE(slot_code_worked, value_code_worked)
                    + Op.STOP,
                )
            ]
        ),
    )
    tx = Transaction(
        to=contract_address,
        gas_limit=10_000_000,
        data=calldata,
        sender=sender,
    )
    post = {contract_address: Account(storage={slot_code_worked: value_code_worked})}
    state_test(env=env, tx=tx, pre=pre, post=post)


def test_rjumpi_forwards(
    eof_state_test: EOFStateTestFiller,
):
    """EOF1V4200_0004 (Valid) EOF code containing RJUMPI (Positive)."""
    eof_state_test(
        container=Container(
            sections=[
                Section.Code(
                    code=Op.PUSH1(1)
                    + Op.RJUMPI[3]
                    + Op.NOOP
                    + Op.NOOP
                    + Op.STOP
                    + Op.SSTORE(slot_code_worked, value_code_worked)
                    + Op.STOP,
                )
            ],
        ),
        container_post=Account(storage={slot_code_worked: value_code_worked}),
    )


def test_rjumpi_backwards(
    eof_state_test: EOFStateTestFiller,
):
    """EOF1V4200_0005 (Valid) EOF code containing RJUMPI (Negative)."""
    eof_state_test(
        container=Container(
            sections=[
                Section.Code(
                    code=Op.PUSH1(1)
                    + Op.RJUMPI[7]
                    + Op.SSTORE(slot_code_worked, value_code_worked)
                    + Op.STOP
                    + Op.PUSH1(1)
                    + Op.RJUMPI[-12]
                    + Op.STOP,
                )
            ],
        ),
        container_post=Account(storage={slot_code_worked: value_code_worked}),
    )


def test_rjumpi_zero(
    eof_state_test: EOFStateTestFiller,
):
    """EOF1V4200_0006 (Valid) EOF code containing RJUMPI (Zero)."""
    eof_state_test(
        container=Container(
            sections=[
                Section.Code(
                    code=Op.PUSH1(1)
                    + Op.RJUMPI[0]
                    + Op.SSTORE(slot_code_worked, value_code_worked)
                    + Op.STOP,
                )
            ],
        ),
        container_post=Account(storage={slot_code_worked: value_code_worked}),
    )


def test_rjumpi_max_forward(
    eof_state_test: EOFStateTestFiller,
):
    """EOF1V4200_0007 (Valid) EOF with RJUMPI containing the maximum offset (32767)."""
    eof_state_test(
        container=Container(
            sections=[
                Section.Code(
                    code=Op.PUSH1(1)
                    + Op.RJUMPI[32767]
                    + Op.NOOP * 32768
                    + Op.SSTORE(slot_code_worked, value_code_worked)
                    + Op.STOP,
                )
            ],
        ),
        container_post=Account(storage={slot_code_worked: value_code_worked}),
    )


def test_rjumpi_max_backward(
    eof_state_test: EOFStateTestFiller,
):
    """EOF with RJUMPI containing the maximum negative offset (-32768)."""
    (
        eof_state_test(
            container=Container(
                sections=[
                    Section.Code(
                        code=Op.PUSH0
                        + Op.RJUMPI[0x7FFF]
                        + Op.NOOP * (0x7FFF - 7)
                        + Op.SSTORE(slot_code_worked, value_code_worked)
                        + Op.STOP
                        + Op.PUSH0
                        + Op.RJUMPI[0x8000]
                        + Op.STOP,
                    )
                ],
            ),
            container_post=Account(storage={slot_code_worked: value_code_worked}),
        ),
    )


@pytest.mark.parametrize(
    "container",
    [
        Container(
            name="forwards_rjumpi_0",
            sections=[
                Section.Code(
                    code=Op.PUSH1[1] + Op.RJUMPI[0] + Op.STOP,
                    max_stack_height=1,
                ),
            ],
            expected_bytecode="ef0001010004020001000604000000008000016001e1000000",
        ),
        Container(
            name="forwards_rjumpi_1",
            sections=[
                Section.Code(
                    code=Op.PUSH0 + Op.PUSH1[0] + Op.RJUMPI[1] + Op.NOT + Op.STOP,
                    max_stack_height=2,
                ),
            ],
            expected_bytecode="ef0001010004020001000804000000008000025f6000e100011900",
        ),
        Container(
            name="forwards_rjumpi_10",
            sections=[
                Section.Code(
                    code=Op.PUSH0
                    + Op.PUSH1[0]
                    + Op.RJUMPI[4]
                    + Op.POP
                    + Op.RJUMP[1]
                    + Op.NOT
                    + Op.STOP,
                    max_stack_height=2,
                ),
            ],
            expected_bytecode="ef0001010004020001000c04000000008000025f6000e1000450e000011900",
        ),
        Container(
            name="forwards_rjumpi_11",
            sections=[
                Section.Code(
                    code=Op.PUSH0 + Op.PUSH1[0] + Op.RJUMPI[3] + Op.RJUMP[0] + Op.STOP,
                    max_stack_height=2,
                ),
            ],
            expected_bytecode="ef0001010004020001000a04000000008000025f6000e10003e0000000",
        ),
        Container(
            name="forwards_rjumpi_12",
            sections=[
                Section.Code(
                    code=Op.PUSH0 + Op.PUSH1[0] + Op.RJUMPI[4] + Op.PUSH0 + Op.RJUMP[0] + Op.STOP,
                    max_stack_height=2,
                ),
            ],
            expected_bytecode="ef0001010004020001000b04000000008000025f6000e100045fe0000000",
        ),
        Container(
            name="forwards_rjumpi_2",
            sections=[
                Section.Code(
                    code=Op.PUSH0
                    + Op.PUSH1[0]
                    + Op.RJUMPI[6]
                    + Op.PUSH1[0]
                    + Op.RJUMPI[1]
                    + Op.NOT
                    + Op.STOP,
                    max_stack_height=2,
                ),
            ],
            expected_bytecode="ef0001010004020001000d04000000008000025f6000e100066000e100011900",
        ),
        Container(
            name="forwards_rjumpi_3",
            sections=[
                Section.Code(
                    code=Op.PUSH0 + Op.PUSH1[0] + Op.RJUMPI[1] + Op.PUSH0 + Op.STOP,
                    max_stack_height=2,
                ),
            ],
            expected_bytecode="ef0001010004020001000804000000008000025f6000e100015f00",
        ),
        Container(
            name="forwards_rjumpi_4",
            sections=[
                Section.Code(
                    code=Op.PUSH0
                    + Op.PUSH1[0]
                    + Op.RJUMPI[7]
                    + Op.PUSH0
                    + Op.PUSH1[0]
                    + Op.RJUMPI[1]
                    + Op.NOT
                    + Op.STOP,
                    max_stack_height=3,
                ),
            ],
            expected_bytecode="ef0001010004020001000e04000000008000035f6000e100075f6000e100011900",
        ),
        Container(
            name="forwards_rjumpi_5",
            sections=[
                Section.Code(
                    code=Op.PUSH0
                    + Op.PUSH1[1]
                    + Op.ADD
                    + Op.DUP1
                    + Op.PUSH1[10]
                    + Op.GT
                    + Op.RJUMPI[4]
                    + Op.DUP1
                    + Op.RJUMPI[-14]
                    + Op.STOP,
                    max_stack_height=3,
                ),
            ],
            expected_bytecode="ef0001010004020001001004000000008000035f60010180600a11e1000480e1fff200",
        ),
        Container(
            name="forwards_rjumpi_6",
            sections=[
                Section.Code(
                    code=Op.PUSH0
                    + Op.PUSH1[1]
                    + Op.ADD
                    + Op.DUP1
                    + Op.PUSH1[10]
                    + Op.GT
                    + Op.RJUMPI[5]
                    + Op.PUSH0
                    + Op.DUP1
                    + Op.RJUMPI[-13]
                    + Op.STOP,
                    max_stack_height=3,
                ),
            ],
            expected_bytecode="ef0001010004020001001104000000008000035f60010180600a11e100055f80e1fff300",
        ),
        Container(
            name="forwards_rjumpi_7",
            sections=[
                Section.Code(
                    code=Op.PUSH0
                    + Op.PUSH1[0]
                    + Op.RJUMPI[4]
                    + Op.PUSH0
                    + Op.RJUMP[1]
                    + Op.PUSH0
                    + Op.STOP,
                    max_stack_height=2,
                ),
            ],
            expected_bytecode="ef0001010004020001000c04000000008000025f6000e100045fe000015f00",
        ),
        Container(
            name="forwards_rjumpi_8",
            sections=[
                Section.Code(
                    code=Op.PUSH0
                    + Op.PUSH1[0]
                    + Op.RJUMPI[4]
                    + Op.PUSH0
                    + Op.RJUMP[1]
                    + Op.NOT
                    + Op.STOP,
                    max_stack_height=2,
                ),
            ],
            expected_bytecode="ef0001010004020001000c04000000008000025f6000e100045fe000011900",
        ),
        Container(
            name="forwards_rjumpi_9",
            sections=[
                Section.Code(
                    code=Op.PUSH0
                    + Op.PUSH1[0]
                    + Op.RJUMPI[4]
                    + Op.POP
                    + Op.RJUMP[1]
                    + Op.POP
                    + Op.STOP,
                    max_stack_height=2,
                ),
            ],
            expected_bytecode="ef0001010004020001000c04000000008000025f6000e1000450e000015000",
        ),
        Container(
            name="forwards_rjumpi_variable_stack_0",
            sections=[
                Section.Code(
                    code=Op.PUSH0
                    + Op.PUSH1[0]
                    + Op.RJUMPI[2]
                    + Op.PUSH0
                    + Op.PUSH0
                    + Op.PUSH1[1]
                    + Op.RJUMPI[0]
                    + Op.STOP,
                    max_stack_height=4,
                ),
            ],
            expected_bytecode="ef0001010004020001000e04000000008000045f6000e100025f5f6001e1000000",
        ),
        Container(
            name="forwards_rjumpi_variable_stack_1",
            sections=[
                Section.Code(
                    code=Op.PUSH0
                    + Op.PUSH1[0]
                    + Op.RJUMPI[2]
                    + Op.PUSH0
                    + Op.PUSH0
                    + Op.PUSH0
                    + Op.PUSH1[0]
                    + Op.RJUMPI[1]
                    + Op.NOT
                    + Op.STOP,
                    max_stack_height=5,
                ),
            ],
            expected_bytecode="ef0001010004020001001004000000008000055f6000e100025f5f5f6000e100011900",
        ),
        Container(
            name="forwards_rjumpi_variable_stack_10",
            sections=[
                Section.Code(
                    code=Op.PUSH0
                    + Op.PUSH1[0]
                    + Op.RJUMPI[2]
                    + Op.PUSH0
                    + Op.PUSH0
                    + Op.PUSH0
                    + Op.PUSH1[0]
                    + Op.RJUMPI[4]
                    + Op.POP
                    + Op.RJUMP[1]
                    + Op.NOT
                    + Op.STOP,
                    max_stack_height=5,
                ),
            ],
            expected_bytecode="ef0001010004020001001404000000008000055f6000e100025f5f5f6000e1000450e000011900",
        ),
        Container(
            name="forwards_rjumpi_variable_stack_11",
            sections=[
                Section.Code(
                    code=Op.PUSH0
                    + Op.PUSH1[0]
                    + Op.RJUMPI[2]
                    + Op.PUSH0
                    + Op.PUSH0
                    + Op.PUSH0
                    + Op.PUSH1[0]
                    + Op.RJUMPI[3]
                    + Op.RJUMP[0]
                    + Op.STOP,
                    max_stack_height=5,
                ),
            ],
            expected_bytecode="ef0001010004020001001204000000008000055f6000e100025f5f5f6000e10003e0000000",
        ),
        Container(
            name="forwards_rjumpi_variable_stack_12",
            sections=[
                Section.Code(
                    code=Op.PUSH0
                    + Op.PUSH1[0]
                    + Op.RJUMPI[2]
                    + Op.PUSH0
                    + Op.PUSH0
                    + Op.PUSH0
                    + Op.PUSH1[0]
                    + Op.RJUMPI[4]
                    + Op.PUSH0
                    + Op.RJUMP[0]
                    + Op.STOP,
                    max_stack_height=5,
                ),
            ],
            expected_bytecode="ef0001010004020001001304000000008000055f6000e100025f5f5f6000e100045fe0000000",
        ),
        Container(
            name="forwards_rjumpi_variable_stack_2",
            sections=[
                Section.Code(
                    code=Op.PUSH0
                    + Op.PUSH1[0]
                    + Op.RJUMPI[2]
                    + Op.PUSH0
                    + Op.PUSH0
                    + Op.PUSH0
                    + Op.PUSH1[0]
                    + Op.RJUMPI[6]
                    + Op.PUSH1[0]
                    + Op.RJUMPI[1]
                    + Op.NOT
                    + Op.STOP,
                    max_stack_height=5,
                ),
            ],
            expected_bytecode="ef0001010004020001001504000000008000055f6000e100025f5f5f6000e100066000e100011900",
        ),
        Container(
            name="forwards_rjumpi_variable_stack_3",
            sections=[
                Section.Code(
                    code=Op.PUSH0
                    + Op.PUSH1[0]
                    + Op.RJUMPI[2]
                    + Op.PUSH0
                    + Op.PUSH0
                    + Op.PUSH0
                    + Op.PUSH1[0]
                    + Op.RJUMPI[1]
                    + Op.PUSH0
                    + Op.STOP,
                    max_stack_height=5,
                ),
            ],
            expected_bytecode="ef0001010004020001001004000000008000055f6000e100025f5f5f6000e100015f00",
        ),
        Container(
            name="forwards_rjumpi_variable_stack_4",
            sections=[
                Section.Code(
                    code=Op.PUSH0
                    + Op.PUSH1[0]
                    + Op.RJUMPI[2]
                    + Op.PUSH0
                    + Op.PUSH0
                    + Op.PUSH0
                    + Op.PUSH1[0]
                    + Op.RJUMPI[7]
                    + Op.PUSH0
                    + Op.PUSH1[0]
                    + Op.RJUMPI[1]
                    + Op.NOT
                    + Op.STOP,
                    max_stack_height=6,
                ),
            ],
            expected_bytecode="ef0001010004020001001604000000008000065f6000e100025f5f5f6000e100075f6000e100011900",
        ),
        Container(
            name="forwards_rjumpi_variable_stack_5",
            sections=[
                Section.Code(
                    code=Op.PUSH0
                    + Op.PUSH1[0]
                    + Op.RJUMPI[2]
                    + Op.PUSH0
                    + Op.PUSH0
                    + Op.PUSH0
                    + Op.PUSH1[1]
                    + Op.ADD
                    + Op.DUP1
                    + Op.PUSH1[10]
                    + Op.GT
                    + Op.RJUMPI[4]
                    + Op.DUP1
                    + Op.RJUMPI[-14]
                    + Op.STOP,
                    max_stack_height=6,
                ),
            ],
            expected_bytecode="ef0001010004020001001804000000008000065f6000e100025f5f5f60010180600a11e1000480e1fff200",
        ),
        Container(
            name="forwards_rjumpi_variable_stack_6",
            sections=[
                Section.Code(
                    code=Op.PUSH0
                    + Op.PUSH1[0]
                    + Op.RJUMPI[2]
                    + Op.PUSH0
                    + Op.PUSH0
                    + Op.PUSH0
                    + Op.PUSH1[1]
                    + Op.ADD
                    + Op.DUP1
                    + Op.PUSH1[10]
                    + Op.GT
                    + Op.RJUMPI[5]
                    + Op.PUSH0
                    + Op.DUP1
                    + Op.RJUMPI[-13]
                    + Op.STOP,
                    max_stack_height=6,
                ),
            ],
            expected_bytecode="ef0001010004020001001904000000008000065f6000e100025f5f5f60010180600a11e100055f80e1fff300",
        ),
        Container(
            name="forwards_rjumpi_variable_stack_7",
            sections=[
                Section.Code(
                    code=Op.PUSH0
                    + Op.PUSH1[0]
                    + Op.RJUMPI[2]
                    + Op.PUSH0
                    + Op.PUSH0
                    + Op.PUSH0
                    + Op.PUSH1[0]
                    + Op.RJUMPI[4]
                    + Op.PUSH0
                    + Op.RJUMP[1]
                    + Op.PUSH0
                    + Op.STOP,
                    max_stack_height=5,
                ),
            ],
            expected_bytecode="ef0001010004020001001404000000008000055f6000e100025f5f5f6000e100045fe000015f00",
        ),
        Container(
            name="forwards_rjumpi_variable_stack_8",
            sections=[
                Section.Code(
                    code=Op.PUSH0
                    + Op.PUSH1[0]
                    + Op.RJUMPI[2]
                    + Op.PUSH0
                    + Op.PUSH0
                    + Op.PUSH0
                    + Op.PUSH1[0]
                    + Op.RJUMPI[4]
                    + Op.PUSH0
                    + Op.RJUMP[1]
                    + Op.NOT
                    + Op.STOP,
                    max_stack_height=5,
                ),
            ],
            expected_bytecode="ef0001010004020001001404000000008000055f6000e100025f5f5f6000e100045fe000011900",
        ),
        Container(
            name="forwards_rjumpi_variable_stack_9",
            sections=[
                Section.Code(
                    code=Op.PUSH0
                    + Op.PUSH1[0]
                    + Op.RJUMPI[2]
                    + Op.PUSH0
                    + Op.PUSH0
                    + Op.PUSH0
                    + Op.PUSH1[0]
                    + Op.RJUMPI[4]
                    + Op.POP
                    + Op.RJUMP[1]
                    + Op.POP
                    + Op.STOP,
                    max_stack_height=5,
                ),
            ],
            expected_bytecode="ef0001010004020001001404000000008000055f6000e100025f5f5f6000e1000450e000015000",
        ),
    ],
    ids=lambda x: x.name,
)
def test_rjumpi_valid_forward(
    eof_test: EOFTestFiller,
    container: Container,
):
    """
    Validate a valid code section containing at least one forward RJUMPI.
    These tests exercise the stack height validation.
    """
    eof_test(container=container)


@pytest.mark.parametrize(
    "container",
    [
        Container(
            name="backwards_rjumpi_0",
            sections=[
                Section.Code(
                    code=Op.PUSH1[0] + Op.RJUMPI[-5] + Op.STOP,
                    max_stack_height=1,
                ),
            ],
            expected_bytecode="ef0001010004020001000604000000008000016000e1fffb00",
        ),
        Container(
            name="backwards_rjumpi_1",
            sections=[
                Section.Code(
                    code=Op.PUSH0 + Op.POP + Op.PUSH1[0] + Op.RJUMPI[-7] + Op.STOP,
                    max_stack_height=1,
                ),
            ],
            expected_bytecode="ef0001010004020001000804000000008000015f506000e1fff900",
        ),
        Container(
            name="backwards_rjumpi_2",
            sections=[
                Section.Code(
                    code=Op.PUSH0
                    + Op.POP
                    + Op.PUSH1[0]
                    + Op.RJUMPI[-7]
                    + Op.PUSH1[0]
                    + Op.RJUMPI[-12]
                    + Op.STOP,
                    max_stack_height=1,
                ),
            ],
            expected_bytecode="ef0001010004020001000d04000000008000015f506000e1fff96000e1fff400",
        ),
        Container(
            name="backwards_rjumpi_4",
            sections=[
                Section.Code(
                    code=Op.PUSH0 + Op.PUSH1[1] + Op.ADD + Op.DUP1 + Op.RJUMPI[-7] + Op.STOP,
                    max_stack_height=2,
                ),
            ],
            expected_bytecode="ef000101000402000100090400000000800002 5f60010180e1fff900",
        ),
        Container(
            name="backwards_rjumpi_7",
            sections=[
                Section.Code(
                    code=Op.PUSH0 + Op.POP + Op.PUSH1[0] + Op.RJUMPI[-7] + Op.RJUMP[-10],
                    max_stack_height=1,
                ),
            ],
            expected_bytecode="ef0001010004020001000a04000000008000015f506000e1fff9e0fff6",
        ),
        Container(
            name="backwards_rjumpi_variable_stack_0",
            sections=[
                Section.Code(
                    code=Op.PUSH0
                    + Op.PUSH1[0]
                    + Op.RJUMPI[2]
                    + Op.PUSH0
                    + Op.PUSH0
                    + Op.PUSH1[0]
                    + Op.RJUMPI[-5]
                    + Op.STOP,
                    max_stack_height=4,
                ),
            ],
            expected_bytecode="ef0001010004020001000e04000000008000045f6000e100025f5f6000e1fffb00",
        ),
        Container(
            name="backwards_rjumpi_variable_stack_1",
            sections=[
                Section.Code(
                    code=Op.PUSH0
                    + Op.PUSH1[0]
                    + Op.RJUMPI[2]
                    + Op.PUSH0
                    + Op.PUSH0
                    + Op.PUSH0
                    + Op.POP
                    + Op.PUSH1[0]
                    + Op.RJUMPI[-7]
                    + Op.STOP,
                    max_stack_height=4,
                ),
            ],
            expected_bytecode="ef0001010004020001001004000000008000045f6000e100025f5f5f506000e1fff900",
        ),
        Container(
            name="backwards_rjumpi_variable_stack_2",
            sections=[
                Section.Code(
                    code=Op.PUSH0
                    + Op.PUSH1[0]
                    + Op.RJUMPI[2]
                    + Op.PUSH0
                    + Op.PUSH0
                    + Op.PUSH0
                    + Op.POP
                    + Op.PUSH1[0]
                    + Op.RJUMPI[-7]
                    + Op.PUSH1[0]
                    + Op.RJUMPI[-12]
                    + Op.STOP,
                    max_stack_height=4,
                ),
            ],
            expected_bytecode="ef0001010004020001001504000000008000045f6000e100025f5f5f506000e1fff96000e1fff400",
        ),
        Container(
            name="backwards_rjumpi_variable_stack_4",
            sections=[
                Section.Code(
                    code=Op.PUSH0
                    + Op.PUSH1[0]
                    + Op.RJUMPI[2]
                    + Op.PUSH0
                    + Op.PUSH0
                    + Op.PUSH0
                    + Op.PUSH1[1]
                    + Op.ADD
                    + Op.DUP1
                    + Op.RJUMPI[-7]
                    + Op.STOP,
                    max_stack_height=5,
                ),
            ],
            expected_bytecode="ef0001010004020001001104000000008000055f6000e100025f5f5f60010180e1fff900",
        ),
        Container(
            name="backwards_rjumpi_variable_stack_7",
            sections=[
                Section.Code(
                    code=Op.PUSH0
                    + Op.PUSH1[0]
                    + Op.RJUMPI[2]
                    + Op.PUSH0
                    + Op.PUSH0
                    + Op.PUSH0
                    + Op.POP
                    + Op.PUSH1[0]
                    + Op.RJUMPI[-7]
                    + Op.RJUMP[-10],
                    max_stack_height=4,
                ),
            ],
            expected_bytecode="ef0001010004020001001204000000008000045f6000e100025f5f5f506000e1fff9e0fff6",
        ),
    ],
    ids=lambda x: x.name,
)
def test_rjumpi_valid_backward(
    eof_test: EOFTestFiller,
    container: Container,
):
    """
    Validate a valid code section containing at least one backward RJUMPI.
    These tests exercise the stack height validation.
    """
    eof_test(container=container)


def test_rjumpi_max_bytecode_size(
    eof_test: EOFTestFiller,
):
    """
    EOF1V4200_0003 EOF with RJUMPI containing the maximum offset that does not exceed the maximum
    bytecode size.
    """
    noop_count = MAX_BYTECODE_SIZE - 24
    code = Op.RJUMPI[len(Op.NOOP) * noop_count](Op.ORIGIN) + (Op.NOOP * noop_count) + Op.STOP
    container = Container.Code(code=code)
    assert len(container) == MAX_BYTECODE_SIZE
    eof_test(container=container)


def test_rjumpi_truncated(
    eof_test: EOFTestFiller,
):
    """EOF1I4200_0014 (Invalid) EOF code containing truncated RJUMPI."""
    eof_test(
        container=Container(
            sections=[
                Section.Code(
                    code=Op.PUSH1(0) + Op.RJUMPI,
                )
            ],
        ),
        expect_exception=EOFException.TRUNCATED_INSTRUCTION,
    )


def test_rjumpi_truncated_2(
    eof_test: EOFTestFiller,
):
    """EOF1I4200_0015 (Invalid) EOF code containing truncated RJUMPI."""
    eof_test(
        container=Container(
            sections=[
                Section.Code(
                    code=Op.PUSH1(0) + Op.RJUMPI + b"\x00",
                )
            ],
        ),
        expect_exception=EOFException.TRUNCATED_INSTRUCTION,
    )


@pytest.mark.parametrize("offset", [-7, -15])
def test_rjumpi_into_header(
    eof_test: EOFTestFiller,
    offset: int,
):
    """
    EOF1I4200_0016 (Invalid) EOF code containing RJUMPI with target outside code bounds
    (Jumping into header).
    """
    eof_test(
        container=Container(
            sections=[
                Section.Code(
                    code=Op.PUSH1(1) + Op.RJUMPI[offset] + Op.STOP,
                )
            ],
        ),
        expect_exception=EOFException.INVALID_RJUMP_DESTINATION,
    )


def test_rjumpi_jump_before_header(
    eof_test: EOFTestFiller,
):
    """
    EOF1I4200_0017 (Invalid) EOF code containing RJUMPI with target outside code bounds
    (Jumping to before code begin).
    """
    eof_test(
        container=Container(
            sections=[
                Section.Code(
                    code=Op.PUSH1(1) + Op.RJUMPI[-25] + Op.STOP,
                )
            ],
        ),
        expect_exception=EOFException.INVALID_RJUMP_DESTINATION,
    )


def test_rjumpi_into_data(
    eof_test: EOFTestFiller,
):
    """
    EOF1I4200_0018 (Invalid) EOF code containing RJUMPI with target outside code bounds
    (Jumping into data section).
    """
    eof_test(
        container=Container(
            sections=[
                Section.Code(
                    code=Op.PUSH1(1) + Op.RJUMPI[2] + Op.STOP,
                ),
                Section.Data(data=b"\xaa\xbb\xcc"),
            ],
        ),
        expect_exception=EOFException.INVALID_RJUMP_DESTINATION,
    )


def test_rjumpi_after_container(
    eof_test: EOFTestFiller,
):
    """
    EOF1I4200_0019 (Invalid) EOF code containing RJUMPI with target outside code bounds
    (Jumping to after code end).
    """
    eof_test(
        container=Container(
            sections=[
                Section.Code(
                    code=Op.PUSH1(1) + Op.RJUMPI[2] + Op.STOP,
                )
            ],
        ),
        expect_exception=EOFException.INVALID_RJUMP_DESTINATION,
    )


def test_rjumpi_to_code_end(
    eof_test: EOFTestFiller,
):
    """
    EOF1I4200_0020 (Invalid) EOF code containing RJUMPI with target outside code bounds
    (Jumping to code end).
    """
    eof_test(
        container=Container(
            sections=[
                Section.Code(
                    code=Op.PUSH1(1) + Op.RJUMPI[1] + Op.STOP,
                ),
            ],
        ),
        expect_exception=EOFException.INVALID_RJUMP_DESTINATION,
    )


@pytest.mark.parametrize("offset", range(1, Op.RJUMP.data_portion_length + 1))
def test_rjumpi_into_self_data_portion(
    eof_test: EOFTestFiller,
    offset: int,
):
    """
    EOF1I4200_0021 (Invalid) EOF code containing RJUMPI with target same RJUMPI immediate
    (with offset).
    """
    eof_test(
        container=Container(
            sections=[
                Section.Code(
                    code=Op.PUSH1(1) + Op.RJUMPI[-offset] + Op.STOP,
                )
            ],
        ),
        expect_exception=EOFException.INVALID_RJUMP_DESTINATION,
    )


def test_rjumpi_into_self(
    eof_test: EOFTestFiller,
):
    """EOF1I4200_0021 (Invalid) EOF code containing RJUMPI with target same RJUMPI immediate."""
    eof_test(
        container=Container(
            sections=[
                Section.Code(
                    code=Op.PUSH1(1) + Op.RJUMPI[-len(Op.RJUMPI[0])] + Op.STOP,
                )
            ],
        ),
        expect_exception=EOFException.STACK_HEIGHT_MISMATCH,
    )


def test_rjumpi_into_stack_height_diff(
    eof_test: EOFTestFiller,
):
    """EOF code containing RJUMPI with target instruction that causes stack height difference."""
    eof_test(
        container=Container(
            sections=[
                Section.Code(
                    code=Op.PUSH1(0)
                    + Op.PUSH1(0)
                    + Op.RJUMPI[-(len(Op.RJUMPI[0]) + len(Op.PUSH1(0)) + len(Op.PUSH1(0)))]
                    + Op.STOP,
                ),
            ],
        ),
        expect_exception=EOFException.STACK_HEIGHT_MISMATCH,
    )


def test_rjumpi_into_stack_underflow(
    eof_test: EOFTestFiller,
):
    """EOF code containing RJUMPI with target instruction that cause stack underflow."""
    eof_test(
        container=Container(
            sections=[
                Section.Code(
                    code=Op.ORIGIN + Op.RJUMPI[len(Op.STOP)] + Op.STOP + Op.POP + Op.STOP
                ),
            ],
        ),
        expect_exception=EOFException.STACK_UNDERFLOW,
    )


def test_rjumpi_skips_stack_underflow(
    eof_test: EOFTestFiller,
):
    """EOF code containing RJUMPI where the default path produces a stack underflow."""
    eof_test(
        container=Container(
            sections=[
                Section.Code(code=Op.ORIGIN + Op.RJUMPI[len(Op.POP)] + Op.POP + Op.STOP),
            ],
        ),
        expect_exception=EOFException.STACK_UNDERFLOW,
    )


def test_rjumpi_into_rjump(
    eof_test: EOFTestFiller,
):
    """EOF1I4200_0023 (Invalid) EOF code containing RJUMPI with target RJUMP immediate."""
    eof_test(
        container=Container(
            sections=[
                Section.Code(
                    code=Op.PUSH1(1) + Op.RJUMPI[3] + Op.STOP + Op.RJUMP[-9],
                )
            ],
        ),
        expect_exception=EOFException.INVALID_RJUMP_DESTINATION,
    )


def test_rjumpi_into_rjumpi(
    eof_test: EOFTestFiller,
):
    """EOF1I4200_0022 (Invalid) EOF code containing RJUMPI with target other RJUMPI immediate."""
    eof_test(
        container=Container(
            sections=[
                Section.Code(
                    code=Op.PUSH1(1)
                    + Op.RJUMPI[5]
                    + Op.STOP
                    + Op.PUSH1(1)
                    + Op.RJUMPI[-11]
                    + Op.STOP,
                )
            ],
        ),
        expect_exception=EOFException.INVALID_RJUMP_DESTINATION,
    )


@pytest.mark.parametrize("jump", [JumpDirection.FORWARD, JumpDirection.BACKWARD])
def test_rjumpi_into_push_1(
    eof_test: EOFTestFiller,
    jump: JumpDirection,
):
    """EOF1I4200_0024 (Invalid) EOF code containing RJUMPI with target PUSH1 immediate."""
    code = (
        Op.PUSH1[1] + Op.RJUMPI[-4]
        if jump == JumpDirection.BACKWARD
        else Op.PUSH1[1] + Op.RJUMPI[1] + Op.PUSH1[1] + Op.POP
    ) + Op.STOP
    eof_test(
        container=Container(
            sections=[
                Section.Code(code=code),
            ],
        ),
        expect_exception=EOFException.INVALID_RJUMP_DESTINATION,
    )


@pytest.mark.parametrize(
    "opcode",
    [
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
@pytest.mark.parametrize("jump", [JumpDirection.FORWARD, JumpDirection.BACKWARD])
@pytest.mark.parametrize(
    "data_portion_end",
    [True, False],
    ids=["data_portion_end", "data_portion_start"],
)
def test_rjumpi_into_push_n(
    eof_test: EOFTestFiller,
    opcode: Op,
    jump: JumpDirection,
    data_portion_end: bool,
):
    """EOF1I4200_0024 (Invalid) EOF code containing RJUMPI with target PUSH2+ immediate."""
    data_portion_length = int.from_bytes(opcode, byteorder="big") - 0x5F
    if jump == JumpDirection.FORWARD:
        offset = data_portion_length if data_portion_end else 1
        code = Op.PUSH1(1) + Op.RJUMPI[offset] + opcode[0] + Op.STOP
    else:
        offset = -4 if data_portion_end else -4 - data_portion_length + 1
        code = opcode[0] + Op.RJUMPI[offset] + Op.STOP
    eof_test(
        container=Container(
            sections=[
                Section.Code(code=code),
            ],
        ),
        expect_exception=EOFException.INVALID_RJUMP_DESTINATION,
    )


@pytest.mark.parametrize("target_rjumpv_table_size", [1, 256])
@pytest.mark.parametrize(
    "data_portion_end",
    [True, False],
    ids=["data_portion_end", "data_portion_start"],
)
def test_rjumpi_into_rjumpv(
    eof_test: EOFTestFiller,
    target_rjumpv_table_size: int,
    data_portion_end: bool,
):
    """EOF1I4200_0025 (Invalid) EOF code containing RJUMPI with target RJUMPV immediate."""
    invalid_destination = 4 + (2 * target_rjumpv_table_size) if data_portion_end else 4
    target_jump_table = [0 for _ in range(target_rjumpv_table_size)]
    eof_test(
        container=Container(
            sections=[
                Section.Code(
                    code=Op.PUSH1(1)
                    + Op.RJUMPI[invalid_destination]
                    + Op.STOP
                    + Op.PUSH1(1)
                    + Op.RJUMPV[target_jump_table]
                    + Op.STOP,
                )
            ],
        ),
        expect_exception=EOFException.INVALID_RJUMP_DESTINATION,
    )


@pytest.mark.parametrize(
    "data_portion_end",
    [True, False],
    ids=["data_portion_end", "data_portion_start"],
)
def test_rjumpi_into_callf(
    eof_test: EOFTestFiller,
    data_portion_end: bool,
):
    """EOF1I4200_0026 (Invalid) EOF code containing RJUMPI with target CALLF immediate."""
    invalid_destination = 2 if data_portion_end else 1
    eof_test(
        container=Container(
            sections=[
                Section.Code(
                    code=Op.PUSH1(1) + Op.RJUMPI[invalid_destination] + Op.CALLF[1] + Op.STOP,
                ),
                Section.Code(
                    code=Op.SSTORE(1, 1) + Op.RETF,
                    code_outputs=0,
                ),
            ],
        ),
        expect_exception=EOFException.INVALID_RJUMP_DESTINATION,
    )


def test_rjumpi_into_dupn(
    eof_test: EOFTestFiller,
):
    """EOF code containing RJUMPI with target DUPN immediate."""
    eof_test(
        container=Container(
            sections=[
                Section.Code(
                    code=Op.PUSH1(1)
                    + Op.PUSH1(1)
                    + Op.PUSH1(1)
                    + Op.RJUMPI[1]
                    + Op.DUPN[1]
                    + Op.SSTORE
                    + Op.STOP,
                ),
            ],
        ),
        expect_exception=EOFException.INVALID_RJUMP_DESTINATION,
    )


def test_rjumpi_into_swapn(
    eof_test: EOFTestFiller,
):
    """EOF code containing RJUMPI with target SWAPN immediate."""
    eof_test(
        container=Container(
            sections=[
                Section.Code(
                    code=Op.PUSH1(1)
                    + Op.PUSH1(1)
                    + Op.PUSH1(1)
                    + Op.RJUMPI[1]
                    + Op.SWAPN[1]
                    + Op.SSTORE
                    + Op.STOP,
                ),
            ],
        ),
        expect_exception=EOFException.INVALID_RJUMP_DESTINATION,
    )


def test_rjumpi_into_exchange(
    eof_test: EOFTestFiller,
):
    """EOF code containing RJUMPI with target EXCHANGE immediate."""
    eof_test(
        container=Container(
            sections=[
                Section.Code(
                    code=Op.PUSH1(1)
                    + Op.PUSH1(2)
                    + Op.PUSH1(3)
                    + Op.PUSH1(1)
                    + Op.RJUMPI[1]
                    + Op.EXCHANGE[0x00]
                    + Op.SSTORE
                    + Op.STOP,
                ),
            ],
        ),
        expect_exception=EOFException.INVALID_RJUMP_DESTINATION,
    )


def test_rjumpi_into_eofcreate(
    eof_test: EOFTestFiller,
):
    """EOF code containing RJUMPI with target EOFCREATE immediate."""
    eof_test(
        container=Container(
            sections=[
                Section.Code(
                    code=Op.PUSH0 * 5 + Op.RJUMPI[1] + Op.EOFCREATE[0] + Op.STOP,
                ),
                Section.Container(
                    container=Container(
                        sections=[
                            Section.Code(
                                code=Op.RETURNCONTRACT[0](0, 0),
                            ),
                            Section.Container(
                                container=Container.Code(code=Op.STOP),
                            ),
                        ]
                    )
                ),
            ],
        ),
        expect_exception=EOFException.INVALID_RJUMP_DESTINATION,
    )


def test_rjumpi_into_returncontract(
    eof_test: EOFTestFiller,
):
    """EOF code containing RJUMPI with target RETURNCONTRACT immediate."""
    eof_test(
        container=Container(
            sections=[
                Section.Code(
                    code=Op.EOFCREATE[0](0, 0, 0, 0) + Op.STOP,
                ),
                Section.Container(
                    container=Container(
                        sections=[
                            Section.Code(
                                code=Op.PUSH0 * 3 + Op.RJUMPI[1] + Op.RETURNCONTRACT[0],
                            ),
                            Section.Container(
                                container=Container.Code(code=Op.STOP),
                            ),
                        ]
                    )
                ),
            ],
        ),
        expect_exception=EOFException.INVALID_RJUMP_DESTINATION,
    )


def test_rjumpi_backwards_reference_only(
    eof_test: EOFTestFiller,
):
    """EOF code containing instructions only reachable by backwards RJUMPI."""
    container = Container.Code(
        code=(
            Op.RJUMP[RJUMP_LEN]
            + Op.RJUMP[RJUMPI_LEN + len(Op.ORIGIN)]
            + Op.ORIGIN
            + Op.RJUMPI[-(RJUMP_LEN + RJUMPI_LEN + len(Op.ORIGIN))]
            + Op.STOP
        )
    )
    eof_test(
        container=container,
        expect_exception=EOFException.UNREACHABLE_INSTRUCTIONS,
    )


def test_rjumpi_stack_validation(
    eof_test: EOFTestFiller,
):
    """
    Check that you can get to the same opcode with two different stack heights
    Spec now allows this:
    4.b in https://github.com/ipsilon/eof/blob/main/spec/eof.md#stack-validation.
    """
    container = Container.Code(code=Op.RJUMPI[1](1) + Op.ADDRESS + Op.NOOP + Op.STOP)
    eof_test(
        container=container,
        expect_exception=None,
    )


def test_rjumpi_at_the_end(
    eof_test: EOFTestFiller,
):
    """
    Test invalid RJUMPI as the end of a code section.
    https://github.com/ipsilon/eof/blob/main/spec/eof.md#stack-validation 4.i:
    This implies that the last instruction must be a terminating instruction or RJUMP.
    """
    eof_test(
        container=Container(
            sections=[
                Section.Code(
                    code=Op.PUSH0 + Op.PUSH0 + Op.RJUMPI[1] + Op.STOP + Op.RJUMPI[-4],
                )
            ],
        ),
        expect_exception=EOFException.MISSING_STOP_OPCODE,
    )


def test_tangled_rjumpi(
    eof_test: EOFTestFiller,
):
    """EOF code containing tangled RJUMPI paths."""
    container = Container.Code(
        code=(
            Op.PUSH0  # [0,0]
            + Op.PUSH0  # [1,1]
            + Op.RJUMPI[8]  # [2,2]
            + Op.PUSH1(127)  # [1,1]
            + Op.RJUMPI[7]  # [2,2]
            + Op.RJUMP[5]  # [1,1]
            + Op.PUSH0  # [1,1]
            + Op.RJUMP[0]  # [2,1]
            + Op.LT  # [1,x]
            + Op.STOP  # [1,x]
        )
    )
    eof_test(
        container=container,
        expect_exception=EOFException.STACK_UNDERFLOW,
    )


def test_rjumpi_backwards_onto_dup(
    eof_test: EOFTestFiller,
):
    """Backwards jumpi onto a dup."""
    container = Container.Code(
        code=(Op.PUSH0 + Op.DUP1 + Op.RJUMPI[-4] + Op.STOP),
        max_stack_height=2,
    )
    eof_test(
        container=container,
    )


def test_rjumpi_backwards_min_stack_wrong(
    eof_test: EOFTestFiller,
):
    """Backwards rjumpi where min_stack does not match."""
    container = Container.Code(
        code=(
            Op.PUSH0  # (0, 0)
            + Op.PUSH1(0)  # (1, 1)
            + Op.RJUMPI[1]  # (2, 2) To PUSH1
            + Op.PUSH0  # (1, 1)
            + Op.PUSH1(4)  # (1, 2)
            + Op.RJUMPI[-9]  # (2, 3) To first RJUMPI with (1, 2)
            + Op.STOP  # (1, 2)
        ),
        max_stack_height=3,
    )
    eof_test(
        container=container,
        expect_exception=EOFException.STACK_HEIGHT_MISMATCH,
    )


def test_rjumpi_rjumpv_backwards_min_stack_wrong(
    eof_test: EOFTestFiller,
):
    """Backwards rjumpi rjumpv where min_stack does not match."""
    container = Container.Code(
        code=(
            Op.PUSH0  # (0, 0)
            + Op.PUSH1(0)  # (1, 1)
            + Op.RJUMPI[1]  # (2, 2) To PUSH1
            + Op.PUSH0  # (1, 1)
            + Op.PUSH1(4)  # (1, 2)
            + Op.RJUMPV[-10]  # (2, 3) To first RJUMPI with (1, 2)
            + Op.STOP  # (1, 2)
        ),
        max_stack_height=3,
    )
    eof_test(
        container=container,
        expect_exception=EOFException.STACK_HEIGHT_MISMATCH,
    )


def test_double_rjumpi_stack_underflow(
    eof_test: EOFTestFiller,
):
    """Two RJUMPIs, causing the min stack to underflow."""
    container = Container.Code(
        code=(
            Op.PUSH0  # (0, 0)
            + Op.PUSH0  # (1, 1)
            + Op.RJUMPI[5]  # (2, 2) To RETURN
            + Op.PUSH0  # (1, 1)
            + Op.PUSH0  # (2, 2)
            + Op.RJUMPI[0]  # (3, 3)
            + Op.RETURN  # (1, 2) Underflow
        ),
        max_stack_height=3,
    )
    eof_test(
        container=container,
        expect_exception=EOFException.STACK_UNDERFLOW,
    )


def test_double_rjumpi_stack_height_mismatch(
    eof_test: EOFTestFiller,
):
    """
    Test stack height check of the backward RJUMP
    targeted by two RJUMPIs with the non-uniform stack height range.
    """
    eof_test(
        container=Container(
            sections=[
                Section.Code(
                    code=Op.PUSH0  # BEGIN: (0, 0)
                    + Op.PUSH0  # (1, 1)
                    + Op.RJUMPI[3]  # (2, 2) to LAST
                    + Op.RJUMPI[0]  # (1, 1) to LAST
                    + Op.RJUMP[-11],  # LAST: (0, 1) to BEGIN; stack height mismatch
                    max_stack_height=2,
                ),
            ],
        ),
        expect_exception=EOFException.STACK_HEIGHT_MISMATCH,
    )


def test_double_rjumpi_invalid_max_stack_height(
    eof_test: EOFTestFiller,
):
    """
    Test max stack height of the final block
    targeted by two RJUMPIs with the non-uniform stack height range.
    """
    eof_test(
        container=Container(
            sections=[
                Section.Code(
                    code=Op.PUSH0  # (0, 0)
                    + Op.PUSH0  # (1, 1)
                    + Op.RJUMPI[3]  # (2, 2) to EXIT
                    + Op.RJUMPI[0]  # (1, 1) to EXIT
                    + Op.PUSH0  # EXIT: (0, 1)
                    + Op.PUSH0  # (1, 2)
                    + Op.INVALID,  # (2, 3)
                    max_stack_height=2,  # should be 3
                ),
            ],
        ),
        expect_exception=EOFException.INVALID_MAX_STACK_HEIGHT,
    )


@pytest.mark.parametrize(
    "container",
    [
        Container(
            name="backwards_rjumpi_10",
            sections=[
                Section.Code(
                    code=Op.PUSH1[190]
                    + Op.PUSH1[0]
                    + Op.RJUMPI[1]
                    + Op.POP
                    + Op.PUSH1[0]
                    + Op.RJUMPI[-11]
                    + Op.STOP,
                    max_stack_height=3,
                ),
            ],
            expected_bytecode="ef0001010004020001000e040000000080000360be6000e10001506000e1fff500",
        ),
        Container(
            name="backwards_rjumpi_3",
            sections=[
                Section.Code(
                    code=Op.PUSH0
                    + Op.POP
                    + Op.PUSH1[0]
                    + Op.RJUMPI[-7]
                    + Op.PUSH0
                    + Op.PUSH1[0]
                    + Op.RJUMPI[-13]
                    + Op.STOP,
                    max_stack_height=2,
                ),
            ],
            expected_bytecode="ef0001010004020001000e04000000008000025f506000e1fff95f6000e1fff300",
        ),
        Container(
            name="backwards_rjumpi_5",
            sections=[
                Section.Code(
                    code=Op.PUSH0
                    + Op.PUSH1[1]
                    + Op.ADD
                    + Op.DUP1
                    + Op.DUP1
                    + Op.RJUMPI[-8]
                    + Op.STOP,
                    max_stack_height=2,
                ),
            ],
            expected_bytecode="ef0001010004020001000a04000000008000025f6001018080e1fff800",
        ),
        Container(
            name="backwards_rjumpi_8",
            sections=[
                Section.Code(
                    code=Op.PUSH0
                    + Op.POP
                    + Op.PUSH1[0]
                    + Op.RJUMPI[-6]
                    + Op.PUSH0
                    + Op.RJUMP[-10],
                    max_stack_height=1,
                ),
            ],
        ),
        Container(
            name="backwards_rjumpi_9",
            sections=[
                Section.Code(
                    code=Op.PUSH0
                    + Op.PUSH1[0]
                    + Op.RJUMPI[1]
                    + Op.PUSH0
                    + Op.PUSH1[0]
                    + Op.RJUMPI[-11]
                    + Op.STOP,
                    max_stack_height=3,
                ),
            ],
            expected_bytecode="ef0001010004020001000d04000000008000035f6000e100015f6000e1fff500",
        ),
        Container(
            name="backwards_rjumpi_variable_stack_3",
            sections=[
                Section.Code(
                    code=Op.PUSH0
                    + Op.PUSH1[0]
                    + Op.RJUMPI[2]
                    + Op.PUSH0
                    + Op.PUSH0
                    + Op.PUSH0
                    + Op.POP
                    + Op.PUSH1[0]
                    + Op.RJUMPI[-7]
                    + Op.PUSH0
                    + Op.PUSH1[0]
                    + Op.RJUMPI[-13]
                    + Op.STOP,
                    max_stack_height=5,
                ),
            ],
            expected_bytecode="ef0001010004020001001604000000008000055f6000e100025f5f5f506000e1fff95f6000e1fff300",
        ),
        Container(
            name="backwards_rjumpi_variable_stack_5",
            sections=[
                Section.Code(
                    code=Op.PUSH0
                    + Op.PUSH1[0]
                    + Op.RJUMPI[2]
                    + Op.PUSH0
                    + Op.PUSH0
                    + Op.PUSH0
                    + Op.PUSH1[1]
                    + Op.ADD
                    + Op.DUP1
                    + Op.DUP1
                    + Op.RJUMPI[-8]
                    + Op.STOP,
                    max_stack_height=5,
                ),
            ],
            expected_bytecode="ef0001010004020001001204000000008000055f6000e100025f5f5f6001018080e1fff800",
        ),
        Container(
            name="backwards_rjumpi_variable_stack_6",
            sections=[
                Section.Code(
                    code=Op.PUSH0
                    + Op.PUSH1[0]
                    + Op.RJUMPI[2]
                    + Op.PUSH0
                    + Op.PUSH0
                    + Op.PUSH0
                    + Op.PUSH0
                    + Op.PUSH0
                    + Op.POP
                    + Op.RJUMPI[-4]
                    + Op.STOP,
                    max_stack_height=5,
                ),
            ],
            expected_bytecode="ef0001010004020001001004000000008000055f6000e100025f5f5f5f5f50e1fffc00",
        ),
        Container(
            name="backwards_rjumpi_variable_stack_6a",
            sections=[
                Section.Code(
                    code=Op.PUSH0
                    + Op.PUSH1[0]
                    + Op.RJUMPI[2]
                    + Op.PUSH0
                    + Op.PUSH0
                    + Op.PUSH0
                    + Op.PUSH0
                    + Op.POP
                    + Op.PUSH0
                    + Op.RJUMPI[-5]
                    + Op.STOP,
                    max_stack_height=5,
                ),
            ],
        ),
        Container(
            name="backwards_rjumpi_variable_stack_8",
            sections=[
                Section.Code(
                    code=Op.PUSH0
                    + Op.PUSH1[0]
                    + Op.RJUMPI[2]
                    + Op.PUSH0
                    + Op.PUSH0
                    + Op.PUSH0
                    + Op.POP
                    + Op.PUSH1[0]
                    + Op.RJUMPI[-8]
                    + Op.PUSH0
                    + Op.RJUMP[-10],
                    max_stack_height=4,
                ),
            ],
        ),
    ],
    ids=lambda x: x.name,
)
def test_rjumpi_backward_invalid_max_stack_height(
    eof_test: EOFTestFiller,
    container: Container,
):
    """
    Validate a code section containing at least one backward RJUMPI
    invalid because of the incorrect max stack height.
    """
    eof_test(container=container, expect_exception=EOFException.STACK_HEIGHT_MISMATCH)
