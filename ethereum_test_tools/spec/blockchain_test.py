"""
Blockchain test filler.
"""

from dataclasses import dataclass
from pprint import pprint
from typing import Any, Callable, Dict, Generator, List, Mapping, Optional, Tuple, Type

from ethereum_test_forks import Fork
from evm_block_builder import BlockBuilder
from evm_transition_tool import TransitionTool

from ..common import (
    Account,
    Block,
    EmptyTrieRoot,
    Environment,
    FixtureBlock,
    FixtureHeader,
    str_or_none,
    to_json,
    to_json_or_none,
)
from .base_test import BaseTest, verify_post_alloc, verify_transactions
from .debugging import print_traces


@dataclass(kw_only=True)
class BlockchainTest(BaseTest):
    """
    Filler type that tests multiple blocks (valid or invalid) in a chain.
    """

    pre: Mapping[str, Account]
    post: Mapping[str, Account]
    blocks: List[Block]
    genesis_environment: Environment = Environment()
    tag: str = ""

    @classmethod
    def pytest_parameter_name(cls) -> str:
        """
        Returns the parameter name used to identify this filler in a test.
        """
        return "blockchain_test"

    def make_genesis(
        self,
        b11r: BlockBuilder,
        t8n: TransitionTool,
        fork: Fork,
    ) -> Tuple[str, FixtureHeader]:
        """
        Create a genesis block from the state test definition.
        """
        env = self.genesis_environment.set_fork_requirements(fork)

        genesis = FixtureHeader(
            parent_hash="0x0000000000000000000000000000000000000000000000000000000000000000",
            ommers_hash="0x1dcc4de8dec75d7aab85b567b6ccd41ad312451b948a7413f0a142fd40d49347",
            coinbase="0x0000000000000000000000000000000000000000",
            state_root=t8n.calc_state_root(
                to_json(self.pre),
                fork,
            ),
            transactions_root=EmptyTrieRoot,
            receipt_root=EmptyTrieRoot,
            bloom="0x00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000",  # noqa: E501
            difficulty=0x20000 if env.difficulty is None else env.difficulty,
            number=0,
            gas_limit=env.gas_limit,
            gas_used=0,
            timestamp=0,
            extra_data="0x00",
            mix_digest="0x0000000000000000000000000000000000000000000000000000000000000000",
            nonce="0x0000000000000000",
            base_fee=env.base_fee,
            data_gas_used=env.data_gas_used,
            excess_data_gas=env.excess_data_gas,
            withdrawals_root=t8n.calc_withdrawals_root(env.withdrawals, fork)
            if env.withdrawals is not None
            else None,
        )

        (genesis_rlp, genesis.hash) = b11r.build(
            header=genesis.to_geth_dict(),
            txs="",
            ommers=[],
            withdrawals=env.withdrawals,
        )
        return genesis_rlp, genesis

    def make_block(
        self,
        b11r: BlockBuilder,
        t8n: TransitionTool,
        fork: Fork,
        block: Block,
        previous_env: Environment,
        previous_alloc: Dict[str, Any],
        previous_head: str,
        chain_id=1,
        eips: Optional[List[int]] = None,
    ) -> Tuple[FixtureBlock, Environment, Dict[str, Any], str]:
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

            (next_alloc, result, txs_rlp) = t8n.evaluate(
                alloc=previous_alloc,
                txs=to_json_or_none(block.txs),
                env=to_json(env),
                fork=fork,
                chain_id=chain_id,
                reward=fork.get_reward(env.number, env.timestamp),
                eips=eips,
            )
            try:
                rejected_txs = verify_transactions(block.txs, result)
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

            header = FixtureHeader.from_dict(
                result
                | {
                    "parentHash": env.parent_hash(),
                    "miner": env.coinbase,
                    "transactionsRoot": result.get("txRoot"),
                    "difficulty": str_or_none(result.get("currentDifficulty"), "0"),
                    "number": str(env.number),
                    "gasLimit": str(env.gas_limit),
                    "timestamp": str(env.timestamp),
                    "extraData": block.extra_data
                    if block.extra_data is not None and len(block.extra_data) != 0
                    else "0x",
                    "sha3Uncles": "0x1dcc4de8dec75d7aab85b567b6ccd41ad312451b948a7413f0a142fd40d49347",  # noqa: E501
                    "mixHash": "0x0000000000000000000000000000000000000000000000000000000000000000",  # noqa: E501
                    "nonce": "0x0000000000000000",
                    "baseFeePerGas": result.get("currentBaseFee"),
                    "excessDataGas": result.get("currentExcessDataGas"),
                }
            )

            assert len(header.state_root) == 66

            if block.rlp_modifier is not None:
                # Modify any parameter specified in the `rlp_modifier` after
                # transition tool processing.
                header = header.join(block.rlp_modifier)

            rlp, header.hash = b11r.build(
                header=header.to_geth_dict(),
                txs=txs_rlp,
                ommers=[],
                withdrawals=to_json_or_none(env.withdrawals),
            )

            if block.exception is None:
                # Return environment and allocation of the following block
                return (
                    FixtureBlock(
                        rlp=rlp,
                        block_header=header,
                        block_number=header.number,
                        txs=block.txs if block.txs is not None else [],
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
                        expected_exception=block.exception,
                        block_number=header.number,
                    ),
                    previous_env,
                    previous_alloc,
                    previous_head,
                )
        else:
            return (
                FixtureBlock(
                    rlp=block.rlp,
                    expected_exception=block.exception,
                ),
                previous_env,
                previous_alloc,
                previous_head,
            )

    def make_blocks(
        self,
        b11r: BlockBuilder,
        t8n: TransitionTool,
        genesis: FixtureHeader,
        fork: Fork,
        chain_id=1,
        eips: Optional[List[int]] = None,
    ) -> Tuple[List[FixtureBlock], str, Dict[str, Any]]:
        """
        Create a block list from the blockchain test definition.
        Performs checks against the expected behavior of the test.
        Raises exception on invalid test behavior.
        """
        alloc = to_json(self.pre)
        env = Environment.from_parent_header(genesis)
        blocks: List[FixtureBlock] = []
        head = (
            genesis.hash
            if genesis.hash is not None
            else "0x0000000000000000000000000000000000000000000000000000000000000000"
        )
        for block in self.blocks:
            fixture_block, env, alloc, head = self.make_block(
                b11r=b11r,
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
