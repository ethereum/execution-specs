"""
Tests for EIP-2780 x EIP-7702 interaction.

When a type-4 transaction's authorization list installs a delegation on
``tx.to``, ``set_delegation`` runs before the top-frame check fires.
That ordering changes which top-frame charges apply:

- ``COLD_ACCOUNT_ACCESS`` for the delegated recipient still fires; the
  spec charges the access uniformly whenever the recipient holds a
  delegation prefix at top-frame time, regardless of who installed it.
- ``NEW_ACCOUNT`` for a value transfer to an otherwise-empty recipient
  is suppressed implicitly: ``set_delegation`` writes the delegation
  code and increments the nonce, so ``is_account_alive`` returns
  ``True`` by the time the top-frame check evaluates it.

A complementary set of scenarios installs the delegation on the
*sender* (self-sponsored authorization). The authorization's nonce
must equal the sender's nonce *after* the transaction's nonce
increment.
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

from ...prague.eip7702_set_code_tx.spec import Spec as Spec7702
from .spec import ref_spec_2780

REFERENCE_SPEC_GIT_PATH = ref_spec_2780.git_path
REFERENCE_SPEC_VERSION = ref_spec_2780.version

pytestmark = pytest.mark.valid_from("Amsterdam")


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
    ``tx.to``. The top-frame ``COLD_ACCOUNT_ACCESS`` charge for the
    now-delegated recipient still fires.

    The pre-existing authority account also produces a
    ``REFUND_AUTH_PER_EXISTING_ACCOUNT`` state refund.
    """
    gsc = fork.gas_costs()
    sender_initial_balance = 10**18
    sender = pre.fund_eoa(sender_initial_balance)

    target_initial_balance = 100
    target = pre.fund_eoa(amount=target_initial_balance)
    delegated_to = pre.deploy_contract(code=Op.STOP)

    auth = AuthorizationTuple(
        address=delegated_to,
        nonce=0,
        signer=target,
    )

    # Intrinsic sees the recipient in its pre-tx form (funded EOA);
    # the delegation is materialized later by ``set_delegation`` and
    # only surfaces at the top-frame check.
    intrinsic_gas = fork.transaction_intrinsic_cost_calculator()(
        sends_value=bool(value),
        recipient_type=RecipientType.EOA,
        authorization_list_or_count=[auth],
        return_cost_deducted_prior_execution=True,
    )
    top_frame_gas = fork.transaction_top_frame_gas_calculator()(
        sends_value=bool(value),
        recipient_type=RecipientType.DELEGATION_7702,
    )
    # The full intrinsic is deducted upfront. For each existing
    # authority, ``set_delegation`` refunds ``NEW_ACCOUNT`` into the
    # state gas reservoir (uncapped) and ``ACCOUNT_WRITE`` into the
    # regular refund counter (capped at ``gas_used // 5`` by EIP-3529).
    total_gas_cost = intrinsic_gas + top_frame_gas
    state_refund = gsc.REFUND_AUTH_PER_EXISTING_ACCOUNT
    gas_used_pre_regular_refund = total_gas_cost - state_refund
    regular_refund = min(gsc.ACCOUNT_WRITE, gas_used_pre_regular_refund // 5)
    gas_used = gas_used_pre_regular_refund - regular_refund

    tx_gas_limit = total_gas_cost + 1000
    gas_price = 1_000_000_000

    tx = Transaction(
        sender=sender,
        to=target,
        value=value,
        authorization_list=[auth],
        gas_limit=tx_gas_limit,
        max_fee_per_gas=gas_price,
        max_priority_fee_per_gas=gas_price,
    )

    sender_final_balance = (
        sender_initial_balance - value - (gas_used * gas_price)
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

    ``set_delegation`` runs before the top-frame check and makes the
    recipient alive, so the ``NEW_ACCOUNT`` state-gas charge that a
    value transfer to an empty recipient would otherwise incur is
    implicitly suppressed. The ``COLD_ACCOUNT_ACCESS`` charge for the
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
    )

    # Intrinsic sees the recipient in its pre-tx form (empty); the
    # delegation is materialized later by ``set_delegation`` and only
    # surfaces at the top-frame check.
    intrinsic_gas = fork.transaction_intrinsic_cost_calculator()(
        sends_value=bool(value),
        recipient_type=RecipientType.EMPTY_ACCOUNT,
        authorization_list_or_count=[auth],
        return_cost_deducted_prior_execution=True,
    )
    top_frame_gas = fork.transaction_top_frame_gas_calculator()(
        sends_value=bool(value),
        recipient_type=RecipientType.DELEGATION_7702,
    )
    # Authority does not pre-exist, so no auth refund applies.
    total_gas_cost = intrinsic_gas + top_frame_gas

    tx_gas_limit = total_gas_cost + 1000
    gas_price = 1_000_000_000

    tx = Transaction(
        sender=sender,
        to=target,
        value=value,
        authorization_list=[auth],
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

    Parametrized over the call target:

    - ``calls_self``: ``tx.to == sender``. The intrinsic self-transfer
      carve-out suppresses the recipient access and value-transfer
      charges; the top-frame fires ``COLD_ACCOUNT_ACCESS`` because
      ``set_delegation`` has installed delegation code on the sender
      by then. The transaction then dispatches into the sender's
      delegated code.
    - ``calls_other``: ``tx.to`` is a separate funded EOA. The
      intrinsic charges include ``COLD_ACCOUNT_ACCESS`` for the
      recipient (and the value-transfer charges when ``value > 0``).
      The top-frame fires nothing because the recipient is a plain
      EOA. The sender's delegation is installed and persists past the
      transaction without ever being invoked.
    """
    gsc = fork.gas_costs()
    sender_initial_balance = 10**18
    sender = pre.fund_eoa(sender_initial_balance)

    delegated_to = pre.deploy_contract(code=Op.STOP)

    auth = AuthorizationTuple(
        address=delegated_to,
        nonce=1,
        signer=sender,
    )

    target_initial_balance = 0
    if call_target == "self":
        target = sender
        # Intrinsic carve-out fires (SELF); top-frame fires
        # ``COLD_ACCOUNT_ACCESS`` because the sender is delegated by
        # the time the check runs.
        intrinsic_recipient_type = RecipientType.SELF
        top_frame_recipient_type = RecipientType.DELEGATION_7702
    else:
        target_initial_balance = 100
        target = pre.fund_eoa(amount=target_initial_balance)
        # Recipient is a plain EOA, so no carve-out and no top-frame
        # charge.
        intrinsic_recipient_type = RecipientType.EOA
        top_frame_recipient_type = RecipientType.EOA

    intrinsic_gas = fork.transaction_intrinsic_cost_calculator()(
        sends_value=bool(value),
        recipient_type=intrinsic_recipient_type,
        authorization_list_or_count=[auth],
        return_cost_deducted_prior_execution=True,
    )
    top_frame_gas = fork.transaction_top_frame_gas_calculator()(
        sends_value=bool(value),
        recipient_type=top_frame_recipient_type,
    )

    # Sender is the existing authority, so ``set_delegation`` refunds
    # ``NEW_ACCOUNT`` to the state-gas reservoir and ``ACCOUNT_WRITE``
    # to the regular refund counter (the latter capped at
    # ``gas_used // 5`` by EIP-3529).
    total_gas_cost = intrinsic_gas + top_frame_gas
    state_refund = gsc.REFUND_AUTH_PER_EXISTING_ACCOUNT
    gas_used_pre_regular_refund = total_gas_cost - state_refund
    regular_refund = min(gsc.ACCOUNT_WRITE, gas_used_pre_regular_refund // 5)
    gas_used = gas_used_pre_regular_refund - regular_refund

    tx_gas_limit = total_gas_cost + 1000
    gas_price = 1_000_000_000

    tx = Transaction(
        sender=sender,
        to=target,
        value=value,
        authorization_list=[auth],
        gas_limit=tx_gas_limit,
        max_fee_per_gas=gas_price,
        max_priority_fee_per_gas=gas_price,
    )

    if call_target == "self":
        # Value moves sender -> sender, net zero on balance.
        sender_final_balance = sender_initial_balance - gas_used * gas_price
        post = {
            sender: Account(
                nonce=2,
                balance=sender_final_balance,
                code=Spec7702.delegation_designation(delegated_to),
            ),
        }
    else:
        sender_final_balance = (
            sender_initial_balance - value - gas_used * gas_price
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
