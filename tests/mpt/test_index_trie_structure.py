"""
Exercise Merkle Patricia Trie shapes of the transaction and receipt tries.

Both tries key on `rlp(position)`, so their shape is a function of the
transaction count alone: `rlp(0) = 0x80` sits under nibble 8, `1..127`
under nibbles 0..7, `128..255` have two-byte keys `0x81xx`, and 256 onward
three-byte keys `0x82xxxx`. Keys sharing a byte's high nibble are the only
way an index trie contains an extension: a 1-nibble one from 130 to 144
entries and a 3-nibble one from 258, split at its last nibble from 273.
Dense sequential indices never break an extension anywhere but its last
nibble. Transaction and receipt values exceed 32 bytes, so these tries
never inline a node.
"""

import pytest
from execution_testing import (
    Account,
    Alloc,
    Block,
    BlockchainTestFiller,
    Transaction,
)

from .trie_shape import Shape, index_shape

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"

pytestmark = pytest.mark.valid_from("Osaka")


@pytest.mark.parametrize(
    "count,last_shape",
    [
        pytest.param(
            17,
            [(0, "branch", 3), (1, "leaf", 1)],
            id="txs_17",
        ),
        pytest.param(
            129,
            [(0, "branch", 9), (1, "branch", 2), (2, "leaf", 2)],
            id="txs_129",
        ),
        pytest.param(
            130,
            [
                (0, "branch", 9),
                (1, "branch", 2),
                (2, "ext", 1),
                (3, "branch", 2),
                (4, "leaf", 0),
            ],
            id="txs_130",
        ),
        pytest.param(
            145,
            [
                (0, "branch", 9),
                (1, "branch", 2),
                (2, "branch", 2),
                (3, "leaf", 1),
            ],
            id="txs_145",
        ),
        pytest.param(
            257,
            [(0, "branch", 9), (1, "branch", 3), (2, "leaf", 4)],
            id="txs_257",
        ),
        pytest.param(
            258,
            [
                (0, "branch", 9),
                (1, "branch", 3),
                (2, "ext", 3),
                (5, "branch", 2),
                (6, "leaf", 0),
            ],
            id="txs_258",
        ),
        pytest.param(
            273,
            [
                (0, "branch", 9),
                (1, "branch", 3),
                (2, "ext", 2),
                (4, "branch", 2),
                (5, "leaf", 1),
            ],
            id="txs_273",
        ),
    ],
)
def test_index_trie_shapes(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    count: int,
    last_shape: Shape,
) -> None:
    """
    One block of `count` transfers; the index tries take the shape below.

    post along the last key:
      17:  branch@0 -> {.., 1: leaf(1)}                 nibble-1 slot opens
      129: branch@0 -> {8: branch@1 -> {leaf(0), leaf(2)}}
      130: .. -> branch@1 -> {.., 1: ext(1) -> branch@3}   1-nibble ext
      145: .. -> branch@1 -> {.., 1: branch@2}             the ext dissolves
      257: branch@0 -> {8: branch@1 -> {.., 2: leaf(4)}}   3-byte key
      258: .. -> branch@1 -> {.., 2: ext(3) -> branch@5}   3-nibble ext
      273: .. -> branch@1 -> {.., 2: ext(2) -> branch@4}   split at last nibble
    Same keys drive the receipts trie of the block.
    """
    assert index_shape(count, count - 1) == last_shape
    assert index_shape(count, 0)[0] == last_shape[0]
    sender = pre.fund_eoa()
    recipient = pre.fund_eoa(amount=0)

    blockchain_test(
        pre=pre,
        post={recipient: Account(balance=count)},
        blocks=[
            Block(
                txs=[
                    Transaction(sender=sender, to=recipient, value=1)
                    for _ in range(count)
                ]
            )
        ],
    )
