"""
Mainnet marked execute checklist tests for
[EIP-7778: Block Gas Accounting without Refunds](https://eips.ethereum.org/EIPS/eip-7778).
"""

import pytest
from execution_testing import (
    Alloc,
    Fork,
    Header,
    RefundTypes,
    StateTestFiller,
)

from .helpers import RefundTransaction
from .spec import ref_spec_7778

REFERENCE_SPEC_GIT_PATH = ref_spec_7778.git_path
REFERENCE_SPEC_VERSION = ref_spec_7778.version

pytestmark = [pytest.mark.valid_at("EIP7778"), pytest.mark.mainnet]


def test_storage_clear_refund_mainnet(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    Test that a storage-clearing transaction still refunds the sender
    while the block is charged the gas used before the refund.

    The sender's balance change is the only side of EIP-7778 a live
    network exposes per transaction, so it carries the refund; the
    block's own accounting is pinned by the header at fill time.
    """
    refund_tx = RefundTransaction.build(
        fork=fork,
        sender=pre.fund_eoa(),
        refund_types={RefundTypes.STORAGE_CLEAR},
    )
    refund_tx.set_pre(pre)

    state_test(
        pre=pre,
        tx=refund_tx,
        post=refund_tx.post(pre),
        blockchain_test_header_verify=Header(
            gas_used=refund_tx.block_gas_used()
        ),
    )
