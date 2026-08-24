"""Unit tests for Frontier ``get_last_256_block_hashes``."""

from typing import List, Tuple

import pytest
from ethereum_rlp import rlp
from ethereum_types.bytes import Bytes8, Bytes32
from ethereum_types.numeric import U64, U256, Uint

from ethereum.crypto.hash import Hash32, keccak256
from ethereum.forks.frontier.blocks import Block, Header
from ethereum.forks.frontier.fork import BlockChain, get_last_256_block_hashes
from ethereum.forks.frontier.fork_types import Bloom
from ethereum.state import Address
from ethereum.state_mpt import State

ZERO_HASH = Hash32(b"\0" * 32)
EMPTY_BLOOM = Bloom(b"\0" * 256)
EMPTY_OMMERS_HASH = keccak256(rlp.encode(()))


def _header_hash(header: Header) -> Hash32:
    """Return ``keccak256(rlp(header))``."""
    return Hash32(keccak256(rlp.encode(header)))


def _make_header(parent_hash: Hash32, number: int) -> Header:
    """Return a dummy Frontier header unique for ``number``."""
    return Header(
        parent_hash=parent_hash,
        ommers_hash=EMPTY_OMMERS_HASH,
        coinbase=Address(b"\0" * 20),
        state_root=ZERO_HASH,
        transactions_root=ZERO_HASH,
        receipt_root=ZERO_HASH,
        bloom=EMPTY_BLOOM,
        difficulty=Uint(1),
        number=Uint(number),
        gas_limit=Uint(1),
        gas_used=Uint(0),
        timestamp=U256(number),
        extra_data=number.to_bytes(2, "big"),
        mix_digest=Bytes32(b"\0" * 32),
        nonce=Bytes8(b"\0" * 8),
    )


def _make_chain(length: int) -> Tuple[BlockChain, List[Hash32]]:
    """Build a linked dummy chain of ``length`` blocks."""
    blocks: List[Block] = []
    hashes: List[Hash32] = []
    parent_hash = ZERO_HASH
    for number in range(length):
        header = _make_header(parent_hash, number)
        block_hash = _header_hash(header)
        blocks.append(Block(header=header, transactions=(), ommers=()))
        hashes.append(block_hash)
        parent_hash = block_hash
    chain = BlockChain(blocks=blocks, state=State(), chain_id=U64(1))
    return chain, hashes


def _expected_hashes(block_hashes: List[Hash32]) -> List[Hash32]:
    """Return the expected window: oldest first, at most 256 hashes."""
    count = len(block_hashes)
    if count == 0:
        return []
    if count < 256:
        return [ZERO_HASH, *block_hashes]
    return block_hashes[-256:]


@pytest.mark.parametrize(
    "length",
    [
        pytest.param(0, id="empty_chain"),
        pytest.param(1, id="one_block"),
        pytest.param(255, id="last_untruncated_length"),
        pytest.param(256, id="first_truncation"),
        pytest.param(257, id="genesis_hash_dropped"),
    ],
)
def test_hash_window(length: int) -> None:
    """Match the expected window and the keccak of the latest header."""
    chain, hashes = _make_chain(length)
    result = get_last_256_block_hashes(chain)
    assert result == _expected_hashes(hashes)
    if length > 0:
        assert result[-1] == _header_hash(chain.blocks[-1].header)
