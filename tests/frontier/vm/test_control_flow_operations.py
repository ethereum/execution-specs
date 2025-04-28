from functools import partial

import pytest

from tests.helpers import TEST_FIXTURES

from .vm_test_helpers import run_test

ETHEREUM_TESTS_PATH = TEST_FIXTURES["ethereum_tests"]["fixture_path"]

run_control_flow_ops_vm_test = partial(
    run_test,
    f"{ETHEREUM_TESTS_PATH}/LegacyTests/Constantinople/VMTests/vmIOandFlowOperations",
)


@pytest.mark.parametrize(
    "test_file",
    [
        "jump0_jumpdest0.json",
        "jump0_jumpdest2.json",
        "jumpAfterStop.json",
        "jumpdestBigList.json",
        "jumpTo1InstructionafterJump.json",
        "jumpDynamicJumpSameDest.json",
        "indirect_jump1.json",
        "indirect_jump2.json",
        "indirect_jump3.json",
        "DynamicJump_value1.json",
        "DynamicJump_value2.json",
        "DynamicJump_value3.json",
        "stackjump1.json",
        "indirect_jump4.json",
        "JDfromStorageDynamicJump0_jumpdest0.json",
        "JDfromStorageDynamicJump0_jumpdest2.json",
        "DynamicJump0_jumpdest0.json",
        "DynamicJump0_jumpdest2.json",
        "DynamicJumpAfterStop.json",
        "DynamicJumpJD_DependsOnJumps1.json",
        "DynamicJumpPathologicalTest0.json",
        "DynamicJumpStartWithJumpDest.json",
        "BlockNumberDynamicJump0_jumpdest0.json",
        "BlockNumberDynamicJump0_jumpdest2.json",
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
        "DynamicJump0_outOfBoundary.json",
        "DynamicJump0_AfterJumpdest.json",
        "DynamicJump0_AfterJumpdest3.json",
        "DynamicJump0_withoutJumpdest.json",
        "DynamicJump1.json",
        "DynamicJumpInsidePushWithJumpDest.json",
        "DynamicJumpInsidePushWithoutJumpDest.json",
        "DynamicJumpJD_DependsOnJumps0.json",
        "DynamicJumpPathologicalTest1.json",
        "DynamicJumpPathologicalTest2.json",
        "DynamicJumpPathologicalTest3.json",
        "BlockNumberDynamicJump0_AfterJumpdest.json",
        "BlockNumberDynamicJump0_AfterJumpdest3.json",
        "BlockNumberDynamicJump0_withoutJumpdest.json",
        "BlockNumberDynamicJump1.json",
        "BlockNumberDynamicJumpInsidePushWithJumpDest.json",
        "BlockNumberDynamicJumpInsidePushWithoutJumpDest.json",
        "jump0_foreverOutOfGas.json",
        "JDfromStorageDynamicJump0_foreverOutOfGas.json",
        "DynamicJump0_foreverOutOfGas.json",
        "BlockNumberDynamicJump0_foreverOutOfGas.json",
        "jumpOntoJump.json",
        "DynamicJump_valueUnderflow.json",
        "stack_loop.json",
    ],
)
def test_jump(test_file: str) -> None:
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
        "BlockNumberDynamicJumpi1.json",
        "BlockNumberDynamicJumpiAfterStop.json",
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
        "BlockNumberDynamicJumpi0.json",
        "BlockNumberDynamicJumpi1_jumpdest.json",
        "BlockNumberDynamicJumpifInsidePushWithJumpDest.json",
        "BlockNumberDynamicJumpifInsidePushWithoutJumpDest.json",
        "BlockNumberDynamicJumpiOutsideBoundary.json",
    ],
)
def test_jumpi(test_file: str) -> None:
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
    ["gas0.json", "gas1.json", "gasOverFlow.json"],
)
def test_gas(test_file: str) -> None:
    run_control_flow_ops_vm_test(test_file)


@pytest.mark.parametrize(
    "test_file",
    [
        "for_loop1.json",
        "for_loop2.json",
        "loop_stacklimit_1020.json",
        "loop_stacklimit_1021.json",
    ],
)
def test_loop(test_file: str) -> None:
    run_control_flow_ops_vm_test(test_file)


def test_when() -> None:
    run_control_flow_ops_vm_test("when.json")


@pytest.mark.parametrize(
    "test_file",
    [
        "byte1.json",
        "calldatacopyMemExp.json",
        "codecopyMemExp.json",
        "deadCode_1.json",
        "dupAt51becameMload.json",
        "swapAt52becameMstore.json",
        "log1MemExp.json",
    ],
)
def test_miscellaneous(test_file: str) -> None:
    run_control_flow_ops_vm_test(test_file)
