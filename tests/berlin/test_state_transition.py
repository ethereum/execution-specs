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
    fetch_state_test_files,
    idfn,
    run_blockchain_st_test,
)

fetch_berlin_tests = partial(fetch_state_test_files, network="Berlin")

FIXTURES_LOADER = Load("Berlin", "berlin")

run_berlin_blockchain_st_tests = partial(
    run_blockchain_st_test, load=FIXTURES_LOADER
)

ETHEREUM_TESTS_PATH = TEST_FIXTURES["ethereum_tests"]["fixture_path"]

# Run state tests
test_dir = f"{ETHEREUM_TESTS_PATH}/BlockchainTests/"

# Every test below takes more than  60s to run and
# hence they've been marked as slow
SLOW_TESTS = (
    # GeneralStateTests
    "stTimeConsuming/CALLBlake2f_MaxRounds.json",
    "stTimeConsuming/static_Call50000_sha256.json",
    "vmPerformance/loopExp.json",
    "vmPerformance/loopMul.json",
    "QuadraticComplexitySolidity_CallDataCopy_d0g1v0_Berlin",
    "CALLBlake2f_d9g0v0_Berlin",
    "CALLCODEBlake2f_d9g0v0",
    "stRandom/randomStatetest177.json",
    "stCreateTest/CreateOOGafterMaxCodesize.json",
    # ValidBlockTest
    "bcExploitTest/DelegateCallSpam.json",
    # InvalidBlockTest
    "bcUncleHeaderValidity/nonceWrong.json",
    "bcUncleHeaderValidity/wrongMixHash.json",
)

# These are tests that are considered to be incorrect,
# Please provide an explanation when adding entries
IGNORE_TESTS = (
    # ValidBlockTest
    "bcForkStressTest/ForkStressTest.json",
    "bcGasPricerTest/RPC_API_Test.json",
    "bcMultiChainTest",
    "bcTotalDifficultyTest",
    # InvalidBlockTest
    "bcForgedTest",
    "bcMultiChainTest",
    "GasLimitHigherThan2p63m1_Berlin",
    # TODO: The below tests are being ignored due to a bug in
    # upstream repo. They should be removed from the ignore list
    # once the bug is resolved
    # See: https://github.com/ethereum/execution-spec-tests/pull/134
    "Pyspecs/vm/dup.json",
    "Pyspecs/vm/chain_id.json",
    "Pyspecs/example/yul.json",
)

# All tests that recursively create a large number of frames (50000)
BIG_MEMORY_TESTS = (
    "50000_",
    "/stQuadraticComplexityTest/",
    "/stRandom2/",
    "/stRandom/",
    "/stSpecialTest/",
    "stTimeConsuming/",
)

fetch_state_tests = partial(
    fetch_berlin_tests,
    test_dir,
    ignore_list=IGNORE_TESTS,
    slow_list=SLOW_TESTS,
    big_memory_list=BIG_MEMORY_TESTS,
)


@pytest.mark.parametrize(
    "test_case",
    fetch_state_tests(),
    ids=idfn,
)
def test_general_state_tests(test_case: Dict) -> None:
    run_berlin_blockchain_st_tests(test_case)


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

    assert rlp.rlp_hash(genesis_header) == genesis_header_hash

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

    tx = FIXTURES_LOADER.fork.LegacyTransaction(
        nonce=U256(0x00),
        gas_price=U256(1000),
        gas=U256(150000),
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
        number=genesis_block.header.number + 1,
        gas_limit=genesis_block.header.gas_limit,
        gas_price=tx.gas_price,
        time=genesis_block.header.timestamp,
        difficulty=genesis_block.header.difficulty,
        state=state,
        chain_id=Uint(1),
        traces=[],
    )

    with pytest.raises(InvalidBlock):
        FIXTURES_LOADER.fork.process_transaction(env, tx)
