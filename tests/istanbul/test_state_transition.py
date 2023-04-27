from functools import partial
from typing import Dict

import pytest

from ethereum import rlp
from ethereum.base_types import U256, Bytes, Bytes8, Bytes32, Uint
from ethereum.crypto.hash import Hash32
from ethereum.exceptions import InvalidBlock
from tests.helpers import TEST_FIXTURES
from tests.helpers.load_state_tests import (
    Load,
    NoPostState,
    fetch_state_test_files,
    idfn,
    run_blockchain_st_test,
)

fetch_istanbul_tests = partial(fetch_state_test_files, network="Istanbul")

FIXTURES_LOADER = Load("Istanbul", "istanbul")

run_istanbul_blockchain_st_tests = partial(
    run_blockchain_st_test, load=FIXTURES_LOADER
)

ETHEREUM_TESTS_PATH = TEST_FIXTURES["ethereum_tests"]["fixture_path"]

# Run legacy general state tests
test_dir = f"{ETHEREUM_TESTS_PATH}/BlockchainTests/GeneralStateTests/"

# Every test below takes more than  60s to run and
# hence they've been marked as slow
GENERAL_STATE_SLOW_TESTS = (
    "stTimeConsuming/CALLBlake2f_MaxRounds.json",
    "stTimeConsuming/static_Call50000_sha256.json",
    "vmPerformance/loopExp.json",
    "vmPerformance/loopMul.json",
    "QuadraticComplexitySolidity_CallDataCopy_d0g1v0_Istanbul",
    "CALLBlake2f_d9g0v0_Istanbul",
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
)

fetch_general_state_tests = partial(
    fetch_istanbul_tests,
    test_dir,
    ignore_list=INCORRECT_UPSTREAM_STATE_TESTS,
    slow_list=GENERAL_STATE_SLOW_TESTS,
    big_memory_list=GENERAL_STATE_BIG_MEMORY_TESTS,
)


@pytest.mark.parametrize(
    "test_case",
    fetch_general_state_tests(),
    ids=idfn,
)
def test_general_state_tests(test_case: Dict) -> None:
    try:
        run_istanbul_blockchain_st_tests(test_case)
    except NoPostState:
        # FIXME: Handle tests that don't have post state
        pytest.xfail(f"{test_case} doesn't have post state")


# Run legacy valid block tests
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
    fetch_istanbul_tests(
        test_dir,
        ignore_list=IGNORE_LIST,
        slow_list=VALID_BLOCKS_SLOW_TESTS,
    ),
    ids=idfn,
)
def test_valid_block_tests(test_case: Dict) -> None:
    try:
        run_istanbul_blockchain_st_tests(test_case)
    except NoPostState:
        # FIXME: Handle tests that don't have post state
        pytest.xfail(f"{test_case} doesn't have post state")


# Run legacy invalid block tests
test_dir = f"{ETHEREUM_TESTS_PATH}/BlockchainTests/InvalidBlocks"

# TODO: Handle once https://github.com/ethereum/tests/issues/1037
# is resolved
# All except GasLimitHigherThan2p63m1_Istanbul
xfail_candidates = (
    ("bcUncleHeaderValidity", "timestampTooLow_Istanbul"),
    ("bcUncleHeaderValidity", "timestampTooHigh_Istanbul"),
    ("bcUncleHeaderValidity", "wrongStateRoot_Istanbul"),
    ("bcUncleHeaderValidity", "incorrectUncleTimestamp4_Istanbul"),
    ("bcUncleHeaderValidity", "incorrectUncleTimestamp5_Istanbul"),
    ("bcUncleSpecialTests", "futureUncleTimestamp3_Istanbul"),
    ("bcInvalidHeaderTest", "GasLimitHigherThan2p63m1_Istanbul"),
)

# FIXME: Check if these tests should in fact be ignored
IGNORE_INVALID_BLOCK_TESTS = ("bcForgedTest", "bcMultiChainTest")


def is_in_xfail(test_case: Dict) -> bool:
    for dir, test_key in xfail_candidates:
        if dir in test_case["test_file"] and test_case["test_key"] == test_key:
            return True

    return False


@pytest.mark.parametrize(
    "test_case",
    fetch_istanbul_tests(
        test_dir,
        ignore_list=IGNORE_INVALID_BLOCK_TESTS,
    ),
    ids=idfn,
)
def test_invalid_block_tests(test_case: Dict) -> None:
    try:
        # Ideally correct.json should not have been in the InvalidBlocks folder
        if test_case["test_key"] == "correct_Istanbul":
            run_istanbul_blockchain_st_tests(test_case)
        elif is_in_xfail(test_case):
            # Unclear where this failed requirement comes from
            pytest.xfail()
        else:
            with pytest.raises(InvalidBlock):
                run_istanbul_blockchain_st_tests(test_case)
    except NoPostState:
        # FIXME: Handle tests that don't have post state
        pytest.xfail(
            "{} doesn't have post state".format(test_case["test_key"])
        )


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
        chain_id=Uint(1),
    )

    with pytest.raises(InvalidBlock):
        FIXTURES_LOADER.process_transaction(env, tx)
