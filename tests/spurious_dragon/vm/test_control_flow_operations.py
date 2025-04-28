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
    "test_file, check_gas_left",
    [
        ("jump0_jumpdest0.json", True),
        ("jump0_jumpdest2.json", True),
        ("jumpAfterStop.json", True),
        ("jumpdestBigList.json", True),
        ("jumpTo1InstructionafterJump.json", True),
        ("jumpDynamicJumpSameDest.json", True),
        ("indirect_jump1.json", True),
        ("indirect_jump2.json", True),
        ("indirect_jump3.json", True),
        ("DynamicJump_value1.json", True),
        ("DynamicJump_value2.json", True),
        ("DynamicJump_value3.json", True),
        ("stackjump1.json", True),
        ("indirect_jump4.json", True),
        ("JDfromStorageDynamicJump0_jumpdest0.json", False),
        ("JDfromStorageDynamicJump0_jumpdest2.json", False),
        ("DynamicJump0_jumpdest0.json", True),
        ("DynamicJump0_jumpdest2.json", True),
        ("DynamicJumpAfterStop.json", True),
        ("DynamicJumpJD_DependsOnJumps1.json", True),
        ("DynamicJumpPathologicalTest0.json", True),
        ("DynamicJumpStartWithJumpDest.json", True),
        ("BlockNumberDynamicJump0_jumpdest0.json", True),
        ("BlockNumberDynamicJump0_jumpdest2.json", True),
        ("bad_indirect_jump1.json", True),
        ("bad_indirect_jump2.json", True),
        ("jump0_AfterJumpdest.json", True),
        ("jump0_AfterJumpdest3.json", True),
        ("jump0_outOfBoundary.json", True),
        ("jump0_withoutJumpdest.json", True),
        ("jump1.json", True),
        ("jumpHigh.json", True),
        ("jumpInsidePushWithJumpDest.json", True),
        ("jumpInsidePushWithoutJumpDest.json", True),
        ("jumpTo1InstructionafterJump_jumpdestFirstInstruction.json", True),
        ("jumpTo1InstructionafterJump_noJumpDest.json", True),
        ("jumpToUint64maxPlus1.json", True),
        ("jumpToUintmaxPlus1.json", True),
        ("JDfromStorageDynamicJump0_AfterJumpdest.json", True),
        ("JDfromStorageDynamicJump0_AfterJumpdest3.json", True),
        ("JDfromStorageDynamicJump0_withoutJumpdest.json", True),
        ("JDfromStorageDynamicJump1.json", True),
        ("JDfromStorageDynamicJumpInsidePushWithJumpDest.json", True),
        ("JDfromStorageDynamicJumpInsidePushWithoutJumpDest.json", True),
        ("DynamicJump0_outOfBoundary.json", True),
        ("DynamicJump0_AfterJumpdest.json", True),
        ("DynamicJump0_AfterJumpdest3.json", True),
        ("DynamicJump0_withoutJumpdest.json", True),
        ("DynamicJump1.json", True),
        ("DynamicJumpInsidePushWithJumpDest.json", True),
        ("DynamicJumpInsidePushWithoutJumpDest.json", True),
        ("DynamicJumpJD_DependsOnJumps0.json", True),
        ("DynamicJumpPathologicalTest1.json", True),
        ("DynamicJumpPathologicalTest2.json", True),
        ("DynamicJumpPathologicalTest3.json", True),
        ("BlockNumberDynamicJump0_AfterJumpdest.json", True),
        ("BlockNumberDynamicJump0_AfterJumpdest3.json", True),
        ("BlockNumberDynamicJump0_withoutJumpdest.json", True),
        ("BlockNumberDynamicJump1.json", True),
        ("BlockNumberDynamicJumpInsidePushWithJumpDest.json", True),
        ("BlockNumberDynamicJumpInsidePushWithoutJumpDest.json", True),
        ("jump0_foreverOutOfGas.json", True),
        ("JDfromStorageDynamicJump0_foreverOutOfGas.json", True),
        ("DynamicJump0_foreverOutOfGas.json", True),
        ("BlockNumberDynamicJump0_foreverOutOfGas.json", True),
        ("jumpOntoJump.json", True),
        ("DynamicJump_valueUnderflow.json", True),
        ("stack_loop.json", True),
    ],
)
def test_jump(test_file: str, check_gas_left: bool) -> None:
    run_control_flow_ops_vm_test(test_file, check_gas_left=check_gas_left)


@pytest.mark.parametrize(
    "test_file, check_gas_left",
    [
        ("jumpi1.json", True),
        ("jumpiAfterStop.json", True),
        ("jumpi_at_the_end.json", True),
        ("JDfromStorageDynamicJumpi1.json", False),
        ("JDfromStorageDynamicJumpiAfterStop.json", False),
        ("DynamicJumpi1.json", True),
        ("DynamicJumpiAfterStop.json", True),
        ("BlockNumberDynamicJumpi1.json", True),
        ("BlockNumberDynamicJumpiAfterStop.json", True),
        ("jumpi0.json", True),
        ("jumpi1_jumpdest.json", True),
        ("jumpifInsidePushWithJumpDest.json", True),
        ("jumpifInsidePushWithoutJumpDest.json", True),
        ("jumpiOutsideBoundary.json", True),
        ("jumpiToUint64maxPlus1.json", True),
        ("jumpiToUintmaxPlus1.json", True),
        ("JDfromStorageDynamicJumpi0.json", True),
        ("JDfromStorageDynamicJumpi1_jumpdest.json", True),
        ("JDfromStorageDynamicJumpifInsidePushWithJumpDest.json", True),
        ("JDfromStorageDynamicJumpifInsidePushWithoutJumpDest.json", True),
        ("JDfromStorageDynamicJumpiOutsideBoundary.json", True),
        ("DynamicJumpi0.json", True),
        ("DynamicJumpi1_jumpdest.json", True),
        ("DynamicJumpifInsidePushWithJumpDest.json", True),
        ("DynamicJumpifInsidePushWithoutJumpDest.json", True),
        ("DynamicJumpiOutsideBoundary.json", True),
        ("BlockNumberDynamicJumpi0.json", True),
        ("BlockNumberDynamicJumpi1_jumpdest.json", True),
        ("BlockNumberDynamicJumpifInsidePushWithJumpDest.json", True),
        ("BlockNumberDynamicJumpifInsidePushWithoutJumpDest.json", True),
        ("BlockNumberDynamicJumpiOutsideBoundary.json", True),
    ],
)
def test_jumpi(test_file: str, check_gas_left: bool) -> None:
    run_control_flow_ops_vm_test(test_file, check_gas_left=check_gas_left)


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
