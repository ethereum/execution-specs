from functools import partial
from typing import Dict

import pytest

from tests.helpers import TEST_FIXTURES
from tests.helpers.load_state_tests import (
    Load,
    fetch_state_test_files,
    idfn,
    run_blockchain_st_test,
)

fetch_frontier_tests = partial(fetch_state_test_files, network="Frontier")

FIXTURES_LOADER = Load("Frontier", "frontier")

run_frontier_blockchain_st_tests = partial(
    run_blockchain_st_test, load=FIXTURES_LOADER
)

ETHEREUM_TESTS_PATH = TEST_FIXTURES["ethereum_tests"]["fixture_path"]


# Run legacy general state tests
legacy_test_dir = (
    f"{ETHEREUM_TESTS_PATH}/LegacyTests/Constantinople/BlockchainTests/"
)

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

fetch_legacy_state_tests = partial(
    fetch_frontier_tests,
    legacy_test_dir,
    ignore_list=LEGACY_IGNORE_LIST,
    slow_list=SLOW_LIST,
    big_memory_list=LEGACY_BIG_MEMORY_TESTS,
)


@pytest.mark.parametrize(
    "test_case",
    fetch_legacy_state_tests(),
    ids=idfn,
)
def test_legacy_state_tests(test_case: Dict) -> None:
    run_frontier_blockchain_st_tests(test_case)


# Run Non-Legacy Tests
non_legacy_test_dir = (
    f"{ETHEREUM_TESTS_PATH}/BlockchainTests/GeneralStateTests/"
)

non_legacy_only_in = (
    "stCreateTest/CREATE_HighNonce.json",
    "stCreateTest/CREATE_HighNonceMinus1.json",
)


@pytest.mark.parametrize(
    "test_case",
    fetch_frontier_tests(non_legacy_test_dir, only_in=non_legacy_only_in),
    ids=idfn,
)
def test_non_legacy_tests(test_case: Dict) -> None:
    run_frontier_blockchain_st_tests(test_case)
