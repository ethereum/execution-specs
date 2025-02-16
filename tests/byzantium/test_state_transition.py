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

fetch_byzantium_tests = partial(fetch_state_test_files, network="Byzantium")

FIXTURES_LOADER = Load("Byzantium", "byzantium")

run_byzantium_blockchain_st_tests = partial(
    run_blockchain_st_test, load=FIXTURES_LOADER
)

ETHEREUM_TESTS_PATH = TEST_FIXTURES["ethereum_tests"]["fixture_path"]

# Run legacy state tests
test_dir = f"{ETHEREUM_TESTS_PATH}/LegacyTests/Constantinople/BlockchainTests/"

# These are tests that are considered to be incorrect,
# Please provide an explanation when adding entries
LEGACY_IGNORE_LIST = (
    # ValidBlockTests
    "bcForkStressTest/ForkStressTest.json",
    "bcGasPricerTest/RPC_API_Test.json",
    "bcMultiChainTest",
    "bcTotalDifficultyTest",
    # InvalidBlockTests
    "bcForgedTest",
    "bcMultiChainTest",
    "GasLimitHigherThan2p63m1_Byzantium",
)

# All tests that recursively create a large number of frames (50000)
LEGACY_BIG_MEMORY_TESTS = (
    # GeneralStateTests
    "50000_",
    "/stQuadraticComplexityTest/",
    "/stRandom2/",
    "/stRandom/",
    "/stSpecialTest/",
    "stTimeConsuming/",
    # ValidBlockTests
    "randomStatetest94_",
)

LEGACY_SLOW_TESTS = (
    # GeneralStateTests
    "stRandom/randomStatetest177.json",
    "stCreateTest/CreateOOGafterMaxCodesize.json",
    # ValidBlockTest
    "bcExploitTest/DelegateCallSpam.json",
    # InvalidBlockTest
    "bcUncleHeaderValidity/nonceWrong.json",
    "bcUncleHeaderValidity/wrongMixHash.json",
)

fetch_legacy_state_tests = partial(
    fetch_byzantium_tests,
    test_dir,
    ignore_list=LEGACY_IGNORE_LIST,
    slow_list=LEGACY_SLOW_TESTS,
    big_memory_list=LEGACY_BIG_MEMORY_TESTS,
)


@pytest.mark.parametrize(
    "test_case",
    fetch_legacy_state_tests(),
    ids=idfn,
)
def test_legacy_state_tests(test_case: Dict) -> None:
    run_byzantium_blockchain_st_tests(test_case)


# Run Non-Legacy StateTests
test_dir = f"{ETHEREUM_TESTS_PATH}/BlockchainTests/GeneralStateTests/"

non_legacy_only_in = (
    "stCreateTest/CREATE_HighNonce.json",
    "stCreateTest/CREATE_HighNonceMinus1.json",
)


@pytest.mark.parametrize(
    "test_case",
    fetch_byzantium_tests(test_dir, only_in=non_legacy_only_in),
    ids=idfn,
)
def test_non_legacy_state_tests(test_case: Dict) -> None:
    run_byzantium_blockchain_st_tests(test_case)
