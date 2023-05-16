from functools import partial
from typing import Dict, Tuple

import pytest

from ethereum import rlp
from ethereum.base_types import U256, Bytes, Bytes8, Bytes32, Uint
from ethereum.crypto.hash import Hash32
from ethereum.exceptions import InvalidBlock, RLPDecodingError
from tests.helpers import TEST_FIXTURES
from tests.helpers.load_state_tests import (
    Load,
    NoPostState,
    fetch_state_test_files,
    idfn,
    run_blockchain_st_test,
)

fetch_shanghai_tests = partial(fetch_state_test_files, network="Shanghai")

FIXTURES_LOADER = Load("Shanghai", "shanghai")

run_shanghai_blockchain_st_tests = partial(
    run_blockchain_st_test, load=FIXTURES_LOADER
)

ETHEREUM_TESTS_PATH = TEST_FIXTURES["ethereum_tests"]["fixture_path"]
ETHEREUM_SPEC_TESTS_PATH = TEST_FIXTURES["execution_spec_tests"][
    "fixture_path"
]


# Run general state tests
test_dir = f"{ETHEREUM_TESTS_PATH}/BlockchainTests/GeneralStateTests/"

SLOW_TESTS = (
    "stTimeConsuming/CALLBlake2f_MaxRounds.json",
    "stTimeConsuming/static_Call50000_sha256.json",
    "vmPerformance/loopExp.json",
    "vmPerformance/loopMul.json",
    "QuadraticComplexitySolidity_CallDataCopy_d0g1v0_Shanghai",
    "CALLBlake2f_d9g0v0_Shanghai",
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
)

# All tests that recursively create a large number of frames (50000)
GENERAL_STATE_BIG_MEMORY_TESTS = (
    "50000_",
    "/stQuadraticComplexityTest/",
    "/stRandom2/",
    "/stRandom/",
    "/stSpecialTest/",
    "stTimeConsuming/",
    "stBadOpcode/",
    "stStaticCall/",
)

fetch_general_state_tests = partial(
    fetch_shanghai_tests,
    test_dir,
    ignore_list=INCORRECT_UPSTREAM_STATE_TESTS,
    slow_list=SLOW_TESTS,
    big_memory_list=GENERAL_STATE_BIG_MEMORY_TESTS,
)


@pytest.mark.parametrize(
    "test_case",
    fetch_general_state_tests(),
    ids=idfn,
)
def test_general_state_tests(test_case: Dict) -> None:
    try:
        run_shanghai_blockchain_st_tests(test_case)
    except NoPostState:
        # FIXME: Handle tests that don't have post state
        pytest.xfail(f"{test_case} doesn't have post state")


# Run valid block tests
test_dir = f"{ETHEREUM_TESTS_PATH}/BlockchainTests/ValidBlocks/"

IGNORE_LIST = (
    "bcForkStressTest/ForkStressTest.json",
    "bcGasPricerTest/RPC_API_Test.json",
    "bcMultiChainTest",
    "bcTotalDifficultyTest",
)

# Every test below takes more than  60s to run and
# hence they've been marked as slow
VALID_BLOCKS_SLOW_TESTS = ("bcExploitTest/DelegateCallSpam.json",)


@pytest.mark.parametrize(
    "test_case",
    fetch_shanghai_tests(
        test_dir,
        ignore_list=IGNORE_LIST,
        slow_list=VALID_BLOCKS_SLOW_TESTS,
    ),
    ids=idfn,
)
def test_valid_block_tests(test_case: Dict) -> None:
    try:
        run_shanghai_blockchain_st_tests(test_case)
    except NoPostState:
        # FIXME: Handle tests that don't have post state
        pytest.xfail(f"{test_case} doesn't have post state")


# Run invalid block tests
test_dir = f"{ETHEREUM_TESTS_PATH}/BlockchainTests/InvalidBlocks"

# TODO: Detect tests that throw exceptions automatically
# See: https://github.com/ethereum/execution-specs/issues/760
valid_tests = (
    "amountIs0_Shanghai",
    "twoIdenticalIndex_Shanghai",
    "staticcall_Shanghai",
    "amountIs0TouchAccountAndTransaction_Shanghai",
    "differentValidatorToTheSameAddress_Shanghai",
    "twoIdenticalIndexDifferentValidator_Shanghai",
    "accountInteractions_Shanghai",
    "warmup_Shanghai",
    "amountIs0TouchAccount_Shanghai",
    "DifficultyIsZero_Shanghai",
)

# FIXME: Check if these tests should in fact be ignored
IGNORE_INVALID_BLOCK_TESTS = ("bcForgedTest", "bcMultiChainTest")


@pytest.mark.parametrize(
    "test_case",
    fetch_shanghai_tests(
        test_dir,
        ignore_list=IGNORE_INVALID_BLOCK_TESTS,
    ),
    ids=idfn,
)
def test_invalid_block_tests(test_case: Dict) -> None:
    try:
        # Ideally correct.json should not have been in the InvalidBlocks folder
        if test_case["test_key"] in valid_tests:
            run_shanghai_blockchain_st_tests(test_case)
        elif test_case["test_key"] == "GasLimitHigherThan2p63m1_Shanghai":
            # TODO: Unclear where this failed requirement comes from
            # See: https://github.com/ethereum/tests/issues/1218
            pytest.xfail()
        else:
            with pytest.raises(InvalidBlock):
                run_shanghai_blockchain_st_tests(test_case)
    except NoPostState:
        # FIXME: Handle tests that don't have post state
        pytest.xfail(
            "{} doesn't have post state".format(test_case["test_key"])
        )


# Run execution-spec-generated-tests
test_dir = f"{ETHEREUM_SPEC_TESTS_PATH}/fixtures/withdrawals"


@pytest.mark.parametrize(
    "test_case",
    fetch_shanghai_tests(test_dir),
    ids=idfn,
)
def test_execution_specs_generated_tests(test_case: Dict) -> None:
    try:
        # TODO: Detect this automatically
        # See: https://github.com/ethereum/execution-specs/issues/760
        if (
            "use_value_in_tx" in test_case["test_file"]
            and test_case["test_key"] == "000/shanghai"
        ):
            with pytest.raises(InvalidBlock):
                run_shanghai_blockchain_st_tests(test_case)
        else:
            run_shanghai_blockchain_st_tests(test_case)
    except NoPostState:
        # FIXME: Handle tests that don't have post state
        pytest.xfail(f"{test_case} doesn't have post state")
