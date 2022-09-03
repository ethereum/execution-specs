from functools import partial
from typing import Dict

import pytest

from ethereum.exceptions import InvalidBlock
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


# Run legacy general state tests
test_dir = (
    "tests/fixtures/LegacyTests/Constantinople/BlockchainTests/"
    "GeneralStateTests/"
)


@pytest.mark.parametrize(
    "test_case",
    fetch_frontier_tests(test_dir),
    ids=idfn,
)
def test_general_state_tests(test_case: Dict) -> None:
    try:
        run_frontier_blockchain_st_tests(test_case)
    except KeyError:
        # FIXME: Handle tests that don't have post state
        pytest.xfail(f"{test_case} doesn't have post state")


# Run legacy valid block tests
test_dir = (
    "tests/fixtures/LegacyTests/Constantinople/BlockchainTests/ValidBlocks/"
)

only_in_incorrect = (
    "bcForkStressTest/ForkStressTest.json",
    "bcGasPricerTest/RPC_API_Test.json",
    "bcMultiChainTest/CallContractFromNotBestBlock.json",
    "bcMultiChainTest/ChainAtoChainB_BlockHash.json",
    "bcMultiChainTest/ChainAtoChainB_difficultyB.json",
    "bcMultiChainTest/ChainAtoChainB.json",
    "bcMultiChainTest/ChainAtoChainBCallContractFormA.json",
    "bcMultiChainTest/ChainAtoChainBtoChainA.json",
    "bcMultiChainTest/ChainAtoChainBtoChainAtoChainB.json",
    "bcTotalDifficultyTest/lotsOfBranchesOverrideAtTheEnd.json",
    "bcTotalDifficultyTest/lotsOfBranchesOverrideAtTheMiddle.json",
    "bcTotalDifficultyTest/lotsOfLeafs.json",
    "bcTotalDifficultyTest/newChainFrom4Block.json",
    "bcTotalDifficultyTest/newChainFrom5Block.json",
    "bcTotalDifficultyTest/newChainFrom6Block.json",
    "bcTotalDifficultyTest/sideChainWithMoreTransactions.json",
    "bcTotalDifficultyTest/sideChainWithMoreTransactions2.json",
    "bcTotalDifficultyTest/sideChainWithNewMaxDifficultyStartingFromBlock3AfterBlock4.json",
    "bcTotalDifficultyTest/uncleBlockAtBlock3AfterBlock3.json",
    "bcTotalDifficultyTest/uncleBlockAtBlock3afterBlock4.json",
)

# Every test below takes more than  60s to run and
# hence they've been marked as slow
SLOW_TESTS = (
    "bcForkStressTest/ForkStressTest.json",
    "bcGasPricerTest/RPC_API_Test.json",
    "bcTotalDifficultyTest/newChainFrom4Block.json",
    "bcTotalDifficultyTest/newChainFrom5Block.json",
    "bcTotalDifficultyTest/newChainFrom6Block.json",
    "bcTotalDifficultyTest/uncleBlockAtBlock3afterBlock4.json",
)


@pytest.mark.parametrize(
    "test_case",
    fetch_frontier_tests(
        test_dir,
        only_in=only_in_incorrect,
        slow_list=SLOW_TESTS,
    ),
    ids=idfn,
)
def test_valid_block_incorrect(test_case: Dict) -> None:
    with pytest.raises(InvalidBlock):
        run_frontier_blockchain_st_tests(test_case)


@pytest.mark.parametrize(
    "test_case",
    fetch_frontier_tests(
        test_dir,
        ignore_list=only_in_incorrect,
    ),
    ids=idfn,
)
def test_valid_block_correct(test_case: Dict) -> None:
    try:
        run_frontier_blockchain_st_tests(test_case)
    except KeyError:
        # FIXME: Handle tests that don't have post state
        pytest.xfail(f"{test_case} doesn't have post state")


# Run legacy invalid block tests
test_dir = (
    "tests/fixtures/LegacyTests/Constantinople/BlockchainTests/InvalidBlocks"
)

xfail_candidates = ("GasLimitHigherThan2p63m1_Frontier",)


@pytest.mark.parametrize(
    "test_case",
    fetch_frontier_tests(test_dir),
    ids=idfn,
)
def test_invalid_block_tests(test_case: Dict) -> None:
    try:
        # Ideally correct.json should not have been in the InvalidBlocks folder
        if test_case["test_key"] == "correct_Frontier":
            run_frontier_blockchain_st_tests(test_case)
        elif test_case["test_key"] in xfail_candidates:
            # Unclear where this failed requirement comes from
            pytest.xfail()
        else:
            with pytest.raises(InvalidBlock):
                run_frontier_blockchain_st_tests(test_case)
    except KeyError:
        # FIXME: Handle tests that don't have post state
        pytest.xfail(
            "{} doesn't have post state".format(test_case["test_key"])
        )


# Run Non-Legacy GeneralStateTests
test_dir = "tests/fixtures/BlockchainTests/GeneralStateTests/"

non_legacy_only_in = (
    "stCreateTest/CREATE_HighNonce.json",
    "stCreateTest/CREATE_HighNonceMinus1.json",
)


@pytest.mark.parametrize(
    "test_case",
    fetch_frontier_tests(test_dir, only_in=non_legacy_only_in),
    ids=idfn,
)
def test_general_state_tests_new(test_case: Dict) -> None:
    run_frontier_blockchain_st_tests(test_case)
