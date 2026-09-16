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
from ethereum_types.numeric import U64, Uint
from execution_testing import (
    Account,
    Alloc,
    Block,
    BlockchainTestFiller,
    Withdrawal,
)

from ethereum.forks.osaka.blocks import Withdrawal as SpecWithdrawal
from ethereum.merkle_patricia_trie import (
    bytes_to_nibble_list,
    nibble_list_to_compact,
)
from ethereum.state import Address as SpecAddress

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"

pytestmark = pytest.mark.valid_from("Osaka")

GWEI = 10**9


def _leaf_rlp_size(
    index: int, validator_index: int, address: bytes, amount: int
) -> int:
    """
    RLP size of the withdrawals-trie leaf for `index`, mirroring
    `encode_internal_node`: under 32 bytes the node is inlined into its
    parent instead of hashed.
    """
    value_rlp = rlp.encode(
        SpecWithdrawal(
            index=U64(index),
            validator_index=U64(validator_index),
            address=SpecAddress(address),
            amount=U64(amount),
        )
    )
    key_nibbles = bytes_to_nibble_list(rlp.encode(Uint(index)))
    # Indices 0 and 1 diverge at nibble 0, so the root branch consumes one
    # nibble before each leaf's own path.
    assert key_nibbles[0] in (0x8, 0x0)
    compact_key = nibble_list_to_compact(key_nibbles[1:], True)
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
    for index, recipient in ((0, recipient_a), (1, recipient_b)):
        size = _leaf_rlp_size(index, index + 1, bytes(recipient), amount)
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
