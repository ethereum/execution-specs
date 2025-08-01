from typing import Tuple

import pytest

from .. import TEST_FIXTURES
from ..helpers.load_vm_tests import VmTestLoader
from . import forks_to_test

ETHEREUM_TESTS_PATH = TEST_FIXTURES["ethereum_tests"]["fixture_path"]
TEST_DIR = f"{ETHEREUM_TESTS_PATH}/LegacyTests/Constantinople/VMTests/vmIOandFlowOperations"


@pytest.mark.parametrize("fork", forks_to_test)
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
def test_sstore_and_sload(
    fork: Tuple[str, str], test_file: str, check_gas_left: bool
) -> None:
    VmTestLoader(*fork).run_test(
        TEST_DIR, test_file, check_gas_left=check_gas_left
    )
