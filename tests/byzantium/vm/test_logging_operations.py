from functools import partial

import pytest

from ..vm.vm_test_helpers import run_test

run_logging_ops_vm_test = partial(
    run_test,
    "tests/fixtures/LegacyTests/Constantinople/VMTests/vmLogTest",
)


@pytest.mark.parametrize(
    "test_file",
    [
        "log0_emptyMem.json",
        "log0_logMemsizeZero.json",
        "log0_nonEmptyMem.json",
        "log0_nonEmptyMem_logMemSize1.json",
        "log0_nonEmptyMem_logMemSize1_logMemStart31.json",
        "log0_logMemsizeTooHigh.json",
        "log0_logMemStartTooHigh.json",
    ],
)
def test_log0(test_file: str) -> None:
    run_logging_ops_vm_test(test_file)


@pytest.mark.parametrize(
    "test_file",
    [
        "log1_Caller.json",
        "log1_emptyMem.json",
        "log1_logMemsizeZero.json",
        "log1_MaxTopic.json",
        "log1_nonEmptyMem.json",
        "log1_nonEmptyMem_logMemSize1.json",
        "log1_nonEmptyMem_logMemSize1_logMemStart31.json",
        "log1_logMemsizeTooHigh.json",
        "log1_logMemStartTooHigh.json",
    ],
)
def test_log1(test_file: str) -> None:
    run_logging_ops_vm_test(test_file)


@pytest.mark.parametrize(
    "test_file",
    [
        "log2_Caller.json",
        "log2_emptyMem.json",
        "log2_logMemsizeZero.json",
        "log2_MaxTopic.json",
        "log2_nonEmptyMem.json",
        "log2_nonEmptyMem_logMemSize1.json",
        "log2_nonEmptyMem_logMemSize1_logMemStart31.json",
        "log2_logMemsizeTooHigh.json",
        "log2_logMemStartTooHigh.json",
    ],
)
def test_log2(test_file: str) -> None:
    run_logging_ops_vm_test(test_file)


@pytest.mark.parametrize(
    "test_file",
    [
        "log3_Caller.json",
        "log3_emptyMem.json",
        "log3_logMemsizeZero.json",
        "log3_MaxTopic.json",
        "log3_nonEmptyMem.json",
        "log3_nonEmptyMem_logMemSize1.json",
        "log3_nonEmptyMem_logMemSize1_logMemStart31.json",
        "log3_PC.json",
        "log3_logMemsizeTooHigh.json",
        "log3_logMemStartTooHigh.json",
    ],
)
def test_log3(test_file: str) -> None:
    run_logging_ops_vm_test(test_file)


@pytest.mark.parametrize(
    "test_file",
    [
        "log4_Caller.json",
        "log4_emptyMem.json",
        "log4_logMemsizeZero.json",
        "log4_MaxTopic.json",
        "log4_nonEmptyMem.json",
        "log4_nonEmptyMem_logMemSize1.json",
        "log4_nonEmptyMem_logMemSize1_logMemStart31.json",
        "log4_PC.json",
        "log4_logMemsizeTooHigh.json",
        "log4_logMemStartTooHigh.json",
    ],
)
def test_log4(test_file: str) -> None:
    run_logging_ops_vm_test(test_file)
