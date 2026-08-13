"""
Admission validity tests for
[EIP-8141: Frame Transaction](https://eips.ethereum.org/EIPS/eip-8141).

The rules here need context beyond the transaction itself — the block
environment or the sender's account state — so their verdicts are
pinned only by state tests: a client cannot generally evaluate them on
the transaction alone and may accept such a transaction at that level.
Rules decidable from the transaction alone are in
`test_static_validity.py`, where every case is also pinned at the
transaction level.
"""

from typing import Any, Dict, Optional

import pytest
from execution_testing import (
    Account,
    Alloc,
    Fork,
    StateTestFiller,
    Transaction,
    TransactionException,
)

from .helpers import verify_frame
from .spec import ref_spec_8141

REFERENCE_SPEC_GIT_PATH = ref_spec_8141.git_path
REFERENCE_SPEC_VERSION = ref_spec_8141.version

# EIP-8141 is slated for the fork after Amsterdam, so fixtures are
# labeled with the pseudo `Bogota` fork (Amsterdam + EIP-8141), even
# though the spec prototypes the EIP inside the Amsterdam fork module.
# Fill these tests with `--fork Bogota`.
pytestmark = pytest.mark.valid_from("Bogota")


ADMISSION_CASES = [
    pytest.param(
        dict(max_fee_per_gas=2**255),
        TransactionException.GASLIMIT_PRICE_PRODUCT_OVERFLOW,
        id="max_cost_overflow",
        marks=pytest.mark.exception_test,
    ),
    pytest.param(
        # The largest fee cap whose product with the per-transaction
        # gas cap still fits the maximum cost bound, so the case is
        # includable regardless of the transaction's derived gas limit.
        dict(
            max_fee_per_gas=lambda fork: (2**256 - 1)
            // fork.transaction_gas_limit_cap()
        ),
        None,
        id="max_cost_within_bound",
    ),
]
"""
Field-level variations of a minimal frame transaction, each with the
exception a rule evaluated at admission must reject it with, or `None`
where the variation stays exactly within the rule's bound.
"""


@pytest.mark.parametrize("tx_overrides,error", ADMISSION_CASES)
def test_admission_constraints(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    tx_overrides: Dict[str, Any],
    error: Optional[TransactionException],
) -> None:
    """
    Vary one transaction-level field of a minimal frame transaction and
    check that a rule evaluated at admission rejects it, or accepts it
    exactly within the rule's bound.

    Override values that depend on the fork are expressed as callables
    taking the fork, since the parametrize table is built before the
    fork is known.
    """
    # The sender holds the largest representable balance so that even
    # the case priced at the largest includable fee cap can escrow its
    # maximum cost when a frame approves payment.
    sender = pre.fund_eoa(amount=2**256 - 1)
    tx_kwargs: Dict[str, Any] = dict(
        sender=sender,
        frames=[verify_frame()],
        error=error,
    )
    tx_kwargs.update(
        {
            key: value(fork) if callable(value) else value
            for key, value in tx_overrides.items()
        }
    )
    tx = Transaction(**tx_kwargs)

    state_test(
        pre=pre,
        tx=tx,
        # The sender's nonce only increments if the transaction is
        # valid and executes.
        post={sender: Account(nonce=0 if error else 1)},
    )


# Funding an EOA with a custom nonce mutates the shared pre-alloc.
@pytest.mark.pre_alloc_mutable
def test_nonce_at_maximum(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """
    Accept a frame transaction whose nonce is one below the overflow
    bound: the highest nonce a frame transaction may carry, leaving
    room for the post-execution increment.
    """
    sender = pre.fund_eoa(nonce=2**64 - 2)
    tx = Transaction(
        sender=sender,
        nonce=2**64 - 2,
        frames=[verify_frame()],
    )

    state_test(
        pre=pre,
        tx=tx,
        post={sender: Account(nonce=2**64 - 1)},
    )
