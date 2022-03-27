from functools import partial

import pytest

from ethereum.exceptions import InvalidBlock
from tests.constantinople.blockchain_st_test_helpers import (
    FIXTURES_LOADER,
    run_constantinople_blockchain_st_tests,
)
from tests.helpers.load_state_tests import fetch_state_test_files

# Run legacy general state tests
test_dir = (
    "tests/fixtures/LegacyTests/Constantinople/BlockchainTests/"
    "GeneralStateTests/"
)

run_general_state_tests = partial(
    run_constantinople_blockchain_st_tests, test_dir
)

# Every test below takes more than  60s to run and
# hence they've been marked as slow
SLOW_TESTS = (
    "stRevertTest/RevertInCreateInInit_d0g0v0.json",
    "stSStoreTest/InitCollision_d0g0v0.json",
    "stExtCodeHash/extCodeHashDeletedAccount3_d0g0v0.json",
    "stExtCodeHash/extCodeHashCreatedAndDeletedAccountRecheckInOuterCall_d0g0v0.json",
    "stExtCodeHash/extCodeHashCreatedAndDeletedAccountStaticCall_d0g0v0.json",
    "stExtCodeHash/extCodeHashCreatedAndDeletedAccount_d0g0v0.json",
    "stExtCodeHash/extCodeHashInInitCode_d1g0v0.json",
    "stExtCodeHash/extCodeHashSubcallOOG_d0g0v0.json",
    "stExtCodeHash/extCodeHashSubcallOOG_d1g0v0.json",
    "stExtCodeHash/extCodeHashNewAccount_d0g0v0.json",
    "stExtCodeHash/dynamicAccountOverwriteEmpty_d0g0v0.json",
    "stExtCodeHash/codeCopyZero_d0g0v0.json",
    "stExtCodeHash/extCodeHashCreatedAndDeletedAccountCall_d0g0v0.json",
    "stExtCodeHash/extCodeHashSelfInInit_d0g0v0.json",
    "stExtCodeHash/extCodeHashSubcallOOG_d2g0v0.json",
    "stExtCodeHash/extCodeHashDeletedAccount4_d0g0v0.json",
    "stBadOpcode/badOpcodes_d110g0v0.json",
    "stCreate2/create2collisionCode_d0g0v0.json",
    "stCreate2/create2noCash_d0g0v0.json",
    "stCreate2/create2collisionCode_d1g0v0.json",
    "stCreate2/create2noCash_d1g0v0.json",
    "stCreate2/RevertDepthCreate2OOG_d1g1v0.json",
    "stCreate2/create2collisionBalance_d0g0v0.json",
    "stCreate2/create2collisionBalance_d1g0v0.json",
    "stCreate2/create2checkFieldsInInitcode_d6g0v0.json",
    "stCreate2/create2collisionSelfdestructed2_d1g0v0.json",
    "stCreate2/create2collisionSelfdestructed2_d0g0v0.json",
    "stCreate2/Create2OnDepth1024_d0g0v0.json",
    "stCreate2/create2collisionCode2_d1g0v0.json",
    "stCreate2/create2collisionCode2_d0g0v0.json",
    "stCreate2/returndatacopy_0_0_following_successful_create_d0g0v0.json",
    "stCreate2/Create2OOGafterInitCodeRevert_d0g0v0.json",
    "stCreate2/Create2OOGafterInitCode_d0g1v0.json",
    "stCreate2/CREATE2_Suicide_d8g0v0.json",
    "stCreate2/CREATE2_Suicide_d9g0v0.json",
    "stCreate2/create2InitCodes_d3g0v0.json",
    "stCreate2/create2InitCodes_d2g0v0.json",
    "stCreate2/CREATE2_Suicide_d11g0v0.json",
    "stCreate2/CREATE2_Suicide_d10g0v0.json",
    "stCreate2/RevertDepthCreate2OOG_d1g1v1.json",
    "stCreate2/create2callPrecompiles_d3g0v0.json",
    "stCreate2/create2callPrecompiles_d2g0v0.json",
    "stCreate2/create2InitCodes_d8g0v0.json",
    "stCreate2/create2collisionSelfdestructed_d2g0v0.json",
    "stCreate2/CREATE2_Suicide_d2g0v0.json",
    "stCreate2/CREATE2_Suicide_d3g0v0.json",
    "stCreate2/call_then_create2_successful_then_returndatasize_d0g0v0.json",
    "stCreate2/CreateMessageRevertedOOGInInit_d0g1v0.json",
    "stCreate2/create2InitCodes_d4g0v0.json",
    "stCreate2/create2InitCodes_d5g0v0.json",
    "stCreate2/RevertOpcodeInCreateReturnsCreate2_d0g0v0.json",
    "stCreate2/returndatacopy_following_revert_in_create_d0g0v0.json",
    "stCreate2/Create2OOGafterInitCodeReturndataSize_d0g0v0.json",
    "stCreate2/create2callPrecompiles_d4g0v0.json",
    "stCreate2/create2callPrecompiles_d5g0v0.json",
    "stCreate2/CreateMessageReverted_d0g1v0.json",
    "stCreate2/CREATE2_Suicide_d5g0v0.json",
    "stCreate2/CREATE2_Suicide_d4g0v0.json",
    "stCreate2/create2collisionStorage_d2g0v0.json",
    "stCreate2/create2collisionSelfdestructedRevert_d1g0v0.json",
    "stCreate2/create2collisionSelfdestructedRevert_d0g0v0.json",
    "stCreate2/returndatacopy_afterFailing_create_d0g0v0.json",
    "stCreate2/create2checkFieldsInInitcode_d0g0v0.json",
    "stCreate2/create2checkFieldsInInitcode_d1g0v0.json",
    "stCreate2/create2collisionNonce_d2g0v0.json",
    "stCreate2/create2callPrecompiles_d0g0v0.json",
    "stCreate2/create2callPrecompiles_d1g0v0.json",
    "stCreate2/create2collisionSelfdestructed_d0g0v0.json",
    "stCreate2/create2collisionSelfdestructed_d1g0v0.json",
    "stCreate2/CREATE2_Suicide_d1g0v0.json",
    "stCreate2/CREATE2_Suicide_d0g0v0.json",
    "stCreate2/returndatasize_following_successful_create_d0g0v0.json",
    "stCreate2/Create2OOGafterInitCodeReturndata2_d0g1v0.json",
    "stCreate2/create2SmartInitCode_d1g0v0.json",
    "stCreate2/create2SmartInitCode_d0g0v0.json",
    "stCreate2/create2InitCodes_d0g0v0.json",
    "stCreate2/create2InitCodes_d1g0v0.json",
    "stCreate2/create2checkFieldsInInitcode_d4g0v0.json",
    "stCreate2/create2checkFieldsInInitcode_d5g0v0.json",
    "stCreate2/create2collisionCode_d2g0v0.json",
    "stCreate2/create2collisionBalance_d3g0v0.json",
    "stCreate2/create2collisionBalance_d2g0v0.json",
    "stCreate2/Create2OOGafterInitCode_d0g0v0.json",
    "stCreate2/create2collisionNonce_d1g0v0.json",
    "stCreate2/CreateMessageReverted_d0g0v0.json",
    "stCreate2/create2collisionNonce_d0g0v0.json",
    "stCreate2/create2checkFieldsInInitcode_d2g0v0.json",
    "stCreate2/RevertOpcodeCreate_d0g0v0.json",
    "stCreate2/RevertDepthCreateAddressCollision_d1g1v1.json",
    "stCreate2/Create2OOGafterInitCodeRevert2_d0g0v0.json",
    "stCreate2/CREATE2_ContractSuicideDuringInit_ThenStoreThenReturn_d0g0v0.json",
    "stCreate2/create2collisionStorage_d0g0v0.json",
    "stCreate2/create2collisionStorage_d1g0v0.json",
    "stCreate2/CreateMessageRevertedOOGInInit_d0g0v0.json",
    "stCreate2/create2collisionSelfdestructedRevert_d2g0v0.json",
    "stCreate2/Create2OnDepth1023_d0g0v0.json",
    "stCreate2/create2callPrecompiles_d7g0v0.json",
    "stCreate2/create2callPrecompiles_d6g0v0.json",
    "stCreate2/CREATE2_Suicide_d6g0v0.json",
    "stCreate2/CREATE2_Suicide_d7g0v0.json",
    "stCreate2/RevertInCreateInInitCreate2_d0g0v0.json",
    "stCreate2/call_outsize_then_create2_successful_then_returndatasize_d0g0v0.json",
    "stCreate2/RevertDepthCreateAddressCollision_d1g1v0.json",
    "stCreate2/create2InitCodes_d7g0v0.json",
    "stCreate2/create2InitCodes_d6g0v0.json",
    "stSStoreTest/sstore_XtoXtoY_d4g0v0.json",
    "stSStoreTest/sstore_Xto0toXto0_d9g1v0.json",
    "stSStoreTest/sstore_Xto0toY_d4g0v0.json",
    "stSStoreTest/sstore_Xto0to0_d9g1v0.json",
    "stSStoreTest/sstore_XtoXto0_d9g1v0.json",
    "stSStoreTest/sstore_Xto0_d9g0v0.json",
    "stSStoreTest/sstore_0toXtoX_d4g0v0.json",
    "stSStoreTest/sstore_0to0_d9g0v0.json",
    "stSStoreTest/sstore_0to0toX_d4g0v0.json",
    "stSStoreTest/sstore_XtoYtoX_d4g1v0.json",
    "stSStoreTest/sstore_XtoY_d4g1v0.json",
    "stSStoreTest/sstore_XtoXtoX_d4g1v0.json",
    "stSStoreTest/InitCollisionNonZeroNonce_d2g0v0.json",
    "stSStoreTest/InitCollisionNonZeroNonce_d3g0v0.json",
    "stSStoreTest/sstore_Xto0toX_d4g1v0.json",
    "stSStoreTest/sstore_XtoYtoZ_d9g0v0.json",
    "stSStoreTest/sstore_0toXtoY_d4g1v0.json",
    "stSStoreTest/sstore_0toXto0toX_d9g1v0.json",
    "stSStoreTest/sstore_XtoYto0_d9g1v0.json",
    "stSStoreTest/sstore_0toX_d4g0v0.json",
    "stSStoreTest/sstore_XtoYtoY_d4g0v0.json",
    "stSStoreTest/sstore_0to0to0_d9g0v0.json",
    "stSStoreTest/sstore_changeFromExternalCallInInitCode_d7g0v0.json",
    "stSStoreTest/sstore_changeFromExternalCallInInitCode_d6g0v0.json",
    "stSStoreTest/sstore_XtoX_d4g0v0.json",
    "stSStoreTest/sstore_0toXto0_d9g0v0.json",
    "stSStoreTest/sstore_0toXto0toX_d4g1v0.json",
    "stSStoreTest/sstore_XtoYto0_d4g1v0.json",
    "stSStoreTest/sstore_XtoYtoZ_d4g0v0.json",
    "stSStoreTest/sstore_0toXtoY_d9g1v0.json",
    "stSStoreTest/sstore_XtoX_d9g0v0.json",
    "stSStoreTest/sstore_0toXto0_d4g0v0.json",
    "stSStoreTest/sstore_XtoYtoY_d9g0v0.json",
    "stSStoreTest/sstore_0toX_d9g0v0.json",
    "stSStoreTest/sstore_0to0to0_d4g0v0.json",
    "stSStoreTest/sstore_Xto0toX_d9g1v0.json",
    "stSStoreTest/sstore_XtoXtoX_d9g1v0.json",
    "stSStoreTest/sstore_changeFromExternalCallInInitCode_d1g0v0.json",
    "stSStoreTest/sstore_0to0_d4g0v0.json",
    "stSStoreTest/sstore_0to0toX_d9g0v0.json",
    "stSStoreTest/sstore_changeFromExternalCallInInitCode_d11g0v0.json",
    "stSStoreTest/sstore_changeFromExternalCallInInitCode_d10g0v0.json",
    "stSStoreTest/sstore_Xto0_d4g0v0.json",
    "stSStoreTest/sstore_0toXtoX_d9g0v0.json",
    "stSStoreTest/sstore_XtoY_d9g1v0.json",
    "stSStoreTest/InitCollision_d3g0v0.json",
    "stSStoreTest/InitCollision_d2g0v0.json",
    "stSStoreTest/sstore_XtoYtoX_d9g1v0.json",
    "stSStoreTest/sstore_Xto0toXto0_d4g1v0.json",
    "stSStoreTest/sstore_Xto0toY_d9g0v0.json",
    "stSStoreTest/sstore_XtoXtoY_d9g0v0.json",
    "stSStoreTest/sstore_XtoXto0_d4g1v0.json",
    "stSStoreTest/sstore_Xto0to0_d4g1v0.json",
    "stSStoreTest/sstore_XtoYtoX_d4g0v0.json",
    "stSStoreTest/sstore_XtoY_d4g0v0.json",
    "stSStoreTest/sstore_0toXtoX_d4g1v0.json",
    "stSStoreTest/sstore_Xto0_d9g1v0.json",
    "stSStoreTest/sstore_changeFromExternalCallInInitCode_d5g0v0.json",
    "stSStoreTest/sstore_0to0toX_d4g1v0.json",
    "stSStoreTest/sstore_0to0_d9g1v0.json",
    "stSStoreTest/sstore_Xto0to0_d9g0v0.json",
    "stSStoreTest/sstore_XtoXto0_d9g0v0.json",
    "stSStoreTest/InitCollisionNonZeroNonce_d1g0v0.json",
    "stSStoreTest/sstore_XtoXtoY_d4g1v0.json",
    "stSStoreTest/sstore_Xto0toY_d4g1v0.json",
    "stSStoreTest/sstore_Xto0toXto0_d9g0v0.json",
    "stSStoreTest/sstore_0to0to0_d9g1v0.json",
    "stSStoreTest/sstore_XtoYtoY_d4g1v0.json",
    "stSStoreTest/sstore_0toX_d4g1v0.json",
    "stSStoreTest/sstore_0toXto0_d9g1v0.json",
    "stSStoreTest/sstore_XtoX_d4g1v0.json",
    "stSStoreTest/sstore_0toXtoY_d4g0v0.json",
    "stSStoreTest/sstore_XtoYtoZ_d9g1v0.json",
    "stSStoreTest/sstore_0toXto0toX_d9g0v0.json",
    "stSStoreTest/sstore_XtoYto0_d9g0v0.json",
    "stSStoreTest/sstore_changeFromExternalCallInInitCode_d15g0v0.json",
    "stSStoreTest/sstore_changeFromExternalCallInInitCode_d14g0v0.json",
    "stSStoreTest/sstore_XtoXtoX_d4g0v0.json",
    "stSStoreTest/sstore_Xto0toX_d4g0v0.json",
    "stSStoreTest/sstore_Xto0toX_d9g0v0.json",
    "stSStoreTest/sstore_XtoXtoX_d9g0v0.json",
    "stSStoreTest/sstore_0toXto0_d4g1v0.json",
    "stSStoreTest/sstore_XtoX_d9g1v0.json",
    "stSStoreTest/sstore_changeFromExternalCallInInitCode_d13g0v0.json",
    "stSStoreTest/sstore_0to0to0_d4g1v0.json",
    "stSStoreTest/sstore_0toX_d9g1v0.json",
    "stSStoreTest/sstore_XtoYtoY_d9g1v0.json",
    "stSStoreTest/sstore_0toXto0toX_d4g0v0.json",
    "stSStoreTest/sstore_XtoYto0_d4g0v0.json",
    "stSStoreTest/InitCollision_d1g0v0.json",
    "stSStoreTest/sstore_0toXtoY_d9g0v0.json",
    "stSStoreTest/sstore_XtoYtoZ_d4g1v0.json",
    "stSStoreTest/sstore_XtoXto0_d4g0v0.json",
    "stSStoreTest/sstore_Xto0to0_d4g0v0.json",
    "stSStoreTest/sstore_Xto0toY_d9g1v0.json",
    "stSStoreTest/sstore_Xto0toXto0_d4g0v0.json",
    "stSStoreTest/sstore_XtoXtoY_d9g1v0.json",
    "stSStoreTest/sstore_changeFromExternalCallInInitCode_d3g0v0.json",
    "stSStoreTest/sstore_changeFromExternalCallInInitCode_d2g0v0.json",
    "stSStoreTest/sstore_XtoY_d9g0v0.json",
    "stSStoreTest/sstore_XtoYtoX_d9g0v0.json",
    "stSStoreTest/sstore_0to0toX_d9g1v0.json",
    "stSStoreTest/sstore_changeFromExternalCallInInitCode_d9g0v0.json",
    "stSStoreTest/sstore_0to0_d4g1v0.json",
    "stSStoreTest/sstore_0toXtoX_d9g1v0.json",
    "stSStoreTest/sstore_Xto0_d4g1v0.json",
)


@pytest.mark.parametrize(
    "test_file", fetch_state_test_files(test_dir, SLOW_TESTS, FIXTURES_LOADER)
)
def test_general_state_tests(test_file: str) -> None:
    try:
        run_general_state_tests(test_file)
    except KeyError:
        # FIXME: Handle tests that don't have post state
        pytest.xfail(f"{test_file} doesn't have post state")


# Run legacy valid block tests
test_dir = (
    "tests/fixtures/LegacyTests/Constantinople/BlockchainTests/ValidBlocks/"
)

run_valid_block_test = partial(
    run_constantinople_blockchain_st_tests,
    test_dir,
)


@pytest.mark.parametrize(
    "test_file_uncle_correctness",
    [
        "bcUncleTest/oneUncle.json",
        "bcUncleTest/oneUncleGeneration2.json",
        "bcUncleTest/oneUncleGeneration3.json",
        "bcUncleTest/oneUncleGeneration4.json",
        "bcUncleTest/oneUncleGeneration5.json",
        "bcUncleTest/oneUncleGeneration6.json",
        "bcUncleTest/twoUncle.json",
    ],
)
def test_uncles_correctness(test_file_uncle_correctness: str) -> None:
    run_valid_block_test(test_file_uncle_correctness)


# Run legacy invalid block tests
test_dir = (
    "tests/fixtures/LegacyTests/Constantinople/BlockchainTests/InvalidBlocks"
)

run_invalid_block_test = partial(
    run_constantinople_blockchain_st_tests,
    test_dir,
)


@pytest.mark.parametrize(
    "test_file", fetch_state_test_files(test_dir, (), FIXTURES_LOADER)
)
def test_invalid_block_tests(test_file: str) -> None:
    try:
        # Ideally correct.json should not have been in the InvalidBlocks folder
        if test_file == "bcUncleHeaderValidity/correct.json":
            run_invalid_block_test(test_file)
        elif test_file == "bcInvalidHeaderTest/GasLimitHigherThan2p63m1.json":
            # Unclear where this failed requirement comes from
            pytest.xfail()
        else:
            with pytest.raises(InvalidBlock):
                run_invalid_block_test(test_file)
    except KeyError:
        # FIXME: Handle tests that don't have post state
        pytest.xfail(f"{test_file} doesn't have post state")


# Run Non-Legacy GeneralStateTests
run_general_state_tests_new = partial(
    run_constantinople_blockchain_st_tests,
    "tests/fixtures/BlockchainTests/GeneralStateTests/",
)


@pytest.mark.parametrize(
    "test_file_new",
    [
        "stCreateTest/CREATE_HighNonce.json",
        "stCreateTest/CREATE_HighNonceMinus1.json",
    ],
)
def test_general_state_tests_new(test_file_new: str) -> None:
    try:
        run_general_state_tests_new(test_file_new)
    except KeyError:
        # KeyError is raised when a test_file has no tests for constantinople
        pytest.skip(f"{test_file_new} has no tests for constantinople")
