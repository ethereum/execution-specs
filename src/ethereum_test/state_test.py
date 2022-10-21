"""
State test filler.
"""
import json
import os
import tempfile
from dataclasses import dataclass
from typing import Any, Callable, Generator, List, Mapping, Tuple

from evm_block_builder import BlockBuilder
from evm_transition_tool import TransitionTool

from .common import EmptyTrieRoot
from .types import Account, Environment, Header, JSONEncoder, Transaction


@dataclass
class StateTest:
    """
    Filler type that tests transactions over the period of a single block.
    """

    env: Environment
    pre: Mapping[str, Account]
    post: Mapping[str, Account]
    txs: List[Transaction]

    def make_genesis(
        self, b11r: BlockBuilder, t8n: TransitionTool, env: Any, fork: str
    ) -> Header:
        """
        Create a genesis block from the state test definition.
        """
        genesis = Header(
            parent_hash="0x0000000000000000000000000000000000000000000000000000000000000000",  # noqa: E501
            ommers_hash="0x1dcc4de8dec75d7aab85b567b6ccd41ad312451b948a7413f0a142fd40d49347",  # noqa: E501
            coinbase=self.env.coinbase,
            state_root=t8n.calc_state_root(
                env,
                json.loads(json.dumps(self.pre, cls=JSONEncoder)),
                fork,
            ),
            transactions_root=EmptyTrieRoot,
            receipt_root=EmptyTrieRoot,
            bloom="0x00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000",  # noqa: E501
            difficulty=self.env.difficulty,
            number=self.env.number - 1,
            gas_limit=self.env.gas_limit,
            gas_used=0,
            timestamp=0,
            extra_data="0x00",
            mix_digest="0x0000000000000000000000000000000000000000000000000000000000000000",  # noqa: E501
            nonce="0x0000000000000000",
            base_fee=self.env.base_fee,
        )

        (_, h) = b11r.build(genesis.to_geth_dict(), "", [])
        genesis.hash = h

        return genesis

    def verify_post_alloc(self, alloc):
        """
        Verify that an allocation matches the expected post in the test.
        Raises exception on unexpected values.
        """
        for account in self.post:
            if self.post[account] is None:
                # If an account is None in post, it must not exist in the
                # alloc.
                if account in alloc:
                    raise Exception(f"found unexpected account: {account}")
            else:
                if account in alloc:
                    self.post[account].check_alloc(account, alloc[account])
                else:
                    raise Exception(f"expected account not found: {account}")

    def verify_txs(self, result):
        """
        Verify rejected transactions (if any) against the expected outcome.
        Raises exception on unexpected rejections or unexpected successful txs.
        """
        rejected_txs = {}
        if "rejected" in result:
            for rejected_tx in result["rejected"]:
                if "index" not in rejected_tx or "error" not in rejected_tx:
                    raise Exception("badly formatted result")
                rejected_txs[rejected_tx["index"]] = rejected_tx["error"]

        for i, tx in enumerate(self.txs):
            error = rejected_txs[i] if i in rejected_txs else None
            if tx.error and not error:
                raise Exception("tx expected to fail succeeded")
            elif not tx.error and error:
                raise Exception(f"tx unexpectedly failed: {error}")

            # TODO: Also we need a way to check we actually got the
            # correct error

    def make_block(
        self,
        b11r: BlockBuilder,
        t8n: TransitionTool,
        fork: str,
        chain_id=1,
        reward=0,
    ) -> Tuple[str, str]:
        """
        Create a block from the state test definition.
        Performs checks against the expected behavior of the test.
        Raises exception on invalid test behavior.
        """
        pre = json.loads(json.dumps(self.pre, cls=JSONEncoder))
        txs = json.loads(json.dumps(self.txs, cls=JSONEncoder))
        env = json.loads(json.dumps(self.env, cls=JSONEncoder))

        with tempfile.TemporaryDirectory() as directory:
            txsRlp = os.path.join(directory, "txs.rlp")
            (alloc, result) = t8n.evaluate(
                pre,
                txs,
                env,
                fork,
                txsPath=txsRlp,
                chain_id=chain_id,
                reward=reward,
            )
            with open(txsRlp, "r") as file:
                txs = file.read().strip('"')

        self.verify_txs(result)
        self.verify_post_alloc(alloc)

        header = result | {
            "parentHash": self.env.previous,
            "miner": self.env.coinbase,
            "transactionsRoot": result.get("txRoot"),
            "difficulty": hex(self.env.difficulty),
            "number": str(self.env.number),
            "gasLimit": str(self.env.gas_limit),
            "timestamp": str(self.env.timestamp),
            "extraData": self.env.extra_data
            if len(self.env.extra_data) != 0
            else "0x",
        }
        if self.env.base_fee is not None:
            header["baseFeePerGas"] = str(self.env.base_fee)

        return b11r.build(header, txs, [], None)


StateTestSpec = Callable[[str], Generator[StateTest, None, None]]
