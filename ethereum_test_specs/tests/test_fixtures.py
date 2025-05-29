"""Test suite for `ethereum_test_specs` fixture generation."""

import json
import os
from typing import Any, List, Mapping

import pytest
from click.testing import CliRunner

import cli.check_fixtures
from ethereum_clis import TransitionTool
from ethereum_test_base_types import AccessList, Account, Address, Hash
from ethereum_test_exceptions import TransactionException
from ethereum_test_fixtures import (
    BlockchainEngineFixture,
    BlockchainFixture,
    BlockchainFixtureCommon,
    FixtureFormat,
    StateFixture,
)
from ethereum_test_forks import Berlin, Cancun, Fork, Istanbul, London, Paris, Shanghai
from ethereum_test_types import Alloc, Environment, Transaction, TransactionType
from ethereum_test_vm import Opcodes as Op

from ..blockchain import Block, BlockchainTest, Header
from ..state import StateTest
from .helpers import remove_info_metadata


@pytest.fixture()
def fixture_hash(fork: Fork) -> bytes:
    """Set the fixture hash based on the fork."""
    if fork == Berlin:
        return bytes.fromhex("e57ad774ca")
    elif fork == London:
        return bytes.fromhex("3714102a4c")
    elif fork == Cancun:
        return bytes.fromhex("2885c707e3")
    raise ValueError(f"Unexpected fork: {fork}")


def test_check_helper_fixtures():
    """
    Test that the framework's pydantic models serialization and deserialization
    work correctly and that they are compatible with the helper fixtures defined
    in ./fixtures/ by using the check_fixtures.py script.
    """
    runner = CliRunner()
    args = [
        "--input",
        "src/ethereum_test_specs/tests/fixtures",
        "--quiet",
        "--stop-on-error",
    ]
    result = runner.invoke(cli.check_fixtures.check_fixtures, args)
    assert result.exit_code == 0, (
        "check_fixtures detected errors in the json fixtures:" + f"\n{result}"
    )


@pytest.mark.parametrize(
    "fork",
    [
        Berlin,
        London,
        Cancun,
    ],
)
def test_make_genesis(fork: Fork, fixture_hash: bytes, default_t8n: TransitionTool):  # noqa: D103
    env = Environment(gas_limit=100_000_000_000_000_000)

    pre = Alloc(
        {
            Address(0x0BA1A9CE0BA1A9CE): Account(balance=0x0BA1A9CE0BA1A9CE),
            Address(0xC0DE): Account(
                code=Op.SSTORE(0, Op.ADD(1, 2)) + Op.RETURN(0, 32),
                balance=0x0BA1A9CE0BA1A9CE,
                nonce=1,
            ),
        }
    )

    fixture = BlockchainTest(
        genesis_environment=env,
        pre=pre,
        post={},
        blocks=[],
        tag="some_state_test",
    ).generate(t8n=default_t8n, fork=fork, fixture_format=BlockchainFixture)
    assert isinstance(fixture, BlockchainFixture)
    assert fixture.genesis is not None

    assert fixture.genesis.block_hash is not None
    assert fixture.genesis.block_hash.startswith(fixture_hash)


@pytest.mark.parametrize(
    "fork,fixture_format,tx_type",
    [
        (Istanbul, BlockchainFixture, TransactionType.LEGACY),
        (London, BlockchainFixture, TransactionType.LEGACY),
        (Cancun, BlockchainFixture, TransactionType.LEGACY),
        (Paris, BlockchainEngineFixture, TransactionType.LEGACY),
        (Shanghai, BlockchainEngineFixture, TransactionType.LEGACY),
        (Cancun, BlockchainEngineFixture, TransactionType.LEGACY),
        (Paris, StateFixture, TransactionType.LEGACY),
        (Shanghai, StateFixture, TransactionType.LEGACY),
        (Cancun, StateFixture, TransactionType.LEGACY),
        (Cancun, StateFixture, TransactionType.ACCESS_LIST),
    ],
)
def test_fill_state_test(
    fork: Fork,
    fixture_format: FixtureFormat,
    tx_type: TransactionType,
    default_t8n: TransitionTool,
):
    """Test `ethereum_test.filler.fill_fixtures` with `StateTest`."""
    env = Environment(
        fee_recipient="0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba",
        difficulty=0x20000,
        gas_limit=10000000000,
        number=1,
        timestamp=1000,
    )

    pre = {
        0x1000000000000000000000000000000000000000: Account(code="0x4660015500"),
        "0xa94f5374fce5edbc8e2a8697c15331677e6ebf0b": Account(balance=1000000000000000000000),
    }

    if tx_type == TransactionType.LEGACY:
        tx = Transaction(
            chain_id=0x0,
            nonce=0,
            to="0x1000000000000000000000000000000000000000",
            gas_limit=100000000,
            gas_price=10,
            protected=False,
        )
    elif tx_type == TransactionType.ACCESS_LIST:
        tx = Transaction(
            ty=0x1,
            chain_id=0x1,
            nonce=0,
            to="0x1000000000000000000000000000000000000000",
            gas_limit=100000000,
            gas_price=10,
            access_list=[
                AccessList(
                    address=0x1234,
                    storage_keys=[0, 1],
                )
            ],
        )

    post = {
        "0x1000000000000000000000000000000000000000": Account(
            code="0x4660015500", storage={"0x01": "0x01"}
        ),
    }

    generated_fixture = StateTest(
        env=env,
        pre=pre,
        post=post,
        tx=tx,
        tag="my_chain_id_test",
    ).generate(t8n=default_t8n, fork=fork, fixture_format=fixture_format)
    assert generated_fixture.__class__ == fixture_format
    fixture = {
        f"000/my_chain_id_test/{fork}/tx_type_{tx_type}": generated_fixture.json_dict_with_info(
            hash_only=True
        ),
    }

    format_name = fixture_format.format_name
    expected_json_file = f"chainid_{fork.name().lower()}_{format_name}_tx_type_{tx_type}.json"
    with open(
        os.path.join(
            "src",
            "ethereum_test_specs",
            "tests",
            "fixtures",
            expected_json_file,
        )
    ) as f:
        expected = json.load(f)
        remove_info_metadata(expected)

    remove_info_metadata(fixture)
    assert fixture == expected


class TestFillBlockchainValidTxs:
    """Test `BlockchainTest.generate()` and blockchain fixtures."""

    @pytest.fixture
    def fork(self, request):  # noqa: D102
        return request.param

    @pytest.fixture
    def check_hive(self, fork):  # noqa: D102
        return fork == Shanghai

    @pytest.fixture
    def expected_json_file(self, fork: Fork, check_hive: bool):  # noqa: D102
        if fork == London and not check_hive:
            return "blockchain_london_valid_filled.json"
        elif fork == Shanghai and check_hive:
            return "blockchain_shanghai_valid_filled_engine.json"
        raise ValueError(f"Unexpected fork/check_hive combination: {fork}/{check_hive}")

    @pytest.fixture
    def pre(self, fork: Fork):  # noqa: D102
        pre = {
            "0xa94f5374fce5edbc8e2a8697c15331677e6ebf0b": Account(balance=0x1000000000000000000),
            "0xd02d72E067e77158444ef2020Ff2d325f929B363": Account(
                balance=0x1000000000000000000, nonce=1
            ),
            "0xcccccccccccccccccccccccccccccccccccccccc": Account(
                balance=0x10000000000,
                nonce=1,
                code=(
                    Op.SSTORE(Op.NUMBER(), Op.BASEFEE())
                    + Op.SSTORE(Op.ADD(Op.NUMBER(), 0x1000), Op.SUB(Op.GASPRICE(), Op.BASEFEE()))
                    + Op.SSTORE(Op.ADD(Op.NUMBER(), 0x2000), Op.SELFBALANCE())
                    + Op.STOP()
                ),
            ),
            "0xcccccccccccccccccccccccccccccccccccccccd": Account(
                balance=0x20000000000,
                nonce=1,
                code=(
                    (Op.PUSH1(0) if fork < Shanghai else Op.PUSH0)
                    + Op.DUP1
                    + (Op.PUSH1(0) if fork < Shanghai else Op.PUSH0)
                    + Op.DUP1
                    + Op.PUSH20("0xcccccccccccccccccccccccccccccccccccccccc")
                    + Op.GAS
                    + Op.DELEGATECALL
                    + Op.POP
                ),
            ),
            0xC0DE: Account(
                balance=0,
                nonce=1,
                code=(
                    (Op.PUSH1(0) if fork < Shanghai else Op.PUSH0)
                    + Op.DUP1
                    + (Op.PUSH1(0) if fork < Shanghai else Op.PUSH0)
                    + Op.DUP1
                    + Op.PUSH20("0xcccccccccccccccccccccccccccccccccccccccc")
                    + Op.GAS
                    + Op.DELEGATECALL
                    + Op.POP
                ),
            ),
            "0xccccccccccccccccccccccccccccccccccccccce": Account(
                balance=0x20000000000,
                nonce=1,
                code=(
                    (Op.PUSH1(0) if fork < Shanghai else Op.PUSH0)
                    + Op.DUP1
                    + (Op.PUSH1(0) if fork < Shanghai else Op.PUSH0)
                    + Op.DUP1
                    + Op.PUSH2("0x1000")
                    + Op.PUSH2("0xc0de")
                    + Op.GAS
                    + Op.CALL
                    + (Op.PUSH1(0) if fork < Shanghai else Op.PUSH0)
                    + Op.DUP1
                    + (Op.PUSH1(0) if fork < Shanghai else Op.PUSH0)
                    + Op.DUP1
                    + Op.PUSH20("0xcccccccccccccccccccccccccccccccccccccccc")
                    + Op.GAS
                    + Op.DELEGATECALL
                    + Op.SWAP1
                    + Op.POP
                    + Op.POP
                ),
            ),
        }
        return pre

    @pytest.fixture
    def blocks(self) -> List[Block]:  # noqa: D102
        blocks: List[Block] = [
            Block(
                fee_recipient="0xba5e000000000000000000000000000000000000",
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
                fee_recipient="0xba5e000000000000000000000000000000000000",
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
                fee_recipient="0xba5e000000000000000000000000000000000000",
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
                fee_recipient="0xba5e000000000000000000000000000000000000",
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
        return blocks

    @pytest.fixture
    def post(self):  # noqa: D102
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
        return post

    @pytest.fixture
    def genesis_environment(self):  # noqa: D102
        return Environment(
            gas_limit=100_000_000_000_000_000,
            base_fee_per_gas=1000,
            fee_recipient="0xba5e000000000000000000000000000000000000",
        )

    @pytest.fixture
    def fixture_format(self, check_hive: bool):  # noqa: D102
        return BlockchainEngineFixture if check_hive else BlockchainFixture

    @pytest.fixture
    def blockchain_test_fixture(  # noqa: D102
        self,
        check_hive: bool,
        fork: Fork,
        pre: Mapping[Any, Any],
        post: Mapping[Any, Any],
        blocks: List[Block],
        genesis_environment: Environment,
        fixture_format: FixtureFormat,
        default_t8n: TransitionTool,
    ):
        return BlockchainTest(
            pre=pre,
            post=post,
            blocks=blocks,
            genesis_environment=genesis_environment,
            tag="my_blockchain_test_valid_txs",
        ).generate(t8n=default_t8n, fork=fork, fixture_format=fixture_format)

    @pytest.mark.parametrize("fork", [London, Shanghai], indirect=True)
    def test_fill_blockchain_valid_txs(  # noqa: D102
        self,
        fork: Fork,
        check_hive: bool,
        fixture_format: FixtureFormat,
        expected_json_file: str,
        blockchain_test_fixture: BlockchainFixture,
    ):
        assert blockchain_test_fixture.__class__ == fixture_format
        assert isinstance(blockchain_test_fixture, BlockchainFixtureCommon)

        fixture_name = f"000/my_blockchain_test/{fork.name()}"

        fixture = {
            fixture_name: blockchain_test_fixture.json_dict_with_info(hash_only=True),
        }

        with open(
            os.path.join(
                "src",
                "ethereum_test_specs",
                "tests",
                "fixtures",
                expected_json_file,
            )
        ) as f:
            expected = json.load(f)
            remove_info_metadata(expected)

        remove_info_metadata(fixture)
        assert fixture_name in fixture
        assert fixture_name in expected
        assert fixture[fixture_name] == expected[fixture_name]

    @pytest.mark.parametrize("fork", [London], indirect=True)
    def test_fixture_header_join(self, blockchain_test_fixture: BlockchainFixture):
        """Test `FixtureHeader.join()`."""
        block = blockchain_test_fixture.blocks[0]
        new_difficulty = block.header.difficulty - 1  # type: ignore

        new_state_root = Hash(12345)
        # See description of https://github.com/ethereum/execution-spec-tests/pull/398
        new_transactions_root = 0x100
        header_new_fields = Header(
            difficulty=new_difficulty,
            state_root=new_state_root,
            transactions_trie=new_transactions_root,
        )

        updated_block_header = header_new_fields.apply(block.header)  # type: ignore
        assert updated_block_header.difficulty == new_difficulty
        assert updated_block_header.state_root == new_state_root
        assert updated_block_header.transactions_trie == Hash(new_transactions_root)
        assert updated_block_header.block_hash != block.header.block_hash  # type: ignore
        assert isinstance(updated_block_header.transactions_trie, Hash)


@pytest.mark.parametrize(
    "fork,check_hive,expected_json_file",
    [
        (London, False, "blockchain_london_invalid_filled.json"),
        (Shanghai, True, "blockchain_shanghai_invalid_filled_engine.json"),
    ],
)
def test_fill_blockchain_invalid_txs(
    fork: Fork, check_hive: bool, expected_json_file: str, default_t8n: TransitionTool
):
    """Test `ethereum_test.filler.fill_fixtures` with `BlockchainTest`."""
    pre = {
        "0xa94f5374fce5edbc8e2a8697c15331677e6ebf0b": Account(balance=0x1000000000000000000),
        "0xd02d72E067e77158444ef2020Ff2d325f929B363": Account(
            balance=0x1000000000000000000, nonce=1
        ),
        "0xcccccccccccccccccccccccccccccccccccccccc": Account(
            balance=0x10000000000,
            nonce=1,
            code=(
                Op.SSTORE(Op.NUMBER(), Op.BASEFEE())
                + Op.SSTORE(Op.ADD(Op.NUMBER(), 0x1000), Op.SUB(Op.GASPRICE(), Op.BASEFEE()))
                + Op.SSTORE(Op.ADD(Op.NUMBER(), 0x2000), Op.SELFBALANCE())
                + Op.STOP()
            ),
        ),
        "0xcccccccccccccccccccccccccccccccccccccccd": Account(
            balance=0x20000000000,
            nonce=1,
            code=(
                (Op.PUSH1(0) if fork < Shanghai else Op.PUSH0)
                + Op.DUP1
                + (Op.PUSH1(0) if fork < Shanghai else Op.PUSH0)
                + Op.DUP1
                + Op.PUSH20("0xcccccccccccccccccccccccccccccccccccccccc")
                + Op.GAS
                + Op.DELEGATECALL
                + Op.POP
            ),
        ),
        0xC0DE: Account(
            balance=0,
            nonce=1,
            code=(
                (Op.PUSH1(0) if fork < Shanghai else Op.PUSH0)
                + Op.DUP1
                + (Op.PUSH1(0) if fork < Shanghai else Op.PUSH0)
                + Op.DUP1
                + Op.PUSH20("0xcccccccccccccccccccccccccccccccccccccccc")
                + Op.GAS
                + Op.DELEGATECALL
                + Op.POP
            ),
        ),
        "0xccccccccccccccccccccccccccccccccccccccce": Account(
            balance=0x20000000000,
            nonce=1,
            code=(
                (Op.PUSH1(0) if fork < Shanghai else Op.PUSH0)
                + Op.DUP1
                + (Op.PUSH1(0) if fork < Shanghai else Op.PUSH0)
                + Op.DUP1
                + Op.PUSH2("0x1000")
                + Op.PUSH2("0xc0de")
                + Op.GAS
                + Op.CALL
                + (Op.PUSH1(0) if fork < Shanghai else Op.PUSH0)
                + Op.DUP1
                + (Op.PUSH1(0) if fork < Shanghai else Op.PUSH0)
                + Op.DUP1
                + Op.PUSH20("0xcccccccccccccccccccccccccccccccccccccccc")
                + Op.GAS
                + Op.DELEGATECALL
                + Op.SWAP1
                + Op.POP
                + Op.POP
            ),
        ),
    }

    blocks: List[Block] = [
        Block(
            fee_recipient="0xba5e000000000000000000000000000000000000",
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
            fee_recipient="0xba5e000000000000000000000000000000000000",
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
            fee_recipient="0xba5e000000000000000000000000000000000000",
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
                    error=TransactionException.PRIORITY_GREATER_THAN_MAX_FEE_PER_GAS,
                ),
            ],
            exception=TransactionException.PRIORITY_GREATER_THAN_MAX_FEE_PER_GAS,
        ),
        Block(
            fee_recipient="0xba5e000000000000000000000000000000000000",
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
            fee_recipient="0xba5e000000000000000000000000000000000000",
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
                    error=TransactionException.PRIORITY_GREATER_THAN_MAX_FEE_PER_GAS,
                ),
            ],
            exception=TransactionException.PRIORITY_GREATER_THAN_MAX_FEE_PER_GAS,
        ),
        Block(
            fee_recipient="0xba5e000000000000000000000000000000000000",
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
        gas_limit=100_000_000_000_000_000,
        base_fee_per_gas=1000,
        fee_recipient="0xba5e000000000000000000000000000000000000",
    )

    fixture_format: FixtureFormat = (
        BlockchainEngineFixture if check_hive else BlockchainFixture  # type: ignore
    )
    generated_fixture = BlockchainTest(
        pre=pre,
        post=post,
        blocks=blocks,
        genesis_environment=genesis_environment,
    ).generate(t8n=default_t8n, fork=fork, fixture_format=fixture_format)
    assert generated_fixture.__class__ == fixture_format
    assert isinstance(generated_fixture, BlockchainFixtureCommon)

    fixture_name = f"000/my_blockchain_test/{fork.name()}"

    fixture = {
        fixture_name: generated_fixture.json_dict_with_info(hash_only=True),
    }

    with open(
        os.path.join(
            "src",
            "ethereum_test_specs",
            "tests",
            "fixtures",
            expected_json_file,
        )
    ) as f:
        expected = json.load(f)
        remove_info_metadata(expected)

    remove_info_metadata(fixture)
    assert fixture_name in fixture
    assert fixture_name in expected
    assert fixture[fixture_name] == expected[fixture_name]
