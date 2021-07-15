from functools import partial

import pytest

from ethereum.frontier.vm.error import StackUnderflowError
from tests.frontier.vm.vm_test_helpers import run_test

run_storage_vm_test = partial(
    run_test,
    "tests/fixtures/LegacyTests/Constantinople/VMTests/vmIOandFlowOperations",
)


@pytest.mark.parametrize(
    "test_file",
    [
        "sstore_load_0.json",
        "sstore_load_1.json",
        "sstore_load_2.json",
    ],
)
def test_sstore_and_sload(test_file: str) -> None:
    run_storage_vm_test(test_file)


def test_sstore_underflows() -> None:
    with pytest.raises(StackUnderflowError):
        run_storage_vm_test("sstore_underflow.json")
