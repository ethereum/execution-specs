"""
State test filler.
"""
from dataclasses import dataclass
from typing import Any, Callable, Dict, Generator, List, Mapping, Optional, Tuple, Type

from ethereum_test_forks import Fork
from evm_block_builder import BlockBuilder
from evm_transition_tool import TransitionTool

from ..common import (
    Account,
    EmptyTrieRoot,
    Environment,
    FixtureBlock,
    FixtureHeader,
    Transaction,
    serialize_transactions,
    str_or_none,
    to_json,
    to_json_or_none,
)
from .base_test import BaseTest, verify_post_alloc, verify_transactions
from .debugging import print_traces


@dataclass(kw_only=True)
class StateTest(BaseTest):
    """
    Filler type that tests transactions over the period of a single block.
    """

    env: Environment
    pre: Mapping[str, Account]
    post: Mapping[str, Account]
    txs: List[Transaction]
    tag: str = ""

    @classmethod
    def pytest_parameter_name(cls) -> str:
        """
        Returns the parameter name used to identify this filler in a test.
        """
        return "state_test"

    def make_genesis(
        self,
        b11r: BlockBuilder,
        t8n: TransitionTool,
        fork: Fork,
    ) -> Tuple[str, FixtureHeader]:
        """
        Create a genesis block from the state test definition.
        """
        env = self.env.set_fork_requirements(fork)

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
            number=env.number - 1,
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
            serialized_txs=bytes(),
            ommers=[],
            withdrawals=env.withdrawals,
        )
        return genesis_rlp, genesis

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
        Create a block from the state test definition.
        Performs checks against the expected behavior of the test.
        Raises exception on invalid test behavior.
        """
        env = self.env.apply_new_parent(genesis)
        env = env.set_fork_requirements(fork)

        txs = [tx.with_signature_and_sender() for tx in self.txs] if self.txs is not None else []

        alloc, result = t8n.evaluate(
            alloc=to_json(self.pre),
            txs=to_json(txs),
            env=to_json(env),
            fork=fork,
            chain_id=chain_id,
            reward=fork.get_reward(env.number, env.timestamp),
            eips=eips,
        )

        rejected_txs = verify_transactions(txs, result)
        if len(rejected_txs) > 0:
            raise Exception(
                "one or more transactions in `StateTest` are "
                + "intrinsically invalid, which are not allowed. "
                + "Use `BlockchainTest` to verify rejection of blocks "
                + "that include invalid transactions."
            )

        try:
            verify_post_alloc(self.post, alloc)
        except Exception as e:
            print_traces(traces=t8n.get_traces())
            raise e

        header = FixtureHeader.from_dict(
            result
            | {
                "parentHash": genesis.hash,
                "miner": env.coinbase,
                "transactionsRoot": result.get("txRoot"),
                "difficulty": str_or_none(env.difficulty, result.get("currentDifficulty")),
                "number": str(env.number),
                "gasLimit": str(env.gas_limit),
                "timestamp": str(env.timestamp),
                "extraData": "0x00",
                "sha3Uncles": "0x1dcc4de8dec75d7aab85b567b6ccd41ad312451b948a7413f0a142fd40d49347",
                "mixHash": "0x0000000000000000000000000000000000000000000000000000000000000000",
                "nonce": "0x0000000000000000",
                "baseFeePerGas": result.get("currentBaseFee"),
                "excessDataGas": result.get("currentExcessDataGas"),
            }
        )

        block, head = b11r.build(
            header=header.to_geth_dict(),
            serialized_txs=serialize_transactions(txs),
            ommers=[],
            withdrawals=to_json_or_none(env.withdrawals),
        )
        header.hash = head

        return (
            [
                FixtureBlock(
                    rlp=block,
                    block_header=header,
                    txs=txs,
                    ommers=[],
                    withdrawals=env.withdrawals,
                )
            ],
            head,
            alloc,
        )


StateTestSpec = Callable[[str], Generator[StateTest, None, None]]
StateTestFiller = Type[StateTest]
