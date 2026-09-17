"""
Exercise Merkle Patricia Trie node embedding via the withdrawals trie.

The withdrawals trie is unsecured (keys are `rlp(index)`) and its leaves
are tiny, so realistic payloads straddle the 32-byte embedding threshold
naturally: no preimage mining is needed, and indices 0 and 1 already
diverge at the first nibble (`rlp(0) = 0x80`, `rlp(1) = 0x01`). Growing
the `amount` field by one RLP byte at a time moves the leaf from inlined
(31 bytes) to hashed (32, 33).

Pinned to the latest deployed fork so every client consumes one identical
fixture set.
"""

import pytest
from ethereum_rlp import rlp
from ethereum_types.bytes import Bytes
from ethereum_types.numeric import U64, Uint
from execution_testing import (
    Account,
    Alloc,
    Block,
    BlockchainTestFiller,
    Withdrawal,
)

from ethereum.crypto.hash import keccak256
from ethereum.forks.osaka.blocks import Withdrawal as SpecWithdrawal
from ethereum.merkle_patricia_trie import (
    Trie,
    bytes_to_nibble_list,
    nibble_list_to_compact,
    root,
    trie_set,
)
from ethereum.state import Address as SpecAddress

from .trie_shape import Shape, path_shape

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"

pytestmark = pytest.mark.valid_from("Osaka")

GWEI = 10**9


def _keys(count: int) -> list[bytes]:
    """Withdrawals-trie keys for a block with `count` withdrawals."""
    return [bytes(rlp.encode(Uint(i))) for i in range(count)]


def _shape(count: int, index: int) -> Shape:
    return path_shape(_keys(count), _keys(index + 1)[index], secured=False)


def _value_rlp(
    index: int, validator_index: int, address: bytes, amount: int
) -> bytes:
    return bytes(
        rlp.encode(
            SpecWithdrawal(
                index=U64(index),
                validator_index=U64(validator_index),
                address=SpecAddress(address),
                amount=U64(amount),
            )
        )
    )


def _leaf_rlp_size(
    count: int, index: int, validator_index: int, address: bytes, amount: int
) -> int:
    """
    RLP size of the leaf for withdrawal `index` in a trie of `count`
    withdrawals, mirroring `encode_internal_node`: under 32 bytes the node
    is inlined into its parent instead of hashed. The remaining path
    comes from the reference trie, so the root branch, or the branch of
    empty-path leaves under nibble 0, is accounted for.
    """
    depth, kind, rest = _shape(count, index)[-1]
    assert kind == "leaf"
    key_nibbles = bytes_to_nibble_list(Bytes(_keys(index + 1)[index]))
    compact_key = nibble_list_to_compact(
        key_nibbles[-rest:] if rest else Bytes(b""), True
    )
    value_rlp = _value_rlp(index, validator_index, address, amount)
    return len(rlp.encode((compact_key, value_rlp)))


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
    Two withdrawals (indices 0 and 1) diverge at the root; each leaf's RLP
    size, set by `amount`'s byte length, decides whether it is embedded.
    """
    recipient_a = pre.fund_eoa(amount=0)
    recipient_b = pre.fund_eoa(amount=0)
    assert _shape(2, 0) == [(0, "branch", 2), (1, "leaf", 1)]
    for index, recipient in ((0, recipient_a), (1, recipient_b)):
        size = _leaf_rlp_size(2, index, index + 1, bytes(recipient), amount)
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
    Pre: no withdrawals-trie content (each block builds its own).
    Op: one block with a single withdrawal of 100 Gwei, index 0 and
    validator 0, so the whole trie is one leaf with path `[8, 0]` whose
    RLP is 30 bytes.
    Post: `withdrawalsRoot` must be keccak256 of that 30-byte RLP. A node
    under 32 bytes is embedded everywhere except at the root, where the
    root is always hashed; state-trie roots are never this small, so only
    the withdrawals trie can exercise the rule.
    Exercises: `root()` hashing an under-32-byte root node instead of
    returning its inline encoding, and the empty-trie constant not being
    confused with a small non-empty root.
    """
    recipient = pre.fund_eoa(amount=0)
    amount = 100
    assert _shape(1, 0) == [(0, "leaf", 2)]
    leaf_size = _leaf_rlp_size(1, 0, 0, bytes(recipient), amount)
    assert leaf_size == 30
    key = Bytes(_keys(1)[0])
    value = Bytes(_value_rlp(0, 0, bytes(recipient), amount))
    trie: Trie[Bytes, Bytes] = Trie(secured=False, default=Bytes(b""))
    trie_set(trie, key, value)
    leaf_rlp = rlp.encode(
        (nibble_list_to_compact(bytes_to_nibble_list(key), True), value)
    )
    assert len(leaf_rlp) == leaf_size
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
    Pre: no withdrawals-trie content (each block builds its own).
    Op: one block with `count` withdrawals; odd indices carry 2**16 Gwei,
    even ones 2**24 Gwei.
    Post: root branch -> {nibble 8: leaf for index 0 (path `[0]`),
    nibble 0: branch of `count - 1` leaves with an *empty* path}. Odd
    leaves encode to 31 bytes and are inlined in that branch, even ones to
    32 bytes and are hashed, so one branch mixes both child encodings.
    Exercises: zero-length leaf paths (compact prefix `0x20`), unreachable
    in state tries, and a branch whose children alternate between inline
    lists and 32-byte hashes. With 16 withdrawals the inner branch is at
    the protocol maximum of 15 children plus the index-0 leaf elsewhere.
    """
    recipients = [pre.fund_eoa(amount=0) for _ in range(count)]
    amounts = [2**16 if i % 2 else 2**24 for i in range(count)]
    assert _shape(count, 1) == [
        (0, "branch", 2),
        (1, "branch", count - 1),
        (2, "leaf", 0),
    ]
    assert _shape(count, 0) == [(0, "branch", 2), (1, "leaf", 1)]
    for i in range(1, count):
        size = _leaf_rlp_size(count, i, i, bytes(recipients[i]), amounts[i])
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
