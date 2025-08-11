from typing import Tuple

import pytest

from .. import TEST_FIXTURES
from ..helpers.load_vm_tests import VmTestLoader
from . import FORKS

ETHEREUM_TESTS_PATH = TEST_FIXTURES["ethereum_tests"]["fixture_path"]
TEST_DIR = f"{ETHEREUM_TESTS_PATH}/LegacyTests/Constantinople/VMTests/vmIOandFlowOperations"


@pytest.mark.vm_test
@pytest.mark.parametrize("fork", FORKS)
@pytest.mark.parametrize(
    "test_file",
    [
        "mstore0.json",
        "mstore1.json",
        "mstoreMemExp.json",
    ],
)
def test_mstore(fork: Tuple[str, str], test_file: str) -> None:
    VmTestLoader(*fork).run_test(TEST_DIR, test_file)


@pytest.mark.vm_test
@pytest.mark.parametrize("fork", FORKS)
@pytest.mark.parametrize(
    "test_file",
    [
        "mstore8_0.json",
        "mstore8_1.json",
        "mstore8WordToBigError.json",
        "mstore8MemExp.json",
    ],
)
def test_mstore8(fork: Tuple[str, str], test_file: str) -> None:
    VmTestLoader(*fork).run_test(TEST_DIR, test_file)


@pytest.mark.vm_test
@pytest.mark.parametrize("fork", FORKS)
@pytest.mark.parametrize(
    "test_file",
    [
        "mloadError0.json",
        "mloadError1.json",
        "mstore_mload0.json",
        "mloadOutOfGasError2.json",
    ],
)
def test_mload(fork: Tuple[str, str], test_file: str) -> None:
    VmTestLoader(*fork).run_test(TEST_DIR, test_file)


@pytest.mark.vm_test
@pytest.mark.parametrize("fork", FORKS)
@pytest.mark.parametrize(
    "test_file",
    [
        "mstore_mload0.json",
    ],
)
def test_mstore_mload(fork: Tuple[str, str], test_file: str) -> None:
    VmTestLoader(*fork).run_test(TEST_DIR, test_file)


@pytest.mark.vm_test
@pytest.mark.parametrize("fork", FORKS)
@pytest.mark.parametrize(
    "test_file",
    [
        "msize0.json",
        "msize1.json",
        "msize2.json",
        "msize3.json",
    ],
)
def test_msize(fork: Tuple[str, str], test_file: str) -> None:
    VmTestLoader(*fork).run_test(TEST_DIR, test_file)
