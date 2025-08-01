from typing import Tuple

import pytest

from .. import TEST_FIXTURES
from ..helpers.load_vm_tests import VmTestLoader
from . import forks_to_test

ETHEREUM_TESTS_PATH = TEST_FIXTURES["ethereum_tests"]["fixture_path"]
TEST_DIR = (
    f"{ETHEREUM_TESTS_PATH}/LegacyTests/Constantinople/VMTests/vmSha3Test"
)
SPECIAL_TEST_DIR = f"{ETHEREUM_TESTS_PATH}/LegacyTests/Constantinople/VMTests/vmIOandFlowOperations"


@pytest.mark.parametrize("fork", forks_to_test)
@pytest.mark.parametrize(
    "test_file",
    [
        "sha3_0.json",
        "sha3_1.json",
        "sha3_2.json",
        "sha3_bigOffset2.json",
        "sha3_memSizeNoQuadraticCost31.json",
        "sha3_memSizeQuadraticCost32.json",
        "sha3_memSizeQuadraticCost32_zeroSize.json",
        "sha3_memSizeQuadraticCost33.json",
        "sha3_memSizeQuadraticCost63.json",
        "sha3_memSizeQuadraticCost64.json",
        "sha3_memSizeQuadraticCost64_2.json",
        "sha3_memSizeQuadraticCost65.json",
        "sha3_3.json",
        "sha3_4.json",
        "sha3_5.json",
        "sha3_6.json",
        "sha3_bigOffset.json",
        "sha3_bigSize.json",
    ],
)
def test_sha3_succeeds(fork: Tuple[str, str], test_file: str) -> None:
    VmTestLoader(*fork).run_test(TEST_DIR, test_file)


@pytest.mark.parametrize("fork", forks_to_test)
def test_sha3_fails_out_of_gas_memory_expansion(fork: Tuple[str, str]) -> None:
    VmTestLoader(*fork).run_test(SPECIAL_TEST_DIR, "sha3MemExp.json")
