"""
Exercise Merkle Patricia Trie node embedding via the withdrawals trie.

The withdrawals trie is unsecured (keys are `rlp(index)`) and its leaves
are tiny, so realistic payloads straddle the 32-byte inlining threshold
naturally: no preimage mining is needed. With at most 16 withdrawals per
block the trie has exactly three shapes: one entry is a root leaf, two
entries a root branch with two one-nibble leaves, three to sixteen a root
branch whose nibble-0 child is a branch of empty-path leaves. Growing
`amount` by one RLP byte moves a leaf from inlined to hashed.
"""

import pytest
from ethereum_rlp import rlp
from execution_testing import (
    Account,
    Alloc,
    Block,
    BlockchainTestFiller,
    Withdrawal,
)

from .constants import GWEI
from .trie_shape import index_shape, leaf_rlp_size

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"

pytestmark = pytest.mark.valid_from("Osaka")


def _leaf_size(count: int, withdrawal: Withdrawal) -> int:
    """Return the RLP size of `withdrawal`'s leaf in a trie of `count`."""
    depth, kind, rest = index_shape(count, int(withdrawal.index))[-1]
    assert kind == "leaf"
    value = rlp.encode(withdrawal.to_serializable_list())
    return leaf_rlp_size(rest, bytes(value))


@pytest.mark.parametrize(
    "amount,leaf_size",
    [
        pytest.param(2**16, 31, id="embedded_31"),
        pytest.param(2**24, 32, id="hashed_32"),
        pytest.param(2**32, 33, id="hashed_33"),
    ],
)
def test_withdrawal_leaf_embedding_boundary(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    amount: int,
    leaf_size: int,
) -> None:
    """
    Two withdrawals whose leaves are exactly 31, 32 or 33 bytes.

    post: branch@0 -> {8: leaf(1) index 0, 0: leaf(1) index 1}
    `amount`'s byte length decides whether the leaves are inlined.
    """
    recipient_a = pre.fund_eoa(amount=0)
    recipient_b = pre.fund_eoa(amount=0)
    withdrawals = [
        Withdrawal(
            index=0, validator_index=1, address=recipient_a, amount=amount
        ),
        Withdrawal(
            index=1, validator_index=2, address=recipient_b, amount=amount
        ),
    ]
    assert index_shape(2, 0) == [(0, "branch", 2), (1, "leaf", 1)]
    for withdrawal in withdrawals:
        assert _leaf_size(2, withdrawal) == leaf_size, withdrawal

    blockchain_test(
        pre=pre,
        post={
            recipient_a: Account(balance=amount * GWEI),
            recipient_b: Account(balance=amount * GWEI),
        },
        blocks=[Block(withdrawals=withdrawals)],
    )


def test_single_small_withdrawal_root_is_hashed(
    blockchain_test: BlockchainTestFiller, pre: Alloc
) -> None:
    """
    One 100 Gwei withdrawal: the whole trie is a 30-byte leaf.

    post: leaf(2), 30 B
    A node under 32 B is inlined everywhere except at the root, which is
    always hashed: `withdrawalsRoot` is keccak256 of the leaf RLP. State
    tries never have a root this small.
    """
    recipient = pre.fund_eoa(amount=0)
    amount = 100
    withdrawal = Withdrawal(
        index=0, validator_index=0, address=recipient, amount=amount
    )
    assert index_shape(1, 0) == [(0, "leaf", 2)]
    assert _leaf_size(1, withdrawal) == 30

    blockchain_test(
        pre=pre,
        post={recipient: Account(balance=amount * GWEI)},
        blocks=[Block(withdrawals=[withdrawal])],
    )


@pytest.mark.parametrize("count", [3, 16], ids=["count_3", "count_16"])
def test_withdrawal_branch_mixes_embedded_and_hashed(
    blockchain_test: BlockchainTestFiller, pre: Alloc, count: int
) -> None:
    """
    Three or sixteen withdrawals; odd indices inline, even ones hashed.

    post: branch@0 -> {8: leaf(1) index 0, 0: branch@1 -> {leaf(0) ..}}
    Empty-path leaves (compact prefix 0x20) cannot occur in a state trie;
    the nibble-0 branch mixes inline lists and 32-byte hashes.
    """
    recipients = [pre.fund_eoa(amount=0) for _ in range(count)]
    amounts = [2**16 if i % 2 else 2**24 for i in range(count)]
    withdrawals = [
        Withdrawal(
            index=i,
            validator_index=i,
            address=recipients[i],
            amount=amounts[i],
        )
        for i in range(count)
    ]
    assert index_shape(count, 1) == [
        (0, "branch", 2),
        (1, "branch", count - 1),
        (2, "leaf", 0),
    ]
    assert index_shape(count, 0) == [(0, "branch", 2), (1, "leaf", 1)]
    for i, withdrawal in enumerate(withdrawals[1:], start=1):
        size = _leaf_size(count, withdrawal)
        assert (size < 32) == bool(i % 2), (i, size)

    blockchain_test(
        pre=pre,
        post={
            recipient: Account(balance=amount * GWEI)
            for recipient, amount in zip(recipients, amounts, strict=True)
        },
        blocks=[Block(withdrawals=withdrawals)],
    )
