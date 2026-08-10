"""
Reconstruction of consensus blocks from Engine API payloads.

An Engine X fixture stores each block as the `engine_newPayload` request
that delivers it. A payload omits the header fields the client is
expected to derive - the two transaction and withdrawal tries, and the
constants a post-merge header carries - so serving those blocks over the
wire means putting them back.

The reconstruction is self checking: a rebuilt header is only accepted if
its hash equals the block hash the payload already claims.
"""

import hashlib
import logging
from dataclasses import dataclass
from typing import Dict, List, Sequence

import ethereum_rlp as eth_rlp
from ethereum_types.numeric import Uint
from trie import HexaryTrie

from execution_testing.base_types import Bytes, Hash
from execution_testing.fixtures.blockchain import (
    FixtureEngineNewPayload,
    FixtureExecutionPayload,
    FixtureHeader,
)
from execution_testing.test_types.block_types import Withdrawal

from .protocol import encode_list, encode_transactions

logger = logging.getLogger(__name__)

EMPTY_OMMERS_HASH = Hash(
    0x1DCC4DE8DEC75D7AAB85B567B6CCD41AD312451B948A7413F0A142FD40D49347
)
"""Keccak-256 of an empty ommer list, the only value a merged chain has."""

EMPTY_OMMERS_RLP = b"\xc0"


class ChainReconstructionError(Exception):
    """Raised when a payload cannot be turned back into a valid block."""


def _requests_hash(execution_requests: Sequence[Bytes]) -> Hash:
    """
    Return the EIP-7685 requests hash over `execution_requests`.

    Each request arrives from the payload as its type byte followed by
    the request data, and the header commits to the flat sha256 scheme:
    `sha256(sha256(r_0) ++ sha256(r_1) ++ ...)`.
    """
    digest = hashlib.sha256()
    for request in execution_requests:
        digest.update(hashlib.sha256(bytes(request)).digest())
    return Hash(digest.digest())


def _transactions_root(transactions: Sequence[Bytes]) -> bytes:
    """Return the transactions trie root over raw transaction bytes."""
    trie = HexaryTrie(db={})
    for index, transaction in enumerate(transactions):
        trie.set(eth_rlp.encode(Uint(index)), transaction)
    return trie.root_hash


@dataclass
class Block:
    """One reconstructed block, ready to be served to a peer."""

    header: FixtureHeader
    transactions: List[Bytes]
    withdrawals: List[Withdrawal] | None

    @property
    def number(self) -> int:
        """Return the block number."""
        return int(self.header.number)

    @property
    def block_hash(self) -> bytes:
        """Return the block hash."""
        return bytes(self.header.block_hash)

    def header_rlp(self) -> bytes:
        """Return the RLP encoded header."""
        return bytes(self.header.rlp)

    def body_rlp(self) -> bytes:
        """Return the RLP encoded block body."""
        items = [
            encode_transactions([bytes(t) for t in self.transactions]),
            EMPTY_OMMERS_RLP,
        ]
        if self.withdrawals is not None:
            items.append(
                encode_list(
                    [
                        eth_rlp.encode(withdrawal.to_serializable_list())
                        for withdrawal in self.withdrawals
                    ]
                )
            )
        return encode_list(items)


def block_from_payload(payload: FixtureEngineNewPayload) -> Block:
    """
    Rebuild the block that `payload` delivers.

    Raise `ChainReconstructionError` if the rebuilt header does not hash
    to the block hash the payload declares, which is what would happen if
    a fork introduced a header field this reconstruction does not know
    about.
    """
    execution_payload = payload.params[0]
    if not isinstance(execution_payload, FixtureExecutionPayload):
        raise ChainReconstructionError("payload has no execution payload")

    withdrawals = execution_payload.withdrawals
    beacon_root = payload.params[2] if len(payload.params) > 2 else None
    execution_requests = payload.params[3] if len(payload.params) > 3 else None
    block_access_list = execution_payload.block_access_list

    header = FixtureHeader(
        parent_hash=execution_payload.parent_hash,
        ommers_hash=EMPTY_OMMERS_HASH,
        fee_recipient=execution_payload.fee_recipient,
        state_root=execution_payload.state_root,
        transactions_trie=Hash(
            _transactions_root(execution_payload.transactions)
        ),
        receipts_root=execution_payload.receipts_root,
        logs_bloom=execution_payload.logs_bloom,
        difficulty=0,
        number=execution_payload.number,
        gas_limit=execution_payload.gas_limit,
        gas_used=execution_payload.gas_used,
        timestamp=execution_payload.timestamp,
        extra_data=execution_payload.extra_data,
        prev_randao=execution_payload.prev_randao,
        nonce=0,
        base_fee_per_gas=execution_payload.base_fee_per_gas,
        withdrawals_root=(
            None
            if withdrawals is None
            else Hash(Withdrawal.list_root(withdrawals))
        ),
        blob_gas_used=execution_payload.blob_gas_used,
        excess_blob_gas=execution_payload.excess_blob_gas,
        parent_beacon_block_root=beacon_root,
        requests_hash=(
            None
            if execution_requests is None
            else _requests_hash(execution_requests)
        ),
        block_access_list_hash=(
            None
            if block_access_list is None
            else block_access_list.keccak256()
        ),
        slot_number=execution_payload.slot_number,
    )

    if header.block_hash != execution_payload.block_hash:
        raise ChainReconstructionError(
            f"reconstructed block {execution_payload.number} hashes to "
            f"{header.block_hash} but the payload declares "
            f"{execution_payload.block_hash}"
        )

    return Block(
        header=header,
        transactions=list(execution_payload.transactions),
        withdrawals=None if withdrawals is None else list(withdrawals),
    )


class Chain:
    """
    The canonical chain a mock peer serves for one test.

    Blocks are indexed by both number and hash because a syncing client
    walks headers backwards by hash from the head it was told to reach,
    then asks for bodies by hash.
    """

    def __init__(self, genesis: FixtureHeader, blocks: Sequence[Block]):
        """Build a chain of `blocks` descending from `genesis`."""
        self.genesis = genesis
        self.blocks = list(blocks)
        self._by_number: Dict[int, Block] = {
            block.number: block for block in self.blocks
        }
        self._by_hash: Dict[bytes, Block] = {
            block.block_hash: block for block in self.blocks
        }

    @property
    def head(self) -> Block:
        """Return the last block of the chain."""
        return self.blocks[-1]

    def header_rlp_by_hash(self, block_hash: bytes) -> bytes | None:
        """Return the RLP of the header with `block_hash`, if held."""
        if block_hash == bytes(self.genesis.block_hash):
            return bytes(self.genesis.rlp)
        block = self._by_hash.get(block_hash)
        return None if block is None else block.header_rlp()

    def header_rlp_by_number(self, number: int) -> bytes | None:
        """Return the RLP of the header at `number`, if held."""
        if number == int(self.genesis.number):
            return bytes(self.genesis.rlp)
        block = self._by_number.get(number)
        return None if block is None else block.header_rlp()

    def number_of(self, block_hash: bytes) -> int | None:
        """Return the number of the block with `block_hash`, if held."""
        if block_hash == bytes(self.genesis.block_hash):
            return int(self.genesis.number)
        block = self._by_hash.get(block_hash)
        return None if block is None else block.number

    def body_rlp_by_hash(self, block_hash: bytes) -> bytes | None:
        """
        Return the RLP of the body with `block_hash`, if held.

        The genesis body is empty by definition, but its shape follows
        its header: a genesis whose header commits to a withdrawals
        root must serve the empty withdrawals list too, or the body
        cannot validate against the header.
        """
        if block_hash == bytes(self.genesis.block_hash):
            items = [encode_list([]), EMPTY_OMMERS_RLP]
            if self.genesis.withdrawals_root is not None:
                items.append(encode_list([]))
            return encode_list(items)
        block = self._by_hash.get(block_hash)
        return None if block is None else block.body_rlp()


class ServedChains:
    """
    Every chain a peer has served over one connection.

    A client is reused across the tests of a pre-allocation group, and
    each test installs its own chain. The client's downloader does not
    forget the previous one that fast: it keeps asking for blocks of the
    chain it was syncing when the test ended. A real peer would still
    hold those blocks, so this one does too, and answers from whichever
    installed chain a requested hash belongs to.

    Requests that name a block by number are answered from the current
    chain only, since a number alone does not identify a chain.
    """

    def __init__(self) -> None:
        """Start with no chain installed."""
        self._chain_by_hash: Dict[bytes, Chain] = {}
        self._current: Chain | None = None

    def install(self, chain: Chain) -> None:
        """Serve `chain` from now on, keeping earlier chains available."""
        self._current = chain
        for block in chain.blocks:
            self._chain_by_hash.setdefault(block.block_hash, chain)

    @property
    def current(self) -> Chain:
        """Return the chain currently being served."""
        assert self._current is not None, "no chain installed"
        return self._current

    def chain_for_hash(self, block_hash: bytes) -> Chain | None:
        """Return the chain holding `block_hash`, if any."""
        if self._current is not None and block_hash == bytes(
            self._current.genesis.block_hash
        ):
            return self._current
        return self._chain_by_hash.get(block_hash)

    def header_rlp_by_hash(self, block_hash: bytes) -> bytes | None:
        """Return the RLP of the header with `block_hash`, if held."""
        chain = self.chain_for_hash(block_hash)
        return None if chain is None else chain.header_rlp_by_hash(block_hash)

    def body_rlp_by_hash(self, block_hash: bytes) -> bytes | None:
        """Return the RLP of the body with `block_hash`, if held."""
        chain = self.chain_for_hash(block_hash)
        return None if chain is None else chain.body_rlp_by_hash(block_hash)


def chain_from_payloads(
    genesis: FixtureHeader, payloads: Sequence[FixtureEngineNewPayload]
) -> Chain:
    """
    Build the chain that `payloads` describe, rooted at `genesis`.

    Every payload must reconstruct, and every block must name its
    predecessor: a chain served with a gap in it would make a client's
    sync failure look like a client bug.
    """
    blocks = [block_from_payload(payload) for payload in payloads]

    parent_hash = bytes(genesis.block_hash)
    for block in blocks:
        if bytes(block.header.parent_hash) != parent_hash:
            raise ChainReconstructionError(
                f"block {block.number} does not extend its predecessor"
            )
        parent_hash = block.block_hash

    return Chain(genesis, blocks)
