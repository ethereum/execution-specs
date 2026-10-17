"""
Public mempool payer exposure tests for
[EIP-8141: Frame Transaction](https://eips.ethereum.org/EIPS/eip-8141).

A node must not hold pending frame transactions whose summed maximum
costs exceed their payer's balance, so that a single balance change
cannot invalidate an unbounded set of them. Filled, every transaction
lands in a valid block, the payer settling each one's actual cost
before the next collects its maximum: the bound is mempool policy, not
consensus.
"""

import pytest
from execution_testing import (
    EOA,
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
    frame_max_cost_bounds,
    prefix_transaction,
)
from .spec import ref_spec_8141

REFERENCE_SPEC_GIT_PATH = ref_spec_8141.git_path
REFERENCE_SPEC_VERSION = ref_spec_8141.version

pytestmark = pytest.mark.valid_from("Bogota")

STAND_IN_SPONSOR = EOA(key=1)
"""Sponsor of the template transaction pricing the sponsored ones."""


def sponsored(
    pre: Alloc, fork: Fork, sponsor: EOA, sender: EOA
) -> Transaction:
    """Return a transaction by `sender` paid by `sponsor` at pinned fees."""
    return prefix_transaction(
        pre,
        fork,
        PrefixShape.ONLY_VERIFY_PAY,
        payer=sponsor,
        sender=sender,
        nonce=0,
        max_fee_per_gas=PINNED_MAX_FEE_PER_GAS,
        max_priority_fee_per_gas=PINNED_MAX_PRIORITY_FEE_PER_GAS,
    )


def test_payer_exposure(
    mempool_test: MempoolTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    Test that a sponsor covering the summed maximum costs of two pending
    transactions backs both, while one short of that backs only the
    first.

    A sponsor's address and the signature bytes are only known once the
    sponsor is funded, so the balances bound the maximum cost over every
    value of those bytes.
    """
    senders = [pre.fund_eoa(amount=1) for _ in range(4)]
    least, greatest = frame_max_cost_bounds(
        fork, sponsored(pre, fork, STAND_IN_SPONSOR, senders[0])
    )
    covering = pre.fund_eoa(amount=2 * greatest)
    short = pre.fund_eoa(amount=2 * least - 1)
    mempool_test(
        pre=pre,
        txs=[
            MempoolTransaction(
                tx=sponsored(pre, fork, covering, senders[0]), accepted=True
            ),
            MempoolTransaction(
                tx=sponsored(pre, fork, covering, senders[1]), accepted=True
            ),
            MempoolTransaction(
                tx=sponsored(pre, fork, short, senders[2]), accepted=True
            ),
            MempoolTransaction(
                tx=sponsored(pre, fork, short, senders[3]),
                accepted=False,
                reason="pending maximum costs exceed the payer's balance",
            ),
        ],
    )
