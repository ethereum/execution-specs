import os
from functools import partial

import pytest

from ..vm.vm_test_helpers import run_test

run_system_vm_test = partial(
    run_test,
    os.path.join(
        os.environ["ETHEREUM_TESTS"],
        "LegacyTests/Constantinople/VMTests/vmSystemOperations",
    ),
)

run_vm_test = partial(
    run_test,
    os.path.join(
        os.environ["ETHEREUM_TESTS"],
        "LegacyTests/Constantinople/VMTests/vmTests",
    ),
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
