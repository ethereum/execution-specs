"""
Public mempool paymaster tests for
[EIP-8141: Frame Transaction](https://eips.ethereum.org/EIPS/eip-8141).

A paymaster contract whose code is not the canonical implementation may
back at most `MAX_PENDING_TXS_USING_NON_CANONICAL_PAYMASTER` pending
transactions, as its state could invalidate all of them at once, while
a sponsor running the default code is not a paymaster and is bounded by
its balance alone. Filled, every transaction lands in a valid block:
the limit is mempool policy, not consensus.
"""

import pytest
from execution_testing import (
    Alloc,
    Fork,
    MempoolTestFiller,
    MempoolTransaction,
)

from .mempool_helpers import (
    PrefixShape,
    deploy_paymaster,
    prefix_transaction,
)
from .spec import Spec, ref_spec_8141

REFERENCE_SPEC_GIT_PATH = ref_spec_8141.git_path
REFERENCE_SPEC_VERSION = ref_spec_8141.version

pytestmark = pytest.mark.valid_from("Bogota")


def test_non_canonical_paymaster_pending_cap(
    mempool_test: MempoolTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    Test that a non-canonical paymaster backs no more pending
    transactions than the cap, whichever senders send them.
    """
    paymaster = deploy_paymaster(pre)
    cap = Spec.MAX_PENDING_TXS_USING_NON_CANONICAL_PAYMASTER
    mempool_test(
        pre=pre,
        txs=[
            MempoolTransaction(
                tx=prefix_transaction(
                    pre, fork, PrefixShape.ONLY_VERIFY_PAY, payer=paymaster
                ),
                accepted=True,
            )
            for _ in range(cap)
        ]
        + [
            MempoolTransaction(
                tx=prefix_transaction(
                    pre, fork, PrefixShape.ONLY_VERIFY_PAY, payer=paymaster
                ),
                accepted=False,
                reason="non-canonical paymaster backs too many pending txs",
            ),
        ],
    )


def test_default_code_sponsor_is_not_capped(
    mempool_test: MempoolTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    Test that a sponsor running the default code may back more pending
    transactions than a non-canonical paymaster, its balance covering
    them all.
    """
    sponsor = pre.fund_eoa()
    count = Spec.MAX_PENDING_TXS_USING_NON_CANONICAL_PAYMASTER + 1
    mempool_test(
        pre=pre,
        txs=[
            MempoolTransaction(
                tx=prefix_transaction(
                    pre, fork, PrefixShape.ONLY_VERIFY_PAY, payer=sponsor
                ),
                accepted=True,
            )
            for _ in range(count)
        ],
    )
