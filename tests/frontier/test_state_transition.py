import pytest

from tests.frontier.blockchain_st_test_helpers import (
    run_frontier_blockchain_st_tests,
)

TEST_DIR = (
    "tests/fixtures/LegacyTests/Constantinople/BlockchainTests/"
    "GeneralStateTests/"
)


def test_add() -> None:
    run_frontier_blockchain_st_tests("stExample/add11_d0g0v0.json")


@pytest.mark.parametrize(
    "test_file",
    [
        f"stTransactionTest/Opcodes_TransactionInit_d{i}g0v0.json"
        for i in range(128)
        if i not in [33, 37, 38, 124, 125, 126, 127]
        # NOTE:
        # - Test 33, 127 has no tests for Frontier
        # - test 37, 38 124, 125, 126 have invalid opcodes
        # that need to be handled gracefully
    ],
)
def test_transaction_init(test_file: str) -> None:
    run_frontier_blockchain_st_tests(test_file)


# TODO: Run the below test cases once CALL opcode has been implemented.
# @pytest.mark.parametrize(
#     "test_file",
#     list(os.listdir(os.path.join(TEST_DIR, "stLogTests")))
# )
# def test_log_operations(test_file: str) -> None:
#     print(test_file)
#     run_frontier_blockchain_st_tests(f"stLogTests/{test_file}")
#     assert 1 == 0


@pytest.mark.parametrize(
    "test_file",
    [
        "stPreCompiledContracts2/CALLCODEEcrecover0_0input_d0g0v0.json",
        "stPreCompiledContracts2/CALLCODEEcrecover0_0input_d0g0v0.json",
        "stPreCompiledContracts2/CALLCODEEcrecover0_Gas2999_d0g0v0.json",
        "stPreCompiledContracts2/CALLCODEEcrecover0_NoGas_d0g0v0.json",
        "stPreCompiledContracts2/CALLCODEEcrecover0_completeReturnValue_d0g0v0.json",
        "stPreCompiledContracts2/CALLCODEEcrecover0_d0g0v0.json",
        "stPreCompiledContracts2/CALLCODEEcrecover0_gas3000_d0g0v0.json",
        "stPreCompiledContracts2/CALLCODEEcrecover0_overlappingInputOutput_d0g0v0.json",
        "stPreCompiledContracts2/CALLCODEEcrecover1_d0g0v0.json",
        "stPreCompiledContracts2/CALLCODEEcrecover2_d0g0v0.json",
        "stPreCompiledContracts2/CALLCODEEcrecover3_d0g0v0.json",
        "stPreCompiledContracts2/CALLCODEEcrecover80_d0g0v0.json",
        "stPreCompiledContracts2/CALLCODEEcrecoverH_prefixed0_d0g0v0.json",
        "stPreCompiledContracts2/CALLCODEEcrecoverR_prefixed0_d0g0v0.json",
        "stPreCompiledContracts2/CALLCODEEcrecoverS_prefixed0_d0g0v0.json",
        "stPreCompiledContracts2/CALLCODEEcrecoverV_prefixed0_d0g0v0.json",
        "stPreCompiledContracts2/CALLCODEEcrecoverV_prefixedf0_d0g0v0.json",
        "stPreCompiledContracts2/CALLCODEEcrecoverV_prefixedf0_d1g0v0.json",
        "stPreCompiledContracts2/CALLCODEIdentitiy_0_d0g0v0.json",
        "stPreCompiledContracts2/CALLCODEIdentitiy_1_d0g0v0.json",
        "stPreCompiledContracts2/CALLCODEIdentity_1_nonzeroValue_d0g0v0.json",
        "stPreCompiledContracts2/CALLCODEIdentity_2_d0g0v0.json",
        "stPreCompiledContracts2/CALLCODEIdentity_3_d0g0v0.json",
        "stPreCompiledContracts2/CALLCODEIdentity_4_d0g0v0.json",
        "stPreCompiledContracts2/CALLCODEIdentity_4_gas17_d0g0v0.json",
        "stPreCompiledContracts2/CALLCODEIdentity_4_gas18_d0g0v0.json",
        "stPreCompiledContracts2/CALLCODEIdentity_5_d0g0v0.json",
        "stPreCompiledContracts2/CALLCODERipemd160_0_d0g0v0.json",
        "stPreCompiledContracts2/CALLCODERipemd160_1_d0g0v0.json",
        "stPreCompiledContracts2/CALLCODERipemd160_2_d0g0v0.json",
        "stPreCompiledContracts2/CALLCODERipemd160_3_d0g0v0.json",
        "stPreCompiledContracts2/CALLCODERipemd160_3_postfixed0_d0g0v0.json",
        "stPreCompiledContracts2/CALLCODERipemd160_3_prefixed0_d0g0v0.json",
        "stPreCompiledContracts2/CALLCODERipemd160_4_d0g0v0.json",
        "stPreCompiledContracts2/CALLCODERipemd160_4_gas719_d0g0v0.json",
        "stPreCompiledContracts2/CALLCODERipemd160_5_d0g0v0.json",
        "stPreCompiledContracts2/CALLCODESha256_0_d0g0v0.json",
        "stPreCompiledContracts2/CALLCODESha256_1_d0g0v0.json",
        "stPreCompiledContracts2/CALLCODESha256_1_nonzeroValue_d0g0v0.json",
        "stPreCompiledContracts2/CALLCODESha256_2_d0g0v0.json",
        "stPreCompiledContracts2/CALLCODESha256_3_d0g0v0.json",
        "stPreCompiledContracts2/CALLCODESha256_3_postfix0_d0g0v0.json",
        "stPreCompiledContracts2/CALLCODESha256_3_prefix0_d0g0v0.json",
        "stPreCompiledContracts2/CALLCODESha256_4_d0g0v0.json",
        "stPreCompiledContracts2/CALLCODESha256_4_gas99_d0g0v0.json",
        "stPreCompiledContracts2/CALLCODESha256_5_d0g0v0.json",
        "stPreCompiledContracts2/CallEcrecover0_0input_d0g0v0.json",
        "stPreCompiledContracts2/CallEcrecover0_Gas2999_d0g0v0.json",
        "stPreCompiledContracts2/CallEcrecover0_NoGas_d0g0v0.json",
        "stPreCompiledContracts2/CallEcrecover0_completeReturnValue_d0g0v0.json",
        "stPreCompiledContracts2/CallEcrecover0_d0g0v0.json",
        "stPreCompiledContracts2/CallEcrecover0_gas3000_d0g0v0.json",
        "stPreCompiledContracts2/CallEcrecover0_overlappingInputOutput_d0g0v0.json",
        "stPreCompiledContracts2/CallEcrecover1_d0g0v0.json",
        "stPreCompiledContracts2/CallEcrecover2_d0g0v0.json",
        "stPreCompiledContracts2/CallEcrecover3_d0g0v0.json",
        "stPreCompiledContracts2/CallEcrecover80_d0g0v0.json",
        "stPreCompiledContracts2/CallEcrecoverCheckLengthWrongV_d0g0v0.json",
        "stPreCompiledContracts2/CallEcrecoverCheckLength_d0g0v0.json",
        "stPreCompiledContracts2/CallEcrecoverH_prefixed0_d0g0v0.json",
        "stPreCompiledContracts2/CallEcrecoverInvalidSignature_d0g0v0.json",
        "stPreCompiledContracts2/CallEcrecoverR_prefixed0_d0g0v0.json",
        "stPreCompiledContracts2/CallEcrecoverS_prefixed0_d0g0v0.json",
        "stPreCompiledContracts2/CallEcrecoverUnrecoverableKey_d0g0v0.json",
        "stPreCompiledContracts2/CallEcrecoverV_prefixed0_d0g0v0.json",
        "stPreCompiledContracts2/CallIdentitiy_0_d0g0v0.json",
        "stPreCompiledContracts2/CallIdentitiy_1_d0g0v0.json",
        "stPreCompiledContracts2/CallIdentity_1_nonzeroValue_d0g0v0.json",
        "stPreCompiledContracts2/CallIdentity_2_d0g0v0.json",
        "stPreCompiledContracts2/CallIdentity_3_d0g0v0.json",
        "stPreCompiledContracts2/CallIdentity_4_d0g0v0.json",
        "stPreCompiledContracts2/CallIdentity_4_gas17_d0g0v0.json",
        "stPreCompiledContracts2/CallIdentity_4_gas18_d0g0v0.json",
        "stPreCompiledContracts2/CallIdentity_5_d0g0v0.json",
        "stPreCompiledContracts2/CallIdentity_6_inputShorterThanOutput_d0g0v0.json",
        "stPreCompiledContracts2/CallRipemd160_0_d0g0v0.json",
        "stPreCompiledContracts2/CallRipemd160_1_d0g0v0.json",
        "stPreCompiledContracts2/CallRipemd160_2_d0g0v0.json",
        "stPreCompiledContracts2/CallRipemd160_3_d0g0v0.json",
        "stPreCompiledContracts2/CallRipemd160_3_postfixed0_d0g0v0.json",
        "stPreCompiledContracts2/CallRipemd160_3_prefixed0_d0g0v0.json",
        "stPreCompiledContracts2/CallRipemd160_4_d0g0v0.json",
        "stPreCompiledContracts2/CallRipemd160_4_gas719_d0g0v0.json",
        "stPreCompiledContracts2/CallRipemd160_5_d0g0v0.json",
        "stPreCompiledContracts2/CallSha256_0_d0g0v0.json",
        "stPreCompiledContracts2/CallSha256_1_d0g0v0.json",
        "stPreCompiledContracts2/CallSha256_1_nonzeroValue_d0g0v0.json",
        "stPreCompiledContracts2/CallSha256_2_d0g0v0.json",
        "stPreCompiledContracts2/CallSha256_3_d0g0v0.json",
        "stPreCompiledContracts2/CallSha256_3_postfix0_d0g0v0.json",
        "stPreCompiledContracts2/CallSha256_3_prefix0_d0g0v0.json",
        "stPreCompiledContracts2/CallSha256_4_d0g0v0.json",
        "stPreCompiledContracts2/CallSha256_4_gas99_d0g0v0.json",
        "stPreCompiledContracts2/CallSha256_5_d0g0v0.json",
    ],
)
def test_precompiles(test_file: str) -> None:
    run_frontier_blockchain_st_tests(test_file)
