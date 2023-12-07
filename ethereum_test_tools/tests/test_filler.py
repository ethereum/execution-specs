"""
Test suite for `ethereum_test` module.
"""

import json
import os
from typing import Any, Dict, List

import pytest
from semver import Version

from ethereum_test_forks import Berlin, Fork, Istanbul, London, Merge, Shanghai
from evm_transition_tool import GethTransitionTool

from ..code import Yul
from ..common import Account, Environment, TestAddress, Transaction, to_json
from ..spec import BaseTestConfig, BlockchainTest, StateTest
from ..spec.blockchain.types import Block
from ..spec.blockchain.types import Fixture as BlockchainFixture
from .conftest import SOLC_PADDING_VERSION


def remove_info(fixture_json: Dict[str, Any]):  # noqa: D103
    for t in fixture_json:
        if "_info" in fixture_json[t]:
            del fixture_json[t]["_info"]


@pytest.fixture()
def hash(request: pytest.FixtureRequest, solc_version: Version):
    """
    Set the hash based on the fork and solc version.
    """
    if solc_version == Version.parse("0.8.20"):
        if request.node.funcargs["fork"] == Berlin:
            return bytes.fromhex("193e550de3")
        elif request.node.funcargs["fork"] == London:
            return bytes.fromhex("b053deac0e")
    else:
        if request.node.funcargs["fork"] == Berlin:
            return bytes.fromhex("f3a35d34f6")
        elif request.node.funcargs["fork"] == London:
            return bytes.fromhex("c5fa75d7f6")


@pytest.mark.parametrize(
    "fork,hash",
    [
        (Berlin, "set using indirect & hash fixture"),
        (London, "set using indirect & hash fixture"),
    ],
    indirect=["hash"],
)
def test_make_genesis(fork: Fork, hash: bytes):  # noqa: D103
    env = Environment()

    pre = {
        "0x1000000000000000000000000000000000000000": Account(
            balance=0x0BA1A9CE0BA1A9CE,
            code=Yul(
                """
            {
                function f(a, b) -> c {
                    c := add(a, b)
                }

                sstore(0, f(1, 2))
                return(0, 32)
            }
            """,
                fork=fork,
            ),
        ),
        TestAddress: Account(balance=0x0BA1A9CE0BA1A9CE),
    }

    t8n = GethTransitionTool()
    state_test = StateTest(env=env, pre=pre, post={}, txs=[], tag="some_state_test")
    fixture = state_test.generate(t8n, fork)
    assert fixture is not None
    assert isinstance(fixture, BlockchainFixture)
    assert fixture.genesis is not None

    assert fixture.genesis.hash is not None
    assert fixture.genesis.hash.startswith(hash)


@pytest.mark.parametrize(
    "fork,enable_hive,expected_json_file",
    [
        (Istanbul, False, "chainid_istanbul_filled.json"),
        (London, False, "chainid_london_filled.json"),
        (Merge, True, "chainid_merge_filled_hive.json"),
        (Shanghai, True, "chainid_shanghai_filled_hive.json"),
    ],
)
def test_fill_state_test(fork: Fork, expected_json_file: str, enable_hive: bool):
    """
    Test `ethereum_test.filler.fill_fixtures` with `StateTest`.
    """
    env = Environment(
        coinbase="0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba",
        difficulty=0x20000,
        gas_limit=10000000000,
        number=1,
        timestamp=1000,
    )

    pre = {
        0x1000000000000000000000000000000000000000: Account(code="0x4660015500"),
        "0xa94f5374fce5edbc8e2a8697c15331677e6ebf0b": Account(balance=1000000000000000000000),
    }

    tx = Transaction(
        ty=0x0,
        chain_id=0x0,
        nonce=0,
        to="0x1000000000000000000000000000000000000000",
        gas_limit=100000000,
        gas_price=10,
        protected=False,
    )

    post = {
        "0x1000000000000000000000000000000000000000": Account(
            code="0x4660015500", storage={"0x01": "0x01"}
        ),
    }

    state_test = StateTest(
        env=env,
        pre=pre,
        post=post,
        txs=[tx],
        tag="my_chain_id_test",
        base_test_config=BaseTestConfig(
            blockchain_test=True,
            enable_hive=enable_hive,
        ),
    )

    t8n = GethTransitionTool()

    fixture = {
        f"000/my_chain_id_test/{fork}": state_test.generate(
            t8n=t8n,
            fork=fork,
        ),
    }

    with open(
        os.path.join(
            "src",
            "ethereum_test_tools",
            "tests",
            "test_fixtures",
            expected_json_file,
        )
    ) as f:
        expected = json.load(f)

    fixture_json = to_json(fixture)
    remove_info(fixture_json)
    assert fixture_json == expected


@pytest.mark.parametrize(
    "fork,enable_hive,expected_json_file",
    [
        (London, False, "blockchain_london_valid_filled.json"),
        (Shanghai, True, "blockchain_shanghai_valid_filled_hive.json"),
    ],
)
def test_fill_blockchain_valid_txs(
    fork: Fork, solc_version: str, enable_hive: bool, expected_json_file: str
):
    """
    Test `ethereum_test.filler.fill_fixtures` with `BlockchainTest`.
    """
    pre = {
        "0xa94f5374fce5edbc8e2a8697c15331677e6ebf0b": Account(balance=0x1000000000000000000),
        "0xd02d72E067e77158444ef2020Ff2d325f929B363": Account(
            balance=0x1000000000000000000, nonce=1
        ),
        "0xcccccccccccccccccccccccccccccccccccccccc": Account(
            balance=0x10000000000,
            nonce=1,
            code=Yul(
                """
                {
                    sstore(number(), basefee())
                    sstore(add(number(), 0x1000), sub(gasprice(), basefee()))
                    sstore(add(number(), 0x2000), selfbalance())
                    stop()
                }
                """,
                fork=fork,
            ),
        ),
        "0xcccccccccccccccccccccccccccccccccccccccd": Account(
            balance=0x20000000000,
            nonce=1,
            code=Yul(
                """
                {
                    let throwMe := delegatecall(gas(),
                      0xcccccccccccccccccccccccccccccccccccccccc,
                      0, 0, 0, 0)
                }
                """,
                fork=fork,
            ),
        ),
        0xC0DE: Account(
            balance=0,
            nonce=1,
            code=Yul(
                """
                {
                    let throwMe := delegatecall(gas(),
                            0xcccccccccccccccccccccccccccccccccccccccc,
                            0, 0, 0, 0)
                }
                """,
                fork=fork,
            ),
        ),
        "0xccccccccccccccccccccccccccccccccccccccce": Account(
            balance=0x20000000000,
            nonce=1,
            code=Yul(
                """
                {
                    let throwMe := call(gas(), 0xC0DE, 0x1000,
                            0, 0, 0, 0)
                    throwMe := delegatecall(gas(),
                            0xcccccccccccccccccccccccccccccccccccccccc,
                            0, 0, 0, 0)
                }
                """,
                fork=fork,
            ),
        ),
    }

    blocks: List[Block] = [
        Block(
            coinbase="0xba5e000000000000000000000000000000000000",
            txs=[
                Transaction(
                    data="0x01",
                    nonce=0,
                    gas_limit=1000000,
                    max_priority_fee_per_gas=1,
                    max_fee_per_gas=1000,
                    to="0xCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCC",
                ),
            ],
        ),
        Block(
            coinbase="0xba5e000000000000000000000000000000000000",
            txs=[
                Transaction(
                    data="0x0201",
                    nonce=1,
                    gas_limit=1000000,
                    max_priority_fee_per_gas=10,
                    max_fee_per_gas=1000,
                    to="0xCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCC",
                ),
                Transaction(
                    data="0x0202",
                    nonce=2,
                    gas_limit=1000000,
                    max_priority_fee_per_gas=100,
                    max_fee_per_gas=1000,
                    to="0xCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCD",
                ),
                Transaction(
                    data="0x0203",
                    nonce=3,
                    gas_limit=1000000,
                    max_priority_fee_per_gas=100,
                    max_fee_per_gas=1000,
                    to="0xCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCE",
                ),
            ],
        ),
        Block(
            coinbase="0xba5e000000000000000000000000000000000000",
            txs=[
                Transaction(
                    data="0x0301",
                    nonce=4,
                    gas_limit=1000000,
                    max_priority_fee_per_gas=1000,
                    max_fee_per_gas=1000,
                    to="0xCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCC",
                ),
                Transaction(
                    data="0x0303",
                    nonce=5,
                    gas_limit=1000000,
                    max_priority_fee_per_gas=100,
                    max_fee_per_gas=1000,
                    to="0xCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCE",
                ),
                Transaction(
                    data="0x0304",
                    nonce=6,
                    gas_limit=1000000,
                    max_priority_fee_per_gas=100000,
                    max_fee_per_gas=100000,
                    to="0xCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCD",
                ),
            ],
        ),
        Block(
            coinbase="0xba5e000000000000000000000000000000000000",
            txs=[
                Transaction(
                    data="0x0401",
                    nonce=7,
                    gas_limit=1000000,
                    max_priority_fee_per_gas=1000,
                    max_fee_per_gas=1000,
                    to="0xCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCC",
                ),
                Transaction(
                    data="0x0403",
                    nonce=8,
                    gas_limit=1000000,
                    max_priority_fee_per_gas=100,
                    max_fee_per_gas=1000,
                    to="0xCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCE",
                ),
                Transaction(
                    data="0x0404",
                    nonce=9,
                    gas_limit=1000000,
                    max_priority_fee_per_gas=100000,
                    max_fee_per_gas=100000,
                    to="0xCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCD",
                ),
            ],
        ),
    ]

    post = {
        "0xCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCC": Account(
            storage={
                # BASEFEE and the tip in block 1
                0x0001: 875,  # BASEFEE
                0x1001: 1,  # tip
                # Block 2
                0x0002: 766,  # BASEFEE
                0x1002: 10,  # tip
                # Block 3
                0x0003: 671,
                0x1003: 329,
                # Block 4
                0x0004: 588,
                0x1004: 412,
                # SELFBALANCE, always the same
                0x2001: 0x010000000000,
                0x2002: 0x010000000000,
                0x2003: 0x010000000000,
                0x2004: 0x010000000000,
            }
        ),
        "0xCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCD": Account(
            storage={
                # Block 2
                0x0002: 766,  # BASEFEE
                0x1002: 100,  # tip
                # Block 3
                0x0003: 671,
                0x1003: 99329,
                # Block 4
                0x0004: 588,
                0x1004: 99412,
                # SELFBALANCE, always the same
                0x2002: 0x020000000000,
                0x2003: 0x020000000000,
                0x2004: 0x020000000000,
            }
        ),
        "0xCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCE": Account(
            storage={
                # Block 2
                0x0002: 766,  # BASEFEE
                0x1002: 100,  # tip
                0x0003: 671,
                0x1003: 100,
                0x0004: 588,
                0x1004: 100,
                # SELFBALANCE
                0x2002: 0x01FFFFFFF000,
                0x2003: 0x01FFFFFFE000,
                0x2004: 0x01FFFFFFD000,
            }
        ),
        0xC0DE: Account(
            storage={
                # Block 2
                0x0002: 766,
                0x1002: 100,
                # Block 3
                0x0003: 671,
                0x1003: 100,
                # Block 4
                0x0004: 588,
                0x1004: 100,
                # SELFBALANCE
                0x2002: 0x1000,
                0x2003: 0x2000,
                0x2004: 0x3000,
            }
        ),
    }

    # We start genesis with a baseFee of 1000
    genesis_environment = Environment(
        base_fee=1000,
        coinbase="0xba5e000000000000000000000000000000000000",
    )

    blockchain_test = BlockchainTest(
        pre=pre,
        post=post,
        blocks=blocks,
        genesis_environment=genesis_environment,
        tag="my_blockchain_test_valid_txs",
        base_test_config=BaseTestConfig(enable_hive=enable_hive),
    )

    t8n = GethTransitionTool()

    fixture = {
        f"000/my_blockchain_test/{fork.name()}": blockchain_test.generate(
            t8n=t8n,
            fork=fork,
        )
    }

    with open(
        os.path.join(
            "src",
            "ethereum_test_tools",
            "tests",
            "test_fixtures",
            expected_json_file,
        )
    ) as f:
        expected = json.load(f)

    fixture_json = to_json(fixture)
    remove_info(fixture_json)

    if solc_version >= SOLC_PADDING_VERSION:
        expected = expected["solc=padding_version"]
    else:
        expected = expected[f"solc={solc_version}"]

    assert fixture_json == expected


@pytest.mark.parametrize(
    "fork,enable_hive,expected_json_file",
    [
        (London, False, "blockchain_london_invalid_filled.json"),
        (Shanghai, True, "blockchain_shanghai_invalid_filled_hive.json"),
    ],
)
def test_fill_blockchain_invalid_txs(
    fork: Fork, solc_version: str, enable_hive: bool, expected_json_file: str
):
    """
    Test `ethereum_test.filler.fill_fixtures` with `BlockchainTest`.
    """
    pre = {
        "0xa94f5374fce5edbc8e2a8697c15331677e6ebf0b": Account(balance=0x1000000000000000000),
        "0xd02d72E067e77158444ef2020Ff2d325f929B363": Account(
            balance=0x1000000000000000000, nonce=1
        ),
        "0xcccccccccccccccccccccccccccccccccccccccc": Account(
            balance=0x10000000000,
            nonce=1,
            code=Yul(
                """
                {
                    sstore(number(), basefee())
                    sstore(add(number(), 0x1000), sub(gasprice(), basefee()))
                    sstore(add(number(), 0x2000), selfbalance())
                    stop()
                }
                """,
                fork=fork,
            ),
        ),
        "0xcccccccccccccccccccccccccccccccccccccccd": Account(
            balance=0x20000000000,
            nonce=1,
            code=Yul(
                """
                {
                    let throwMe := delegatecall(gas(),
                      0xcccccccccccccccccccccccccccccccccccccccc,
                      0, 0, 0, 0)
                }
                """,
                fork=fork,
            ),
        ),
        0xC0DE: Account(
            balance=0,
            nonce=1,
            code=Yul(
                """
                {
                    let throwMe := delegatecall(gas(),
                            0xcccccccccccccccccccccccccccccccccccccccc,
                            0, 0, 0, 0)
                }
                """,
                fork=fork,
            ),
        ),
        "0xccccccccccccccccccccccccccccccccccccccce": Account(
            balance=0x20000000000,
            nonce=1,
            code=Yul(
                """
                {
                    let throwMe := call(gas(), 0xC0DE, 0x1000,
                            0, 0, 0, 0)
                    throwMe := delegatecall(gas(),
                            0xcccccccccccccccccccccccccccccccccccccccc,
                            0, 0, 0, 0)
                }
                """,
                fork=fork,
            ),
        ),
    }

    blocks: List[Block] = [
        Block(
            coinbase="0xba5e000000000000000000000000000000000000",
            txs=[
                Transaction(
                    data="0x01",
                    nonce=0,
                    gas_limit=1000000,
                    max_priority_fee_per_gas=1,
                    max_fee_per_gas=1000,
                    to="0xCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCC",
                ),
            ],
        ),
        Block(
            coinbase="0xba5e000000000000000000000000000000000000",
            txs=[
                Transaction(
                    data="0x0201",
                    nonce=1,
                    gas_limit=1000000,
                    max_priority_fee_per_gas=10,
                    max_fee_per_gas=1000,
                    to="0xCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCC",
                ),
                Transaction(
                    data="0x0202",
                    nonce=2,
                    gas_limit=1000000,
                    max_priority_fee_per_gas=100,
                    max_fee_per_gas=1000,
                    to="0xCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCD",
                ),
                Transaction(
                    data="0x0203",
                    nonce=3,
                    gas_limit=1000000,
                    max_priority_fee_per_gas=100,
                    max_fee_per_gas=1000,
                    to="0xCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCE",
                ),
            ],
        ),
        Block(
            coinbase="0xba5e000000000000000000000000000000000000",
            txs=[
                Transaction(
                    data="0x0301",
                    nonce=4,
                    gas_limit=1000000,
                    max_priority_fee_per_gas=1000,
                    max_fee_per_gas=1000,
                    to="0xCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCC",
                ),
                Transaction(
                    data="0x0302",
                    nonce=5,
                    gas_limit=1000000,
                    max_priority_fee_per_gas=100000,
                    max_fee_per_gas=1000,
                    to="0xCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCD",
                    error="TR_TipGtFeeCap",
                ),
            ],
            exception="invalid transaction",
        ),
        Block(
            coinbase="0xba5e000000000000000000000000000000000000",
            txs=[
                Transaction(
                    data="0x0301",
                    nonce=4,
                    gas_limit=1000000,
                    max_priority_fee_per_gas=1000,
                    max_fee_per_gas=1000,
                    to="0xCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCC",
                ),
                Transaction(
                    data="0x0303",
                    nonce=5,
                    gas_limit=1000000,
                    max_priority_fee_per_gas=100,
                    max_fee_per_gas=1000,
                    to="0xCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCE",
                ),
                Transaction(
                    data="0x0304",
                    nonce=6,
                    gas_limit=1000000,
                    max_priority_fee_per_gas=100000,
                    max_fee_per_gas=100000,
                    to="0xCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCD",
                ),
            ],
        ),
        Block(
            coinbase="0xba5e000000000000000000000000000000000000",
            txs=[
                Transaction(
                    data="0x0401",
                    nonce=7,
                    gas_limit=1000000,
                    max_priority_fee_per_gas=1000,
                    max_fee_per_gas=1000,
                    to="0xCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCC",
                ),
                Transaction(
                    data="0x0402",
                    nonce=8,
                    gas_limit=1000000,
                    max_priority_fee_per_gas=100000,
                    max_fee_per_gas=1000,
                    to="0xCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCD",
                    error="TR_TipGtFeeCap",
                ),
            ],
            exception="invalid transaction",
        ),
        Block(
            coinbase="0xba5e000000000000000000000000000000000000",
            txs=[
                Transaction(
                    data="0x0401",
                    nonce=7,
                    gas_limit=1000000,
                    max_priority_fee_per_gas=1000,
                    max_fee_per_gas=1000,
                    to="0xCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCC",
                ),
                Transaction(
                    data="0x0403",
                    nonce=8,
                    gas_limit=1000000,
                    max_priority_fee_per_gas=100,
                    max_fee_per_gas=1000,
                    to="0xCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCE",
                ),
                Transaction(
                    data="0x0404",
                    nonce=9,
                    gas_limit=1000000,
                    max_priority_fee_per_gas=100000,
                    max_fee_per_gas=100000,
                    to="0xCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCD",
                ),
            ],
        ),
    ]

    post = {
        "0xCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCC": Account(
            storage={
                # BASEFEE and the tip in block 1
                0x0001: 875,  # BASEFEE
                0x1001: 1,  # tip
                # Block 2
                0x0002: 766,  # BASEFEE
                0x1002: 10,  # tip
                # Block 3
                0x0003: 671,
                0x1003: 329,
                # Block 4
                0x0004: 588,
                0x1004: 412,
                # SELFBALANCE, always the same
                0x2001: 0x010000000000,
                0x2002: 0x010000000000,
                0x2003: 0x010000000000,
                0x2004: 0x010000000000,
            }
        ),
        "0xCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCD": Account(
            storage={
                # Block 2
                0x0002: 766,  # BASEFEE
                0x1002: 100,  # tip
                # Block 3
                0x0003: 671,
                0x1003: 99329,
                # Block 4
                0x0004: 588,
                0x1004: 99412,
                # SELFBALANCE, always the same
                0x2002: 0x020000000000,
                0x2003: 0x020000000000,
                0x2004: 0x020000000000,
            }
        ),
        "0xCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCE": Account(
            storage={
                # Block 2
                0x0002: 766,  # BASEFEE
                0x1002: 100,  # tip
                0x0003: 671,
                0x1003: 100,
                0x0004: 588,
                0x1004: 100,
                # SELFBALANCE
                0x2002: 0x01FFFFFFF000,
                0x2003: 0x01FFFFFFE000,
                0x2004: 0x01FFFFFFD000,
            }
        ),
        0xC0DE: Account(
            storage={
                # Block 2
                0x0002: 766,
                0x1002: 100,
                # Block 3
                0x0003: 671,
                0x1003: 100,
                # Block 4
                0x0004: 588,
                0x1004: 100,
                # SELFBALANCE
                0x2002: 0x1000,
                0x2003: 0x2000,
                0x2004: 0x3000,
            }
        ),
    }

    # We start genesis with a baseFee of 1000
    genesis_environment = Environment(
        base_fee=1000,
        coinbase="0xba5e000000000000000000000000000000000000",
    )

    blockchain_test = BlockchainTest(
        pre=pre,
        post=post,
        blocks=blocks,
        genesis_environment=genesis_environment,
        base_test_config=BaseTestConfig(enable_hive=enable_hive),
    )

    t8n = GethTransitionTool()

    fixture = {
        f"000/my_blockchain_test/{fork.name()}": blockchain_test.generate(
            t8n=t8n,
            fork=fork,
        )
    }

    with open(
        os.path.join(
            "src",
            "ethereum_test_tools",
            "tests",
            "test_fixtures",
            expected_json_file,
        )
    ) as f:
        expected = json.load(f)

    fixture_json = to_json(fixture)
    remove_info(fixture_json)

    if solc_version >= SOLC_PADDING_VERSION:
        expected = expected["solc=padding_version"]
    else:
        expected = expected[f"solc={solc_version}"]

    assert fixture_json == expected
