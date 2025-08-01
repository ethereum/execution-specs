from typing import Tuple

import pytest

from .. import TEST_FIXTURES
from ..helpers.load_vm_tests import VmTestLoader
from . import forks_to_test

ETHEREUM_TESTS_PATH = TEST_FIXTURES["ethereum_tests"]["fixture_path"]
TEST_DIR = f"{ETHEREUM_TESTS_PATH}/LegacyTests/Constantinople/VMTests/vmEnvironmentalInfo"


@pytest.mark.parametrize("fork", forks_to_test)
@pytest.mark.parametrize(
    "test_file",
    [
        "address0.json",
        "address1.json",
    ],
)
def test_address(fork: Tuple[str, str], test_file: str) -> None:
    VmTestLoader(*fork).run_test(TEST_DIR, test_file)


@pytest.mark.parametrize("fork", forks_to_test)
def test_origin(fork: Tuple[str, str]) -> None:
    VmTestLoader(*fork).run_test(TEST_DIR, "origin.json")


@pytest.mark.parametrize("fork", forks_to_test)
def test_caller(fork: Tuple[str, str]) -> None:
    VmTestLoader(*fork).run_test(TEST_DIR, "caller.json")


@pytest.mark.parametrize("fork", forks_to_test)
def test_callvalue(fork: Tuple[str, str]) -> None:
    VmTestLoader(*fork).run_test(TEST_DIR, "callvalue.json")


@pytest.mark.parametrize("fork", forks_to_test)
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
def test_calldataload(fork: Tuple[str, str], test_file: str) -> None:
    VmTestLoader(*fork).run_test(TEST_DIR, test_file)


@pytest.mark.parametrize("fork", forks_to_test)
@pytest.mark.parametrize(
    "test_file",
    [
        "calldatasize0.json",
        "calldatasize1.json",
        "calldatasize2.json",
    ],
)
def test_calldatasize(fork: Tuple[str, str], test_file: str) -> None:
    VmTestLoader(*fork).run_test(TEST_DIR, test_file)


@pytest.mark.parametrize("fork", forks_to_test)
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
def test_calldatacopy(fork: Tuple[str, str], test_file: str) -> None:
    VmTestLoader(*fork).run_test(TEST_DIR, test_file)


@pytest.mark.parametrize("fork", forks_to_test)
def test_codesize(fork: Tuple[str, str]) -> None:
    VmTestLoader(*fork).run_test(TEST_DIR, "codesize.json")


@pytest.mark.parametrize("fork", forks_to_test)
@pytest.mark.parametrize(
    "test_file",
    [
        "codecopy0.json",
        "codecopyZeroMemExpansion.json",
        "codecopy_DataIndexTooHigh.json",
    ],
)
def test_codecopy(fork: Tuple[str, str], test_file: str) -> None:
    VmTestLoader(*fork).run_test(TEST_DIR, test_file)


@pytest.mark.parametrize("fork", forks_to_test)
def test_gasprice(fork: Tuple[str, str]) -> None:
    VmTestLoader(*fork).run_test(TEST_DIR, "gasprice.json")
