from functools import partial

import pytest

from tests.frontier.vm.vm_test_helpers import run_test

run_environmental_vm_test = partial(
    run_test,
    "tests/fixtures/LegacyTests/Constantinople/VMTests/vmEnvironmentalInfo",
)


@pytest.mark.parametrize(
    "test_file",
    [
        "address0.json",
        "address1.json",
    ],
)
def test_address(test_file: str) -> None:
    run_environmental_vm_test(test_file)


def test_origin() -> None:
    run_environmental_vm_test("origin.json")


def test_caller() -> None:
    run_environmental_vm_test("caller.json")


def test_callvalue() -> None:
    run_environmental_vm_test("callvalue.json")


@pytest.mark.parametrize(
    "test_file",
    [
        "calldataload0.json",
        "calldataload1.json",
        "calldataload2.json",
        "calldataload_BigOffset.json",
        "calldataloadSizeTooHigh.json",
        "calldataloadSizeTooHighPartial.json",
    ],
)
def test_calldataload(test_file: str) -> None:
    run_environmental_vm_test(test_file)


@pytest.mark.parametrize(
    "test_file",
    [
        "calldatasize0.json",
        "calldatasize1.json",
        "calldatasize2.json",
    ],
)
def test_calldatasize(test_file: str) -> None:
    run_environmental_vm_test(test_file)


@pytest.mark.parametrize(
    "test_file",
    [
        "calldatacopy0.json",
        "calldatacopy1.json",
        "calldatacopy2.json",
        "calldatacopyZeroMemExpansion.json",
        "calldatacopy_DataIndexTooHigh.json",
        "calldatacopy_DataIndexTooHigh2.json",
        "calldatacopy_sec.json",
        "calldatacopyUnderFlow.json",
        "calldatacopy0_return.json",
        "calldatacopy1_return.json",
        "calldatacopy2_return.json",
        "calldatacopyZeroMemExpansion_return.json",
        "calldatacopy_DataIndexTooHigh_return.json",
        "calldatacopy_DataIndexTooHigh2_return.json",
    ],
)
def test_calldatacopy(test_file: str) -> None:
    run_environmental_vm_test(test_file)


def test_codesize() -> None:
    run_environmental_vm_test("codesize.json")


@pytest.mark.parametrize(
    "test_file",
    [
        "codecopy0.json",
        "codecopyZeroMemExpansion.json",
        "codecopy_DataIndexTooHigh.json",
    ],
)
def test_codecopy(test_file: str) -> None:
    run_environmental_vm_test(test_file)


def test_gasprice() -> None:
    run_environmental_vm_test("gasprice.json")
