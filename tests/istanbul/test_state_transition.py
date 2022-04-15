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

fetch_istanbul_tests = partial(fetch_state_test_files, network="Istanbul")

FIXTURES_LOADER = Load("Istanbul", "istanbul")

run_istanbul_blockchain_st_tests = partial(
    run_blockchain_st_test, load=FIXTURES_LOADER
)

# Run legacy general state tests
test_dir = "tests/fixtures/BlockchainTests/GeneralStateTests/"

# Every test below takes more than  60s to run and
# hence they've been marked as slow
SLOW_TESTS = (
    "stTimeConsuming/CALLBlake2f_MaxRounds.json",
    "stTimeConsuming/static_Call50000_sha256.json",
    "vmPerformance/loopExp.json",
    "vmPerformance/loopMul.json",
    "QuadraticComplexitySolidity_CallDataCopy_d0g1v0_Istanbul",
    "CALLBlake2f_d9g0v0_Istanbul",
    "CALLCODEBlake2f_d9g0v0",
)

# These are tests that are considered to be incorrect,
# Please provide an explanation when adding entries
INCORRECT_UPSTREAM_STATE_TESTS = (
    # The test considers a scenario that cannot be reached by following the
    # rules of consensus. For more details, read:
    # https://github.com/ethereum/py-evm/pull/1224#issuecomment-418775512
    "stRevertTest/RevertInCreateInInit.json",
    # The test considers a scenario that cannot be reached by following the
    # rules of consensus.
    "stCreate2/RevertInCreateInInitCreate2.json",
    # The test considers a scenario that cannot be reached by following the
    # rules of consensus.
    "stSStoreTest/InitCollision.json",
    "chainId_d0g0v0_Istanbul",  # TODO: remove after EIP-1344
    "chainIdGasCost_d0g0v0_Istanbul",  # TODO: remove after EIP-1344
    "badOpcodes_d21g0v0_Istanbul",  # TODO: remove after EIP-1344
)


@pytest.mark.parametrize(
    "test_case",
    fetch_istanbul_tests(
        test_dir,
        ignore_list=INCORRECT_UPSTREAM_STATE_TESTS,
        slow_list=SLOW_TESTS,
    ),
    ids=idfn,
)
def test_general_state_tests(test_case: Dict) -> None:
    try:
        run_istanbul_blockchain_st_tests(test_case)
    except KeyError:
        # FIXME: Handle tests that don't have post state
        pytest.xfail(f"{test_case} doesn't have post state")


# Run legacy valid block tests
test_dir = "tests/fixtures/BlockchainTests/ValidBlocks/"

only_in = (
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
    fetch_istanbul_tests(test_dir, only_in=only_in),
    ids=idfn,
)
def test_uncles_correctness(test_case: Dict) -> None:
    run_istanbul_blockchain_st_tests(test_case)


# Run legacy invalid block tests
test_dir = "tests/fixtures/BlockchainTests/InvalidBlocks"

# TODO: Investigate why some of the below tests pass
# All except GasLimitHigherThan2p63m1_Istanbul
xfail_candidates = (
    "timestampTooLow_Istanbul",
    "timestampTooHigh_Istanbul",
    "wrongStateRoot_Istanbul",
    "incorrectUncleTimestamp4_Istanbul",
    "incorrectUncleTimestamp5_Istanbul",
    "futureUncleTimestamp3_Istanbul",
    "GasLimitHigherThan2p63m1_Istanbul",
)


@pytest.mark.parametrize(
    "test_case",
    fetch_istanbul_tests(test_dir),
    ids=idfn,
)
def test_invalid_block_tests(test_case: Dict) -> None:
    try:
        # Ideally correct.json should not have been in the InvalidBlocks folder
        if test_case["test_key"] == "correct_Istanbul":
            run_istanbul_blockchain_st_tests(test_case)
        elif test_case["test_key"] in xfail_candidates:
            # Unclear where this failed requirement comes from
            pytest.xfail()
        else:
            with pytest.raises(InvalidBlock):
                run_istanbul_blockchain_st_tests(test_case)
    except KeyError:
        # FIXME: Handle tests that don't have post state
        pytest.xfail(
            "{} doesn't have post state".format(test_case["test_key"])
        )
