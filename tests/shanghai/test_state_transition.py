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


# Run state tests
test_dir = f"{ETHEREUM_TESTS_PATH}/BlockchainTests/"

SLOW_TESTS = (
    # GeneralStateTests
    "stTimeConsuming/CALLBlake2f_MaxRounds.json",
    "stTimeConsuming/static_Call50000_sha256.json",
    "vmPerformance/loopExp.json",
    "vmPerformance/loopMul.json",
    "QuadraticComplexitySolidity_CallDataCopy_d0g1v0_Shanghai",
    "CALLBlake2f_d9g0v0_Shanghai",
    "CALLCODEBlake2f_d9g0v0",
    # ValidBlockTest
    "bcExploitTest/DelegateCallSpam.json",
)

# These are tests that are considered to be incorrect,
# Please provide an explanation when adding entries
IGNORE_LIST = (
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
    # ValidBlockTest
    "bcForkStressTest/ForkStressTest.json",
    "bcGasPricerTest/RPC_API_Test.json",
    "bcMultiChainTest",
    "bcTotalDifficultyTest",
    # InvalidBlockTest
    "bcForgedTest",
    "bcMultiChainTest",
    "GasLimitHigherThan2p63m1_Shanghai",
    # TODO: The below tests are being ignored due to a bug in
    # upstream repo. They should be removed from the ignore list
    # once the bug is resolved
    # See: https://github.com/ethereum/execution-spec-tests/pull/134
    "Pyspecs/vm/chain_id.json",
    "Pyspecs/vm/dup.json",
    "Pyspecs/example/yul.json",
    "Pyspecs/eips/warm_coinbase_gas_usage.json",
    "Pyspecs/eips/warm_coinbase_call_out_of_gas.json",
)

# All tests that recursively create a large number of frames (50000)
BIG_MEMORY_TEST = (
    # GeneralStateTests
    "50000_",
    "/stQuadraticComplexityTest/",
    "/stRandom2/",
    "/stRandom/",
    "/stSpecialTest/",
    "stTimeConsuming/",
    "stBadOpcode/",
    "stStaticCall/",
)

fetch_state_tests = partial(
    fetch_shanghai_tests,
    test_dir,
    ignore_list=IGNORE_LIST,
    slow_list=SLOW_TESTS,
    big_memory_list=BIG_MEMORY_TEST,
)


@pytest.mark.parametrize(
    "test_case",
    fetch_state_tests(),
    ids=idfn,
)
def test_general_state_tests(test_case: Dict) -> None:
    run_shanghai_blockchain_st_tests(test_case)


# Run execution-spec-generated-tests
test_dir = f"{ETHEREUM_SPEC_TESTS_PATH}/fixtures/withdrawals"


@pytest.mark.parametrize(
    "test_case",
    fetch_shanghai_tests(test_dir),
    ids=idfn,
)
def test_execution_specs_generated_tests(test_case: Dict) -> None:
    run_shanghai_blockchain_st_tests(test_case)
