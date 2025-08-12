from typing import Tuple


def get_exceptional_blockchain_test_patterns(
    json_fork: str, eels_fork: str
) -> Tuple[tuple[str, ...], tuple[str, ...], tuple[str, ...]]:
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
    slow_tests :
        Patterns to match test files or test ids that should be marked as slow.
    ignore_tests :
        Patterns to match test files or test ids that should be ignored.
    big_memory_tests :
        Patterns to match test files or test ids that require large memory.
    """
    slow_tests = (
        # GeneralStateTests
        "stTimeConsuming/CALLBlake2f_MaxRounds.json",
        "stTimeConsuming/static_Call50000_sha256.json",
        "vmPerformance/loopExp.json",
        "vmPerformance/loopMul.json",
        f"QuadraticComplexitySolidity_CallDataCopy_d0g1v0_{json_fork}",
        f"CALLBlake2f_d9g0v0_{json_fork}",
        "CALLCODEBlake2f_d9g0v0",
        # GeneralStateTests
        "stRandom/randomStatetest177.json",
        "stCreateTest/CreateOOGafterMaxCodesize.json",
        # ValidBlockTest
        "bcExploitTest/DelegateCallSpam.json",
        # InvalidBlockTest
        "bcUncleHeaderValidity/nonceWrong.json",
        "bcUncleHeaderValidity/wrongMixHash.json",
        f"tests/{eels_fork}/eip2537_bls_12_381_precompiles/test_bls12_pairing\\.py\\:\\:test_valid\\[fork_{json_fork}-blockchain_test-bls_pairing_non-degeneracy-\\]",
        f"tests/{eels_fork}/eip2537_bls_12_381_precompiles/test_bls12_pairing\\.py\\:\\:test_valid\\[fork_{json_fork}-blockchain_test-bls_pairing_bilinearity-\\]",
        f"tests/{eels_fork}/eip2537_bls_12_381_precompiles/test_bls12_pairing\\.py\\:\\:test_valid\\[fork_{json_fork}-blockchain_test-bls_pairing_e\\(G1,-G2\\)=e\\(-G1,G2\\)-\\]",
        f"tests/{eels_fork}/eip2537_bls_12_381_precompiles/test_bls12_pairing\\.py\\:\\:test_valid\\[fork_{json_fork}-blockchain_test-bls_pairing_e\\(aG1,bG2\\)=e\\(abG1,G2\\)-\\]",
        f"tests/{eels_fork}/eip2537_bls_12_381_precompiles/test_bls12_pairing\\.py\\:\\:test_valid\\[fork_{json_fork}-blockchain_test-bls_pairing_e\\(aG1,bG2\\)=e\\(G1,abG2\\)-\\]",
        f"tests/{eels_fork}/eip2537_bls_12_381_precompiles/test_bls12_pairing\\.py\\:\\:test_valid\\[fork_{json_fork}-blockchain_test-inf_pair-\\]",
        f"tests/{eels_fork}/eip2537_bls_12_381_precompiles/test_bls12_pairing\\.py\\:\\:test_valid\\[fork_{json_fork}-blockchain_test-multi_inf_pair-\\]",
        f"tests/{eels_fork}/eip2935_historical_block_hashes_from_state/test_block_hashes\\.py\\:\\:test_block_hashes_history\\[fork_{json_fork}-blockchain_test-full_history_plus_one_check_blockhash_first\\]",
    )

    # These are tests that are considered to be incorrect,
    # Please provide an explanation when adding entries
    ignore_tests = (
        # ValidBlockTest
        "bcForkStressTest/ForkStressTest.json",
        "bcGasPricerTest/RPC_API_Test.json",
        "bcMultiChainTest",
        "bcTotalDifficultyTest",
        # InvalidBlockTest
        "bcForgedTest",
        "bcMultiChainTest",
        f"GasLimitHigherThan2p63m1_{json_fork}",
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

    return slow_tests, ignore_tests, big_memory_tests


def get_exceptional_state_test_patterns(
    json_fork: str, eels_fork: str
) -> tuple[str, ...]:
    slow_tests = (
        "CALLBlake2f_MaxRounds",
        "CALLCODEBlake2f",
        "CALLBlake2f",
        "loopExp",
        "loopMul",
        "GeneralStateTests/stTimeConsuming/CALLBlake2f_MaxRounds.json::CALLBlake2f_MaxRounds-fork_[Cancun-Prague]-d0g0v0",
        "GeneralStateTests/VMTests/vmPerformance/loopExp.json::loopExp-fork_[Cancun-Prague]-d[0-14]g0v0",
        "GeneralStateTests/VMTests/vmPerformance/loopMul.json::loopMul-fork_[Cancun-Prague]-d[0-2]g0v0",
        f"tests/{eels_fork}/eip2537_bls_12_381_precompiles/test_bls12_pairing.py::test_valid[fork_{json_fork}-state_test-bls_pairing_non-degeneracy-]",
        f"tests/{eels_fork}/eip2537_bls_12_381_precompiles/test_bls12_pairing.py::test_valid[fork_{json_fork}-state_test-bls_pairing_bilinearity-]",
        f"tests/{eels_fork}/eip2537_bls_12_381_precompiles/test_bls12_pairing.py::test_valid[fork_{json_fork}-state_test-bls_pairing_e(G1,-G2)=e(-G1,G2)-]",
        f"tests/{eels_fork}/eip2537_bls_12_381_precompiles/test_bls12_pairing.py::test_valid[fork_{json_fork}-state_test-bls_pairing_e(aG1,bG2)=e(abG1,G2)-]",
        f"tests/{eels_fork}/eip2537_bls_12_381_precompiles/test_bls12_pairing.py::test_valid[fork_{json_fork}-state_test-bls_pairing_e(aG1,bG2)=e(G1,abG2)-]",
        f"tests/{eels_fork}/eip2537_bls_12_381_precompiles/test_bls12_pairing.py::test_valid[fork_{json_fork}-state_test-inf_pair-]",
        f"tests/{eels_fork}/eip2537_bls_12_381_precompiles/test_bls12_pairing.py::test_valid[fork_{json_fork}-state_test-multi_inf_pair-]",
    )

    return slow_tests
