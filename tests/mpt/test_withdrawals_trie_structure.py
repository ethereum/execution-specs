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
from ethereum_types.bytes import Bytes, Bytes20
from ethereum_types.numeric import U64, Uint
from execution_testing import (
    Account,
    Alloc,
    Block,
    BlockchainTestFiller,
    Withdrawal,
)

from ethereum.crypto.hash import keccak256
from ethereum.merkle_patricia_trie import (
    Trie,
    bytes_to_nibble_list,
    nibble_list_to_compact,
    root,
    trie_set,
)

from .trie_shape import index_shape, leaf_rlp_size

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"

pytestmark = pytest.mark.valid_from("Osaka")

GWEI = 10**9


def _key(index: int) -> bytes:
    return bytes(rlp.encode(Uint(index)))


def _value_rlp(
    index: int, validator_index: int, address: bytes, amount: int
) -> bytes:
    """RLP of the withdrawal object stored in the trie."""
    return bytes(
        rlp.encode(
            (U64(index), U64(validator_index), Bytes20(address), U64(amount))
        )
    )


def _leaf_size(
    count: int, index: int, validator_index: int, address: bytes, amount: int
) -> int:
    """RLP size of the leaf for `index` in a trie of `count` withdrawals."""
    depth, kind, rest = index_shape(count, index)[-1]
    assert kind == "leaf"
    return leaf_rlp_size(
        rest, _value_rlp(index, validator_index, address, amount)
    )


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
    assert index_shape(2, 0) == [(0, "branch", 2), (1, "leaf", 1)]
    for index, recipient in ((0, recipient_a), (1, recipient_b)):
        size = _leaf_size(2, index, index + 1, bytes(recipient), amount)
        assert size == leaf_size, (index, size)

    blockchain_test(
        pre=pre,
        post={
            recipient_a: Account(balance=amount * GWEI),
            recipient_b: Account(balance=amount * GWEI),
        },
        blocks=[
            Block(
                withdrawals=[
                    Withdrawal(
                        index=0,
                        validator_index=1,
                        address=recipient_a,
                        amount=amount,
                    ),
                    Withdrawal(
                        index=1,
                        validator_index=2,
                        address=recipient_b,
                        amount=amount,
                    ),
                ]
            )
        ],
    )


def test_single_small_withdrawal_root_is_hashed(
    blockchain_test: BlockchainTestFiller, pre: Alloc
) -> None:
    """
    One 100 Gwei withdrawal: the whole trie is a 30-byte leaf.

    post: leaf(2), 30 bytes
    A node under 32 bytes is inlined everywhere except at the root, which
    is always hashed; `withdrawalsRoot` is keccak256 of the leaf RLP.
    State-trie roots are never this small.
    """
    recipient = pre.fund_eoa(amount=0)
    amount = 100
    assert index_shape(1, 0) == [(0, "leaf", 2)]
    assert _leaf_size(1, 0, 0, bytes(recipient), amount) == 30
    key = Bytes(_key(0))
    value = Bytes(_value_rlp(0, 0, bytes(recipient), amount))
    trie: Trie[Bytes, Bytes] = Trie(secured=False, default=Bytes(b""))
    trie_set(trie, key, value)
    leaf_rlp = rlp.encode(
        (nibble_list_to_compact(bytes_to_nibble_list(key), True), value)
    )
    assert root(trie) == keccak256(leaf_rlp)

    blockchain_test(
        pre=pre,
        post={recipient: Account(balance=amount * GWEI)},
        blocks=[
            Block(
                withdrawals=[
                    Withdrawal(
                        index=0,
                        validator_index=0,
                        address=recipient,
                        amount=amount,
                    )
                ]
            )
        ],
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
    assert index_shape(count, 1) == [
        (0, "branch", 2),
        (1, "branch", count - 1),
        (2, "leaf", 0),
    ]
    assert index_shape(count, 0) == [(0, "branch", 2), (1, "leaf", 1)]
    for i in range(1, count):
        size = _leaf_size(count, i, i, bytes(recipients[i]), amounts[i])
        assert (size < 32) == bool(i % 2), (i, size)

    blockchain_test(
        pre=pre,
        post={
            recipient: Account(balance=amount * GWEI)
            for recipient, amount in zip(recipients, amounts, strict=True)
        },
        blocks=[
            Block(
                withdrawals=[
                    Withdrawal(
                        index=i,
                        validator_index=i,
                        address=recipients[i],
                        amount=amounts[i],
                    )
                    for i in range(count)
                ]
            )
        ],
    )
