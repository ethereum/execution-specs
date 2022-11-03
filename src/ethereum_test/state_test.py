"""
State test filler.
"""
import json
import os
import tempfile
from dataclasses import dataclass
from typing import Callable, Generator, List, Mapping, Tuple

from evm_block_builder import BlockBuilder
from evm_transition_tool import TransitionTool

from .base_test import BaseTest, verify_post_alloc, verify_transactions
from .common import EmptyTrieRoot
from .fork import is_london
from .types import (
    Account,
    Environment,
    FixtureBlock,
    FixtureHeader,
    JSONEncoder,
    Transaction,
)

default_base_fee = 7
"""
Default base_fee used in the genesis and block 1 for the StateTests.
"""


@dataclass(kw_only=True)
class StateTest(BaseTest):
    """
    Filler type that tests transactions over the period of a single block.
    """

    env: Environment
    pre: Mapping[str, Account]
    post: Mapping[str, Account]
    txs: List[Transaction]

    def make_genesis(
        self,
        b11r: BlockBuilder,
        t8n: TransitionTool,
        fork: str,
    ) -> FixtureHeader:
        """
        Create a genesis block from the state test definition.
        """
        base_fee = self.env.base_fee
        if is_london(fork) and base_fee is None:
            # If there is no base fee specified in the environment, we use a
            # default.
            base_fee = default_base_fee
        elif not is_london(fork) and base_fee is not None:
            base_fee = None

        genesis = FixtureHeader(
            parent_hash="0x0000000000000000000000000000000000000000000000000000000000000000",  # noqa: E501
            ommers_hash="0x1dcc4de8dec75d7aab85b567b6ccd41ad312451b948a7413f0a142fd40d49347",  # noqa: E501
            coinbase="0x0000000000000000000000000000000000000000",
            state_root=t8n.calc_state_root(
                self.env,
                json.loads(json.dumps(self.pre, cls=JSONEncoder)),
                fork,
            ),
            transactions_root=EmptyTrieRoot,
            receipt_root=EmptyTrieRoot,
            bloom="0x00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000",  # noqa: E501
            difficulty=0x20000,
            number=self.env.number - 1,
            gas_limit=self.env.gas_limit,
            # We need the base fee to remain unchanged from the genesis
            # to block 1.
            # To do that we set the gas used to exactly half of the limit
            # so the base fee is unchanged.
            gas_used=self.env.gas_limit // 2,
            timestamp=0,
            extra_data="0x00",
            mix_digest="0x0000000000000000000000000000000000000000000000000000000000000000",  # noqa: E501
            nonce="0x0000000000000000",
            base_fee=base_fee,
        )

        (_, h) = b11r.build(genesis.to_geth_dict(), "", [])
        genesis.hash = h

        return genesis

    def make_blocks(
        self,
        b11r: BlockBuilder,
        t8n: TransitionTool,
        genesis: FixtureHeader,
        fork: str,
        chain_id=1,
        reward=0,
    ) -> Tuple[List[FixtureBlock], str]:
        """
        Create a block from the state test definition.
        Performs checks against the expected behavior of the test.
        Raises exception on invalid test behavior.
        """
        env = self.env.apply_new_parent(genesis)
        if env.base_fee is None and is_london(fork):
            env.base_fee = default_base_fee
        pre = json.loads(json.dumps(self.pre, cls=JSONEncoder))
        txs = json.loads(json.dumps(self.txs, cls=JSONEncoder))

        with tempfile.TemporaryDirectory() as directory:
            txsRlp = os.path.join(directory, "txs.rlp")
            (alloc, result) = t8n.evaluate(
                pre,
                txs,
                json.loads(json.dumps(env, cls=JSONEncoder)),
                fork,
                txsPath=txsRlp,
                chain_id=chain_id,
                reward=reward,
            )
            with open(txsRlp, "r") as file:
                txs = file.read().strip('"')

        rejected_txs = verify_transactions(self.txs, result)
        if len(rejected_txs) > 0:
            raise Exception(
                "one or more transactions in `StateTest` are "
                + "intrinsically invalid, which are not allowed. "
                + "Use `BlockchainTest` to verify rejection of blocks "
                + "that include invalid transactions."
            )

        verify_post_alloc(self.post, alloc)

        header = result | {
            "parentHash": genesis.hash,
            "miner": env.coinbase,
            "transactionsRoot": result.get("txRoot"),
            "difficulty": hex(env.difficulty)
            if env.difficulty is not None
            else result.get("currentDifficulty"),
            "number": str(env.number),
            "gasLimit": str(env.gas_limit),
            "timestamp": str(env.timestamp),
            "extraData": "0x00",
            "sha3Uncles": "0x1dcc4de8dec75d7aab85b567b6ccd41ad312451b948a7413f0a142fd40d49347",  # noqa: E501
            "mixHash": "0x0000000000000000000000000000000000000000000000000000000000000000",  # noqa: E501
            "nonce": "0x0000000000000000",
        }
        if env.base_fee is not None:
            header["baseFeePerGas"] = str(env.base_fee)
        block, head = b11r.build(header, txs, [], None)
        header["hash"] = head
        return (
            [
                FixtureBlock(
                    rlp=block,
                    block_header=FixtureHeader.from_dict(header),
                )
            ],
            head,
        )


StateTestSpec = Callable[[str], Generator[StateTest, None, None]]
