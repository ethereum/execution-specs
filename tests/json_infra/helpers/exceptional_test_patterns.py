import re
from dataclasses import dataclass
from typing import Pattern, Tuple


@dataclass
class TestPatterns:
    """
    Identify test patterns which are slow, are to be ignored
    or are to be marked as consuming large memory at runtime.
    """

    slow: Tuple[Pattern[str], ...]
    expected_fail: Tuple[Pattern[str], ...]
    big_memory: Tuple[Pattern[str], ...]


def exceptional_blockchain_test_patterns(
    json_fork: str, eels_fork: str
) -> TestPatterns:
    """
    Returns patterns for slow, ignored, and big-memory tests for a given json_fork and eels_fork.

    Parameters
    ----------
    json_fork : str
        The json_fork name (e.g., "Frontier", "EIP150").
    eels_fork : str
        The eels_fork name (e.g., "frontier", "tangerine_whistle").

    Returns
    -------
    TestPatterns :
        Patterns that are relevant to the current fork.
    """
    jf = re.escape(json_fork)
    ef = re.escape(eels_fork)

    slow_tests = (
        # GeneralStateTests
        "stTimeConsuming/CALLBlake2f_MaxRounds\\.json",
        "stTimeConsuming/static_Call50000_sha256\\.json",
        "vmPerformance/loopExp\\.json",
        "vmPerformance/loopMul\\.json",
        f"QuadraticComplexitySolidity_CallDataCopy_d0g1v0_{jf}",
        f"CALLBlake2f_d9g0v0_{jf}",
        "CALLCODEBlake2f_d9g0v0",
        # GeneralStateTests
        "stRandom/randomStatetest177\\.json",
        "stCreateTest/CreateOOGafterMaxCodesize\\.json",
        # ValidBlockTest
        "bcExploitTest/DelegateCallSpam\\.json",
        # InvalidBlockTest
        "bcUncleHeaderValidity/nonceWrong\\.json",
        "bcUncleHeaderValidity/wrongMixHash\\.json",
        f"tests/{ef}/eip2537_bls_12_381_precompiles/test_bls12_pairing\\.py::test_valid\\[fork_{jf}-blockchain_test-bls_pairing_non-degeneracy-\\]",
        f"tests/{ef}/eip2537_bls_12_381_precompiles/test_bls12_pairing\\.py::test_valid\\[fork_{jf}-blockchain_test-bls_pairing_bilinearity-\\]",
        f"tests/{ef}/eip2537_bls_12_381_precompiles/test_bls12_pairing\\.py::test_valid\\[fork_{jf}-blockchain_test-bls_pairing_e(G1,-G2)=e(-G1,G2)-\\]",
        f"tests/{ef}/eip2537_bls_12_381_precompiles/test_bls12_pairing\\.py::test_valid\\[fork_{jf}-blockchain_test-bls_pairing_e(aG1,bG2)=e(abG1,G2)-\\]",
        f"tests/{ef}/eip2537_bls_12_381_precompiles/test_bls12_pairing\\.py::test_valid\\[fork_{jf}-blockchain_test-bls_pairing_e(aG1,bG2)=e(G1,abG2)-\\]",
        f"tests/{ef}/eip2537_bls_12_381_precompiles/test_bls12_pairing\\.py::test_valid\\[fork_{jf}-blockchain_test-inf_pair-\\]",
        f"tests/{ef}/eip2537_bls_12_381_precompiles/test_bls12_pairing\\.py::test_valid\\[fork_{jf}-blockchain_test-multi_inf_pair-\\]",
        f"tests/{ef}/eip2935_historical_block_hashes_from_state/test_block_hashes\\.py::test_block_hashes_history\\[fork_{jf}-blockchain_test-full_history_plus_one_check_blockhash_first\\]",
    )

    # These are tests that are considered to be incorrect,
    # Please provide an explanation when adding entries
    expected_fail = (
        # ValidBlockTest
        "bcForkStressTest/ForkStressTest\\.json",
        "bcGasPricerTest/RPC_API_Test\\.json",
        "bcMultiChainTest",
        "bcTotalDifficultyTest",
        # InvalidBlockTest
        "bcForgedTest",
        "bcMultiChainTest",
        f"GasLimitHigherThan2p63m1_{jf}",
    )

    # All tests that recursively create a large number of frames (50000)
    big_memory_tests = (
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

    return TestPatterns(
        slow=tuple(re.compile(p) for p in slow_tests),
        expected_fail=tuple(re.compile(p) for p in expected_fail),
        big_memory=tuple(re.compile(p) for p in big_memory_tests),
    )


def exceptional_state_test_patterns(
    json_fork: str, eels_fork: str
) -> TestPatterns:
    jf = re.escape(json_fork)
    ef = re.escape(eels_fork)
    slow_tests = (
        "CALLBlake2f_MaxRounds",
        "CALLCODEBlake2f",
        "CALLBlake2f",
        "loopExp",
        "loopMul",
        "GeneralStateTests/stTimeConsuming/CALLBlake2f_MaxRounds\\.json::CALLBlake2f_MaxRounds-fork_\\[Cancun-Prague\\]-d0g0v0",
        "GeneralStateTests/VMTests/vmPerformance/loopExp\\.json::loopExp-fork_\\[Cancun-Prague\\]-d[0-14]g0v0",
        "GeneralStateTests/VMTests/vmPerformance/loopMul\\.json::loopMul-fork_\\[Cancun-Prague\\]-d[0-2]g0v0",
        f"tests/{ef}/eip2537_bls_12_381_precompiles/test_bls12_pairing\\.py::test_valid\\[fork_{jf}-state_test-bls_pairing_non-degeneracy-\\]",
        f"tests/{ef}/eip2537_bls_12_381_precompiles/test_bls12_pairing\\.py::test_valid\\[fork_{jf}-state_test-bls_pairing_bilinearity-\\]",
        f"tests/{ef}/eip2537_bls_12_381_precompiles/test_bls12_pairing\\.py::test_valid\\[fork_{jf}-state_test-bls_pairing_e(G1,-G2)=e(-G1,G2)-\\]",
        f"tests/{ef}/eip2537_bls_12_381_precompiles/test_bls12_pairing\\.py::test_valid\\[fork_{jf}-state_test-bls_pairing_e(aG1,bG2)=e(abG1,G2)-\\]",
        f"tests/{ef}/eip2537_bls_12_381_precompiles/test_bls12_pairing\\.py::test_valid\\[fork_{jf}-state_test-bls_pairing_e(aG1,bG2)=e(G1,abG2)-\\]",
        f"tests/{ef}/eip2537_bls_12_381_precompiles/test_bls12_pairing\\.py::test_valid\\[fork_{jf}-state_test-inf_pair-\\]",
        f"tests/{ef}/eip2537_bls_12_381_precompiles/test_bls12_pairing\\.py::test_valid\\[fork_{jf}-state_test-multi_inf_pair-\\]",
    )

    return TestPatterns(
        slow=tuple(re.compile(p) for p in slow_tests),
        expected_fail=tuple(),
        big_memory=tuple(),
    )
