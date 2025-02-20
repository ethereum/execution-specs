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
NETWORK = "Homestead"
PACKAGE = "homestead"

# Every test below takes more than  60s to run and
# hence they've been marked as slow
LEGACY_SLOW_TESTS = (
    # GeneralStateTests
    "stRandom/randomStatetest177_d0g0v0.json",
    "stQuadraticComplexityTest/Call50000_d0g1v0.json",
    "stQuadraticComplexityTest/Call50000_sha256_d0g1v0.json",
    "stQuadraticComplexityTest/Call50000_rip160_d0g1v0.json",
    "stQuadraticComplexityTest/Call50000_identity2_d0g0v0.json",
    "stQuadraticComplexityTest/Callcode50000_d0g0v0.json",
    "stQuadraticComplexityTest/Return50000_2_d0g0v0.json",
    "stQuadraticComplexityTest/Call1MB1024Calldepth_d0g1v0.json",
    "stQuadraticComplexityTest/Call50000bytesContract50_3_d0g0v0.json",
    "stQuadraticComplexityTest/Create1000_d0g0v0.json",
    "stQuadraticComplexityTest/Call50000_identity_d0g1v0.json",
    "stQuadraticComplexityTest/Call50000_ecrec_d0g0v0.json",
    "stQuadraticComplexityTest/QuadraticComplexitySolidity_CallDataCopy_d0g1v0.json",
    "stQuadraticComplexityTest/Call50000bytesContract50_2_d0g1v0.json",
    "stQuadraticComplexityTest/Call50000_identity2_d0g1v0.json",
    "stQuadraticComplexityTest/Call50000_rip160_d0g0v0.json",
    "stQuadraticComplexityTest/Return50000_d0g0v0.json",
    "stQuadraticComplexityTest/Call50000_sha256_d0g0v0.json",
    "stQuadraticComplexityTest/Call50000_d0g0v0.json",
    "stQuadraticComplexityTest/Call50000bytesContract50_1_d0g0v0.json",
    "stQuadraticComplexityTest/Return50000_2_d0g1v0.json",
    "stQuadraticComplexityTest/Callcode50000_d0g1v0.json",
    "stQuadraticComplexityTest/Call50000bytesContract50_3_d0g1v0.json",
    "stQuadraticComplexityTest/Call1MB1024Calldepth_d0g0v0.json",
    "stQuadraticComplexityTest/Call50000bytesContract50_2_d0g0v0.json",
    "stQuadraticComplexityTest/Call50000_ecrec_d0g1v0.json",
    "stQuadraticComplexityTest/QuadraticComplexitySolidity_CallDataCopy_d0g0v0.json",
    "stQuadraticComplexityTest/Call50000_identity_d0g0v0.json",
    "stStackTests/stackOverflowM1DUP_d10g0v0.json",
    "stStackTests/stackOverflowM1DUP_d11g0v0.json",
    "stCallDelegateCodesHomestead/callcallcodecall_010_OOGE_d0g0v0.json",
    "stCallDelegateCodesHomestead/callcallcallcode_001_OOGE_d0g0v0.json",
    "stCallDelegateCodesHomestead/callcodecallcodecallcode_111_OOGMAfter_d0g0v0.json",
    "stCallDelegateCodesHomestead/callcodecallcodecall_ABCB_RECURSIVE_d0g0v0.json",
    "stCallDelegateCodesHomestead/callcallcodecall_010_SuicideEnd_d0g0v0.json",
    "stCallDelegateCodesHomestead/callcallcallcode_001_SuicideMiddle_d0g0v0.json",
    "stCallDelegateCodesHomestead/callcodecallcodecall_110_OOGE_d0g0v0.json",
    "stCallDelegateCodesHomestead/callcodecallcodecall_110_SuicideEnd_d0g0v0.json",
    "stCallDelegateCodesHomestead/callcallcodecallcode_011_OOGMBefore_d0g0v0.json",
    "stCallDelegateCodesHomestead/callcallcallcode_ABCB_RECURSIVE_d0g0v0.json",
    "stCallDelegateCodesHomestead/callcodecallcall_100_SuicideMiddle_d0g0v0.json",
    "stCallDelegateCodesHomestead/callcodecallcallcode_101_OOGE_d0g0v0.json",
    "stCallDelegateCodesHomestead/callcodecallcodecallcode_111_OOGE_d0g0v0.json",
    "stCallDelegateCodesHomestead/callcodecallcall_100_SuicideEnd_d0g0v0.json",
    "stCallDelegateCodesHomestead/callcallcodecallcode_011_OOGE_d0g0v0.json",
    "stCallDelegateCodesHomestead/callcallcode_01_d0g0v0.json",
    "stCallDelegateCodesHomestead/callcodecallcodecall_110_OOGMBefore_d0g0v0.json",
    "stCallDelegateCodesHomestead/callcodecallcode_11_SuicideEnd_d0g0v0.json",
    "stCallDelegateCodesHomestead/callcallcodecallcode_011_SuicideEnd_d0g0v0.json",
    "stCallDelegateCodesHomestead/callcodecallcall_100_OOGE_d0g0v0.json",
    "stCallDelegateCodesHomestead/callcallcodecall_ABCB_RECURSIVE_d0g0v0.json",
    "stCallDelegateCodesHomestead/callcodecallcall_100_OOGMBefore_d0g0v0.json",
    "stCallDelegateCodesHomestead/callcodecallcall_100_OOGMAfter_d0g0v0.json",
    "stCallDelegateCodesHomestead/callcallcodecallcode_ABCB_RECURSIVE_d0g0v0.json",
    "stCallDelegateCodesHomestead/callcodecall_10_d0g0v0.json",
    "stCallDelegateCodesHomestead/callcodecallcallcode_101_SuicideMiddle_d0g0v0.json",
    "stCallDelegateCodesHomestead/callcodecall_10_OOGE_d0g0v0.json",
    "stCallDelegateCodesHomestead/callcodecallcode_11_OOGE_d0g0v0.json",
    "stCallDelegateCodesHomestead/callcodecallcallcode_ABCB_RECURSIVE_d0g0v0.json",
    "stCallDelegateCodesHomestead/callcodecallcodecallcode_111_SuicideMiddle_d0g0v0.json",
    "stCallDelegateCodesHomestead/callcallcodecall_010_OOGMBefore_d0g0v0.json",
    "stCallDelegateCodesHomestead/callcodecallcodecallcode_111_OOGMBefore_d0g0v0.json",
    "stCallDelegateCodesHomestead/callcallcallcode_001_d0g0v0.json",
    "stCallDelegateCodesHomestead/callcodecallcallcode_101_SuicideEnd_d0g0v0.json",
    "stCallDelegateCodesHomestead/callcallcodecallcode_011_SuicideMiddle_d0g0v0.json",
    "stCallDelegateCodesHomestead/callcallcodecallcode_011_OOGMAfter_d0g0v0.json",
    "stCallDelegateCodesHomestead/callcodecallcallcode_101_d0g0v0.json",
    "stCallDelegateCodesHomestead/callcallcodecallcode_011_d0g0v0.json",
    "stCallDelegateCodesHomestead/callcodecallcodecall_110_d0g0v0.json",
    "stCallDelegateCodesHomestead/callcallcode_01_SuicideEnd_d0g0v0.json",
    "stCallDelegateCodesHomestead/callcodecallcodecall_110_OOGMAfter_d0g0v0.json",
    "stCallDelegateCodesHomestead/callcallcodecall_010_OOGMAfter_d0g0v0.json",
    "stCallDelegateCodesHomestead/callcallcode_01_OOGE_d0g0v0.json",
    "stCallDelegateCodesHomestead/callcodecallcodecallcode_ABCB_RECURSIVE_d0g0v0.json",
    "stSpecialTest/JUMPDEST_AttackwithJump_d0g0v0.json",
    "stSpecialTest/JUMPDEST_Attack_d0g0v0.json",
    # ValidBlockTests
    "bcExploitTest/DelegateCallSpam.json",
    # InvalidBlockTests
    "bcUncleHeaderValidity/nonceWrong.json",
    "bcUncleHeaderValidity/wrongMixHash.json",
)


# These are tests that are considered to be incorrect,
# Please provide an explanation when adding entries
LEGACY_IGNORE_LIST = (
    # ValidBlockTests
    "bcForkStressTest/ForkStressTest.json",
    "bcGasPricerTest/RPC_API_Test.json",
    "bcMultiChainTest/",
    "bcTotalDifficultyTest/",
    # InvalidBlockTests
    "bcForgedTest",
    "bcMultiChainTest",
    "GasLimitHigherThan2p63m1_Homestead",
)

LEGACY_BIG_MEMORY_TESTS = (
    # GeneralStateTests
    "/stQuadraticComplexityTest/",
    "/stRandom2/",
    "/stRandom/",
    "/stSpecialTest/",
    "stTimeConsuming/",
    # ValidBlockTests
    "randomStatetest94_",
)

# Define Tests
fetch_tests = partial(
    fetch_state_test_files,
    network=NETWORK,
    ignore_list=LEGACY_IGNORE_LIST,
    slow_list=LEGACY_SLOW_TESTS,
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
