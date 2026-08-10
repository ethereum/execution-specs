"""
Tests for rebuilding served blocks from Engine API payloads.

The reconstruction self-checks each header's hash but not its body, so
these check every rebuilt body against the roots its header commits to.
"""

import dataclasses
import functools
import json
from pathlib import Path
from typing import Any, List, Sequence, Tuple, cast

import ethereum_rlp as eth_rlp
import pytest
from ethereum_types.numeric import Uint
from trie import HexaryTrie

from execution_testing.base_types import Address, Bytes
from execution_testing.fixtures.blockchain import (
    BlockchainEngineFixture,
    FixtureEngineNewPayload,
    FixtureHeader,
)
from execution_testing.test_types.block_types import Withdrawal

from ..chain import (
    Block,
    Chain,
    ChainReconstructionError,
    chain_from_payloads,
)

FIXTURES = Path(__file__).parents[2] / "specs" / "tests" / "fixtures"

ENGINE_FIXTURES = [
    "blockchain_shanghai_valid_filled_engine.json",
    "chainid_cancun_blockchain_test_engine_tx_type_0.json",
]


@functools.cache
def _fixture(name: str = ENGINE_FIXTURES[0]) -> BlockchainEngineFixture:
    """Load the single engine fixture in the file `name`."""
    (fixture,) = json.loads((FIXTURES / name).read_text()).values()
    return BlockchainEngineFixture.model_validate(fixture)


def _trie_root(items: Sequence[bytes]) -> bytes:
    """Return the root of the trie keyed by each item's index."""
    trie = HexaryTrie(db={})
    for index, item in enumerate(items):
        trie.set(eth_rlp.encode(Uint(index)), item)
    return trie.root_hash


def _decoded_body(body_rlp: bytes) -> List[Any]:
    """Decode a body into its transactions, ommers and withdrawals."""
    return cast(List[Any], eth_rlp.decode(body_rlp))


def _transaction_bytes(item: Any) -> bytes:
    """
    Return a decoded body transaction as the bytes its trie holds.

    A legacy transaction decodes as a list, a typed one as the byte
    string of its type prefix and payload.
    """
    return item if isinstance(item, bytes) else eth_rlp.encode(item)


def _shanghai_head() -> Block:
    """Return the rebuilt head block of the Shanghai engine fixture."""
    fixture = _fixture()
    return chain_from_payloads(fixture.genesis, fixture.payloads).head


def _tampered(payload: FixtureEngineNewPayload) -> FixtureEngineNewPayload:
    """Return `payload` with its extra data changed, hash unchanged."""
    execution_payload, *rest = payload.params
    changed = execution_payload.model_copy(
        update={"extra_data": Bytes(b"tampered")}
    )
    return payload.model_copy(update={"params": (changed, *rest)})


class TestChainFromPayloads:
    """A fixture's payloads rebuild into the chain they deliver."""

    @pytest.mark.parametrize("name", ENGINE_FIXTURES)
    def test_chain_from_payloads_round_trips(self, name: str) -> None:
        """Every block hashes as declared; every body matches its roots."""
        fixture = _fixture(name)
        chain = chain_from_payloads(fixture.genesis, fixture.payloads)

        assert len(chain.blocks) == len(fixture.payloads)
        assert chain.head.block_hash == bytes(fixture.last_block_hash)
        for block, payload in zip(chain.blocks, fixture.payloads, strict=True):
            execution_payload = payload.params[0]
            assert block.block_hash == bytes(execution_payload.block_hash)
            assert chain.number_of(block.block_hash) == block.number

            body_rlp = chain.body_rlp_by_hash(block.block_hash)
            assert body_rlp == block.body_rlp()
            transactions, ommers, withdrawals = _decoded_body(body_rlp)
            raw = [_transaction_bytes(item) for item in transactions]
            assert raw == [bytes(t) for t in execution_payload.transactions]
            assert _trie_root(raw) == bytes(block.header.transactions_trie)
            assert ommers == []
            assert block.header.withdrawals_root is not None
            assert _trie_root(
                [eth_rlp.encode(withdrawal) for withdrawal in withdrawals]
            ) == bytes(block.header.withdrawals_root)

    def test_a_tampered_payload_is_refused(self) -> None:
        """A payload whose fields no longer hash to its block is refused."""
        fixture = _fixture()
        payloads = list(fixture.payloads)
        payloads[1] = _tampered(payloads[1])
        with pytest.raises(ChainReconstructionError, match="hashes to"):
            chain_from_payloads(fixture.genesis, payloads)

    @pytest.mark.parametrize(
        "order",
        [
            pytest.param((1, 0, 2, 3), id="reordered"),
            pytest.param((0, 2, 3), id="gap"),
        ],
    )
    def test_a_broken_chain_is_refused(self, order: Tuple[int, ...]) -> None:
        """Blocks that do not each extend their predecessor are refused."""
        fixture = _fixture()
        payloads = [fixture.payloads[index] for index in order]
        with pytest.raises(
            ChainReconstructionError, match="does not extend its predecessor"
        ):
            chain_from_payloads(fixture.genesis, payloads)


class TestBodyShape:
    """A body carries exactly the lists its header commits to."""

    def test_withdrawals_encode_as_their_root_commits(self) -> None:
        """The served withdrawals hash to `Withdrawal.list_root`."""
        block = _shanghai_head()
        withdrawals = [
            Withdrawal(
                index=index,
                validator_index=index + 7,
                address=Address(0x100 + index),
                amount=10**9 + index,
            )
            for index in range(3)
        ]
        body = dataclasses.replace(block, withdrawals=withdrawals).body_rlp()
        _, _, served = _decoded_body(body)
        assert _trie_root(
            [eth_rlp.encode(withdrawal) for withdrawal in served]
        ) == bytes(Withdrawal.list_root(withdrawals))

    def test_a_block_without_withdrawals_serves_two_lists(self) -> None:
        """A pre-Shanghai body has no withdrawals list at all."""
        block = _shanghai_head()
        body = dataclasses.replace(block, withdrawals=None).body_rlp()
        assert len(_decoded_body(body)) == 2

    @pytest.mark.parametrize(
        "with_withdrawals,expected",
        [
            pytest.param(True, b"\xc3\xc0\xc0\xc0", id="shanghai"),
            pytest.param(False, b"\xc2\xc0\xc0", id="paris"),
        ],
    )
    def test_genesis_body_follows_its_header(
        self, with_withdrawals: bool, expected: bytes
    ) -> None:
        """Genesis has a withdrawals list exactly when it has a root."""
        shanghai = _fixture().genesis
        assert shanghai.withdrawals_root is not None
        genesis = (
            shanghai
            if with_withdrawals
            else FixtureHeader(
                **shanghai.model_dump(exclude={"withdrawals_root"})
            )
        )
        chain = Chain(genesis, [])
        assert chain.body_rlp_by_hash(bytes(genesis.block_hash)) == expected
