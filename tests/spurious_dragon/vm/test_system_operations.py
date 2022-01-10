from functools import partial

import pytest

from ..vm.vm_test_helpers import run_test

run_system_vm_test = partial(
    run_test,
    "tests/fixtures/LegacyTests/Constantinople/VMTests/vmSystemOperations",
)

run_vm_test = partial(
    run_test,
    "tests/fixtures/LegacyTests/Constantinople/VMTests/vmTests",
)


@pytest.mark.parametrize(
    "test_file, check_gas_left",
    [
        ("suicide0.json", False),
        ("suicideNotExistingAccount.json", False),
        ("suicideSendEtherToMe.json", False),
    ],
)
def test_seldestruct(test_file: str, check_gas_left: bool) -> None:
    run_system_vm_test(test_file, check_gas_left=check_gas_left)


def test_seldestruct_vm_test() -> None:
    run_vm_test("suicide.json", check_gas_left=False)


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
