"""
Tests for EIP-2780 x EIP-7702 interaction.

A type-4 transaction's authorizations are processed at the top frame
(in ``set_delegation``), where their state-dependent costs are charged.
Each authorization pays, on top of the state-independent
``EXECUTION_PER_AUTH_BASE_COST`` charged in the intrinsic:

- ``NEW_ACCOUNT`` (state) + ``ACCOUNT_WRITE`` (execution) when the
  authority's account leaf does not yet exist, and
- ``AUTH_BASE`` (state) when a net-new delegation indicator is written.

The intrinsic no longer over-charges and refunds; the costs are charged
exactly, keyed on each authority's pre-transaction state. Each
authorization carries that state as its ``creates_account`` /
``writes_delegation`` annotations, and the top-frame calculators read
them off the same list that is handed to ``authorization_list``.

When the authorization installs a delegation on ``tx.to``,
``set_delegation`` runs before the recipient top-frame check, so:

- the recipient's delegation-target access charge fires for the
  now-delegated recipient (warm or cold per the target's warmth); and
- the ``NEW_ACCOUNT`` charge a value transfer to an empty recipient
  would otherwise incur is suppressed -- ``set_delegation`` has made the
  recipient alive, and the per-authorization ``NEW_ACCOUNT`` accounts
  for the leaf instead.

A complementary set of scenarios installs the delegation on the
*sender* (self-sponsored authorization), whose nonce must equal the
sender's nonce after the transaction-side increment.
"""

import pytest
from execution_testing import (
    Account,
    Alloc,
    AuthorizationTuple,
    Fork,
    Op,
    RecipientType,
    StateTestFiller,
    Transaction,
)
from execution_testing.checklists import EIPChecklist

from ...prague.eip7702_set_code_tx.spec import Spec as Spec7702
from .spec import ref_spec_2780

REFERENCE_SPEC_GIT_PATH = ref_spec_2780.git_path
REFERENCE_SPEC_VERSION = ref_spec_2780.version

pytestmark = pytest.mark.valid_from("Amsterdam")


@EIPChecklist.GasCostChanges.Test.GasUpdatesMeasurement()
@pytest.mark.parametrize(
    "value",
    [
        pytest.param(0, id="zero_value"),
        pytest.param(1, id="non-zero_value"),
    ],
)
def test_tx_installs_delegation_on_funded_recipient(
    fork: Fork,
    pre: Alloc,
    state_test: StateTestFiller,
    value: int,
) -> None:
    """
    Scenario 1: ``tx.to`` is a funded EOA with no prior delegation.
    The type-4 transaction's authorization installs delegation on
    ``tx.to``.

    The authority (``tx.to``) already exists, so it pays no
    ``NEW_ACCOUNT``; it has no prior code, so writing the delegation
    indicator pays ``AUTH_BASE``. Whether it pays ``ACCOUNT_WRITE``
    depends on the value transfer: with ``zero_value`` the delegation
    write is the transaction's first write to ``tx.to`` and
    ``ACCOUNT_WRITE`` is charged; with ``non-zero_value`` the
    transaction already pays to write ``tx.to`` when it transfers value
    to it, so no ``ACCOUNT_WRITE`` accrues. The top-frame
    ``COLD_ACCOUNT_ACCESS`` charge for the now-delegated recipient (its
    fresh delegation target is cold) still fires.
    """
    sender_initial_balance = 10**18
    sender = pre.fund_eoa(sender_initial_balance)

    target_initial_balance = 100
    target = pre.fund_eoa(amount=target_initial_balance)
    delegated_to = pre.deploy_contract(code=Op.STOP)

    auth = AuthorizationTuple(
        address=delegated_to,
        nonce=0,
        signer=target,
        # Funded authority already exists, so no NEW_ACCOUNT.
        creates_account=False,
        first_write=not bool(value),
    )
    authorization_list = [auth]

    # Intrinsic sees the recipient in its pre-tx form (funded EOA); the
    # delegation only surfaces at the top-frame check.
    intrinsic_gas = fork.transaction_intrinsic_cost_calculator()(
        sends_value=bool(value),
        recipient_type=RecipientType.EOA,
        authorization_list_or_count=authorization_list,
        return_cost_deducted_prior_execution=True,
    )
    top_frame_execution = fork.transaction_top_frame_execution_gas(
        sends_value=bool(value),
        recipient_type=RecipientType.DELEGATION_7702,
        delegation_warm=False,
        authorizations=authorization_list,
    )
    top_frame_state = fork.transaction_top_frame_state_gas(
        sends_value=bool(value),
        recipient_type=RecipientType.DELEGATION_7702,
        authorizations=authorization_list,
    )

    # Costs are charged exactly (no refund); under the default zero
    # state-gas reservoir the state gas spills into execution gas.
    total_gas_cost = intrinsic_gas + top_frame_execution + top_frame_state
    tx_gas_limit = total_gas_cost + 1000
    gas_price = 1_000_000_000

    tx = Transaction(
        sender=sender,
        to=target,
        value=value,
        authorization_list=authorization_list,
        gas_limit=tx_gas_limit,
        max_fee_per_gas=gas_price,
        max_priority_fee_per_gas=gas_price,
    )

    sender_final_balance = (
        sender_initial_balance - value - (total_gas_cost * gas_price)
    )

    post = {
        sender: Account(nonce=1, balance=sender_final_balance),
        target: Account(
            nonce=1,
            balance=target_initial_balance + value,
            code=Spec7702.delegation_designation(delegated_to),
        ),
    }

    state_test(pre=pre, tx=tx, post=post)


@EIPChecklist.GasCostChanges.Test.GasUpdatesMeasurement()
@pytest.mark.parametrize(
    "value",
    [
        pytest.param(0, id="zero_value"),
        pytest.param(1, id="non-zero_value"),
    ],
)
def test_tx_installs_delegation_on_empty_recipient(
    fork: Fork,
    pre: Alloc,
    state_test: StateTestFiller,
    value: int,
) -> None:
    """
    Scenario 2: ``tx.to`` is a non-existent (empty) account. The type-4
    transaction's authorization installs delegation on ``tx.to``.

    The authority's account leaf does not exist, so the authorization
    pays ``NEW_ACCOUNT`` (account creation) and ``AUTH_BASE`` (net-new
    delegation indicator). Whether it also pays ``ACCOUNT_WRITE``
    depends on the value transfer: with ``zero_value`` the delegation
    write is the transaction's first write to ``tx.to`` and
    ``ACCOUNT_WRITE`` is charged; with ``non-zero_value`` the
    transaction already pays to write ``tx.to`` when it transfers value
    to it, so no ``ACCOUNT_WRITE`` accrues. ``set_delegation`` runs
    before the recipient top-frame check and makes the recipient alive,
    so the recipient ``NEW_ACCOUNT`` charge a value transfer would
    otherwise incur is suppressed (the per-authorization ``NEW_ACCOUNT``
    accounts for the leaf). The ``COLD_ACCOUNT_ACCESS`` charge for the
    now-delegated recipient still fires.
    """
    sender_initial_balance = 10**18
    sender = pre.fund_eoa(sender_initial_balance)

    target = pre.fund_eoa(amount=0)
    delegated_to = pre.deploy_contract(code=Op.STOP)

    auth = AuthorizationTuple(
        address=delegated_to,
        nonce=0,
        signer=target,
        # Empty authority leaf must be created.
        creates_account=True,
        first_write=not bool(value),
    )
    authorization_list = [auth]

    intrinsic_gas = fork.transaction_intrinsic_cost_calculator()(
        sends_value=bool(value),
        recipient_type=RecipientType.EMPTY_ACCOUNT,
        authorization_list_or_count=authorization_list,
        return_cost_deducted_prior_execution=True,
    )
    top_frame_execution = fork.transaction_top_frame_execution_gas(
        sends_value=bool(value),
        recipient_type=RecipientType.DELEGATION_7702,
        delegation_warm=False,
        authorizations=authorization_list,
    )
    top_frame_state = fork.transaction_top_frame_state_gas(
        sends_value=bool(value),
        recipient_type=RecipientType.DELEGATION_7702,
        authorizations=authorization_list,
    )

    total_gas_cost = intrinsic_gas + top_frame_execution + top_frame_state
    tx_gas_limit = total_gas_cost + 1000
    gas_price = 1_000_000_000

    tx = Transaction(
        sender=sender,
        to=target,
        value=value,
        authorization_list=authorization_list,
        gas_limit=tx_gas_limit,
        max_fee_per_gas=gas_price,
        max_priority_fee_per_gas=gas_price,
    )

    sender_final_balance = (
        sender_initial_balance - value - (total_gas_cost * gas_price)
    )

    post = {
        sender: Account(nonce=1, balance=sender_final_balance),
        target: Account(
            nonce=1,
            balance=value,
            code=Spec7702.delegation_designation(delegated_to),
        ),
    }

    state_test(pre=pre, tx=tx, post=post)


@EIPChecklist.GasCostChanges.Test.GasUpdatesMeasurement()
@pytest.mark.parametrize(
    "value",
    [
        pytest.param(0, id="zero_value"),
        pytest.param(1, id="non-zero_value"),
    ],
)
@pytest.mark.parametrize(
    "call_target",
    [
        pytest.param("self", id="calls_self"),
        pytest.param("other_eoa", id="calls_other"),
    ],
)
def test_tx_installs_delegation_on_sender(
    fork: Fork,
    pre: Alloc,
    state_test: StateTestFiller,
    call_target: str,
    value: int,
) -> None:
    """
    Self-sponsored type-4 transaction: the sender signs an
    authorization installing delegation on itself, and the
    authorization's nonce equals the sender's nonce *after* the
    transaction-side increment (``1``). After ``set_delegation`` the
    sender holds delegation code and its nonce reaches ``2``.

    The sender authority already exists, so no ``NEW_ACCOUNT`` accrues,
    and its leaf was already written at inclusion (priced into
    ``TX_BASE``), so the delegation write is not the transaction's
    first write to it and no ``ACCOUNT_WRITE`` accrues either. The
    authorization pays only ``AUTH_BASE`` (the net-new delegation
    indicator).

    Parametrized over the call target:

    - ``calls_self``: ``tx.to == sender``. The intrinsic self-transfer
      carve-out suppresses the recipient access and value-transfer
      charges; the top-frame fires the delegation access charge because
      ``set_delegation`` has installed delegation code on the sender by
      then. The transaction then dispatches into the sender's delegated
      code.
    - ``calls_other``: ``tx.to`` is a separate funded EOA. The intrinsic
      charges include ``COLD_ACCOUNT_ACCESS`` for the recipient (and the
      value-transfer charges when ``value > 0``). The top-frame fires no
      recipient charge because the recipient is a plain EOA. The
      sender's delegation is installed and persists past the transaction
      without ever being invoked.
    """
    sender_initial_balance = 10**18
    sender = pre.fund_eoa(sender_initial_balance)

    delegated_to = pre.deploy_contract(code=Op.STOP)

    auth = AuthorizationTuple(
        address=delegated_to,
        nonce=1,
        signer=sender,
        # Sender authority already exists, so no NEW_ACCOUNT; its leaf
        # was already written at inclusion, so no ACCOUNT_WRITE.
        creates_account=False,
        first_write=False,
    )
    authorization_list = [auth]

    target_initial_balance = 0
    if call_target == "self":
        target = sender
        # Intrinsic carve-out fires (SELF); top-frame fires the
        # delegation access charge because the sender is delegated by
        # the time the check runs.
        intrinsic_recipient_type = RecipientType.SELF
        top_frame_recipient_type = RecipientType.DELEGATION_7702
    else:
        target_initial_balance = 100
        target = pre.fund_eoa(amount=target_initial_balance)
        # Recipient is a plain EOA, so no carve-out and no top-frame
        # recipient charge.
        intrinsic_recipient_type = RecipientType.EOA
        top_frame_recipient_type = RecipientType.EOA

    intrinsic_gas = fork.transaction_intrinsic_cost_calculator()(
        sends_value=bool(value),
        recipient_type=intrinsic_recipient_type,
        authorization_list_or_count=authorization_list,
        return_cost_deducted_prior_execution=True,
    )
    top_frame_execution = fork.transaction_top_frame_execution_gas(
        sends_value=bool(value),
        recipient_type=top_frame_recipient_type,
        delegation_warm=False,
        authorizations=authorization_list,
    )
    top_frame_state = fork.transaction_top_frame_state_gas(
        sends_value=bool(value),
        recipient_type=top_frame_recipient_type,
        authorizations=authorization_list,
    )

    total_gas_cost = intrinsic_gas + top_frame_execution + top_frame_state
    tx_gas_limit = total_gas_cost + 1000
    gas_price = 1_000_000_000

    tx = Transaction(
        sender=sender,
        to=target,
        value=value,
        authorization_list=authorization_list,
        gas_limit=tx_gas_limit,
        max_fee_per_gas=gas_price,
        max_priority_fee_per_gas=gas_price,
    )

    if call_target == "self":
        # Value moves sender -> sender, net zero on balance.
        sender_final_balance = (
            sender_initial_balance - total_gas_cost * gas_price
        )
        post = {
            sender: Account(
                nonce=2,
                balance=sender_final_balance,
                code=Spec7702.delegation_designation(delegated_to),
            ),
        }
    else:
        sender_final_balance = (
            sender_initial_balance - value - total_gas_cost * gas_price
        )
        post = {
            sender: Account(
                nonce=2,
                balance=sender_final_balance,
                code=Spec7702.delegation_designation(delegated_to),
            ),
            target: Account(balance=target_initial_balance + value),
        }

    state_test(pre=pre, tx=tx, post=post)
