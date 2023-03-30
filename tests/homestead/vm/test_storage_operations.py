from functools import partial

import pytest

from tests.helpers import TEST_FIXTURES

from ..vm.vm_test_helpers import run_test

ETHEREUM_TESTS_PATH = TEST_FIXTURES["ethereum_tests"]["fixture_path"]

run_storage_vm_test = partial(
    run_test,
    f"{ETHEREUM_TESTS_PATH}/LegacyTests/Constantinople/VMTests/vmIOandFlowOperations",
)


@pytest.mark.parametrize(
    "test_file",
    [
        "sstore_load_0.json",
        "sstore_load_1.json",
        "sstore_load_2.json",
        "sstore_underflow.json",
        "kv1.json",
    ],
)
def test_sstore_and_sload(test_file: str) -> None:
    run_storage_vm_test(test_file)
