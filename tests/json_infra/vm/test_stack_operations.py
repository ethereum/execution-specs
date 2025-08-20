from typing import Tuple

import pytest

from .. import TEST_FIXTURES
from ..helpers.load_vm_tests import VmTestLoader
from . import FORKS

ETHEREUM_TESTS_PATH = TEST_FIXTURES["ethereum_tests"]["fixture_path"]
PUSH_TEST_DIR = f"{ETHEREUM_TESTS_PATH}/LegacyTests/Constantinople/VMTests/vmPushDupSwapTest"
POP_TEST_DIR = f"{ETHEREUM_TESTS_PATH}/LegacyTests/Constantinople/VMTests/vmIOandFlowOperations"

DUP_TEST_DIR = SWAP_TEST_DIR = PUSH_TEST_DIR


@pytest.mark.vm_test
@pytest.mark.parametrize("fork", FORKS)
@pytest.mark.parametrize(
    "test_file, check_gas_left",
    [(f"push{i}.json", True) for i in range(1, 34)]
    + [
        ("push32Undefined2.json", True),
        ("push32AndSuicide.json", False),
    ],
)
def test_push_successfully(
    fork: Tuple[str, str], test_file: str, check_gas_left: bool
) -> None:
    VmTestLoader(*fork).run_test(
        PUSH_TEST_DIR, test_file, check_gas_left=check_gas_left
    )


@pytest.mark.vm_test
@pytest.mark.parametrize("fork", FORKS)
@pytest.mark.parametrize(
    "test_file",
    [
        "push1_missingStack.json",
        "push32Undefined.json",
        "push32Undefined3.json",
        "push32FillUpInputWithZerosAtTheEnd.json",
    ],
)
def test_push_failed(fork: Tuple[str, str], test_file: str) -> None:
    VmTestLoader(*fork).run_test(PUSH_TEST_DIR, test_file)


@pytest.mark.vm_test
@pytest.mark.parametrize("fork", FORKS)
def test_dup(fork: Tuple[str, str]) -> None:
    for i in range(1, 17):
        VmTestLoader(*fork).run_test(DUP_TEST_DIR, f"dup{i}.json")


@pytest.mark.vm_test
@pytest.mark.parametrize("fork", FORKS)
def test_dup_error(fork: Tuple[str, str]) -> None:
    VmTestLoader(*fork).run_test(DUP_TEST_DIR, "dup2error.json")


@pytest.mark.vm_test
@pytest.mark.parametrize("fork", FORKS)
def test_swap(fork: Tuple[str, str]) -> None:
    for i in range(1, 17):
        VmTestLoader(*fork).run_test(SWAP_TEST_DIR, f"swap{i}.json")


@pytest.mark.vm_test
@pytest.mark.parametrize("fork", FORKS)
def test_swap_jump(fork: Tuple[str, str]) -> None:
    VmTestLoader(*fork).run_test(SWAP_TEST_DIR, "swapjump1.json")


@pytest.mark.vm_test
@pytest.mark.parametrize("fork", FORKS)
def test_swap_error(fork: Tuple[str, str]) -> None:
    VmTestLoader(*fork).run_test(SWAP_TEST_DIR, "swap2error.json")


@pytest.mark.vm_test
@pytest.mark.parametrize("fork", FORKS)
def test_pop(fork: Tuple[str, str]) -> None:
    VmTestLoader(*fork).run_test(POP_TEST_DIR, "pop0.json")


@pytest.mark.vm_test
@pytest.mark.parametrize("fork", FORKS)
def test_pop_fails_when_stack_underflowed(fork: Tuple[str, str]) -> None:
    VmTestLoader(*fork).run_test(POP_TEST_DIR, "pop1.json")
