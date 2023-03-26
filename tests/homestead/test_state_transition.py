import os
from functools import partial
from typing import Dict

import pytest

from ethereum import rlp
from ethereum.base_types import U256, Bytes, Bytes8, Bytes32, Uint
from ethereum.crypto.hash import Hash32
from ethereum.exceptions import InvalidBlock
from tests.helpers.load_state_tests import (
    Load,
    NoPostState,
    fetch_state_test_files,
    idfn,
    run_blockchain_st_test,
)

fetch_homestead_tests = partial(fetch_state_test_files, network="Homestead")

FIXTURES_LOADER = Load("Homestead", "homestead")

run_homestead_blockchain_st_tests = partial(
    run_blockchain_st_test, load=FIXTURES_LOADER
)


# Run legacy general state tests
test_dir = os.path.join(
    os.environ["ETHEREUM_TESTS"],
    "LegacyTests/Constantinople/BlockchainTests/GeneralStateTests/",
)

# Every test below takes more than  60s to run and
# hence they've been marked as slow
GENERAL_STATE_SLOW_TESTS = (
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


# These are tests that are considered to be incorrect,
# Please provide an explanation when adding entries
INCORRECT_UPSTREAM_STATE_TESTS = ()

GENERAL_STATE_BIG_MEMORY_TESTS = (
    "/stQuadraticComplexityTest/",
    "/stRandom2/",
    "/stRandom/",
    "/stSpecialTest/",
    "stTimeConsuming/",
)


@pytest.mark.parametrize(
    "test_case",
    fetch_homestead_tests(
        test_dir,
        slow_list=GENERAL_STATE_SLOW_TESTS,
        big_memory_list=GENERAL_STATE_BIG_MEMORY_TESTS,
    ),
    ids=idfn,
)
def test_general_state_tests(test_case: Dict) -> None:
    try:
        run_homestead_blockchain_st_tests(test_case)
    except NoPostState:
        # FIXME: Handle tests that don't have post state
        pytest.xfail(f"{test_case} doesn't have post state")


# Run legacy valid block tests
test_dir = os.path.join(
    os.environ["ETHEREUM_TESTS"],
    "LegacyTests/Constantinople/BlockchainTests/ValidBlocks/",
)

IGNORE_LIST = (
    "bcForkStressTest/ForkStressTest.json",
    "bcGasPricerTest/RPC_API_Test.json",
    "bcMultiChainTest/",
    "bcTotalDifficultyTest/",
)

# Every test below takes more than  60s to run and
# hence they've been marked as slow
VALID_BLOCKS_SLOW_TESTS = ("bcExploitTest/DelegateCallSpam.json",)

VALID_BLOCKS_BIG_MEMORY_TESTS = ("randomStatetest94_",)


@pytest.mark.parametrize(
    "test_case",
    fetch_homestead_tests(
        test_dir,
        ignore_list=IGNORE_LIST,
        slow_list=VALID_BLOCKS_SLOW_TESTS,
        big_memory_list=VALID_BLOCKS_BIG_MEMORY_TESTS,
    ),
    ids=idfn,
)
def test_valid_block_tests(test_case: Dict) -> None:
    try:
        run_homestead_blockchain_st_tests(test_case)
    except NoPostState:
        # FIXME: Handle tests that don't have post state
        pytest.xfail(f"{test_case} doesn't have post state")


# Run legacy invalid block tests
test_dir = os.path.join(
    os.environ["ETHEREUM_TESTS"],
    "LegacyTests/Constantinople/BlockchainTests/InvalidBlocks",
)

xfail_candidates = ("GasLimitHigherThan2p63m1_Homestead",)

# FIXME: Check if these tests should in fact be ignored
IGNORE_INVALID_BLOCK_TESTS = ("bcForgedTest", "bcMultiChainTest")


@pytest.mark.parametrize(
    "test_case",
    fetch_homestead_tests(test_dir, ignore_list=IGNORE_INVALID_BLOCK_TESTS),
    ids=idfn,
)
def test_invalid_block_tests(test_case: Dict) -> None:
    try:
        # Ideally correct.json should not have been in the InvalidBlocks folder
        if test_case["test_key"] == "correct_Homestead":
            run_homestead_blockchain_st_tests(test_case)
        elif test_case["test_key"] in xfail_candidates:
            # Unclear where this failed requirement comes from
            pytest.xfail()
        else:
            with pytest.raises(InvalidBlock):
                run_homestead_blockchain_st_tests(test_case)
    except NoPostState:
        # FIXME: Handle tests that don't have post state
        pytest.xfail(
            "{} doesn't have post state".format(test_case["test_key"])
        )


# Run Non-Legacy GeneralStateTests
test_dir = os.path.join(
    os.environ["ETHEREUM_TESTS"],
    "BlockchainTests/GeneralStateTests/",
)

non_legacy_only_in = (
    "stCreateTest/CREATE_HighNonce.json",
    "stCreateTest/CREATE_HighNonceMinus1.json",
)


@pytest.mark.parametrize(
    "test_case",
    fetch_homestead_tests(test_dir, only_in=non_legacy_only_in),
    ids=idfn,
)
def test_general_state_tests_new(test_case: Dict) -> None:
    run_homestead_blockchain_st_tests(test_case)


def test_transaction_with_insufficient_balance_for_value() -> None:
    genesis_header = FIXTURES_LOADER.Header(
        parent_hash=Hash32([0] * 32),
        ommers_hash=Hash32.fromhex(
            "1dcc4de8dec75d7aab85b567b6ccd41ad312451b948a7413f0a142fd40d49347"
        ),
        coinbase=FIXTURES_LOADER.hex_to_address(
            "8888f1f195afa192cfee860698584c030f4c9db1"
        ),
        state_root=FIXTURES_LOADER.hex_to_root(
            "d84598d90e2a72125c111171717f5508fd40ed0d0cd067ceb4e734d4da3a810a"
        ),
        transactions_root=FIXTURES_LOADER.hex_to_root(
            "56e81f171bcc55a6ff8345e692c0f86e5b48e01b996cadc001622fb5e363b421"
        ),
        receipt_root=FIXTURES_LOADER.hex_to_root(
            "56e81f171bcc55a6ff8345e692c0f86e5b48e01b996cadc001622fb5e363b421"
        ),
        bloom=FIXTURES_LOADER.Bloom([0] * 256),
        difficulty=Uint(0x020000),
        number=Uint(0x00),
        gas_limit=Uint(0x2FEFD8),
        gas_used=Uint(0x00),
        timestamp=U256(0x54C98C81),
        extra_data=Bytes([0x42]),
        mix_digest=Bytes32([0] * 32),
        nonce=Bytes8([0] * 8),
    )

    genesis_header_hash = bytes.fromhex(
        "0b22b0d49035cb4f8a969d584f36126e0ac6996b9db7264ac5a192b8698177eb"
    )

    assert rlp.rlp_hash(genesis_header) == genesis_header_hash

    genesis_block = FIXTURES_LOADER.Block(
        genesis_header,
        (),
        (),
    )

    state = FIXTURES_LOADER.State()

    address = FIXTURES_LOADER.hex_to_address(
        "a94f5374fce5edbc8e2a8697c15331677e6ebf0b"
    )

    account = FIXTURES_LOADER.Account(
        nonce=Uint(0),
        balance=U256(0x056BC75E2D63100000),
        code=Bytes(),
    )

    FIXTURES_LOADER.set_account(state, address, account)

    tx = FIXTURES_LOADER.LegacyTransaction(
        nonce=U256(0x00),
        gas_price=U256(1000),
        gas=U256(150000),
        to=FIXTURES_LOADER.hex_to_address(
            "c94f5374fce5edbc8e2a8697c15331677e6ebf0b"
        ),
        value=U256(1000000000000000000000),
        data=Bytes(),
        v=U256(0),
        r=U256(0),
        s=U256(0),
    )

    env = FIXTURES_LOADER.Environment(
        caller=address,
        origin=address,
        block_hashes=[genesis_header_hash],
        coinbase=genesis_block.header.coinbase,
        number=genesis_block.header.number + 1,
        gas_limit=genesis_block.header.gas_limit,
        gas_price=tx.gas_price,
        time=genesis_block.header.timestamp,
        difficulty=genesis_block.header.difficulty,
        state=state,
    )

    with pytest.raises(InvalidBlock):
        FIXTURES_LOADER.process_transaction(env, tx)
