"""
abstract: Filler self-tests (canaries) for receipt-status verification.

   These tests exist to prove, during a real fill session, that the
   filler verifies receipt statuses against ``expected_receipt_status``.
   The mismatch canary is marked ``xfail(strict=True)``: the session
   passes only when the filler raises the receipt-status mismatch. If
   verification ever silently stops working, the canary XPASSes and
   fails the session. They run in every fill mode; against a live
   client (fill-stateful) they additionally prove statuses are read
   back correctly via ``eth_getTransactionReceipt``.
"""

import pytest
from execution_testing import (
    Alloc,
    BenchmarkTestFiller,
    Block,
    Op,
    Transaction,
)

REFERENCE_SPEC_GIT_PATH = "DUMMY/bloatnet.md"
REFERENCE_SPEC_VERSION = "1.0"


@pytest.mark.xfail(
    strict=True,
    raises=Exception,
    reason=(
        "Filler self-test: the transaction reverts (status 0) while the "
        "test expects status 1, so the filler must refuse to fill."
    ),
)
def test_receipt_status_mismatch_fails_fill(
    benchmark_test: BenchmarkTestFiller,
    pre: Alloc,
) -> None:
    """
    Canary: a reverting transaction with ``expected_receipt_status=1``
    must abort the fill with a receipt-status mismatch.
    """
    reverter = pre.deploy_contract(code=Op.REVERT(0, 0))
    tx = Transaction(
        to=reverter,
        sender=pre.fund_eoa(),
    )

    benchmark_test(
        pre=pre,
        post={},
        blocks=[Block(txs=[tx])],
        expected_receipt_status=1,
        skip_gas_used_validation=True,
    )


def test_receipt_status_expected_revert_fills(
    benchmark_test: BenchmarkTestFiller,
    pre: Alloc,
) -> None:
    """
    Control for the canary above: the same reverting transaction with
    ``expected_receipt_status=0`` must fill normally, proving the
    receipt status is actually read back as 0 rather than the mismatch
    being masked by a missing receipt lookup.
    """
    reverter = pre.deploy_contract(code=Op.REVERT(0, 0))
    tx = Transaction(
        to=reverter,
        sender=pre.fund_eoa(),
    )

    benchmark_test(
        pre=pre,
        post={},
        blocks=[Block(txs=[tx])],
        expected_receipt_status=0,
        skip_gas_used_validation=True,
    )
