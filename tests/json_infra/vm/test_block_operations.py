from typing import Tuple

import pytest

from .. import TEST_FIXTURES
from ..helpers.load_vm_tests import VmTestLoader
from . import forks_to_test

ETHEREUM_TESTS_PATH = TEST_FIXTURES["ethereum_tests"]["fixture_path"]
TEST_DIR = (
    f"{ETHEREUM_TESTS_PATH}/LegacyTests/Constantinople/VMTests/vmBlockInfoTest"
)


@pytest.mark.parametrize("fork", forks_to_test)
def test_coinbase(fork: Tuple[str, str]) -> None:
    VmTestLoader(*fork).run_test(TEST_DIR, "coinbase.json")


@pytest.mark.parametrize("fork", forks_to_test)
def test_timestamp(fork: Tuple[str, str]) -> None:
    VmTestLoader(*fork).run_test(TEST_DIR, "timestamp.json")


@pytest.mark.parametrize("fork", forks_to_test)
def test_number(fork: Tuple[str, str]) -> None:
    VmTestLoader(*fork).run_test(TEST_DIR, "number.json")


@pytest.mark.parametrize("fork", forks_to_test)
def test_difficulty(fork: Tuple[str, str]) -> None:
    VmTestLoader(*fork).run_test(TEST_DIR, "difficulty.json")


@pytest.mark.parametrize("fork", forks_to_test)
def test_gas_limit(fork: Tuple[str, str]) -> None:
    VmTestLoader(*fork).run_test(TEST_DIR, "gaslimit.json")
