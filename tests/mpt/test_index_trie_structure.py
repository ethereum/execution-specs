"""
Exercise Merkle Patricia Trie shapes of the transaction and receipt tries.

Both tries key on `rlp(position)`, so their shape is fixed by the number of
transactions in the block and nothing else: `rlp(0) = 0x80` sits under
nibble 8 while `rlp(1..127)` sit under nibbles 0..7, indices 128..255 get
two-byte keys `0x81xx`, and 256 onward three-byte keys `0x82xxxx`. Two-byte
keys sharing their second byte's high nibble are the only way an index trie
ever contains an extension node: at 130..144 transactions (length 1) and
from 258 on (length 3). Transaction and receipt values are always larger
than 32 bytes, so these tries never embed a node.

Pinned to the latest deployed fork so every client consumes one identical
fixture set.
"""

import pytest
from ethereum_rlp import rlp
from ethereum_types.numeric import Uint
from execution_testing import (
    Account,
    Alloc,
    Block,
    BlockchainTestFiller,
    Transaction,
)

from .trie_shape import Shape, path_shape

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"

pytestmark = pytest.mark.valid_from("Osaka")


def _shape(count: int, position: int) -> Shape:
    keys = [bytes(rlp.encode(Uint(i))) for i in range(count)]
    return path_shape(keys, keys[position], secured=False)


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
    ],
)
def test_index_trie_shapes(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    count: int,
    last_shape: Shape,
) -> None:
    """
    Pre: one funded sender, one empty recipient.
    Op: one block of `count` 1-wei transfers.
    Post: the transaction and receipt tries take the shape fixed by
    `count`. 17: key `0x10` opens the nibble-1 slot of the root branch as
    a single leaf. 129: key `0x8180` turns the nibble-8 slot into a branch
    holding the index-0 leaf and a 2-nibble leaf. 130: keys `0x8180` and
    `0x8181` share nibble 8 below `[8, 1]`, creating a 1-nibble extension
    at depth 2. 258: keys `0x820100` and `0x820101` share `[0, 1, 0]`,
    creating a 3-nibble extension at depth 2.
    Exercises: the only extension nodes an index trie can contain, plus
    the two-byte and three-byte key transitions, in both the transaction
    and the receipt trie of the same block (same keys, values > 32 bytes
    in both, so both roots are key-determined).
    """
    assert _shape(count, count - 1) == last_shape
    assert _shape(count, 0)[0] == last_shape[0]
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
