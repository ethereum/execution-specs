from functools import partial

import pytest

from tests.helpers import TEST_FIXTURES

from ..vm.vm_test_helpers import run_test

ETHEREUM_TESTS_PATH = TEST_FIXTURES["ethereum_tests"]["fixture_path"]

run_memory_vm_test = partial(
    run_test,
    f"{ETHEREUM_TESTS_PATH}/LegacyTests/Constantinople/VMTests/vmIOandFlowOperations/",
)


@pytest.mark.parametrize(
    "test_file",
    [
        "mstore0.json",
        "mstore1.json",
        "mstoreMemExp.json",
    ],
)
def test_mstore(test_file: str) -> None:
    run_memory_vm_test(test_file)


@pytest.mark.parametrize(
    "test_file",
    [
        "mstore8_0.json",
        "mstore8_1.json",
        "mstore8WordToBigError.json",
        "mstore8MemExp.json",
    ],
)
def test_mstore8(test_file: str) -> None:
    run_memory_vm_test(test_file)


@pytest.mark.parametrize(
    "test_file",
    [
        "mloadError0.json",
        "mloadError1.json",
        "mstore_mload0.json",
        "mloadOutOfGasError2.json",
    ],
)
def test_mload(test_file: str) -> None:
    run_memory_vm_test(test_file)


@pytest.mark.parametrize(
    "test_file",
    [
        "mstore_mload0.json",
    ],
)
def test_mstore_mload(test_file: str) -> None:
    run_memory_vm_test(test_file)


@pytest.mark.parametrize(
    "test_file",
    [
        "msize0.json",
        "msize1.json",
        "msize2.json",
        "msize3.json",
    ],
)
def test_msize(test_file: str) -> None:
    run_memory_vm_test(test_file)
