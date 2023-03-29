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


def is_in_list(test_case: Dict, test_list: Tuple) -> bool:
    for test in test_list:
        if test in test_case["test_file"]:
            return True

    return False


# Run EIP-4895 tests
test_dir = f"{ETHEREUM_TESTS_PATH}/BlockchainTests/EIPTests/"

invalid_rlp_tests = (
    "bc4895-withdrawals/withdrawalsRLPlessElements.json",
    "bc4895-withdrawals/withdrawalsRLPmoreElements.json",
    "bc4895-withdrawals/shanghaiWithoutWithdrawalsRLP.json",
    "bc4895-withdrawals/withdrawalsRLPnotAList.json",
)

invalid_bounds_tests = (
    "bc4895-withdrawals/withdrawalsAmountBounds.json",
    "bc4895-withdrawals/withdrawalsAddressBounds.json",
    "bc4895-withdrawals/withdrawalsIndexBounds.json",
    "bc4895-withdrawals/withdrawalsValidatorIndexBounds.json",
)

invalid_block_tests = ("bc4895-withdrawals/incorrectWithdrawalsRoot.json",)


@pytest.mark.parametrize(
    "test_case",
    fetch_shanghai_tests(test_dir),
    ids=idfn,
)
def test_general_state_tests_4895(test_case: Dict) -> None:
    try:
        if is_in_list(test_case, invalid_rlp_tests):
            with pytest.raises(RLPDecodingError):
                run_shanghai_blockchain_st_tests(test_case)

        elif is_in_list(test_case, invalid_bounds_tests):
            with pytest.raises(InvalidBlock):
                run_shanghai_blockchain_st_tests(test_case)

        elif is_in_list(test_case, invalid_block_tests):
            with pytest.raises(InvalidBlock):
                run_shanghai_blockchain_st_tests(test_case)

        else:
            run_shanghai_blockchain_st_tests(test_case)
    except NoPostState:
        # FIXME: Handle tests that don't have post state
        pytest.xfail(f"{test_case} doesn't have post state")


# Run EIP-3860 tests
test_dir = f"{ETHEREUM_TESTS_PATH}/BlockchainTests/GeneralStateTests/EIPTests/stEIP3860"


@pytest.mark.parametrize(
    "test_case",
    fetch_shanghai_tests(test_dir),
    ids=idfn,
)
def test_general_state_tests_3860(test_case: Dict) -> None:
    try:
        run_shanghai_blockchain_st_tests(test_case)
    except NoPostState:
        # FIXME: Handle tests that don't have post state
        pytest.xfail(f"{test_case} doesn't have post state")


# Run execution-spec-generated-tests
test_dir = f"{ETHEREUM_SPEC_TESTS_PATH}/fixtures/withdrawals"


@pytest.mark.parametrize(
    "test_case",
    fetch_shanghai_tests(test_dir),
    ids=idfn,
)
def test_execution_specs_generated_tests(test_case: Dict) -> None:
    try:
        if (
            "withdrawals_use_value_in_tx" in test_case["test_file"]
            and test_case["test_key"] == "000_shanghai"
        ):
            with pytest.raises(InvalidBlock):
                run_shanghai_blockchain_st_tests(test_case)
        else:
            run_shanghai_blockchain_st_tests(test_case)
    except NoPostState:
        # FIXME: Handle tests that don't have post state
        pytest.xfail(f"{test_case} doesn't have post state")
