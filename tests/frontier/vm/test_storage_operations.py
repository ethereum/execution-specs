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
