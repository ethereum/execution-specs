from typing import Tuple

import pytest

from .. import TEST_FIXTURES
from ..helpers.load_vm_tests import VmTestLoader
from . import forks_to_test

ETHEREUM_TESTS_PATH = TEST_FIXTURES["ethereum_tests"]["fixture_path"]
TEST_DIR = f"{ETHEREUM_TESTS_PATH}/LegacyTests/Constantinople/VMTests/vmSystemOperations"
VM_TEST_DIR = (
    f"{ETHEREUM_TESTS_PATH}/LegacyTests/Constantinople/VMTests/vmTests"
)


@pytest.mark.parametrize("fork", forks_to_test)
@pytest.mark.parametrize(
    "test_file, check_gas_left",
    [
        ("suicide0.json", False),
        ("suicideNotExistingAccount.json", False),
        ("suicideSendEtherToMe.json", False),
    ],
)
def test_seldestruct(
    fork: Tuple[str, str], test_file: str, check_gas_left: bool
) -> None:
    VmTestLoader(*fork).run_test(
        TEST_DIR, test_file, check_gas_left=check_gas_left
    )


@pytest.mark.parametrize("fork", forks_to_test)
def test_seldestruct_vm_test(fork: Tuple[str, str]) -> None:
    VmTestLoader(*fork).run_test(
        VM_TEST_DIR, "suicide.json", check_gas_left=False
    )


@pytest.mark.parametrize("fork", forks_to_test)
@pytest.mark.parametrize(
    "test_file",
    [
        "return0.json",
        "return1.json",
        "return2.json",
    ],
)
def test_return(fork: Tuple[str, str], test_file: str) -> None:
    VmTestLoader(*fork).run_test(TEST_DIR, test_file)
