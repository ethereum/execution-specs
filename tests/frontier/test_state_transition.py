from functools import partial
from typing import Dict

import pytest
from ethereum_rlp import rlp
from ethereum_types.bytes import Bytes, Bytes8, Bytes32
from ethereum_types.numeric import U256, Uint

from ethereum.crypto.hash import Hash32, keccak256
from ethereum.exceptions import InvalidBlock
from tests.helpers import TEST_FIXTURES
from tests.helpers.load_state_tests import (
    Load,
    fetch_state_test_files,
    idfn,
    run_blockchain_st_test,
)

fetch_frontier_tests = partial(fetch_state_test_files, network="Frontier")

FIXTURES_LOADER = Load("Frontier", "frontier")

run_frontier_blockchain_st_tests = partial(
    run_blockchain_st_test, load=FIXTURES_LOADER
)

ETHEREUM_TESTS_PATH = TEST_FIXTURES["ethereum_tests"]["fixture_path"]


# Run legacy general state tests
legacy_test_dir = (
    f"{ETHEREUM_TESTS_PATH}/LegacyTests/Constantinople/BlockchainTests/"
)

LEGACY_IGNORE_LIST = (
    # Valid block tests to be ignored
    "bcForkStressTest/ForkStressTest.json",
    "bcGasPricerTest/RPC_API_Test.json",
    "bcMultiChainTest/",
    "bcTotalDifficultyTest/",
    "stTimeConsuming/",
    # Invalid block tests to be ignored
    "bcForgedTest",
    "bcMultiChainTest",
    # TODO: See https://github.com/ethereum/tests/issues/1218
    "GasLimitHigherThan2p63m1_Frontier",
)

LEGACY_BIG_MEMORY_TESTS = (
    "/stQuadraticComplexityTest/",
    "/stRandom2/",
    "/stRandom/",
    "/stSpecialTest/",
)

SLOW_LIST = (
    # InvalidBlockTest
    "bcUncleHeaderValidity/nonceWrong.json",
    "bcUncleHeaderValidity/wrongMixHash.json",
)

fetch_legacy_state_tests = partial(
    fetch_frontier_tests,
    legacy_test_dir,
    ignore_list=LEGACY_IGNORE_LIST,
    slow_list=SLOW_LIST,
    big_memory_list=LEGACY_BIG_MEMORY_TESTS,
)


@pytest.mark.parametrize(
    "test_case",
    fetch_legacy_state_tests(),
    ids=idfn,
)
def test_legacy_state_tests(test_case: Dict) -> None:
    run_frontier_blockchain_st_tests(test_case)


# Run Non-Legacy Tests
non_legacy_test_dir = (
    f"{ETHEREUM_TESTS_PATH}/BlockchainTests/GeneralStateTests/"
)

non_legacy_only_in = (
    "stCreateTest/CREATE_HighNonce.json",
    "stCreateTest/CREATE_HighNonceMinus1.json",
)


@pytest.mark.parametrize(
    "test_case",
    fetch_frontier_tests(non_legacy_test_dir, only_in=non_legacy_only_in),
    ids=idfn,
)
def test_non_legacy_tests(test_case: Dict) -> None:
    run_frontier_blockchain_st_tests(test_case)


def test_transaction_with_insufficient_balance_for_value() -> None:
    genesis_header = FIXTURES_LOADER.fork.Header(
        parent_hash=Hash32([0] * 32),
        ommers_hash=Hash32.fromhex(
            "1dcc4de8dec75d7aab85b567b6ccd41ad312451b948a7413f0a142fd40d49347"
        ),
        coinbase=FIXTURES_LOADER.fork.hex_to_address(
            "8888f1f195afa192cfee860698584c030f4c9db1"
        ),
        state_root=FIXTURES_LOADER.fork.hex_to_root(
            "d84598d90e2a72125c111171717f5508fd40ed0d0cd067ceb4e734d4da3a810a"
        ),
        transactions_root=FIXTURES_LOADER.fork.hex_to_root(
            "56e81f171bcc55a6ff8345e692c0f86e5b48e01b996cadc001622fb5e363b421"
        ),
        receipt_root=FIXTURES_LOADER.fork.hex_to_root(
            "56e81f171bcc55a6ff8345e692c0f86e5b48e01b996cadc001622fb5e363b421"
        ),
        bloom=FIXTURES_LOADER.fork.Bloom([0] * 256),
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

    assert keccak256(rlp.encode(genesis_header)) == genesis_header_hash

    genesis_block = FIXTURES_LOADER.fork.Block(
        genesis_header,
        (),
        (),
    )

    state = FIXTURES_LOADER.fork.State()

    address = FIXTURES_LOADER.fork.hex_to_address(
        "a94f5374fce5edbc8e2a8697c15331677e6ebf0b"
    )

    account = FIXTURES_LOADER.fork.Account(
        nonce=Uint(0),
        balance=U256(0x056BC75E2D63100000),
        code=Bytes(),
    )

    FIXTURES_LOADER.fork.set_account(state, address, account)

    tx = FIXTURES_LOADER.fork.Transaction(
        nonce=U256(0x00),
        gas_price=Uint(1000),
        gas=Uint(150000),
        to=FIXTURES_LOADER.fork.hex_to_address(
            "c94f5374fce5edbc8e2a8697c15331677e6ebf0b"
        ),
        value=U256(1000000000000000000000),
        data=Bytes(),
        v=U256(0),
        r=U256(0),
        s=U256(0),
    )

    env = FIXTURES_LOADER.fork.Environment(
        caller=address,
        origin=address,
        block_hashes=[genesis_header_hash],
        coinbase=genesis_block.header.coinbase,
        number=genesis_block.header.number + Uint(1),
        gas_limit=genesis_block.header.gas_limit,
        gas_price=tx.gas_price,
        time=genesis_block.header.timestamp,
        difficulty=genesis_block.header.difficulty,
        state=state,
        traces=[],
    )

    with pytest.raises(InvalidBlock):
        FIXTURES_LOADER.fork.process_transaction(env, tx)
