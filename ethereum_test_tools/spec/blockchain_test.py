"""
Blockchain test filler.
"""

from dataclasses import dataclass, field
from pprint import pprint
from typing import Any, Callable, Dict, Generator, List, Mapping, Optional, Tuple, Type

from ethereum_test_forks import Fork
from evm_transition_tool import TransitionTool

from ..common import (
    Address,
    Alloc,
    Block,
    Bloom,
    Bytes,
    EmptyTrieRoot,
    Environment,
    FixtureBlock,
    FixtureEngineNewPayload,
    FixtureHeader,
    Hash,
    HeaderNonce,
    Number,
    ZeroPaddedHexNumber,
    to_json,
)
from ..common.constants import EmptyOmmersRoot
from .base_test import BaseTest, verify_post_alloc, verify_transactions
from .debugging import print_traces


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

    @classmethod
    def pytest_parameter_name(cls) -> str:
        """
        Returns the parameter name used to identify this filler in a test.
        """
        return "blockchain_test"

    def make_genesis(
        self,
        t8n: TransitionTool,
        fork: Fork,
    ) -> Tuple[Bytes, FixtureHeader]:
        """
        Create a genesis block from the state test definition.
        """
        env = self.genesis_environment.set_fork_requirements(fork)

        genesis = FixtureHeader(
            parent_hash=Hash(0),
            ommers_hash=Hash(EmptyOmmersRoot),
            coinbase=Address(0),
            state_root=Hash(
                t8n.calc_state_root(
                    alloc=to_json(Alloc(self.pre)),
                    fork=fork,
                    debug_output_path=self.get_next_transition_tool_output_path(),
                )
            ),
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
                t8n.calc_withdrawals_root(
                    withdrawals=env.withdrawals,
                    fork=fork,
                    debug_output_path=self.get_next_transition_tool_output_path(),
                )
                if env.withdrawals is not None
                else None
            ),
        )

        genesis_rlp, genesis.hash = genesis.build(
            txs=[],
            ommers=[],
            withdrawals=env.withdrawals,
        )

        return genesis_rlp, genesis

    def make_block(
        self,
        t8n: TransitionTool,
        fork: Fork,
        block: Block,
        previous_env: Environment,
        previous_alloc: Dict[str, Any],
        previous_head: Hash,
        chain_id=1,
        eips: Optional[List[int]] = None,
    ) -> Tuple[FixtureBlock, Environment, Dict[str, Any], Hash]:
        """
        Produces a block based on the previous environment and allocation.
        If the block is an invalid block, the environment and allocation
        returned are the same as passed as parameters.
        Raises exception on invalid test behavior.

        Returns
        -------
            FixtureBlock: Block to be appended to the fixture.
            Environment: Environment for the next block to produce.
                If the produced block is invalid, this is exactly the same
                environment as the one passed as parameter.
            Dict[str, Any]: Allocation for the next block to produce.
                If the produced block is invalid, this is exactly the same
                allocation as the one passed as parameter.
            str: Hash of the head of the chain, only updated if the produced
                block is not invalid.

        """
        if block.rlp and block.exception is not None:
            raise Exception(
                "test correctness: post-state cannot be verified if the "
                + "block's rlp is supplied and the block is not supposed "
                + "to produce an exception"
            )

        if block.rlp is None:
            # This is the most common case, the RLP needs to be constructed
            # based on the transactions to be included in the block.
            # Set the environment according to the block to execute.
            env = block.set_environment(previous_env)
            env = env.set_fork_requirements(fork)

            txs = (
                [tx.with_signature_and_sender() for tx in block.txs]
                if block.txs is not None
                else []
            )

            next_alloc, result = t8n.evaluate(
                alloc=previous_alloc,
                txs=to_json(txs),
                env=to_json(env),
                fork_name=fork.fork(
                    block_number=Number(env.number), timestamp=Number(env.timestamp)
                ),
                chain_id=chain_id,
                reward=fork.get_reward(Number(env.number), Number(env.timestamp)),
                eips=eips,
                debug_output_path=self.get_next_transition_tool_output_path(),
            )
            try:
                rejected_txs = verify_transactions(txs, result)
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

            if block.rlp_modifier is not None:
                # Modify any parameter specified in the `rlp_modifier` after
                # transition tool processing.
                header = header.join(block.rlp_modifier)

            rlp, header.hash = header.build(
                txs=txs,
                ommers=[],
                withdrawals=env.withdrawals,
            )

            new_payload: FixtureEngineNewPayload | None = None
            if not self.base_test_config.disable_hive:
                new_payload = FixtureEngineNewPayload.from_fixture_header(
                    fork=fork,
                    header=header,
                    transactions=txs,
                    withdrawals=env.withdrawals,
                    error_code=block.engine_api_error_code,
                )

            if block.exception is None:
                # Return environment and allocation of the following block
                return (
                    FixtureBlock(
                        rlp=rlp,
                        new_payload=new_payload,
                        block_header=header,
                        block_number=Number(header.number),
                        txs=txs,
                        ommers=[],
                        withdrawals=env.withdrawals,
                    ),
                    env.apply_new_parent(header),
                    next_alloc,
                    header.hash,
                )
            else:
                return (
                    FixtureBlock(
                        rlp=rlp,
                        new_payload=new_payload,
                        expected_exception=block.exception,
                        block_number=Number(header.number),
                    ),
                    previous_env,
                    previous_alloc,
                    previous_head,
                )
        else:
            return (
                FixtureBlock(
                    rlp=Bytes(block.rlp),
                    expected_exception=block.exception,
                ),
                previous_env,
                previous_alloc,
                previous_head,
            )

    def make_blocks(
        self,
        t8n: TransitionTool,
        genesis: FixtureHeader,
        fork: Fork,
        chain_id=1,
        eips: Optional[List[int]] = None,
    ) -> Tuple[List[FixtureBlock], Hash, Dict[str, Any]]:
        """
        Create a block list from the blockchain test definition.
        Performs checks against the expected behavior of the test.
        Raises exception on invalid test behavior.
        """
        alloc = to_json(Alloc(self.pre))
        env = Environment.from_parent_header(genesis)
        blocks: List[FixtureBlock] = []
        head = genesis.hash if genesis.hash is not None else Hash(0)
        for block in self.blocks:
            fixture_block, env, alloc, head = self.make_block(
                t8n=t8n,
                fork=fork,
                block=block,
                previous_env=env,
                previous_alloc=alloc,
                previous_head=head,
                chain_id=chain_id,
                eips=eips,
            )
            blocks.append(fixture_block)

        try:
            verify_post_alloc(self.post, alloc)
        except Exception as e:
            print_traces(t8n.get_traces())
            raise e

        return (blocks, head, alloc)


BlockchainTestSpec = Callable[[str], Generator[BlockchainTest, None, None]]
BlockchainTestFiller = Type[BlockchainTest]
