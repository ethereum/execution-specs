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

fetch_tangerine_whistle_tests = partial(
    fetch_state_test_files, network="EIP150"
)

FIXTURES_LOADER = Load("EIP150", "tangerine_whistle")

run_tangerine_whistle_blockchain_st_tests = partial(
    run_blockchain_st_test, load=FIXTURES_LOADER
)

ETHEREUM_TESTS_PATH = TEST_FIXTURES["ethereum_tests"]["fixture_path"]


# Run legacy state tests
test_dir = f"{ETHEREUM_TESTS_PATH}/LegacyTests/Constantinople/BlockchainTests/"

LEGACY_SLOW_TESTS = (
    "stRandom/randomStatetest177.json",
    "stCreateTest/CreateOOGafterMaxCodesize.json",
    # ValidBlockTest
    "bcExploitTest/DelegateCallSpam.json",
    # InvalidBlockTest
    "bcUncleHeaderValidity/nonceWrong.json",
    "bcUncleHeaderValidity/wrongMixHash.json",
)

LEGACY_BIG_MEMORY_TESTS = (
    # GeneralStateTests
    "/stQuadraticComplexityTest/",
    "/stRandom2/",
    "/stRandom/",
    "/stSpecialTest/",
    "stTimeConsuming/",
)

LEGACY_IGNORE_LIST = (
    # ValidBlockTests
    "bcForkStressTest/ForkStressTest.json",
    "bcGasPricerTest/RPC_API_Test.json",
    "bcMultiChainTest",
    "bcTotalDifficultyTest",
    # InvalidBlockTests
    "bcForgedTest",
    "bcMultiChainTest",
    "GasLimitHigherThan2p63m1_EIP150",
)

fetch_legacy_state_tests = partial(
    fetch_tangerine_whistle_tests,
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
    run_tangerine_whistle_blockchain_st_tests(test_case)


# Run Non-Legacy State Tests
test_dir = f"{ETHEREUM_TESTS_PATH}/BlockchainTests/GeneralStateTests/"

non_legacy_only_in = (
    "stCreateTest/CREATE_HighNonce.json",
    "stCreateTest/CREATE_HighNonceMinus1.json",
)


@pytest.mark.parametrize(
    "test_case",
    fetch_tangerine_whistle_tests(test_dir, only_in=non_legacy_only_in),
    ids=idfn,
)
def test_non_legacy_state_tests(test_case: Dict) -> None:
    run_tangerine_whistle_blockchain_st_tests(test_case)
