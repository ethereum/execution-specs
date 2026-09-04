"""Charge accounting for EIP-7702 authorizations under EIP-2780."""

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
    TransactionReceipt,
)

from ...prague.eip7702_set_code_tx.spec import Spec as Spec7702
from .helpers import (
    NULL_ADDRESS,
    AuthorizationAction,
    authorization_transaction_cost,
    build_authorization,
)
from .spec import ref_spec_2780

REFERENCE_SPEC_GIT_PATH = ref_spec_2780.git_path
REFERENCE_SPEC_VERSION = ref_spec_2780.version

pytestmark = pytest.mark.valid_from("Amsterdam")


@pytest.mark.parametrize(
    "action", list(AuthorizationAction), ids=lambda a: a.name.lower()
)
def test_single_authorization_charges(
    fork: Fork,
    pre: Alloc,
    state_test: StateTestFiller,
    action: AuthorizationAction,
) -> None:
    """
    A single authorization on a third-party authority, spanning the
    action space that drives its top-frame charge.

    Every valid action below is the transaction's first write to its
    (third-party) authority, so each pays ``ACCOUNT_WRITE`` on top of
    the charges listed:

    - ``CREATES_ACCOUNT``: the authority does not exist, so the
      authorization also pays ``NEW_ACCOUNT`` (creation) and
      ``AUTH_BASE`` (net-new delegation indicator).
    - ``SETS_NEW_DELEGATION``: an existing empty-code EOA gains a
      delegation, paying ``AUTH_BASE``.
    - ``SETS_DIFFERENT_DELEGATION`` / ``SETS_SAME_DELEGATION``: an
      already-delegated EOA is re-pointed (or re-pointed to the same
      target); it was delegated before the transaction, so no
      ``AUTH_BASE`` accrues. The nonce still advances.
    - ``CLEARS_DELEGATION``: an already-delegated EOA is cleared (the
      authorization target is the null address); no ``AUTH_BASE``
      accrues and the delegation code is removed.
    - ``INVALID``: the authorization nonce does not match the
      authority's account nonce, so ``validate_authorization`` skips it.
      The intrinsic base cost is still paid; no top-frame charge (not
      even ``ACCOUNT_WRITE``) accrues and the authority is untouched.
    """
    sender = pre.fund_eoa()
    recipient = pre.deploy_contract(code=Op.STOP)

    scenario = build_authorization(pre, action)
    authorization_list = [scenario.authorization]
    total_gas_cost = authorization_transaction_cost(fork, authorization_list)

    tx = Transaction(
        sender=sender,
        to=recipient,
        value=0,
        authorization_list=authorization_list,
        gas_limit=total_gas_cost,
        expected_receipt=TransactionReceipt(
            cumulative_gas_used=total_gas_cost,
        ),
    )

    post = {
        scenario.authority: scenario.applied_account,
    }

    state_test(pre=pre, tx=tx, post=post)


@pytest.mark.parametrize(
    "scenario",
    [
        "set_then_modify",
        "create_then_modify",
        "clear_then_set",
        "different_accounts",
    ],
)
def test_multi_authorization_intra_tx_state(
    fork: Fork,
    pre: Alloc,
    state_test: StateTestFiller,
    scenario: str,
) -> None:
    """
    Two authorizations in one transaction, charged against the state
    each leaves for the next.

    ``set_delegation`` applies authorizations in list order and reads
    live state, so a second authorization on the same authority sees the
    code the first installed:

    - ``set_then_modify``: the first sets a fresh delegation on an empty
      EOA (paying ``AUTH_BASE``); the second re-points it. The authority
      now has code, so the second pays no ``AUTH_BASE``.
    - ``create_then_modify``: the first creates the authority and
      delegates it (``NEW_ACCOUNT`` + ``ACCOUNT_WRITE`` + ``AUTH_BASE``);
      the second re-points it and pays no further state charge.
    - ``clear_then_set``: the first clears an existing delegation and
      the second re-delegates. The authority was already delegated
      before the transaction, so the indicator slot was already paid
      for: neither authorization writes a net-new indicator and no
      ``AUTH_BASE`` is charged.
    - ``different_accounts``: the two authorizations touch distinct
      authorities and are charged independently.

    Consecutive authorizations on one authority use consecutive nonces
    (the first bumps the nonce), and the post-state confirms both were
    applied rather than the second being silently skipped.
    """
    sender = pre.fund_eoa()
    recipient = pre.deploy_contract(code=Op.STOP)

    if scenario == "different_accounts":
        first = build_authorization(pre, AuthorizationAction.CREATES_ACCOUNT)
        second = build_authorization(
            pre, AuthorizationAction.SETS_NEW_DELEGATION
        )
        authorization_list = [first.authorization, second.authorization]
        expected_authorities = {
            first.authority: first.applied_account,
            second.authority: second.applied_account,
        }
    else:
        first_action = {
            "set_then_modify": AuthorizationAction.SETS_NEW_DELEGATION,
            "create_then_modify": AuthorizationAction.CREATES_ACCOUNT,
            "clear_then_set": AuthorizationAction.CLEARS_DELEGATION,
        }[scenario]
        leg = build_authorization(pre, first_action)
        new_target = pre.deploy_contract(code=Op.STOP)

        # The second authorization runs on the same authority right
        # after the first, using the next nonce. The first already
        # wrote the authority's leaf (no second ``ACCOUNT_WRITE``) and
        # either set a delegation in this transaction or found one from
        # before it, so the re-point writes no net-new indicator and
        # pays no ``AUTH_BASE``.
        applied_nonce = int(leg.applied_account.nonce)
        second_auth = AuthorizationTuple(
            address=new_target,
            nonce=applied_nonce,
            signer=leg.authority,
            creates_account=False,
            writes_delegation=False,
            first_write=False,
        )
        authorization_list = [leg.authorization, second_auth]
        expected_authorities = {
            leg.authority: Account(
                nonce=applied_nonce + 1,
                balance=int(leg.applied_account.balance),
                code=Spec7702.delegation_designation(new_target),
            ),
        }

    total_gas_cost = authorization_transaction_cost(fork, authorization_list)

    tx = Transaction(
        sender=sender,
        to=recipient,
        value=0,
        authorization_list=authorization_list,
        gas_limit=total_gas_cost,
        expected_receipt=TransactionReceipt(
            cumulative_gas_used=total_gas_cost,
        ),
    )

    post = {
        **expected_authorities,
    }

    state_test(pre=pre, tx=tx, post=post)


def _intrinsic_gas(
    fork: Fork,
    authorization_count: int,
    *,
    recipient_type: RecipientType = RecipientType.CONTRACT,
    sends_value: bool = False,
) -> int:
    """Return the execution intrinsic gas deducted before execution."""
    return fork.transaction_intrinsic_cost_calculator()(
        recipient_type=recipient_type,
        sends_value=sends_value,
        authorization_list_or_count=authorization_count,
        return_cost_deducted_prior_execution=True,
    )


@pytest.mark.parametrize(
    "authority_prestate", ["non_existent", "existing_eoa"]
)
def test_account_write_first_write_of_authority(
    fork: Fork,
    pre: Alloc,
    state_test: StateTestFiller,
    authority_prestate: str,
) -> None:
    """
    ``ACCOUNT_WRITE`` is charged on the first write to the authority
    within the transaction, independent of whether its account leaf
    already exists.

    Applying an authorization writes the authority's leaf (code and
    nonce), so the first authorization on any authority not yet written
    in the transaction pays ``ACCOUNT_WRITE``:

    - ``non_existent``: the authority also pays ``NEW_ACCOUNT`` for the
      fresh leaf (and ``AUTH_BASE`` for the net-new indicator).
    - ``existing_eoa``: the leaf exists, but the delegation write is
      still this transaction's first write to it, so ``ACCOUNT_WRITE``
      is charged all the same (plus ``AUTH_BASE``).
    """
    sender = pre.fund_eoa()
    recipient = pre.deploy_contract(code=Op.STOP)

    if authority_prestate == "non_existent":
        scenario = build_authorization(
            pre, AuthorizationAction.CREATES_ACCOUNT
        )
    else:
        scenario = build_authorization(
            pre, AuthorizationAction.SETS_NEW_DELEGATION
        )

    authorization_list = [scenario.authorization]
    total_gas_cost = authorization_transaction_cost(fork, authorization_list)

    tx = Transaction(
        sender=sender,
        to=recipient,
        value=0,
        authorization_list=authorization_list,
        gas_limit=total_gas_cost,
        expected_receipt=TransactionReceipt(
            cumulative_gas_used=total_gas_cost,
        ),
    )

    post = {
        scenario.authority: scenario.applied_account,
    }

    state_test(pre=pre, tx=tx, post=post)


def test_account_write_authority_is_sender(
    fork: Fork,
    pre: Alloc,
    state_test: StateTestFiller,
) -> None:
    """
    An authority that is the transaction sender pays no
    ``ACCOUNT_WRITE``: the sender's account was already written at
    inclusion (nonce bump and fee deduction, priced into ``TX_BASE``),
    so the delegation write is not the first write to it within the
    transaction.

    The self-sponsored authorization still pays ``AUTH_BASE`` for its
    net-new delegation indicator. This case guards the first-write rule
    against over-charging accounts the transaction has already paid to
    write.
    """
    sender = pre.fund_eoa()
    recipient = pre.deploy_contract(code=Op.STOP)
    delegation_target = pre.deploy_contract(code=Op.STOP)

    # The sender's nonce is bumped at inclusion, before authorizations
    # are processed, so the self-sponsored authorization signs nonce 1.
    authorization = AuthorizationTuple(
        address=delegation_target,
        nonce=1,
        signer=sender,
        first_write=False,
    )

    total_gas_cost = authorization_transaction_cost(fork, [authorization])

    tx = Transaction(
        sender=sender,
        to=recipient,
        value=0,
        authorization_list=[authorization],
        gas_limit=total_gas_cost,
        expected_receipt=TransactionReceipt(
            cumulative_gas_used=total_gas_cost,
        ),
    )

    post = {
        sender: Account(
            nonce=2,
            code=Spec7702.delegation_designation(delegation_target),
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
def test_account_write_authority_is_recipient(
    fork: Fork,
    pre: Alloc,
    state_test: StateTestFiller,
    value: int,
) -> None:
    """
    An authority that is also ``tx.to`` pays ``ACCOUNT_WRITE`` only when
    the transaction moves no value to it.

    The charge depends on whether the transaction transfers value:

    - ``zero_value``: no value is transferred, so at
      authorization-processing time ``tx.to`` has not been written yet
      (only the sender is written at inclusion). The delegation write
      is the transaction's first write to it, so ``ACCOUNT_WRITE`` is
      charged.
    - ``non-zero_value``: the transaction already pays to write
      ``tx.to`` when it transfers value to it, so the delegation write
      is not the first write and no ``ACCOUNT_WRITE`` accrues.

    This resolves the EIP text's "(i.e. the authority differs from
    ``tx.to``)" parenthetical: the rule is first-write tracking, and
    ``tx.to`` counts as pre-written only when the transaction moves
    value to it.

    Either way the authorization writes a net-new delegation indicator
    (``AUTH_BASE``), and after it applies the recipient is delegated, so
    the top frame additionally resolves the delegation target at the
    cold rate before dispatching its code (a ``STOP``).
    """
    authority_initial_balance = 100
    sender = pre.fund_eoa()
    delegation_target = pre.deploy_contract(code=Op.STOP)
    recipient = pre.fund_eoa(amount=authority_initial_balance)

    authorization = AuthorizationTuple(
        address=delegation_target,
        nonce=0,
        signer=recipient,
        first_write=not bool(value),
    )

    # The recipient is delegated by the time the top frame resolves it,
    # so model it as a 7702 delegation: the framework then charges the
    # cold delegation-target access on top of the intrinsic recipient
    # access, matching the spec's resolution of the freshly-set
    # delegation.
    recipient_type = RecipientType.DELEGATION_7702
    authorizations = [authorization]
    top_frame_execution = fork.transaction_top_frame_execution_gas(
        recipient_type=recipient_type,
        authorizations=authorizations,
    )
    top_frame_state = fork.transaction_top_frame_state_gas(
        recipient_type=recipient_type,
        authorizations=authorizations,
    )
    total_gas_cost = (
        _intrinsic_gas(
            fork,
            1,
            recipient_type=recipient_type,
            sends_value=bool(value),
        )
        + top_frame_execution
        + top_frame_state
    )

    tx = Transaction(
        sender=sender,
        to=recipient,
        value=value,
        authorization_list=[authorization],
        gas_limit=total_gas_cost,
        expected_receipt=TransactionReceipt(
            cumulative_gas_used=total_gas_cost,
        ),
    )

    post = {
        recipient: Account(
            nonce=1,
            balance=authority_initial_balance + value,
            code=Spec7702.delegation_designation(delegation_target),
        ),
    }

    state_test(pre=pre, tx=tx, post=post)


@pytest.mark.parametrize(
    "scenario",
    [
        "pre_tx_delegated_re_set",
        "pre_tx_delegated_clear_then_set",
        "multiple_sets",
        "set_clear_cycles",
    ],
)
def test_auth_base_net_new_only(
    fork: Fork,
    pre: Alloc,
    state_test: StateTestFiller,
    scenario: str,
) -> None:
    """
    ``AUTH_BASE`` is charged only when a net-new delegation is set: the
    authority held no delegation before the transaction, none was set
    for it earlier in the transaction, and the current authorization
    sets one. It is charged at most once per authority per transaction
    and is never credited back.

    - ``pre_tx_delegated_re_set``: a pre-delegated authority is
      re-pointed; the indicator bytes already exist, so no
      ``AUTH_BASE``. The re-point is still the transaction's first
      write to the authority, so ``ACCOUNT_WRITE`` applies.
    - ``pre_tx_delegated_clear_then_set``: a pre-delegated authority is
      cleared and then re-delegated in the same transaction. The
      authority held a delegation before the transaction, so neither
      authorization pays ``AUTH_BASE`` (and ``ACCOUNT_WRITE`` applies
      once, at the clear -- the first write).
    - ``multiple_sets``: an empty-code EOA is delegated and then
      re-pointed. Only the first set is net-new: one ``AUTH_BASE``, and
      one ``ACCOUNT_WRITE`` for the first write.
    - ``set_clear_cycles``: an empty-code EOA is set, cleared, set, and
      cleared again. The first set charges ``AUTH_BASE``; the clears
      credit nothing back and the second set is not net-new (a
      delegation was already set in this transaction). Exactly one
      ``AUTH_BASE`` and one ``ACCOUNT_WRITE`` are paid even though the
      authority ends the transaction with no delegation.
    """
    authority_initial_balance = 100
    sender = pre.fund_eoa()
    recipient = pre.deploy_contract(code=Op.STOP)

    target_a = pre.deploy_contract(code=Op.STOP)
    target_b = pre.deploy_contract(code=Op.STOP)

    expected_code: bytes
    if scenario == "pre_tx_delegated_re_set":
        old_target = pre.deploy_contract(code=Op.STOP)
        authority = pre.fund_eoa(
            amount=authority_initial_balance, delegation=old_target
        )
        auth_specs = [target_a]
        first_nonce = 1
        expected_code = Spec7702.delegation_designation(target_a)
        # Delegated before the transaction, so the re-point is not
        # net-new: no AUTH_BASE.
        net_new = [False]
    elif scenario == "pre_tx_delegated_clear_then_set":
        old_target = pre.deploy_contract(code=Op.STOP)
        authority = pre.fund_eoa(
            amount=authority_initial_balance, delegation=old_target
        )
        auth_specs = [NULL_ADDRESS, target_a]
        first_nonce = 1
        expected_code = Spec7702.delegation_designation(target_a)
        # Delegated before the transaction, so neither the clear nor
        # the re-set is net-new.
        net_new = [False, False]
    elif scenario == "multiple_sets":
        authority = pre.fund_eoa(amount=authority_initial_balance)
        auth_specs = [target_a, target_b]
        first_nonce = 0
        expected_code = Spec7702.delegation_designation(target_b)
        # Only the first set is net-new; the re-point is not.
        net_new = [True, False]
    else:  # set_clear_cycles
        authority = pre.fund_eoa(amount=authority_initial_balance)
        auth_specs = [target_a, NULL_ADDRESS, target_b, NULL_ADDRESS]
        first_nonce = 0
        expected_code = b""
        # Only the first set is net-new; the clears credit nothing and
        # the second set is not net-new (already set in this tx).
        net_new = [True, False, False, False]

    authorization_list = [
        AuthorizationTuple(
            address=address,
            nonce=first_nonce + offset,
            signer=authority,
            creates_account=False,
            writes_delegation=net_new[offset],
            # Only the first authorization writes the authority's leaf;
            # later ones on the same authority are not first writes.
            first_write=(offset == 0),
        )
        for offset, address in enumerate(auth_specs)
    ]

    total_gas_cost = authorization_transaction_cost(fork, authorization_list)

    tx = Transaction(
        sender=sender,
        to=recipient,
        value=0,
        authorization_list=authorization_list,
        gas_limit=total_gas_cost,
        expected_receipt=TransactionReceipt(
            cumulative_gas_used=total_gas_cost,
        ),
    )

    post = {
        authority: Account(
            nonce=first_nonce + len(auth_specs),
            balance=authority_initial_balance,
            code=expected_code,
        ),
    }

    state_test(pre=pre, tx=tx, post=post)
