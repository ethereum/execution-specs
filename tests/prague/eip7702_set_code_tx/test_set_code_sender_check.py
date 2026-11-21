"""
Tests the EIP-3607 sender check on an account that holds a delegation
designator, before and after
[EIP-7702: Set EOA account code](https://eips.ethereum.org/EIPS/eip-7702).
"""

import pytest
from execution_testing import (
    Account,
    Alloc,
    Fork,
    Op,
    StateTestFiller,
    Transaction,
    TransactionException,
)

from .spec import Spec, ref_spec_7702

REFERENCE_SPEC_GIT_PATH = ref_spec_7702.git_path
REFERENCE_SPEC_VERSION = ref_spec_7702.version


@pytest.mark.parametrize(
    "expected_error",
    [
        pytest.param(
            TransactionException.SENDER_NOT_EOA,
            id="before_prague",
            marks=[
                pytest.mark.valid_until("Cancun"),
                pytest.mark.exception_test,
                pytest.mark.pre_alloc_mutable,
            ],
        ),
        pytest.param(
            None,
            id="from_prague",
            marks=pytest.mark.valid_from("Prague"),
        ),
    ],
)
@pytest.mark.valid_from("Frontier")
@pytest.mark.inclusion_test
def test_sender_with_delegation_designator(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    expected_error: TransactionException | None,
) -> None:
    """
    Test a value transfer from a sender whose code is a delegation
    designator.

    EIP-7702 exempts the designator from the EIP-3607 sender check, so
    before it the sender has code and the transaction is invalid.
    """
    assert (expected_error is None) == fork.is_eip_enabled(7702)

    delegate = pre.deploy_contract(Op.STOP)
    sender = pre.fund_eoa(delegation=delegate)
    recipient = pre.fund_eoa(amount=0)

    tx = Transaction(
        ty=2 if 2 in fork.tx_types() else 0,
        sender=sender,
        to=recipient,
        value=1,
        protected=fork.supports_protected_txs(),
        error=expected_error,
    )

    designator = Spec.delegation_designation(delegate)
    post = (
        {
            sender: Account(nonce=1, code=designator),
            recipient: Account.NONEXISTENT,
        }
        if expected_error is not None
        else {
            sender: Account(nonce=2, code=designator),
            recipient: Account(balance=1),
        }
    )

    state_test(pre=pre, tx=tx, post=post)
