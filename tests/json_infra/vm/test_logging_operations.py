from typing import Tuple

import pytest

from .. import TEST_FIXTURES
from ..helpers.load_vm_tests import VmTestLoader
from . import forks_to_test

ETHEREUM_TESTS_PATH = TEST_FIXTURES["ethereum_tests"]["fixture_path"]
TEST_DIR = (
    f"{ETHEREUM_TESTS_PATH}/LegacyTests/Constantinople/VMTests/vmLogTest"
)


@pytest.mark.parametrize("fork", forks_to_test)
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
def test_log0(fork: Tuple[str, str], test_file: str) -> None:
    VmTestLoader(*fork).run_test(TEST_DIR, test_file)


@pytest.mark.parametrize("fork", forks_to_test)
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
def test_log1(fork: Tuple[str, str], test_file: str) -> None:
    VmTestLoader(*fork).run_test(TEST_DIR, test_file)


@pytest.mark.parametrize("fork", forks_to_test)
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
def test_log2(fork: Tuple[str, str], test_file: str) -> None:
    VmTestLoader(*fork).run_test(TEST_DIR, test_file)


@pytest.mark.parametrize("fork", forks_to_test)
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
def test_log3(fork: Tuple[str, str], test_file: str) -> None:
    VmTestLoader(*fork).run_test(TEST_DIR, test_file)


@pytest.mark.parametrize("fork", forks_to_test)
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
def test_log4(fork: Tuple[str, str], test_file: str) -> None:
    VmTestLoader(*fork).run_test(TEST_DIR, test_file)
