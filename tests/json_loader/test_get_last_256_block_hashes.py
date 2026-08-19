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


def test_empty_chain() -> None:
    """Return no hashes when the chain has no blocks."""
    chain, hashes = _make_chain(0)
    assert hashes == []
    assert get_last_256_block_hashes(chain) == []


def test_one_block() -> None:
    """Include the genesis parent and the only block hash."""
    chain, hashes = _make_chain(1)
    result = get_last_256_block_hashes(chain)
    assert result == [ZERO_HASH, hashes[0]]
    assert result[-1] == _header_hash(chain.blocks[-1].header)


@pytest.mark.parametrize(
    "length",
    [
        pytest.param(2, id="two_blocks"),
        pytest.param(254, id="less_than_256"),
        pytest.param(255, id="exactly_255"),
        pytest.param(256, id="exactly_256"),
        pytest.param(257, id="more_than_256"),
    ],
)
def test_hash_window(length: int) -> None:
    """Match length, order, and the keccak of the latest header."""
    chain, hashes = _make_chain(length)
    result = get_last_256_block_hashes(chain)
    expected = _expected_hashes(hashes)

    assert result == expected
    assert len(result) == min(length + 1, 256)
    assert result[-1] == _header_hash(chain.blocks[-1].header)
    if length >= 2:
        assert result[-2] == chain.blocks[-1].header.parent_hash
        assert result[-2] == _header_hash(chain.blocks[-2].header)


def test_window_drops_oldest_after_256() -> None:
    """Drop the genesis hash once 257 blocks are on the chain."""
    chain_256, hashes_256 = _make_chain(256)
    chain_257, hashes_257 = _make_chain(257)

    result_256 = get_last_256_block_hashes(chain_256)
    result_257 = get_last_256_block_hashes(chain_257)

    assert result_256 == hashes_256
    assert result_256[0] == hashes_256[0]
    assert ZERO_HASH not in result_256
    assert result_257 == hashes_257[-256:]
    assert result_257[0] == hashes_257[1]
    assert hashes_257[0] not in result_257


def test_hashes_are_in_increasing_block_number_order() -> None:
    """Keep older hashes before newer hashes."""
    chain, hashes = _make_chain(257)
    result = get_last_256_block_hashes(chain)
    for index in range(len(result) - 1):
        older = result[index]
        newer = result[index + 1]
        older_number = hashes.index(older)
        newer_number = hashes.index(newer)
        assert older_number < newer_number
