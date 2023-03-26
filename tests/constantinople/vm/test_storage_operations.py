import os
from functools import partial

import pytest

from ..vm.vm_test_helpers import run_test

run_storage_vm_test = partial(
    run_test,
    os.path.join(
        os.environ["ETHEREUM_TESTS"],
        "LegacyTests/Constantinople/VMTests/vmIOandFlowOperations",
    ),
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
