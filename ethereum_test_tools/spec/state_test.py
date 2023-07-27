"""
State test filler.
"""
from dataclasses import dataclass
from typing import Any, Callable, Dict, Generator, List, Mapping, Optional, Tuple, Type

from ethereum_test_forks import Fork
from evm_transition_tool import TransitionTool

from ..common import (
    Address,
    Alloc,
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
    Transaction,
    ZeroPaddedHexNumber,
    to_json,
)
from ..common.constants import EmptyOmmersRoot, EngineAPIError
from .base_test import BaseTest, verify_post_alloc, verify_transactions
from .debugging import print_traces


@dataclass(kw_only=True)
class StateTest(BaseTest):
    """
    Filler type that tests transactions over the period of a single block.
    """

    env: Environment
    pre: Mapping
    post: Mapping
    txs: List[Transaction]
    engine_api_error_code: Optional[EngineAPIError] = None
    tag: str = ""

    @classmethod
    def pytest_parameter_name(cls) -> str:
        """
        Returns the parameter name used to identify this filler in a test.
        """
        return "state_test"

    def make_genesis(
        self,
        t8n: TransitionTool,
        fork: Fork,
    ) -> Tuple[Bytes, FixtureHeader]:
        """
        Create a genesis block from the state test definition.
        """
        env = self.env.set_fork_requirements(fork)

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
            number=ZeroPaddedHexNumber(Number(env.number) - 1),
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

    def make_blocks(
        self,
        t8n: TransitionTool,
        genesis: FixtureHeader,
        fork: Fork,
        chain_id=1,
        eips: Optional[List[int]] = None,
    ) -> Tuple[List[FixtureBlock], Hash, Dict[str, Any]]:
        """
        Create a block from the state test definition.
        Performs checks against the expected behavior of the test.
        Raises exception on invalid test behavior.
        """
        env = self.env.apply_new_parent(genesis)
        env = env.set_fork_requirements(fork)

        txs = [tx.with_signature_and_sender() for tx in self.txs] if self.txs is not None else []

        alloc, result = t8n.evaluate(
            alloc=to_json(Alloc(self.pre)),
            txs=to_json(txs),
            env=to_json(env),
            fork_name=fork.fork(block_number=Number(env.number), timestamp=Number(env.timestamp)),
            chain_id=chain_id,
            reward=fork.get_reward(Number(env.number), Number(env.timestamp)),
            eips=eips,
            debug_output_path=self.get_next_transition_tool_output_path(),
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

        env.extra_data = b"\x00"
        header = FixtureHeader.collect(
            fork=fork,
            transition_tool_result=result,
            environment=env,
        )

        block, header.hash = header.build(
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
                error_code=self.engine_api_error_code,
            )

        return (
            [
                FixtureBlock(
                    rlp=block,
                    new_payload=new_payload,
                    block_header=header,
                    txs=txs,
                    ommers=[],
                    withdrawals=env.withdrawals,
                )
            ],
            header.hash,
            alloc,
        )


StateTestSpec = Callable[[str], Generator[StateTest, None, None]]
StateTestFiller = Type[StateTest]
