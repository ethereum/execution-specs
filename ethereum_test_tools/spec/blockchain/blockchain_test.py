"""
Ethereum blockchain test spec definition and filler.
"""

from pprint import pprint
from typing import Any, Callable, ClassVar, Dict, Generator, List, Optional, Tuple, Type

from pydantic import Field

from ethereum_test_forks import Fork
from evm_transition_tool import FixtureFormats, TransitionTool

from ...common import Alloc, EmptyTrieRoot, Environment, Hash, Transaction, Withdrawal
from ...common.constants import EmptyOmmersRoot
from ...common.json import to_json
from ...common.types import TransitionToolOutput
from ..base.base_test import BaseFixture, BaseTest, verify_result, verify_transactions
from ..debugging import print_traces
from .types import (
    Block,
    BlockException,
    Fixture,
    FixtureBlock,
    FixtureBlockBase,
    FixtureEngineNewPayload,
    FixtureHeader,
    FixtureTransaction,
    FixtureWithdrawal,
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
        parent_base_fee_per_gas=parent.base_fee_per_gas,
        parent_blob_gas_used=parent.blob_gas_used,
        parent_excess_blob_gas=parent.excess_blob_gas,
        parent_gas_used=parent.gas_used,
        parent_gas_limit=parent.gas_limit,
        parent_ommers_hash=parent.ommers_hash,
        block_hashes={parent.number: parent.block_hash},
    )


def apply_new_parent(env: Environment, new_parent: FixtureHeader) -> "Environment":
    """
    Applies a header as parent to a copy of this environment.
    """
    updated: Dict[str, Any] = {}
    updated["parent_difficulty"] = new_parent.difficulty
    updated["parent_timestamp"] = new_parent.timestamp
    updated["parent_base_fee_per_gas"] = new_parent.base_fee_per_gas
    updated["parent_blob_gas_used"] = new_parent.blob_gas_used
    updated["parent_excess_blob_gas"] = new_parent.excess_blob_gas
    updated["parent_gas_used"] = new_parent.gas_used
    updated["parent_gas_limit"] = new_parent.gas_limit
    updated["parent_ommers_hash"] = new_parent.ommers_hash
    block_hashes = env.block_hashes.copy()
    block_hashes[new_parent.number] = new_parent.block_hash
    updated["block_hashes"] = block_hashes
    return env.copy(**updated)


def count_blobs(txs: List[Transaction]) -> int:
    """
    Returns the number of blobs in a list of transactions.
    """
    return sum(
        [len(tx.blob_versioned_hashes) for tx in txs if tx.blob_versioned_hashes is not None]
    )


class BlockchainTest(BaseTest):
    """
    Filler type that tests multiple blocks (valid or invalid) in a chain.
    """

    pre: Alloc
    post: Alloc
    blocks: List[Block]
    genesis_environment: Environment = Field(default_factory=Environment)
    verify_sync: bool = False
    chain_id: int = 1

    supported_fixture_formats: ClassVar[List[FixtureFormats]] = [
        FixtureFormats.BLOCKCHAIN_TEST,
        FixtureFormats.BLOCKCHAIN_TEST_HIVE,
    ]

    def make_genesis(
        self,
        fork: Fork,
    ) -> Tuple[Alloc, FixtureBlock]:
        """
        Create a genesis block from the blockchain test definition.
        """
        env = self.genesis_environment.set_fork_requirements(fork)
        assert (
            env.withdrawals is None or len(env.withdrawals) == 0
        ), "withdrawals must be empty at genesis"
        assert env.parent_beacon_block_root is None or env.parent_beacon_block_root == Hash(
            0
        ), "parent_beacon_block_root must be empty at genesis"

        pre_alloc = Alloc.merge(
            Alloc.model_validate(fork.pre_allocation_blockchain()),
            self.pre,
        )
        if empty_accounts := pre_alloc.empty_accounts():
            raise Exception(f"Empty accounts in pre state: {empty_accounts}")
        state_root = pre_alloc.state_root()
        genesis = FixtureHeader(
            parent_hash=0,
            ommers_hash=EmptyOmmersRoot,
            fee_recipient=0,
            state_root=state_root,
            transactions_trie=EmptyTrieRoot,
            receipts_root=EmptyTrieRoot,
            logs_bloom=0,
            difficulty=0x20000 if env.difficulty is None else env.difficulty,
            number=0,
            gas_limit=env.gas_limit,
            gas_used=0,
            timestamp=0,
            extra_data=b"\x00",
            prev_randao=0,
            nonce=0,
            base_fee_per_gas=env.base_fee_per_gas,
            blob_gas_used=env.blob_gas_used,
            excess_blob_gas=env.excess_blob_gas,
            withdrawals_root=Withdrawal.list_root(env.withdrawals)
            if env.withdrawals is not None
            else None,
            parent_beacon_block_root=env.parent_beacon_block_root,
        )

        return (
            pre_alloc,
            FixtureBlockBase(
                header=genesis,
                withdrawals=None if env.withdrawals is None else [],
            ).with_rlp(txs=[]),
        )

    def generate_block_data(
        self,
        t8n: TransitionTool,
        fork: Fork,
        block: Block,
        previous_env: Environment,
        previous_alloc: Alloc,
        eips: Optional[List[int]] = None,
    ) -> Tuple[FixtureHeader, List[Transaction], Alloc, Environment]:
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

        txs = [tx.with_signature_and_sender() for tx in block.txs]

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

        transition_tool_output = TransitionToolOutput(
            **t8n.evaluate(
                alloc=to_json(previous_alloc),
                txs=[to_json(tx) for tx in txs],
                env=to_json(env),
                fork_name=fork.transition_tool_name(
                    block_number=env.number, timestamp=env.timestamp
                ),
                chain_id=self.chain_id,
                reward=fork.get_reward(env.number, env.timestamp),
                eips=eips,
                debug_output_path=self.get_next_transition_tool_output_path(),
            )
        )

        try:
            rejected_txs = verify_transactions(txs, transition_tool_output.result)
            verify_result(transition_tool_output.result, env)
        except Exception as e:
            print_traces(t8n.get_traces())
            pprint(transition_tool_output.result)
            pprint(previous_alloc)
            pprint(transition_tool_output.alloc)
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

        # One special case of the invalid transactions is the blob gas used, since this value
        # is not included in the transition tool result, but it is included in the block header,
        # and some clients check it before executing the block by simply counting the type-3 txs,
        # we need to set the correct value by default.
        blob_gas_used: int | None = None
        if (blob_gas_per_blob := fork.blob_gas_per_blob(env.number, env.timestamp)) > 0:
            blob_gas_used = blob_gas_per_blob * count_blobs(txs)

        header = FixtureHeader(
            **(
                transition_tool_output.result.model_dump(
                    exclude_none=True, exclude={"blob_gas_used", "transactions_trie"}
                )
                | env.model_dump(exclude_none=True, exclude={"blob_gas_used"})
            ),
            blob_gas_used=blob_gas_used,
            transactions_trie=Transaction.list_root(txs),
            extra_data=block.extra_data if block.extra_data is not None else b"",
            fork=fork,
        )

        if block.header_verify is not None:
            # Verify the header after transition tool processing.
            header.verify(block.header_verify)

        if block.rlp_modifier is not None:
            # Modify any parameter specified in the `rlp_modifier` after
            # transition tool processing.
            header = header.join(block.rlp_modifier)

        return header, txs, transition_tool_output.alloc, env

    def network_info(self, fork: Fork, eips: Optional[List[int]] = None):
        """
        Returns fixture network information for the fork & EIP/s.
        """
        return (
            "+".join([fork.blockchain_test_network_name()] + [str(eip) for eip in eips])
            if eips
            else fork.blockchain_test_network_name()
        )

    def verify_post_state(self, t8n, alloc: Alloc):
        """
        Verifies the post alloc after all block/s or payload/s are generated.
        """
        try:
            self.post.verify_post_alloc(alloc)
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

        pre, genesis = self.make_genesis(fork)

        alloc = pre
        env = environment_from_parent_header(genesis.header)
        head = genesis.header.block_hash

        for block in self.blocks:
            if block.rlp is None:
                # This is the most common case, the RLP needs to be constructed
                # based on the transactions to be included in the block.
                # Set the environment according to the block to execute.
                header, txs, new_alloc, new_env = self.generate_block_data(
                    t8n=t8n,
                    fork=fork,
                    block=block,
                    previous_env=env,
                    previous_alloc=alloc,
                    eips=eips,
                )
                fixture_block = FixtureBlockBase(
                    header=header,
                    txs=[FixtureTransaction.from_transaction(tx) for tx in txs],
                    ommers=[],
                    withdrawals=[FixtureWithdrawal.from_withdrawal(w) for w in new_env.withdrawals]
                    if new_env.withdrawals is not None
                    else None,
                ).with_rlp(txs=txs)
                if block.exception is None:
                    fixture_blocks.append(fixture_block)
                    # Update env, alloc and last block hash for the next block.
                    alloc = new_alloc
                    env = apply_new_parent(new_env, header)
                    head = header.block_hash
                else:
                    fixture_blocks.append(
                        InvalidFixtureBlock(
                            rlp=fixture_block.rlp,
                            expect_exception=block.exception,
                            rlp_decoded=(
                                None
                                if BlockException.RLP_STRUCTURES_ENCODING in block.exception
                                else fixture_block.without_rlp()
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
                        rlp=block.rlp,
                        expect_exception=block.exception,
                    ),
                )

        self.verify_post_state(t8n, alloc)
        return Fixture(
            fork=self.network_info(fork, eips),
            genesis=genesis.header,
            genesis_rlp=genesis.rlp,
            blocks=fixture_blocks,
            last_block_hash=head,
            pre=pre,
            post_state=alloc,
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

        pre, genesis = self.make_genesis(fork)
        alloc = pre
        env = environment_from_parent_header(genesis.header)
        head_hash = genesis.header.block_hash

        for block in self.blocks:
            header, txs, new_alloc, new_env = self.generate_block_data(
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
                    head_hash = header.block_hash
        fcu_version = fork.engine_forkchoice_updated_version(header.number, header.timestamp)
        assert (
            fcu_version is not None
        ), "A hive fixture was requested but no forkchoice update is defined. The framework should"
        " never try to execute this test case."

        self.verify_post_state(t8n, alloc)

        sync_payload: Optional[FixtureEngineNewPayload] = None
        if self.verify_sync:
            # Test is marked for syncing verification.
            assert (
                genesis.header.block_hash != head_hash
            ), "Invalid payload tests negative test via sync is not supported yet."

            # Most clients require the header to start the sync process, so we create an empty
            # block on top of the last block of the test to send it as new payload and trigger the
            # sync process.
            sync_header, _, _, _ = self.generate_block_data(
                t8n=t8n,
                fork=fork,
                block=Block(),
                previous_env=env,
                previous_alloc=alloc,
                eips=eips,
            )
            sync_payload = FixtureEngineNewPayload.from_fixture_header(
                fork=fork,
                header=sync_header,
                transactions=[],
                withdrawals=[],
                validation_error=None,
                error_code=None,
            )

        return HiveFixture(
            fork=self.network_info(fork, eips),
            genesis=genesis.header,
            payloads=fixture_payloads,
            fcu_version=fcu_version,
            pre=pre,
            post_state=alloc,
            sync_payload=sync_payload,
        )

    def generate(
        self,
        t8n: TransitionTool,
        fork: Fork,
        fixture_format: FixtureFormats,
        eips: Optional[List[int]] = None,
    ) -> BaseFixture:
        """
        Generate the BlockchainTest fixture.
        """
        t8n.reset_traces()
        if fixture_format == FixtureFormats.BLOCKCHAIN_TEST_HIVE:
            return self.make_hive_fixture(t8n, fork, eips)
        elif fixture_format == FixtureFormats.BLOCKCHAIN_TEST:
            return self.make_fixture(t8n, fork, eips)

        raise Exception(f"Unknown fixture format: {fixture_format}")


BlockchainTestSpec = Callable[[str], Generator[BlockchainTest, None, None]]
BlockchainTestFiller = Type[BlockchainTest]
