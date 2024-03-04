"""
Ethereum blockchain test spec definition and filler.
"""

from copy import copy
from dataclasses import dataclass, field, replace
from pprint import pprint
from typing import Any, Callable, Dict, Generator, List, Mapping, Optional, Tuple, Type

from ethereum_test_forks import Fork
from evm_transition_tool import FixtureFormats, TransitionTool

from ...common import (
    Address,
    Alloc,
    Bloom,
    Bytes,
    EmptyTrieRoot,
    Environment,
    Hash,
    HeaderNonce,
    Number,
    Transaction,
    ZeroPaddedHexNumber,
    alloc_to_accounts,
    transaction_list_root,
    withdrawals_root,
)
from ...common.constants import EmptyOmmersRoot
from ...common.json import to_json
from ..base.base_test import (
    BaseFixture,
    BaseTest,
    verify_post_alloc,
    verify_result,
    verify_transactions,
)
from ..debugging import print_traces
from .types import (
    Block,
    BlockException,
    Fixture,
    FixtureBlock,
    FixtureEngineNewPayload,
    FixtureHeader,
    HiveFixture,
    InvalidFixtureBlock,
)


def environment_from_parent_header(parent: "FixtureHeader") -> "Environment":
    """
    Instantiates a new environment with the provided header as parent.
    """
    return Environment(
        parent_difficulty=parent.difficulty,
        parent_timestamp=parent.timestamp,
        parent_base_fee=parent.base_fee,
        parent_blob_gas_used=parent.blob_gas_used,
        parent_excess_blob_gas=parent.excess_blob_gas,
        parent_gas_used=parent.gas_used,
        parent_gas_limit=parent.gas_limit,
        parent_ommers_hash=parent.ommers_hash,
        block_hashes={parent.number: parent.hash if parent.hash is not None else 0},
    )


def apply_new_parent(env: Environment, new_parent: FixtureHeader) -> "Environment":
    """
    Applies a header as parent to a copy of this environment.
    """
    env = copy(env)
    env.parent_difficulty = new_parent.difficulty
    env.parent_timestamp = new_parent.timestamp
    env.parent_base_fee = new_parent.base_fee
    env.parent_blob_gas_used = new_parent.blob_gas_used
    env.parent_excess_blob_gas = new_parent.excess_blob_gas
    env.parent_gas_used = new_parent.gas_used
    env.parent_gas_limit = new_parent.gas_limit
    env.parent_ommers_hash = new_parent.ommers_hash
    env.block_hashes[new_parent.number] = new_parent.hash if new_parent.hash is not None else 0
    return env


def count_blobs(txs: List[Transaction]) -> int:
    """
    Returns the number of blobs in a list of transactions.
    """
    return sum(
        [len(tx.blob_versioned_hashes) for tx in txs if tx.blob_versioned_hashes is not None]
    )


@dataclass(kw_only=True)
class BlockchainTest(BaseTest):
    """
    Filler type that tests multiple blocks (valid or invalid) in a chain.
    """

    pre: Mapping
    post: Mapping
    blocks: List[Block]
    genesis_environment: Environment = field(default_factory=Environment)
    tag: str = ""
    chain_id: int = 1

    @classmethod
    def pytest_parameter_name(cls) -> str:
        """
        Returns the parameter name used to identify this filler in a test.
        """
        return "blockchain_test"

    @classmethod
    def fixture_formats(cls) -> List[FixtureFormats]:
        """
        Returns a list of fixture formats that can be output to the test spec.
        """
        return [
            FixtureFormats.BLOCKCHAIN_TEST,
            FixtureFormats.BLOCKCHAIN_TEST_HIVE,
        ]

    def make_genesis(
        self,
        t8n: TransitionTool,
        fork: Fork,
    ) -> Tuple[Alloc, Bytes, FixtureHeader]:
        """
        Create a genesis block from the blockchain test definition.
        """
        env = self.genesis_environment.set_fork_requirements(fork)
        if env.withdrawals is not None:
            assert len(env.withdrawals) == 0, "withdrawals must be empty at genesis"
        if env.beacon_root is not None:
            assert Hash(env.beacon_root) == Hash(0), "beacon_root must be empty at genesis"

        pre_alloc = Alloc.merge(
            Alloc(fork.pre_allocation_blockchain()),
            Alloc(self.pre),
        )
        if empty_accounts := pre_alloc.empty_accounts():
            raise Exception(f"Empty accounts in pre state: {empty_accounts}")
        state_root = pre_alloc.state_root()
        genesis = FixtureHeader(
            parent_hash=Hash(0),
            ommers_hash=Hash(EmptyOmmersRoot),
            coinbase=Address(0),
            state_root=Hash(state_root),
            transactions_root=Hash(EmptyTrieRoot),
            receipt_root=Hash(EmptyTrieRoot),
            bloom=Bloom(0),
            difficulty=ZeroPaddedHexNumber(0x20000 if env.difficulty is None else env.difficulty),
            number=0,
            gas_limit=ZeroPaddedHexNumber(env.gas_limit),
            gas_used=0,
            timestamp=0,
            extra_data=Bytes([0]),
            mix_digest=Hash(0),
            nonce=HeaderNonce(0),
            base_fee=ZeroPaddedHexNumber.or_none(env.base_fee),
            blob_gas_used=ZeroPaddedHexNumber.or_none(env.blob_gas_used),
            excess_blob_gas=ZeroPaddedHexNumber.or_none(env.excess_blob_gas),
            withdrawals_root=Hash.or_none(
                withdrawals_root(env.withdrawals) if env.withdrawals is not None else None
            ),
            beacon_root=Hash.or_none(env.beacon_root),
        )

        genesis_rlp, genesis.hash = genesis.build(
            txs=[],
            ommers=[],
            withdrawals=env.withdrawals,
        )

        return pre_alloc, genesis_rlp, genesis

    def generate_block_data(
        self,
        t8n: TransitionTool,
        fork: Fork,
        block: Block,
        previous_env: Environment,
        previous_alloc: Dict[str, Any],
        eips: Optional[List[int]] = None,
    ) -> Tuple[FixtureHeader, Bytes, List[Transaction], Dict[str, Any], Environment]:
        """
        Generate common block data for both make_fixture and make_hive_fixture.
        """
        if block.rlp and block.exception is not None:
            raise Exception(
                "test correctness: post-state cannot be verified if the "
                + "block's rlp is supplied and the block is not supposed "
                + "to produce an exception"
            )

        env = block.set_environment(previous_env)
        env = env.set_fork_requirements(fork)

        txs = [tx.with_signature_and_sender() for tx in block.txs] if block.txs is not None else []

        if failing_tx_count := len([tx for tx in txs if tx.error]) > 0:
            if failing_tx_count > 1:
                raise Exception(
                    "test correctness: only one transaction can produce an exception in a block"
                )
            if not txs[-1].error:
                raise Exception(
                    "test correctness: the transaction that produces an exception "
                    + "must be the last transaction in the block"
                )

        next_alloc, result = t8n.evaluate(
            alloc=previous_alloc,
            txs=to_json(txs),
            env=to_json(env),
            fork_name=fork.transition_tool_name(
                block_number=Number(env.number), timestamp=Number(env.timestamp)
            ),
            chain_id=self.chain_id,
            reward=fork.get_reward(Number(env.number), Number(env.timestamp)),
            eips=eips,
            debug_output_path=self.get_next_transition_tool_output_path(),
        )

        try:
            rejected_txs = verify_transactions(txs, result)
            verify_result(result, env)
        except Exception as e:
            print_traces(t8n.get_traces())
            pprint(result)
            pprint(previous_alloc)
            pprint(next_alloc)
            raise e

        if len(rejected_txs) > 0 and block.exception is None:
            print_traces(t8n.get_traces())
            raise Exception(
                "one or more transactions in `BlockchainTest` are "
                + "intrinsically invalid, but the block was not expected "
                + "to be invalid. Please verify whether the transaction "
                + "was indeed expected to fail and add the proper "
                + "`block.exception`"
            )

        env.extra_data = block.extra_data
        header = FixtureHeader.collect(
            fork=fork,
            transition_tool_result=result,
            environment=env,
        )

        # Update the transactions root to the one calculated locally.
        header.transactions_root = transaction_list_root(txs)

        # One special case of the invalid transactions is the blob gas used, since this value
        # is not included in the transition tool result, but it is included in the block header,
        # and some clients check it before executing the block by simply counting the type-3 txs,
        # we need to set the correct value by default.
        if (
            blob_gas_per_blob := fork.blob_gas_per_blob(Number(env.number), Number(env.timestamp))
        ) > 0:
            header.blob_gas_used = blob_gas_per_blob * count_blobs(txs)

        if block.header_verify is not None:
            # Verify the header after transition tool processing.
            header.verify(block.header_verify)

        if block.rlp_modifier is not None:
            # Modify any parameter specified in the `rlp_modifier` after
            # transition tool processing.
            header = header.join(block.rlp_modifier)

        rlp, header.hash = header.build(
            txs=txs,
            ommers=[],
            withdrawals=env.withdrawals,
        )

        return header, rlp, txs, next_alloc, env

    def network_info(self, fork: Fork, eips: Optional[List[int]] = None):
        """
        Returns fixture network information for the fork & EIP/s.
        """
        return (
            "+".join([fork.blockchain_test_network_name()] + [str(eip) for eip in eips])
            if eips
            else fork.blockchain_test_network_name()
        )

    def verify_post_state(self, t8n, alloc):
        """
        Verifies the post alloc after all block/s or payload/s are generated.
        """
        try:
            verify_post_alloc(self.post, alloc)
        except Exception as e:
            print_traces(t8n.get_traces())
            raise e

    def make_fixture(
        self,
        t8n: TransitionTool,
        fork: Fork,
        eips: Optional[List[int]] = None,
    ) -> Fixture:
        """
        Create a fixture from the blockchain test definition.
        """
        fixture_blocks: List[FixtureBlock | InvalidFixtureBlock] = []

        pre, genesis_rlp, genesis = self.make_genesis(t8n, fork)

        alloc = to_json(pre)
        env = environment_from_parent_header(genesis)
        head = genesis.hash if genesis.hash is not None else Hash(0)

        for block in self.blocks:
            if block.rlp is None:
                # This is the most common case, the RLP needs to be constructed
                # based on the transactions to be included in the block.
                # Set the environment according to the block to execute.
                header, rlp, txs, new_alloc, new_env = self.generate_block_data(
                    t8n=t8n,
                    fork=fork,
                    block=block,
                    previous_env=env,
                    previous_alloc=alloc,
                    eips=eips,
                )
                fixture_block = FixtureBlock(
                    rlp=rlp,
                    block_header=header,
                    block_number=Number(header.number),
                    txs=txs,
                    ommers=[],
                    withdrawals=new_env.withdrawals,
                )
                if block.exception is None:
                    fixture_blocks.append(fixture_block)
                    # Update env, alloc and last block hash for the next block.
                    alloc = new_alloc
                    env = apply_new_parent(new_env, header)
                    head = header.hash if header.hash is not None else Hash(0)
                else:
                    fixture_blocks.append(
                        InvalidFixtureBlock(
                            rlp=rlp,
                            expected_exception=block.exception,
                            rlp_decoded=(
                                None
                                if BlockException.RLP_STRUCTURES_ENCODING in block.exception
                                else replace(fixture_block, rlp=None)
                            ),
                        ),
                    )
            else:
                assert block.exception is not None, (
                    "test correctness: if the block's rlp is hard-coded, "
                    + "the block is expected to produce an exception"
                )
                fixture_blocks.append(
                    InvalidFixtureBlock(
                        rlp=Bytes(block.rlp),
                        expected_exception=block.exception,
                    ),
                )

        self.verify_post_state(t8n, alloc)
        return Fixture(
            fork=self.network_info(fork, eips),
            genesis=genesis,
            genesis_rlp=genesis_rlp,
            blocks=fixture_blocks,
            last_block_hash=head,
            pre_state=pre,
            post_state=alloc_to_accounts(alloc),
            name=self.tag,
        )

    def make_hive_fixture(
        self,
        t8n: TransitionTool,
        fork: Fork,
        eips: Optional[List[int]] = None,
    ) -> HiveFixture:
        """
        Create a hive fixture from the blocktest definition.
        """
        fixture_payloads: List[FixtureEngineNewPayload] = []

        pre, _, genesis = self.make_genesis(t8n, fork)
        alloc = to_json(pre)
        env = environment_from_parent_header(genesis)

        for block in self.blocks:
            header, _, txs, new_alloc, new_env = self.generate_block_data(
                t8n=t8n, fork=fork, block=block, previous_env=env, previous_alloc=alloc, eips=eips
            )
            if block.rlp is None:
                fixture_payloads.append(
                    FixtureEngineNewPayload.from_fixture_header(
                        fork=fork,
                        header=header,
                        transactions=txs,
                        withdrawals=new_env.withdrawals,
                        validation_error=block.exception,
                        error_code=block.engine_api_error_code,
                    )
                )
                if block.exception is None:
                    alloc = new_alloc
                    env = apply_new_parent(env, header)
        fcu_version = fork.engine_forkchoice_updated_version(header.number, header.timestamp)
        assert (
            fcu_version is not None
        ), "A hive fixture was requested but no forkchoice update is defined. The framework should"
        " never try to execute this test case."

        self.verify_post_state(t8n, alloc)
        return HiveFixture(
            fork=self.network_info(fork, eips),
            genesis=genesis,
            payloads=fixture_payloads,
            fcu_version=fcu_version,
            pre_state=pre,
            post_state=alloc_to_accounts(alloc),
            name=self.tag,
        )

    def generate(
        self,
        t8n: TransitionTool,
        fork: Fork,
        eips: Optional[List[int]] = None,
    ) -> BaseFixture:
        """
        Generate the BlockchainTest fixture.
        """
        t8n.reset_traces()
        if self.fixture_format == FixtureFormats.BLOCKCHAIN_TEST_HIVE:
            if fork.engine_forkchoice_updated_version() is None:
                raise Exception(
                    "A hive fixture was requested but no forkchoice update is defined. "
                    "The framework should never try to execute this test case."
                )
            return self.make_hive_fixture(t8n, fork, eips)
        elif self.fixture_format == FixtureFormats.BLOCKCHAIN_TEST:
            return self.make_fixture(t8n, fork, eips)

        raise Exception(f"Unknown fixture format: {self.fixture_format}")


BlockchainTestSpec = Callable[[str], Generator[BlockchainTest, None, None]]
BlockchainTestFiller = Type[BlockchainTest]
