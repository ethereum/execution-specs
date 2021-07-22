from functools import partial

import pytest

from ethereum.frontier.vm.error import (
    InvalidJumpDestError,
    OutOfGasError,
    StackUnderflowError,
)

from .vm_test_helpers import run_test

run_control_flow_ops_vm_test = partial(
    run_test,
    "tests/fixtures/LegacyTests/Constantinople/VMTests/vmIOandFlowOperations",
)


@pytest.mark.parametrize(
    "test_file",
    [
        "jump0_jumpdest0.json",
        "jump0_jumpdest2.json",
        "jumpAfterStop.json",
        "jumpdestBigList.json",
        "jumpTo1InstructionafterJump.json",
        # TODO: Run below test once RETURN is implemented
        # "jumpDynamicJumpSameDest.json",
        # "indirect_jump1.json",
        # "indirect_jump2.json",
        # "indirect_jump3.json",
        "indirect_jump4.json",
        "JDfromStorageDynamicJump0_jumpdest0.json",
        "JDfromStorageDynamicJump0_jumpdest2.json",
        # TODO: Run below test once CALLVALUE is implemented
        # "DynamicJump_value1.json",
        # "DynamicJump_value2.json",
        # "DynamicJump_value3.json",
        "DynamicJump0_jumpdest0.json",
        "DynamicJump0_jumpdest2.json",
        "DynamicJumpAfterStop.json",
        # TODO: Run below test cases once NUMBER opcode has been implemented.
        # "DynamicJumpJD_DependsOnJumps1.json",
        # "DynamicJumpPathologicalTest0.json",
        # "DynamicJumpPathologicalTest1.json",
        # "DynamicJumpPathologicalTest2.json",
        # "DynamicJumpPathologicalTest3.json",
        "DynamicJumpStartWithJumpDest.json",
    ],
)
def test_jump(test_file: str) -> None:
    run_control_flow_ops_vm_test(test_file)


@pytest.mark.parametrize(
    "test_file",
    [
        "bad_indirect_jump1.json",
        "bad_indirect_jump2.json",
        "jump0_AfterJumpdest.json",
        "jump0_AfterJumpdest3.json",
        "jump0_outOfBoundary.json",
        "jump0_withoutJumpdest.json",
        "jump1.json",
        "jumpHigh.json",
        "jumpInsidePushWithJumpDest.json",
        "jumpInsidePushWithoutJumpDest.json",
        "jumpTo1InstructionafterJump_jumpdestFirstInstruction.json",
        "jumpTo1InstructionafterJump_noJumpDest.json",
        "jumpToUint64maxPlus1.json",
        "jumpToUintmaxPlus1.json",
        "JDfromStorageDynamicJump0_AfterJumpdest.json",
        "JDfromStorageDynamicJump0_AfterJumpdest3.json",
        "JDfromStorageDynamicJump0_withoutJumpdest.json",
        "JDfromStorageDynamicJump1.json",
        "JDfromStorageDynamicJumpInsidePushWithJumpDest.json",
        "JDfromStorageDynamicJumpInsidePushWithoutJumpDest.json",
        "DyanmicJump0_outOfBoundary.json",
        "DynamicJump0_AfterJumpdest.json",
        "DynamicJump0_AfterJumpdest3.json",
        "DynamicJump0_withoutJumpdest.json",
        "DynamicJump1.json",
        "DynamicJumpInsidePushWithJumpDest.json",
        "DynamicJumpInsidePushWithoutJumpDest.json",
        # TODO: Run below test case once NUMBER opcode has been implemented.
        # "DynamicJumpJD_DependsOnJumps0.json",
    ],
)
def test_jump_raises_invalid_jump_dest_error(test_file: str) -> None:
    with pytest.raises(InvalidJumpDestError):
        run_control_flow_ops_vm_test(test_file)


@pytest.mark.parametrize(
    "test_file",
    [
        "jump0_foreverOutOfGas.json",
        "JDfromStorageDynamicJump0_foreverOutOfGas.json",
        "DynamicJump0_foreverOutOfGas.json",
    ],
)
def test_jump_raises_error_when_out_of_gas(test_file: str) -> None:
    with pytest.raises(OutOfGasError):
        run_control_flow_ops_vm_test(test_file)


@pytest.mark.parametrize(
    "test_file",
    [
        "jumpOntoJump.json",
        # TODO: Run below test once CALLVALUE has been implemented
        # "DynamicJump_valueUnderflow.json",
    ],
)
def test_jump_raises_error_when_stack_underflows(test_file: str) -> None:
    with pytest.raises(StackUnderflowError):
        run_control_flow_ops_vm_test(test_file)


@pytest.mark.parametrize(
    "test_file",
    [
        "jumpi1.json",
        "jumpiAfterStop.json",
        "jumpi_at_the_end.json",
        "JDfromStorageDynamicJumpi1.json",
        "JDfromStorageDynamicJumpiAfterStop.json",
        "DynamicJumpi1.json",
        "DynamicJumpiAfterStop.json",
    ],
)
def test_jumpi(test_file: str) -> None:
    run_control_flow_ops_vm_test(test_file)


@pytest.mark.parametrize(
    "test_file",
    [
        "jumpi0.json",
        "jumpi1_jumpdest.json",
        "jumpifInsidePushWithJumpDest.json",
        "jumpifInsidePushWithoutJumpDest.json",
        "jumpiOutsideBoundary.json",
        "jumpiToUint64maxPlus1.json",
        "jumpiToUintmaxPlus1.json",
        "JDfromStorageDynamicJumpi0.json",
        "JDfromStorageDynamicJumpi1_jumpdest.json",
        "JDfromStorageDynamicJumpifInsidePushWithJumpDest.json",
        "JDfromStorageDynamicJumpifInsidePushWithoutJumpDest.json",
        "JDfromStorageDynamicJumpiOutsideBoundary.json",
        "DynamicJumpi0.json",
        "DynamicJumpi1_jumpdest.json",
        "DynamicJumpifInsidePushWithJumpDest.json",
        "DynamicJumpifInsidePushWithoutJumpDest.json",
        "DynamicJumpiOutsideBoundary.json",
    ],
)
def test_jumpi_raises_invalid_jump_dest_error(test_file: str) -> None:
    with pytest.raises(InvalidJumpDestError):
        run_control_flow_ops_vm_test(test_file)


@pytest.mark.parametrize(
    "test_file",
    [
        "pc0.json",
        "pc1.json",
    ],
)
def test_pc(test_file: str) -> None:
    run_control_flow_ops_vm_test(test_file)


@pytest.mark.parametrize(
    "test_file",
    [
        "gas0.json",
        "gas1.json",
    ],
)
def test_gas(test_file: str) -> None:
    run_control_flow_ops_vm_test(test_file)


def test_gas_fails_overflow() -> None:
    with pytest.raises(InvalidJumpDestError):
        run_control_flow_ops_vm_test("gasOverFlow.json")


# TODO: There are some more test cases to be run. But they depend on block
# operations. Need to run the remaining test cases in
# vmIOandFlowOperations once the mentioned operations are done.
