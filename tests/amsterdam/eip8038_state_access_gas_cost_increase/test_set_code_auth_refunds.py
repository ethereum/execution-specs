"""
Tests for the EIP-7702 authorization charge on an *existing* authority
leaf under [EIP-8038: State Access Gas Cost Increase](https://eips.ethereum.org/EIPS/eip-8038).

EIP-8038 originally over-charged every authorization as if it created a
new account and *refunded* the difference (``ACCOUNT_WRITE`` on the
execution channel, ``NEW_ACCOUNT`` -- and ``AUTH_BASE`` on a clear -- on
the state channel) when the authority leaf already existed.

Under EIP-2780 that over-charge-then-refund is gone: the
state-dependent portion of each authorization is charged lazily at the
top frame in ``set_delegation``. An existing leaf therefore never pays
-- and is never refunded -- the ``NEW_ACCOUNT`` creation cost. It does
pay ``ACCOUNT_WRITE`` once, for the transaction's first write to its
leaf, since applying the authorization writes its code and nonce
regardless of whether the leaf pre-existed. This module pins that
reduced, refund-free charge via the exact receipt gas:

* a non-clearing delegation on an existing empty-code leaf pays the
  intrinsic ``EXECUTION_PER_AUTH_BASE_COST`` plus the top-frame
  ``ACCOUNT_WRITE`` (first leaf write) and ``AUTH_BASE`` (the net-new
  delegation indicator); and
* a *clearing* re-authorization of an existing-delegation authority
  writes no net-new indicator, so it pays only the intrinsic base plus
  the first-write ``ACCOUNT_WRITE``, with no top-frame state charge at
  all.

In both regimes the receipt gas equals the exact charge with no refund
term.
"""

from typing import List

import pytest
from execution_testing import (
    Account,
    Alloc,
    AuthorizationTuple,
    Environment,
    Fork,
    Op,
    StateTestFiller,
    Transaction,
    TransactionReceipt,
)
from execution_testing.checklists import EIPChecklist

from ...prague.eip7702_set_code_tx.spec import Spec as Spec7702
from .spec import ref_spec_8038

REFERENCE_SPEC_GIT_PATH = ref_spec_8038.git_path
REFERENCE_SPEC_VERSION = ref_spec_8038.version

pytestmark = pytest.mark.valid_from("Amsterdam")


@EIPChecklist.GasRefundsChanges.Test.RefundCalculation()
@pytest.mark.parametrize("n", [1, 2])
def test_existing_authority_no_new_account_charge(
    state_test: StateTestFiller,
    env: Environment,
    pre: Alloc,
    fork: Fork,
    n: int,
) -> None:
    """
    An authorization whose authority leaf already exists is charged the
    reduced top-frame cost directly, with no refund.

    Each authority is an existing funded EOA gaining a fresh delegation.
    Its leaf exists, so ``set_delegation`` charges no ``NEW_ACCOUNT``
    (and, unlike the superseded EIP-8038 behaviour, refunds none); it
    charges the first-write ``ACCOUNT_WRITE`` and the top-frame
    ``AUTH_BASE`` for the net-new delegation indicator. The receipt gas
    is therefore exactly the execution intrinsic plus
    ``n * (ACCOUNT_WRITE + AUTH_BASE)``, with no refund term.
    """
    recipient = pre.deploy_contract(code=Op.STOP)
    delegate = pre.deploy_contract(code=Op.STOP)
    signers = [pre.fund_eoa() for _ in range(n)]
    authorization_list = [
        AuthorizationTuple(
            address=delegate,
            nonce=0,
            signer=signer,
            # Existing leaf gaining a net-new delegation indicator; the
            # transaction's first write to the leaf.
            creates_account=False,
            writes_delegation=True,
        )
        for signer in signers
    ]

    # Existing leaf + net-new delegation: the first-write ACCOUNT_WRITE
    # and AUTH_BASE at the top frame. NEW_ACCOUNT is neither charged
    # nor refunded, so the receipt gas is the exact charge.
    intrinsic_execution = fork.transaction_intrinsic_cost_calculator()(
        authorization_list_or_count=n,
        return_cost_deducted_prior_execution=True,
    )
    top_frame_execution = fork.transaction_top_frame_execution_gas(
        authorizations=authorization_list,
    )
    top_frame_state = fork.transaction_top_frame_state_gas(
        authorizations=authorization_list,
    )
    cumulative_gas_used = (
        intrinsic_execution + top_frame_execution + top_frame_state
    )

    tx = Transaction(
        to=recipient,
        authorization_list=authorization_list,
        sender=pre.fund_eoa(),
        expected_receipt=TransactionReceipt(
            cumulative_gas_used=cumulative_gas_used,
        ),
    )

    post = {
        signer: Account(code=Spec7702.delegation_designation(delegate))
        for signer in signers
    }
    state_test(env=env, pre=pre, post=post, tx=tx)


@EIPChecklist.GasRefundsChanges.Test.RefundCalculation()
@pytest.mark.parametrize("n", [1, 3])
def test_clearing_delegation_no_state_charge(
    state_test: StateTestFiller,
    env: Environment,
    pre: Alloc,
    fork: Fork,
    n: int,
) -> None:
    """
    Clearing an existing delegation is charged the intrinsic
    per-authorization base plus the first-write ``ACCOUNT_WRITE``, with
    no top-frame state charge and no refund.

    Each authority already exists and already holds a delegation
    indicator (delegated before the transaction), and the authorization
    resets to the null address, so ``set_delegation`` writes no net-new
    indicator: ``NEW_ACCOUNT`` and ``AUTH_BASE`` fall away. The clear
    still writes the authority's leaf (code emptied, nonce bumped), so
    the transaction's first-write ``ACCOUNT_WRITE`` applies. Nothing is
    refunded (the over-charge is gone), so the receipt gas is exactly
    the execution intrinsic plus ``n * ACCOUNT_WRITE``.
    """
    recipient = pre.deploy_contract(code=Op.STOP)
    delegated_to = pre.deploy_contract(code=Op.STOP)
    # Authorities that already delegate; fund_eoa(delegation=...) sets
    # the authority nonce to 1, which is the expected auth nonce.
    signers = [pre.fund_eoa(delegation=delegated_to) for _ in range(n)]
    authorization_list: List[AuthorizationTuple] = [
        AuthorizationTuple(
            address=Spec7702.RESET_DELEGATION_ADDRESS,
            nonce=1,
            signer=signer,
            # Existing leaf, delegated before the tx: clearing writes no
            # net-new indicator, so no top-frame state charge. The clear
            # is still the transaction's first write to the leaf.
            creates_account=False,
            writes_delegation=False,
        )
        for signer in signers
    ]

    # Clearing an existing delegation writes no net-new indicator, so
    # no top-frame state charge applies and no refund fires; only the
    # first-write ACCOUNT_WRITE is charged per authority.
    intrinsic_execution = fork.transaction_intrinsic_cost_calculator()(
        authorization_list_or_count=n,
        return_cost_deducted_prior_execution=True,
    )
    top_frame_execution = fork.transaction_top_frame_execution_gas(
        authorizations=authorization_list,
    )
    top_frame_state = fork.transaction_top_frame_state_gas(
        authorizations=authorization_list,
    )
    assert top_frame_state == 0
    cumulative_gas_used = intrinsic_execution + top_frame_execution

    tx = Transaction(
        to=recipient,
        authorization_list=authorization_list,
        sender=pre.fund_eoa(),
        expected_receipt=TransactionReceipt(
            cumulative_gas_used=cumulative_gas_used,
        ),
    )

    post = {signer: Account(nonce=2, code=b"") for signer in signers}
    state_test(env=env, pre=pre, post=post, tx=tx)
