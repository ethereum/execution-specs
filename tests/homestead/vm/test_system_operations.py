from functools import partial

import pytest

from tests.helpers import TEST_FIXTURES

from ..vm.vm_test_helpers import run_test

ETHEREUM_TESTS_PATH = TEST_FIXTURES["ethereum_tests"]["fixture_path"]

run_system_vm_test = partial(
    run_test,
    f"{ETHEREUM_TESTS_PATH}/LegacyTests/Constantinople/VMTests/vmSystemOperations",
)

run_vm_test = partial(
    run_test,
    f"{ETHEREUM_TESTS_PATH}/LegacyTests/Constantinople/VMTests/vmTests",
)


@pytest.mark.parametrize(
    "test_file",
    [
        "suicide0.json",
        "suicideNotExistingAccount.json",
        "suicideSendEtherToMe.json",
    ],
)
def test_seldestruct(test_file: str) -> None:
    run_system_vm_test(test_file)


def test_seldestruct_vm_test() -> None:
    run_vm_test("suicide.json")


@pytest.mark.parametrize(
    "test_file",
    [
        "return0.json",
        "return1.json",
        "return2.json",
    ],
)
def test_return(test_file: str) -> None:
    run_system_vm_test(test_file)
