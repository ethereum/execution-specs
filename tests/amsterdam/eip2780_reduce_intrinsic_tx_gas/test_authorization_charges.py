"""
Charge accounting for EIP-7702 authorizations under EIP-2780.

Under EIP-2780 an authorization pays a fixed
``REGULAR_PER_AUTH_BASE_COST`` in the intrinsic and its state-dependent
remainder at the top frame in ``set_delegation``:

- ``NEW_ACCOUNT`` (state) when the authority's account leaf must be
  created,
- ``ACCOUNT_WRITE`` (regular) when applying the authorization is the
  transaction's first write to the authority's leaf (the sender is
  written at inclusion, so a self-sponsored authority pays none), and
- ``AUTH_BASE`` (state) when a net-new delegation is set: none before
  the transaction, none set earlier in the transaction, charged at
  most once per authority and never credited back.

These tests isolate the authorization charge by delegating a
third-party authority (never ``tx.to``), so the recipient top-frame
charge stays out of the picture. The recipient is a plain contract and
no value is transferred, so the transaction's cost is exactly
``intrinsic + top_frame_regular + top_frame_state`` and every scenario
differs only in the authorization's own charges. The post-state
cross-checks that ``set_delegation`` applied each authorization exactly
as its ``creates_account`` / ``writes_delegation`` annotations model.
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

GAS_PRICE = 1_000_000_000


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
    sender_initial_balance = 10**18
    sender = pre.fund_eoa(sender_initial_balance)
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
        max_fee_per_gas=GAS_PRICE,
        max_priority_fee_per_gas=GAS_PRICE,
    )

    post = {
        sender: Account(
            nonce=1,
            balance=sender_initial_balance - total_gas_cost * GAS_PRICE,
        ),
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
    sender_initial_balance = 10**18
    sender = pre.fund_eoa(sender_initial_balance)
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
        max_fee_per_gas=GAS_PRICE,
        max_priority_fee_per_gas=GAS_PRICE,
    )

    post = {
        sender: Account(
            nonce=1,
            balance=sender_initial_balance - total_gas_cost * GAS_PRICE,
        ),
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
    """Return the regular intrinsic gas deducted before execution."""
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
    gas_costs = fork.gas_costs()
    sender_initial_balance = 10**18
    sender = pre.fund_eoa(sender_initial_balance)
    recipient = pre.deploy_contract(code=Op.STOP)

    if authority_prestate == "non_existent":
        scenario = build_authorization(
            pre, AuthorizationAction.CREATES_ACCOUNT
        )
        top_frame_gas = (
            gas_costs.NEW_ACCOUNT
            + gas_costs.ACCOUNT_WRITE
            + gas_costs.AUTH_BASE
        )
    else:
        scenario = build_authorization(
            pre, AuthorizationAction.SETS_NEW_DELEGATION
        )
        top_frame_gas = gas_costs.ACCOUNT_WRITE + gas_costs.AUTH_BASE

    authorization_list = [scenario.authorization]
    total_gas_cost = _intrinsic_gas(fork, 1) + top_frame_gas

    tx = Transaction(
        sender=sender,
        to=recipient,
        value=0,
        authorization_list=authorization_list,
        gas_limit=total_gas_cost,
        max_fee_per_gas=GAS_PRICE,
        max_priority_fee_per_gas=GAS_PRICE,
    )

    post = {
        sender: Account(
            nonce=1,
            balance=sender_initial_balance - total_gas_cost * GAS_PRICE,
        ),
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
    gas_costs = fork.gas_costs()
    sender_initial_balance = 10**18
    sender = pre.fund_eoa(sender_initial_balance)
    recipient = pre.deploy_contract(code=Op.STOP)
    delegation_target = pre.deploy_contract(code=Op.STOP)

    # The sender's nonce is bumped at inclusion, before authorizations
    # are processed, so the self-sponsored authorization signs nonce 1.
    authorization = AuthorizationTuple(
        address=delegation_target,
        nonce=1,
        signer=sender,
    )

    top_frame_gas = gas_costs.AUTH_BASE
    total_gas_cost = _intrinsic_gas(fork, 1) + top_frame_gas

    tx = Transaction(
        sender=sender,
        to=recipient,
        value=0,
        authorization_list=[authorization],
        gas_limit=total_gas_cost,
        max_fee_per_gas=GAS_PRICE,
        max_priority_fee_per_gas=GAS_PRICE,
    )

    post = {
        sender: Account(
            nonce=2,
            balance=sender_initial_balance - total_gas_cost * GAS_PRICE,
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
    An authority that is also ``tx.to`` pays ``ACCOUNT_WRITE``: at
    authorization-processing time the recipient has not been written
    yet (the value transfer only happens at dispatch), so the
    delegation write is the first write to it within the transaction.

    This pins the resolution of the EIP text's "(i.e. the authority
    differs from ``tx.to``)" parenthetical: the rule is first-write
    tracking, and ``tx.to`` is not pre-written -- only the sender is.

    After the authorization applies, the recipient is delegated, so the
    top frame additionally resolves the delegation target at the cold
    rate before dispatching its code (a ``STOP``).
    """
    gas_costs = fork.gas_costs()
    sender_initial_balance = 10**18
    authority_initial_balance = 100
    sender = pre.fund_eoa(sender_initial_balance)
    delegation_target = pre.deploy_contract(code=Op.STOP)
    recipient = pre.fund_eoa(amount=authority_initial_balance)

    authorization = AuthorizationTuple(
        address=delegation_target,
        nonce=0,
        signer=recipient,
    )

    intrinsic_gas = _intrinsic_gas(
        fork,
        1,
        recipient_type=RecipientType.EOA,
        sends_value=bool(value),
    )
    top_frame_gas = (
        gas_costs.ACCOUNT_WRITE
        + gas_costs.AUTH_BASE
        # The recipient is delegated by the time the top frame resolves
        # it; the delegation target is cold.
        + gas_costs.COLD_ACCOUNT_ACCESS
    )
    total_gas_cost = intrinsic_gas + top_frame_gas

    tx = Transaction(
        sender=sender,
        to=recipient,
        value=value,
        authorization_list=[authorization],
        gas_limit=total_gas_cost,
        max_fee_per_gas=GAS_PRICE,
        max_priority_fee_per_gas=GAS_PRICE,
    )

    post = {
        sender: Account(
            nonce=1,
            balance=sender_initial_balance
            - value
            - total_gas_cost * GAS_PRICE,
        ),
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
    gas_costs = fork.gas_costs()
    sender_initial_balance = 10**18
    authority_initial_balance = 100
    sender = pre.fund_eoa(sender_initial_balance)
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
        auth_base_count = 0
    elif scenario == "pre_tx_delegated_clear_then_set":
        old_target = pre.deploy_contract(code=Op.STOP)
        authority = pre.fund_eoa(
            amount=authority_initial_balance, delegation=old_target
        )
        auth_specs = [NULL_ADDRESS, target_a]
        first_nonce = 1
        expected_code = Spec7702.delegation_designation(target_a)
        auth_base_count = 0
    elif scenario == "multiple_sets":
        authority = pre.fund_eoa(amount=authority_initial_balance)
        auth_specs = [target_a, target_b]
        first_nonce = 0
        expected_code = Spec7702.delegation_designation(target_b)
        auth_base_count = 1
    else:  # set_clear_cycles
        authority = pre.fund_eoa(amount=authority_initial_balance)
        auth_specs = [target_a, NULL_ADDRESS, target_b, NULL_ADDRESS]
        first_nonce = 0
        expected_code = b""
        auth_base_count = 1

    authorization_list = [
        AuthorizationTuple(
            address=address,
            nonce=first_nonce + offset,
            signer=authority,
        )
        for offset, address in enumerate(auth_specs)
    ]

    top_frame_gas = (
        gas_costs.ACCOUNT_WRITE + auth_base_count * gas_costs.AUTH_BASE
    )
    total_gas_cost = (
        _intrinsic_gas(fork, len(authorization_list)) + top_frame_gas
    )

    tx = Transaction(
        sender=sender,
        to=recipient,
        value=0,
        authorization_list=authorization_list,
        gas_limit=total_gas_cost,
        max_fee_per_gas=GAS_PRICE,
        max_priority_fee_per_gas=GAS_PRICE,
    )

    post = {
        sender: Account(
            nonce=1,
            balance=sender_initial_balance - total_gas_cost * GAS_PRICE,
        ),
        authority: Account(
            nonce=first_nonce + len(auth_specs),
            balance=authority_initial_balance,
            code=expected_code,
        ),
    }

    state_test(pre=pre, tx=tx, post=post)
