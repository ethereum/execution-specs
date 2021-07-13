from functools import partial

import pytest

from ethereum.frontier.vm.error import OutOfGasError
from tests.frontier.vm.vm_test_helpers import run_test

run_memory_vm_test = partial(
    run_test,
    "tests/fixtures/LegacyTests/Constantinople/VMTests/vmIOandFlowOperations",
)


# TODO: Investigate what is erroneous about these test cases.
@pytest.mark.parametrize(
    "test_file",
    [
        "mloadError0.json",
        "mloadError1.json",
    ],
)
def test_mload(test_file: str) -> None:
    run_memory_vm_test(test_file)


# TODO: Investigate why mloadMemExp.json is not suffixed with Error
@pytest.mark.parametrize(
    "test_file",
    [
        "mloadMemExp.json",
        "mloadOutOfGasError2.json",
    ],
)
def test_mload_out_of_gas_error(test_file: str) -> None:
    with pytest.raises(OutOfGasError):
        run_memory_vm_test(test_file)


@pytest.mark.parametrize(
    "test_file",
    [
        "mstore0.json",
        "mstore1.json",
        # TODO: Investigate why below test is suffixed with Error
        "mstoreWordToBigError.json",
    ],
)
def test_mstore(test_file: str) -> None:
    run_memory_vm_test(test_file)


def test_mstore_out_of_gas_error() -> None:
    with pytest.raises(OutOfGasError):
        run_memory_vm_test("mstoreMemExp.json")


@pytest.mark.parametrize(
    "test_file",
    [
        "mstore8_0.json",
        "mstore8_1.json",
        # TODO: Investigate why below test is suffixed with Error
        "mstore8WordToBigError.json",
    ],
)
def test_mstore8(test_file: str) -> None:
    run_memory_vm_test(test_file)


def test_mstore8_out_of_gas_error() -> None:
    with pytest.raises(OutOfGasError):
        run_memory_vm_test("mstore8MemExp.json")


def test_mstore_mload() -> None:
    run_memory_vm_test("mstore_mload0.json")


# TODO: Run below test once "RETURN" opcode has been implemented.
# def test_generic_memory_operations() -> None:
#     run_memory_vm_test("memory1.json")


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
