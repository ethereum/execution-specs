"""
Tests for the EIP-2780 first-write ``ACCOUNT_WRITE`` exemptions during
EIP-7702 authorization processing under
[EIP-8038: State-access gas cost update](https://eips.ethereum.org/EIPS/eip-8038).

Applying an authorization writes the authority's leaf (code and nonce)
and pays ``ACCOUNT_WRITE`` for the transaction's *first* write to that
leaf. Accounts whose leaf write the transaction has already priced are
exempt: the sender (paid via ``TX_BASE``) and a value-receiving
recipient (paid via ``TX_VALUE_COST``). A zero-value recipient is not
exempt, and a second valid authorization by the same authority pays
nothing further. Every expectation is an exact receipt
``cumulative_gas_used`` pin built from the fork's intrinsic and
top-frame gas oracles.
"""

import pytest
from execution_testing import (
    Account,
    Alloc,
    AuthorizationTuple,
    Environment,
    Fork,
    Op,
    RecipientType,
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


@EIPChecklist.GasCostChanges.Test.GasUpdatesMeasurement()
def test_authority_is_sender_pays_no_account_write(
    state_test: StateTestFiller,
    env: Environment,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    A self-sponsored authorization pays no first-write ``ACCOUNT_WRITE``.

    The sender signs its own authorization; the transaction has already
    priced the sender's leaf write via ``TX_BASE``, so applying the
    authorization charges only the net-new delegation indicator
    (``AUTH_BASE``, state gas) on top of the intrinsic per-auth base.
    """
    recipient = pre.deploy_contract(code=Op.STOP)
    delegate = pre.deploy_contract(code=Op.STOP)
    sender = pre.fund_eoa()
    authorization_list = [
        AuthorizationTuple(
            address=delegate,
            # The transaction increments the sender's nonce before
            # authorizations are processed.
            nonce=1,
            signer=sender,
            creates_account=False,
            writes_delegation=True,
            # Exempt: the sender's leaf write is priced by TX_BASE.
            first_write=False,
        )
    ]

    intrinsic_execution = fork.transaction_intrinsic_cost_calculator()(
        authorization_list_or_count=1,
        return_cost_deducted_prior_execution=True,
    )
    top_frame_execution = fork.transaction_top_frame_execution_gas(
        authorizations=authorization_list,
    )
    # The exemption leaves no top-frame execution charge at all.
    assert top_frame_execution == 0
    top_frame_state = fork.transaction_top_frame_state_gas(
        authorizations=authorization_list,
    )
    cumulative_gas_used = (
        intrinsic_execution + top_frame_execution + top_frame_state
    )

    tx = Transaction(
        to=recipient,
        authorization_list=authorization_list,
        sender=sender,
        expected_receipt=TransactionReceipt(
            cumulative_gas_used=cumulative_gas_used,
        ),
    )

    post = {
        sender: Account(
            nonce=2,
            code=Spec7702.delegation_designation(delegate),
        ),
    }
    state_test(env=env, pre=pre, post=post, tx=tx)


@EIPChecklist.GasCostChanges.Test.GasUpdatesMeasurement()
@pytest.mark.parametrize(
    "sends_value",
    [
        pytest.param(True, id="value_recipient_exempt"),
        pytest.param(False, id="zero_value_recipient_not_exempt"),
    ],
)
def test_authority_is_recipient_account_write_exemption(
    state_test: StateTestFiller,
    env: Environment,
    pre: Alloc,
    fork: Fork,
    sends_value: bool,
) -> None:
    """
    The recipient-authority exemption applies only when value moves.

    The transaction's recipient is also the (existing) authority. With
    value, the recipient's leaf write is already priced by
    ``TX_VALUE_COST``, so the authorization pays no first-write
    ``ACCOUNT_WRITE``; with zero value nothing has priced the write and
    ``ACCOUNT_WRITE`` applies. In both cases dispatching to the
    now-delegated recipient charges the cold delegation-target access.
    """
    delegate = pre.deploy_contract(code=Op.STOP)
    authority = pre.fund_eoa()
    authorization_list = [
        AuthorizationTuple(
            address=delegate,
            nonce=0,
            signer=authority,
            creates_account=False,
            writes_delegation=True,
            # Exempt only when the recipient receives value.
            first_write=not sends_value,
        )
    ]

    intrinsic_execution = fork.transaction_intrinsic_cost_calculator()(
        authorization_list_or_count=1,
        sends_value=sends_value,
        return_cost_deducted_prior_execution=True,
    )
    # The top-level dispatch targets the recipient, which this very
    # transaction delegated: the cold delegate access is charged at the
    # top frame.
    top_frame_execution = fork.transaction_top_frame_execution_gas(
        recipient_type=RecipientType.DELEGATION_7702,
        delegation_warm=False,
        sends_value=sends_value,
        authorizations=authorization_list,
    )
    top_frame_state = fork.transaction_top_frame_state_gas(
        recipient_type=RecipientType.DELEGATION_7702,
        sends_value=sends_value,
        authorizations=authorization_list,
    )
    cumulative_gas_used = (
        intrinsic_execution + top_frame_execution + top_frame_state
    )

    tx = Transaction(
        to=authority,
        value=1 if sends_value else 0,
        authorization_list=authorization_list,
        sender=pre.fund_eoa(),
        expected_receipt=TransactionReceipt(
            cumulative_gas_used=cumulative_gas_used,
        ),
    )

    post = {
        authority: Account(
            nonce=1,
            code=Spec7702.delegation_designation(delegate),
        ),
    }
    state_test(env=env, pre=pre, post=post, tx=tx)


@EIPChecklist.GasCostChanges.Test.GasUpdatesMeasurement()
def test_same_authority_twice_pays_account_write_once(
    state_test: StateTestFiller,
    env: Environment,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    Two valid authorizations by one authority pay ``ACCOUNT_WRITE`` once.

    Both tuples are valid (consecutive nonces) and both apply; the
    second only rewrites the delegation indicator the first installed,
    so it is neither the leaf's first write (no ``ACCOUNT_WRITE``) nor a
    net-new indicator (no ``AUTH_BASE``).
    """
    recipient = pre.deploy_contract(code=Op.STOP)
    first_delegate = pre.deploy_contract(code=Op.STOP)
    second_delegate = pre.deploy_contract(code=Op.STOP)
    authority = pre.fund_eoa()
    authorization_list = [
        AuthorizationTuple(
            address=first_delegate,
            nonce=0,
            signer=authority,
            creates_account=False,
            writes_delegation=True,
        ),
        AuthorizationTuple(
            address=second_delegate,
            nonce=1,
            signer=authority,
            creates_account=False,
            # The indicator already exists (installed by the first
            # tuple) and the leaf was already written this transaction.
            writes_delegation=False,
            first_write=False,
        ),
    ]

    intrinsic_execution = fork.transaction_intrinsic_cost_calculator()(
        authorization_list_or_count=2,
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

    # Both applications took effect: the nonce advanced twice and the
    # designator points at the second delegate.
    post = {
        authority: Account(
            nonce=2,
            code=Spec7702.delegation_designation(second_delegate),
        ),
    }
    state_test(env=env, pre=pre, post=post, tx=tx)


@EIPChecklist.GasCostChanges.Test.GasUpdatesMeasurement()
def test_fresh_authority_full_charge(
    state_test: StateTestFiller,
    env: Environment,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    A non-existent authority pays the full creation-and-write charge.

    The authority's account does not exist before the transaction, so
    applying its authorization pays the first-write ``ACCOUNT_WRITE``
    (execution) plus ``NEW_ACCOUNT`` and ``AUTH_BASE`` (state) at the
    top frame, all pinned exactly in the receipt.
    """
    recipient = pre.deploy_contract(code=Op.STOP)
    delegate = pre.deploy_contract(code=Op.STOP)
    authority = pre.fund_eoa(amount=0)
    authorization_list = [
        AuthorizationTuple(
            address=delegate,
            nonce=0,
            signer=authority,
            creates_account=True,
            writes_delegation=True,
        )
    ]

    intrinsic_execution = fork.transaction_intrinsic_cost_calculator()(
        authorization_list_or_count=1,
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
        authority: Account(
            nonce=1,
            code=Spec7702.delegation_designation(delegate),
        ),
    }
    state_test(env=env, pre=pre, post=post, tx=tx)


@EIPChecklist.GasCostChanges.Test.GasUpdatesMeasurement()
def test_invalid_signature_auth_pays_base_only(
    state_test: StateTestFiller,
    env: Environment,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    An unrecoverable authorization pays only the intrinsic base cost.

    The tuple's ``y_parity`` is out of range, so no authority can be
    recovered and the tuple is skipped during ``set_delegation``: no
    ``ACCOUNT_WRITE``, no state charge, and the receipt gas is exactly
    the intrinsic including one per-authorization base.
    """
    recipient = pre.deploy_contract(code=Op.STOP)
    delegate = pre.deploy_contract(code=Op.STOP)
    authorization_list = [
        AuthorizationTuple(
            address=delegate,
            nonce=0,
            # Out-of-range y_parity: recovery fails, tuple is skipped.
            v=2,
            r=1,
            s=1,
            creates_account=False,
            writes_delegation=False,
            first_write=False,
        )
    ]

    intrinsic_execution = fork.transaction_intrinsic_cost_calculator()(
        authorization_list_or_count=1,
        return_cost_deducted_prior_execution=True,
    )
    top_frame_execution = fork.transaction_top_frame_execution_gas(
        authorizations=authorization_list,
    )
    top_frame_state = fork.transaction_top_frame_state_gas(
        authorizations=authorization_list,
    )
    # A skipped tuple charges nothing beyond the intrinsic base.
    assert top_frame_execution == 0
    assert top_frame_state == 0
    cumulative_gas_used = intrinsic_execution

    tx = Transaction(
        to=recipient,
        authorization_list=authorization_list,
        sender=pre.fund_eoa(),
        expected_receipt=TransactionReceipt(
            cumulative_gas_used=cumulative_gas_used,
        ),
    )

    post = {recipient: Account(code=Op.STOP)}
    state_test(env=env, pre=pre, post=post, tx=tx)
