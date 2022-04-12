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

fetch_spurious_dragon_tests = partial(fetch_state_test_files, network="EIP158")

FIXTURES_LOADER = Load("EIP158", "spurious_dragon")

run_spurious_dragon_blockchain_st_tests = partial(
    run_blockchain_st_test, load=FIXTURES_LOADER
)


# Run legacy general state tests
test_dir = (
    "tests/fixtures/LegacyTests/Constantinople/BlockchainTests/"
    "GeneralStateTests/"
)


@pytest.mark.parametrize(
    "test_case",
    fetch_spurious_dragon_tests(test_dir),
    ids=idfn,
)
def test_general_state_tests(test_case: Dict) -> None:
    try:
        run_spurious_dragon_blockchain_st_tests(test_case)
    except KeyError:
        # FIXME: Handle tests that don't have post state
        pytest.xfail(f"{test_case} doesn't have post state")


# Run legacy valid block tests
test_dir = (
    "tests/fixtures/LegacyTests/Constantinople/BlockchainTests/ValidBlocks/"
)

custom_file_list = (
    "bcUncleTest/oneUncle.json",
    "bcUncleTest/oneUncleGeneration2.json",
    "bcUncleTest/oneUncleGeneration3.json",
    "bcUncleTest/oneUncleGeneration4.json",
    "bcUncleTest/oneUncleGeneration5.json",
    "bcUncleTest/oneUncleGeneration6.json",
    "bcUncleTest/twoUncle.json",
    "bcUncleTest/uncleHeaderAtBlock2.json",
    "bcUncleSpecialTests/uncleBloomNot0.json",
    "bcUncleSpecialTests/futureUncleTimestampDifficultyDrop.json",
)


@pytest.mark.parametrize(
    "test_case",
    fetch_spurious_dragon_tests(test_dir, custom_file_list=custom_file_list),
    ids=idfn,
)
def test_uncles_correctness(test_case: Dict) -> None:
    run_spurious_dragon_blockchain_st_tests(test_case)


# Run legacy invalid block tests
test_dir = (
    "tests/fixtures/LegacyTests/Constantinople/BlockchainTests/InvalidBlocks"
)

xfail_candidates = ("GasLimitHigherThan2p63m1_EIP158",)


@pytest.mark.parametrize(
    "test_case",
    fetch_spurious_dragon_tests(test_dir),
    ids=idfn,
)
def test_invalid_block_tests(test_case: Dict) -> None:
    try:
        # Ideally correct.json should not have been in the InvalidBlocks folder
        if test_case["test_key"] == "correct_EIP158":
            run_spurious_dragon_blockchain_st_tests(test_case)
        elif test_case["test_key"] in xfail_candidates:
            # Unclear where this failed requirement comes from
            pytest.xfail()
        else:
            with pytest.raises(InvalidBlock):
                run_spurious_dragon_blockchain_st_tests(test_case)
    except KeyError:
        # FIXME: Handle tests that don't have post state
        pytest.xfail(
            "{} doesn't have post state".format(test_case["test_key"])
        )


# Run Non-Legacy GeneralStateTests
test_dir = "tests/fixtures/BlockchainTests/GeneralStateTests/"

non_legacy_custom_file_list = (
    "stCreateTest/CREATE_HighNonce.json",
    "stCreateTest/CREATE_HighNonceMinus1.json",
)


@pytest.mark.parametrize(
    "test_case",
    fetch_spurious_dragon_tests(
        test_dir, custom_file_list=non_legacy_custom_file_list
    ),
    ids=idfn,
)
def test_general_state_tests_new(test_case: Dict) -> None:
    run_spurious_dragon_blockchain_st_tests(test_case)
