"""
Public mempool validation budget tests for
[EIP-8141: Frame Transaction](https://eips.ethereum.org/EIPS/eip-8141).

The public mempool bounds the work of simulating a transaction's
validation prefix: the prefix's execution budgets plus its signature
verification gas must not exceed `MAX_VERIFY_GAS`, and its state
budgets must not exceed `MAX_VERIFY_STATE_GAS`. Each test sends a
transaction at the limit, which must be admitted, and one past it,
which must be rejected. Filled, both land in a valid block: the limits
are mempool policy, not consensus.
"""

import pytest
from execution_testing import (
    Alloc,
    Fork,
    MempoolTestFiller,
    MempoolTransaction,
)

from .mempool_helpers import PrefixShape, prefix_transaction
from .spec import Spec, ref_spec_8141

REFERENCE_SPEC_GIT_PATH = ref_spec_8141.git_path
REFERENCE_SPEC_VERSION = ref_spec_8141.version

pytestmark = pytest.mark.valid_from("Bogota")


@pytest.mark.parametrize("shape", list(PrefixShape), ids=str)
def test_verify_gas_cap(
    mempool_test: MempoolTestFiller,
    pre: Alloc,
    fork: Fork,
    shape: PrefixShape,
) -> None:
    """
    Test that a validation prefix using exactly `MAX_VERIFY_GAS` is
    admitted and one using one more is rejected.
    """
    mempool_test(
        pre=pre,
        txs=[
            MempoolTransaction(
                tx=prefix_transaction(
                    pre, fork, shape, total_verify_gas=Spec.MAX_VERIFY_GAS
                ),
                accepted=True,
            ),
            MempoolTransaction(
                tx=prefix_transaction(
                    pre, fork, shape, total_verify_gas=Spec.MAX_VERIFY_GAS + 1
                ),
                accepted=False,
                reason="validation prefix exceeds MAX_VERIFY_GAS",
            ),
        ],
    )
