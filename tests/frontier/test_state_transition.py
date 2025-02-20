from functools import partial
from typing import Dict

import pytest

from tests.helpers import EEST_TESTS_PATH, ETHEREUM_TESTS_PATH
from tests.helpers.load_state_tests import (
    Load,
    fetch_state_test_files,
    idfn,
    run_blockchain_st_test,
)

ETHEREUM_BLOCKCHAIN_TESTS_DIR = (
    f"{ETHEREUM_TESTS_PATH}/LegacyTests/Constantinople/BlockchainTests/"
)
EEST_BLOCKCHAIN_TESTS_DIR = f"{EEST_TESTS_PATH}/blockchain_tests/"
NETWORK = "Frontier"
PACKAGE = "frontier"

LEGACY_IGNORE_LIST = (
    # Valid block tests to be ignored
    "bcForkStressTest/ForkStressTest.json",
    "bcGasPricerTest/RPC_API_Test.json",
    "bcMultiChainTest/",
    "bcTotalDifficultyTest/",
    "stTimeConsuming/",
    # Invalid block tests to be ignored
    "bcForgedTest",
    "bcMultiChainTest",
    # TODO: See https://github.com/ethereum/tests/issues/1218
    "GasLimitHigherThan2p63m1_Frontier",
)

LEGACY_BIG_MEMORY_TESTS = (
    "/stQuadraticComplexityTest/",
    "/stRandom2/",
    "/stRandom/",
    "/stSpecialTest/",
)

SLOW_LIST = (
    # InvalidBlockTest
    "bcUncleHeaderValidity/nonceWrong.json",
    "bcUncleHeaderValidity/wrongMixHash.json",
)

# Define Tests
fetch_tests = partial(
    fetch_state_test_files,
    network=NETWORK,
    ignore_list=LEGACY_IGNORE_LIST,
    slow_list=SLOW_LIST,
    big_memory_list=LEGACY_BIG_MEMORY_TESTS,
)

FIXTURES_LOADER = Load(NETWORK, PACKAGE)

run_tests = partial(run_blockchain_st_test, load=FIXTURES_LOADER)


# Run tests from ethereum/tests
@pytest.mark.parametrize(
    "test_case",
    fetch_tests(ETHEREUM_BLOCKCHAIN_TESTS_DIR),
    ids=idfn,
)
def test_ethereum_tests(test_case: Dict) -> None:
    run_tests(test_case)


# Run EEST test fixtures
@pytest.mark.parametrize(
    "test_case",
    fetch_tests(EEST_BLOCKCHAIN_TESTS_DIR),
    ids=idfn,
)
def test_eest_tests(test_case: Dict) -> None:
    run_tests(test_case)
