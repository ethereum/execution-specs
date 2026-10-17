"""
Public mempool replacement tests for
[EIP-8141: Frame Transaction](https://eips.ethereum.org/EIPS/eip-8141).

Pending frame transactions are identified by sender and nonce. A node
should keep one pending frame transaction per sender, replaced only by
one raising both fee caps by a node-configured increment, conventionally
10%, which these tests assume. Filled, the surviving transaction of
each nonce lands in a valid block: the rules are mempool policy, not
consensus.
"""

import pytest
from execution_testing import (
    Alloc,
    Fork,
    MempoolTestFiller,
    MempoolTransaction,
    Transaction,
)

from .mempool_helpers import (
    PINNED_MAX_FEE_PER_GAS,
    PINNED_MAX_PRIORITY_FEE_PER_GAS,
    PrefixShape,
    prefix_transaction,
)
from .spec import ref_spec_8141

REFERENCE_SPEC_GIT_PATH = ref_spec_8141.git_path
REFERENCE_SPEC_VERSION = ref_spec_8141.version

pytestmark = pytest.mark.valid_from("Bogota")

PRICE_BUMP_PERCENT = 10
"""Conventional minimum fee increment of a replacement."""


def bumped(fee: int) -> int:
    """Return `fee` raised by the conventional minimum increment."""
    return fee * (100 + PRICE_BUMP_PERCENT) // 100


@pytest.mark.parametrize(
    "max_fee_per_gas,max_priority_fee_per_gas,accepted",
    [
        pytest.param(
            bumped(PINNED_MAX_FEE_PER_GAS),
            bumped(PINNED_MAX_PRIORITY_FEE_PER_GAS),
            True,
            id="both_bumped",
        ),
        pytest.param(
            bumped(PINNED_MAX_FEE_PER_GAS) - 1,
            bumped(PINNED_MAX_PRIORITY_FEE_PER_GAS) - 1,
            False,
            id="both_underbumped",
        ),
        pytest.param(
            bumped(PINNED_MAX_FEE_PER_GAS),
            PINNED_MAX_PRIORITY_FEE_PER_GAS,
            False,
            id="max_fee_only",
        ),
        pytest.param(
            PINNED_MAX_FEE_PER_GAS,
            bumped(PINNED_MAX_PRIORITY_FEE_PER_GAS),
            False,
            id="priority_fee_only",
        ),
    ],
)
@pytest.mark.parametrize(
    "replacement_shape",
    [PrefixShape.SELF_VERIFY, PrefixShape.ONLY_VERIFY_PAY],
    ids=["same_payer", "new_payer"],
)
def test_replacement_fee_bump(
    mempool_test: MempoolTestFiller,
    pre: Alloc,
    fork: Fork,
    replacement_shape: PrefixShape,
    max_fee_per_gas: int,
    max_priority_fee_per_gas: int,
    accepted: bool,
) -> None:
    """
    Test that a transaction of the same sender and nonce replaces a
    pending one only by raising both fee caps by the increment, whether
    or not it names a different payer.
    """
    sender = pre.fund_eoa()
    original = prefix_transaction(
        pre,
        fork,
        PrefixShape.SELF_VERIFY,
        sender=sender,
        nonce=0,
        max_fee_per_gas=PINNED_MAX_FEE_PER_GAS,
        max_priority_fee_per_gas=PINNED_MAX_PRIORITY_FEE_PER_GAS,
    )
    replacement = prefix_transaction(
        pre,
        fork,
        replacement_shape,
        sender=sender,
        nonce=0,
        max_fee_per_gas=max_fee_per_gas,
        max_priority_fee_per_gas=max_priority_fee_per_gas,
    )
    mempool_test(
        pre=pre,
        txs=[
            MempoolTransaction(tx=original, accepted=True),
            MempoolTransaction(
                tx=replacement,
                accepted=accepted,
                reason=None if accepted else "replacement fees not bumped",
            ),
        ],
    )


def test_one_pending_transaction_per_sender(
    mempool_test: MempoolTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    Test that a frame transaction at the next nonce of a sender with a
    pending one is rejected, the node keeping one per sender.
    """
    sender = pre.fund_eoa()

    def at_nonce(nonce: int) -> Transaction:
        return prefix_transaction(
            pre, fork, PrefixShape.SELF_VERIFY, sender=sender, nonce=nonce
        )

    mempool_test(
        pre=pre,
        txs=[
            MempoolTransaction(tx=at_nonce(0), accepted=True),
            MempoolTransaction(
                tx=at_nonce(1),
                accepted=False,
                reason="sender already has a pending frame transaction",
            ),
        ],
    )
