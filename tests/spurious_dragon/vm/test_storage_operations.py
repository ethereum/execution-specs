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
    "test_file, check_gas_left",
    [
        ("sstore_load_0.json", False),
        ("sstore_load_1.json", False),
        ("sstore_load_2.json", False),
        ("sstore_underflow.json", True),
        ("kv1.json", True),
    ],
)
def test_sstore_and_sload(test_file: str, check_gas_left: bool) -> None:
    run_storage_vm_test(test_file, check_gas_left=check_gas_left)
