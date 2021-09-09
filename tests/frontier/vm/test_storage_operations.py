from functools import partial

import pytest

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
        "sstore_underflow.json"
        # TODO: Run below test once RETURN opcode has been implemented.
        # "kv1.json",
    ],
)
def test_sstore_and_sload(test_file: str) -> None:
    run_storage_vm_test(test_file)
