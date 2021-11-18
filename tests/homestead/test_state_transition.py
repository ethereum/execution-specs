import os
from functools import partial
from typing import Generator

import pytest

from tests.homestead.blockchain_st_test_helpers import (
    run_homestead_blockchain_st_tests,
)

test_dir = (
    "tests/fixtures/LegacyTests/Constantinople/BlockchainTests/"
    "GeneralStateTests/"
)

run_general_state_tests = partial(run_homestead_blockchain_st_tests, test_dir)

# Every test below takes more than  60s to run and
# hence they've been marked as slow
SLOW_TESTS = (
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
)


def get_test_files() -> Generator[str, None, None]:
    for idx, _dir in enumerate(os.listdir(test_dir)):
        test_file_path = os.path.join(test_dir, _dir)
        for _file in os.listdir(test_file_path):
            _test_file = os.path.join(_dir, _file)
            # TODO: provide a way to run slow tests
            if _test_file in SLOW_TESTS:
                continue
            else:
                yield _test_file


@pytest.mark.parametrize("test_file", get_test_files())
def test_general_state_tests(test_file: str) -> None:
    try:
        run_general_state_tests(test_file)
    except KeyError:
        # KeyError is raised when a test_file has no tests for homestead
        raise pytest.skip(f"{test_file} has no tests for homestead")
