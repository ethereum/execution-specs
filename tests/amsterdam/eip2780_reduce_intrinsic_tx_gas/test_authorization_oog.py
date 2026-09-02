"""
Out-of-gas rollback semantics for EIP-7702 authorizations under
EIP-2780.

At the top frame, EIP-2780 charges each authorization's
state-dependent cost in ``set_delegation`` and then charges the
recipient's or contract-creation ``NEW_ACCOUNT`` and any
delegation-resolution access -- all before dispatching the call. Two
snapshots bound these two phases:

- **Prep-phase OOG** -- a charge anywhere in the top-frame preparation
  runs out: inside ``set_delegation``, on the recipient's
  ``NEW_ACCOUNT``, or on the delegation-resolution access. The whole
  preparation shares one snapshot, so every authorization applied so
  far is rolled back and the frame halts without dispatching. The
  transaction is still included and consumes its full execution budget;
  a state-gas reservoir, whose charges are refilled with the rollback,
  is returned to the sender in full. The sender nonce (bumped at
  inclusion, before the snapshot) is not rolled back.
- **Execution-phase failure** -- the dispatched call itself reverts or
  runs out of gas. A second snapshot is taken after preparation, so the
  applied delegations persist, matching the EIP-7702 "dispatch reverts,
  delegation remains" rule.

Because the applied delegations persist across an execution-phase
failure, the state gas that paid for them (the authority's
``NEW_ACCOUNT`` leaf and ``AUTH_BASE`` indicator bytes) must stay
consumed: only state gas whose state effects are rolled back with the
frame (e.g. an ``SSTORE`` inside the dispatched call) is refilled.

"""

import pytest
from execution_testing import (
    EOA,
    Account,
    Address,
    Alloc,
    AuthorizationTuple,
    BalAccountExpectation,
    BalBalanceChange,
    BalCodeChange,
    BalNonceChange,
    Block,
    BlockAccessListExpectation,
    BlockchainTestFiller,
    Bytecode,
    Environment,
    Fork,
    Header,
    Op,
    RecipientType,
    StateTestFiller,
    Transaction,
    TransactionException,
    TransactionReceipt,
)
from execution_testing.checklists import EIPChecklist

from ...prague.eip7702_set_code_tx.spec import Spec as Spec7702
from .helpers import (
    EOA_INITIAL_BALANCE,
    AuthorizationAction,
    AuthorizationScenario,
    build_authorization,
)
from .spec import ref_spec_2780

REFERENCE_SPEC_GIT_PATH = ref_spec_2780.git_path
REFERENCE_SPEC_VERSION = ref_spec_2780.version

pytestmark = pytest.mark.valid_from("Amsterdam")


def _auth_top_frame_charges(fork: Fork, authorizations: list) -> int:
    """
    Return the top-frame execution + state gas attributable to the
    authorizations alone.

    Computed against a ``CONTRACT`` recipient, which contributes no
    top-frame charge, so the result is exactly the sum of each
    authorization's own ``ACCOUNT_WRITE`` / ``NEW_ACCOUNT`` /
    ``AUTH_BASE``. Under the zero state reservoir these all draw from
    ``gas_left``.
    """
    execution = fork.transaction_top_frame_gas_calculator()(
        recipient_type=RecipientType.CONTRACT,
        authorizations=authorizations,
    )
    state = fork.transaction_top_frame_state_gas(
        recipient_type=RecipientType.CONTRACT,
        authorizations=authorizations,
    )
    return execution + state


def _intrinsic_execution(
    fork: Fork,
    authorization_list: list,
    *,
    recipient_type: RecipientType,
    sends_value: bool = False,
) -> int:
    """Return the execution intrinsic gas deducted before execution."""
    return fork.transaction_intrinsic_cost_calculator()(
        recipient_type=recipient_type,
        sends_value=sends_value,
        authorization_list_or_count=authorization_list,
        return_cost_deducted_prior_execution=True,
    )


def _applied_delegation_bal(
    scenario: AuthorizationScenario,
) -> BalAccountExpectation:
    """
    BAL entry for an authority whose applied delegation reaches the
    post-state.

    The nonce bump and delegation-code write are applied before the
    execution snapshot, so they also survive a dispatched frame's
    revert or halt and must be recorded in the block access list.
    """
    return BalAccountExpectation(
        nonce_changes=[
            BalNonceChange(
                block_access_index=1,
                post_nonce=scenario.applied_account.nonce,
            )
        ],
        code_changes=[
            BalCodeChange(
                block_access_index=1,
                new_code=scenario.applied_account.code,
            )
        ],
    )


@EIPChecklist.GasCostChanges.Test.OutOfGas()
@EIPChecklist.GasCostChanges.Test.GasUpdatesMeasurement()
@pytest.mark.parametrize(
    "outcome", ["new_account", "account_write", "auth_base", "succeeds"]
)
def test_set_delegation_oog_charge_point(
    fork: Fork,
    pre: Alloc,
    state_test: StateTestFiller,
    outcome: str,
) -> None:
    """
    OOG at each distinct charge point inside ``set_delegation`` rolls
    the whole authorization phase back atomically.

    The first authorization creates and delegates its authority in full
    (exercising ``NEW_ACCOUNT`` + ``ACCOUNT_WRITE`` + ``AUTH_BASE``). The
    ``gas_limit`` then starves the second authorization at exactly the
    parametrized charge:

    - ``new_account``: the second (a creation) runs out at its opening
      ``NEW_ACCOUNT`` state charge.
    - ``account_write``: the second covers ``NEW_ACCOUNT`` but runs out
      at the following ``ACCOUNT_WRITE`` execution charge.
    - ``auth_base``: the second (a delegation on an existing empty EOA)
      covers its first-write ``ACCOUNT_WRITE`` but runs out at the
      following ``AUTH_BASE`` state charge.
    - ``succeeds``: as ``auth_base``, but with the one starved gas
      restored the closing ``AUTH_BASE`` is covered exactly and both
      authorizations apply, pinning the off-by-one boundary of the
      last charge from above.

    In every out-of-gas case the transaction halts in
    ``set_delegation`` and both authorizations are rolled back -- the
    first, already applied, as well as the second -- so both
    authorities return to their pre-tx state. The receipt shows the
    full ``gas_limit`` consumed (exactly covered, in the ``succeeds``
    case) and the sender nonce is not rolled back.

    Both authorities are read during authorization validation before
    the halt, so per EIP-7928 they still appear in the block access
    list; only in the ``succeeds`` case do they record changes. The
    recipient is only loaded by the top-frame dispatch, so it must be
    absent whenever the halt precedes it.
    """
    gas_costs = fork.gas_costs()
    sender = pre.fund_eoa()
    recipient = pre.deploy_contract(code=Op.STOP)

    first = build_authorization(pre, AuthorizationAction.CREATES_ACCOUNT)
    if outcome in ("auth_base", "succeeds"):
        second = build_authorization(
            pre, AuthorizationAction.SETS_NEW_DELEGATION
        )
    else:
        second = build_authorization(pre, AuthorizationAction.CREATES_ACCOUNT)

    authorization_list = [first.authorization, second.authorization]

    intrinsic_execution = _intrinsic_execution(
        fork, authorization_list, recipient_type=RecipientType.CONTRACT
    )
    first_auth_charges = _auth_top_frame_charges(fork, [first.authorization])

    # gas_left entering set_delegation is gas_limit - intrinsic_execution
    # (the state reservoir is zero). The first authorization is applied
    # in full; the second is starved by one gas at the target charge,
    # after covering any charges that precede it within that same
    # authorization -- or, for ``succeeds``, covered exactly.
    if outcome == "new_account":
        preceding = 0
        shortfall_charge = gas_costs.NEW_ACCOUNT
    elif outcome == "account_write":
        preceding = gas_costs.NEW_ACCOUNT
        shortfall_charge = gas_costs.ACCOUNT_WRITE
    else:  # auth_base / succeeds
        preceding = gas_costs.ACCOUNT_WRITE
        shortfall_charge = gas_costs.AUTH_BASE

    gas_limit = (
        intrinsic_execution + first_auth_charges + preceding + shortfall_charge
    )
    if outcome != "succeeds":
        gas_limit -= 1

    tx = Transaction(
        sender=sender,
        to=recipient,
        value=0,
        authorization_list=authorization_list,
        gas_limit=gas_limit,
        expected_receipt=TransactionReceipt(
            cumulative_gas_used=gas_limit,
        ),
    )

    post: dict[EOA, Account | None]
    if outcome == "succeeds":
        post = {
            first.authority: first.applied_account,
            second.authority: second.applied_account,
        }
        expected_block_access_list = BlockAccessListExpectation(
            account_expectations={
                recipient: BalAccountExpectation.empty(),
                first.authority: _applied_delegation_bal(first),
                second.authority: _applied_delegation_bal(second),
            }
        )
    else:
        post = {
            first.authority: first.original_account,
            second.authority: second.original_account,
        }
        # An implementation recording accesses only for dispatched
        # frames would drop the authority entries; one recording the
        # recipient at inclusion would add it. Either forks on the BAL
        # hash.
        expected_block_access_list = BlockAccessListExpectation(
            account_expectations={
                recipient: None,
                first.authority: BalAccountExpectation.empty(),
                second.authority: BalAccountExpectation.empty(),
            }
        )

    state_test(
        pre=pre,
        tx=tx,
        post=post,
        expected_block_access_list=expected_block_access_list,
    )


@EIPChecklist.GasCostChanges.Test.OutOfGas()
@pytest.mark.parametrize(
    "first_action",
    [
        AuthorizationAction.SETS_NEW_DELEGATION,
        AuthorizationAction.SETS_DIFFERENT_DELEGATION,
        AuthorizationAction.SETS_SAME_DELEGATION,
        AuthorizationAction.CLEARS_DELEGATION,
    ],
    ids=lambda a: a.name.lower(),
)
def test_set_delegation_oog_rolls_back_first_auth(
    fork: Fork,
    pre: Alloc,
    state_test: StateTestFiller,
    first_action: AuthorizationAction,
) -> None:
    """
    Auth-phase rollback undoes every flavor of the surviving first
    authorization's mutation.

    A second authorization (a creation) is starved at its opening
    ``NEW_ACCOUNT`` charge, so the whole authorization phase rolls back.
    The first authorization -- which applied in full before the OOG --
    is parametrized across the action space, and the post-state confirms
    its mutation is fully reverted:

    - ``SETS_NEW_DELEGATION``: the fresh delegation and nonce bump are
      undone (authority back to an empty EOA).
    - ``SETS_DIFFERENT_DELEGATION`` / ``SETS_SAME_DELEGATION``: the
      re-point and nonce bump are undone (authority back to its original
      delegation).
    - ``CLEARS_DELEGATION``: the clear and nonce bump are undone
      (authority's original delegation restored).

    The creation-first case is covered by
    ``test_set_delegation_oog_charge_point[new_account]``.

    Both authorities are read during validation before the halt and
    stay in the block access list with no recorded changes; the
    recipient, never loaded before the halt, must be absent.
    """
    gas_costs = fork.gas_costs()
    sender = pre.fund_eoa()
    recipient = pre.deploy_contract(code=Op.STOP)

    first = build_authorization(pre, first_action)
    second = build_authorization(pre, AuthorizationAction.CREATES_ACCOUNT)
    authorization_list = [first.authorization, second.authorization]

    intrinsic_execution = _intrinsic_execution(
        fork, authorization_list, recipient_type=RecipientType.CONTRACT
    )
    first_auth_charges = _auth_top_frame_charges(fork, [first.authorization])

    # The first authorization applies in full; the second (a creation)
    # runs out at its opening NEW_ACCOUNT state charge, rolling back the
    # whole authorization phase.
    gas_limit = (
        intrinsic_execution + first_auth_charges + gas_costs.NEW_ACCOUNT - 1
    )

    tx = Transaction(
        sender=sender,
        to=recipient,
        value=0,
        authorization_list=authorization_list,
        gas_limit=gas_limit,
        expected_receipt=TransactionReceipt(
            cumulative_gas_used=gas_limit,
        ),
    )

    post = {
        first.authority: first.original_account,
        second.authority: second.original_account,
    }

    expected_block_access_list = BlockAccessListExpectation(
        account_expectations={
            recipient: None,
            first.authority: BalAccountExpectation.empty(),
            second.authority: BalAccountExpectation.empty(),
        }
    )

    state_test(
        pre=pre,
        tx=tx,
        post=post,
        expected_block_access_list=expected_block_access_list,
    )


@EIPChecklist.GasCostChanges.Test.OutOfGas()
@EIPChecklist.GasCostChanges.Test.GasUpdatesMeasurement()
@pytest.mark.parametrize(
    "succeeds",
    [
        pytest.param(False, id="fails"),
        pytest.param(True, id="succeeds"),
    ],
)
@pytest.mark.parametrize(
    "recipient_charge", ["new_account", "delegation_access"]
)
def test_recipient_charge_oog_rolls_back_delegations(
    fork: Fork,
    pre: Alloc,
    state_test: StateTestFiller,
    recipient_charge: str,
    succeeds: bool,
) -> None:
    """
    A recipient top-frame charge running out of gas rolls back the
    already-applied delegations, because it shares the preparation
    snapshot with ``set_delegation``.

    Two valid authorizations on third-party authorities are paid in
    full, then the recipient's own top-frame charge is starved by one
    gas:

    - ``new_account``: value moves to an EIP-161-empty recipient, whose
      ``NEW_ACCOUNT`` state charge runs out.
    - ``delegation_access``: the recipient is a pre-existing delegation
      whose top-frame ``COLD_ACCOUNT_ACCESS`` charge runs out.

    The recipient charge is part of the top-frame preparation, so its
    out-of-gas unwinds the whole preparation: both authorities return to
    their pre-transaction state. The transaction is still included, the
    receipt shows the full ``gas_limit`` consumed, and the recipient
    itself is unchanged.

    The recipient and both authorities were accessed before the halt,
    so per EIP-7928 all three must still appear in the block access
    list, with no recorded changes. The recipient's delegation target
    is only ever loaded by the resolution the starved charge pays for,
    so it must be absent from the list on the out-of-gas side and
    present (with no changes) on the succeeding side.

    The ``succeeds`` control restores the one starved gas: the
    recipient charge is covered exactly, the dispatch completes (the
    recipient runs no code of its own), and the delegations -- and any
    value moved -- stick, pinning the off-by-one boundary from above.
    """
    gas_costs = fork.gas_costs()
    sender = pre.fund_eoa()

    auth_a = build_authorization(pre, AuthorizationAction.CREATES_ACCOUNT)
    auth_b = build_authorization(pre, AuthorizationAction.SETS_NEW_DELEGATION)
    authorization_list = [auth_a.authorization, auth_b.authorization]
    auth_charges = _auth_top_frame_charges(fork, authorization_list)

    recipient_bal = BalAccountExpectation.empty()
    delegation_target_bal: dict[Address, BalAccountExpectation | None] = {}
    if recipient_charge == "new_account":
        recipient = pre.fund_eoa(amount=0)
        value = 1
        recipient_type = RecipientType.EMPTY_ACCOUNT
        recipient_charge_gas = gas_costs.NEW_ACCOUNT
        if succeeds:
            expected_recipient: Account | None = Account(balance=value)
            recipient_bal = BalAccountExpectation(
                balance_changes=[
                    BalBalanceChange(block_access_index=1, post_balance=value)
                ]
            )
        else:
            expected_recipient = None
    else:  # delegation_access
        delegated_to = pre.deploy_contract(code=Op.STOP)
        recipient = pre.fund_eoa(
            amount=EOA_INITIAL_BALANCE, delegation=delegated_to
        )
        value = 0
        recipient_type = RecipientType.DELEGATION_7702
        recipient_charge_gas = gas_costs.COLD_ACCOUNT_ACCESS
        expected_recipient = Account(
            nonce=1,
            balance=EOA_INITIAL_BALANCE,
            code=Spec7702.delegation_designation(delegated_to),
        )
        # The delegation target is only loaded by the resolution access
        # the starved charge pays for: read (unchanged) on success,
        # never accessed -- so absent from the block access list -- when
        # the charge runs out.
        delegation_target_bal = {
            delegated_to: BalAccountExpectation.empty() if succeeds else None
        }

    intrinsic_execution = _intrinsic_execution(
        fork,
        authorization_list,
        recipient_type=recipient_type,
        sends_value=bool(value),
    )

    # Both authorizations apply, then the recipient's top-frame charge
    # is starved by one gas -- or, with ``succeeds``, covered exactly.
    # The charge shares the preparation snapshot, so its out-of-gas
    # rolls the applied delegations back.
    gas_limit = intrinsic_execution + auth_charges + recipient_charge_gas
    if not succeeds:
        gas_limit -= 1

    tx = Transaction(
        sender=sender,
        to=recipient,
        value=value,
        authorization_list=authorization_list,
        gas_limit=gas_limit,
        expected_receipt=TransactionReceipt(
            cumulative_gas_used=gas_limit,
        ),
    )

    if succeeds:
        post = {
            auth_a.authority: auth_a.applied_account,
            auth_b.authority: auth_b.applied_account,
            recipient: expected_recipient,
        }
        expected_block_access_list = BlockAccessListExpectation(
            account_expectations={
                recipient: recipient_bal,
                auth_a.authority: _applied_delegation_bal(auth_a),
                auth_b.authority: _applied_delegation_bal(auth_b),
                **delegation_target_bal,
            }
        )
    else:
        post = {
            auth_a.authority: auth_a.original_account,
            auth_b.authority: auth_b.original_account,
            recipient: expected_recipient,
        }
        expected_block_access_list = BlockAccessListExpectation(
            account_expectations={
                recipient: BalAccountExpectation.empty(),
                auth_a.authority: BalAccountExpectation.empty(),
                auth_b.authority: BalAccountExpectation.empty(),
                **delegation_target_bal,
            }
        )

    state_test(
        pre=pre,
        tx=tx,
        post=post,
        expected_block_access_list=expected_block_access_list,
    )


@EIPChecklist.GasCostChanges.Test.OutOfGas()
@EIPChecklist.GasCostChanges.Test.GasUpdatesMeasurement()
@pytest.mark.parametrize(
    "failure_point",
    [
        "set_delegation_oog",
        "dispatch_charge_oog",
        "execution_halt",
        "execution_revert",
    ],
)
def test_reservoir_settlement_by_failure_point(
    fork: Fork,
    pre: Alloc,
    state_test: StateTestFiller,
    failure_point: str,
) -> None:
    """
    One transaction shape with a non-zero state-gas reservoir, failed
    at each point along the top frame, settles four different ways.

    A non-zero reservoir requires ``gas_limit`` above the EIP-7825 cap,
    which also hands the frame the *full* execution budget -- so starving
    the preparation is only reachable when its demand exceeds the cap
    plus the reservoir. Account-creating authorizations are the one
    charge dense enough to get there: each demands ~234,606 gas
    (intrinsic base, ``ACCOUNT_WRITE``, and ``NEW_ACCOUNT`` +
    ``AUTH_BASE`` state bytes), so ~73 of them overtop the cap. The
    count is derived from the fork's calculators. The recipient is a
    delegated EOA in every scenario, so the top-frame dispatch always
    owes a cold delegation-resolution access and only the
    ``failure_point`` moves:

    - ``set_delegation_oog``: the last authorization's closing
      ``AUTH_BASE`` charge is starved by one gas. The preparation
      snapshot rolls every delegation back, the refilled state charges
      restore the reservoir, and settlement returns it whole:
      ``gas_used == cap`` exactly, however much extra gas was sent.
    - ``dispatch_charge_oog``: every authorization applies, then the
      recipient's delegation-resolution access is starved by one gas.
      The charge shares the preparation snapshot, so the settlement is
      identical: ``gas_used == cap``.
    - ``execution_halt``: preparation completes and the delegated code
      hits ``INVALID``. The persisting delegations keep their state gas
      consumed -- far more than the reservoir holds -- so the fold
      leaves the reservoir empty and the halt burns the rest:
      ``gas_used == gas_limit``, the full amount.
    - ``execution_revert``: as above, but ``REVERT`` returns the unused
      execution budget: ``gas_used`` is exactly the intrinsic cost plus
      every preparation charge plus the reverting code's own gas.

    Together the four pin that the reservoir's fate follows the state
    it paid for: returned in full while nothing survives, consumed to
    the extent the delegations persist.
    """
    cap = fork.transaction_gas_limit_cap()
    assert cap is not None, "EIP-7825 cap expected on this fork"
    gas_costs = fork.gas_costs()

    sender = pre.fund_eoa()

    # Two distinct delegation targets are in play. ``delegation_target``
    # is the address every *authority's* authorization designates:
    # ``set_delegation`` writes it into the authorities' code but never
    # reads the account itself.
    delegation_target = pre.deploy_contract(code=Op.STOP)
    recipient_code: Bytecode
    if failure_point == "execution_halt":
        recipient_code = Op.INVALID
    elif failure_point == "execution_revert":
        recipient_code = Op.REVERT(0, 0)
    else:
        recipient_code = Op.STOP
    # ``code_target`` is the *recipient's* pre-existing delegation
    # target: the top-frame dispatch pays a cold access to resolve it
    # and, once paid, loads and runs its code.
    code_target = pre.deploy_contract(code=recipient_code)
    recipient = pre.fund_eoa(
        amount=EOA_INITIAL_BALANCE, delegation=code_target
    )

    def creation_authorization(authority: EOA) -> AuthorizationTuple:
        """Authorization creating a fresh authority's account leaf."""
        return AuthorizationTuple(
            address=delegation_target,
            nonce=0,
            signer=authority,
            creates_account=True,
        )

    probe_authority = pre.fund_eoa(amount=0)
    probe = creation_authorization(probe_authority)
    base_intrinsic = _intrinsic_execution(
        fork, [], recipient_type=RecipientType.DELEGATION_7702
    )
    per_auth_intrinsic = (
        _intrinsic_execution(
            fork, [probe], recipient_type=RecipientType.DELEGATION_7702
        )
        - base_intrinsic
    )
    per_auth_charges = _auth_top_frame_charges(fork, [probe])
    per_auth_total = per_auth_intrinsic + per_auth_charges

    # The smallest authorization count whose starved-by-one gas limit
    # exceeds the cap, plus one more so the reservoir is larger than a
    # full authorization's preparation charge -- a refund too big to be
    # confused with any single refilled charge.
    min_count = (cap + 1 - base_intrinsic) // per_auth_total + 1
    auth_count = min_count + 1

    authorities = [probe_authority] + [
        pre.fund_eoa(amount=0) for _ in range(auth_count - 1)
    ]
    authorization_list = [probe] + [
        creation_authorization(authority) for authority in authorities[1:]
    ]

    intrinsic_execution = base_intrinsic + auth_count * per_auth_intrinsic
    auth_charges = auth_count * per_auth_charges
    dispatch_charge = gas_costs.COLD_ACCOUNT_ACCESS
    auth_state_total = fork.transaction_top_frame_state_gas(
        recipient_type=RecipientType.CONTRACT,
        authorizations=authorization_list,
    )

    if failure_point == "set_delegation_oog":
        # The final authorization's closing AUTH_BASE is starved by one.
        gas_limit = intrinsic_execution + auth_charges - 1
        expected_gas_used = cap
        delegations_persist = False
    elif failure_point == "dispatch_charge_oog":
        # All authorizations apply; the recipient's cold
        # delegation-resolution access is starved by one.
        gas_limit = intrinsic_execution + auth_charges + dispatch_charge - 1
        expected_gas_used = cap
        delegations_persist = False
    elif failure_point == "execution_halt":
        gas_limit = (
            intrinsic_execution + auth_charges + dispatch_charge + 10_000
        )
        expected_gas_used = gas_limit
        delegations_persist = True
    else:  # execution_revert
        exec_gas = recipient_code.gas_cost(fork)
        gas_limit = (
            intrinsic_execution
            + auth_charges
            + dispatch_charge
            + exec_gas
            + 10_000
        )
        expected_gas_used = (
            intrinsic_execution + auth_charges + dispatch_charge + exec_gas
        )
        delegations_persist = True

    reservoir = gas_limit - cap
    if delegations_persist:
        # The persisting delegations' state gas exceeds the reservoir,
        # so the reservoir is consumed in full.
        assert reservoir < auth_state_total, (
            "the persisted auth state gas must swallow the reservoir"
        )
    else:
        assert reservoir > per_auth_charges, (
            "the reservoir must exceed one authorization's charges"
        )

    tx = Transaction(
        sender=sender,
        to=recipient,
        value=0,
        authorization_list=authorization_list,
        gas_limit=gas_limit,
        expected_receipt=TransactionReceipt(
            cumulative_gas_used=expected_gas_used,
        ),
    )

    applied_authority = Account(
        nonce=1,
        balance=0,
        code=Spec7702.delegation_designation(delegation_target),
    )
    post = {
        recipient: Account(
            nonce=1,
            balance=EOA_INITIAL_BALANCE,
            code=Spec7702.delegation_designation(code_target),
        ),
        **(
            dict.fromkeys(authorities, applied_authority)
            if delegations_persist
            # Every authority's account creation is rolled back.
            else dict.fromkeys(authorities)
        ),
    }

    # All authorities are read during authorization validation before
    # any failure, so they always appear in the block access list --
    # with their persisted nonce and code writes past an execution
    # failure, with no recorded changes past a preparation rollback.
    # The recipient is only loaded once preparation reaches the
    # dispatch charge, and its delegation target only once that charge
    # is paid and the delegated code loads -- so both out-of-gas
    # scenarios must leave the target absent from the list. The
    # authorities' delegation target is never read at all: writing a
    # designation does not access the designated account.
    if delegations_persist:
        authority_bal = BalAccountExpectation(
            nonce_changes=[BalNonceChange(block_access_index=1, post_nonce=1)],
            code_changes=[
                BalCodeChange(
                    block_access_index=1,
                    new_code=Spec7702.delegation_designation(
                        delegation_target
                    ),
                )
            ],
        )
    else:
        authority_bal = BalAccountExpectation.empty()
    recipient_bal = (
        None
        if failure_point == "set_delegation_oog"
        else BalAccountExpectation.empty()
    )
    code_target_bal = (
        BalAccountExpectation.empty() if delegations_persist else None
    )
    expected_block_access_list = BlockAccessListExpectation(
        account_expectations={
            recipient: recipient_bal,
            code_target: code_target_bal,
            delegation_target: None,
            **dict.fromkeys(authorities, authority_bal),
        }
    )

    state_test(
        pre=pre,
        tx=tx,
        post=post,
        expected_block_access_list=expected_block_access_list,
    )


@EIPChecklist.GasCostChanges.Test.OutOfGas()
@EIPChecklist.GasCostChanges.Test.GasUpdatesMeasurement()
@pytest.mark.parametrize(
    "failure_point",
    ["set_delegation_oog", "dispatch_charge_oog", "execution_halt"],
)
def test_reservoir_settlement_with_value_to_empty_recipient(
    fork: Fork,
    pre: Alloc,
    state_test: StateTestFiller,
    failure_point: str,
) -> None:
    """
    The many-authorization reservoir transaction, now moving value to an
    empty recipient, carries both classes of state charge at once --
    and a failure settles each class by whether its state survives.

    The value transfer adds the recipient's ``NEW_ACCOUNT`` dispatch
    charge alongside the authorizations' ``NEW_ACCOUNT`` + ``AUTH_BASE``
    charges. The recipient is a precompile (here the bn254 pairing) --
    an empty account that still executes, so an execution-phase failure
    is reachable (a 1-byte input makes the pairing exceptionally halt
    after the value has moved). An empty recipient runs no code of its
    own, so there is no revert scenario here; the delegated-recipient
    variant above covers it.

    - ``set_delegation_oog``: the last authorization's closing
      ``AUTH_BASE`` is starved by one gas. Everything rolls back and
      the whole reservoir returns: ``gas_used == cap``.
    - ``dispatch_charge_oog``: every authorization applies, then the
      recipient's ``NEW_ACCOUNT`` state charge is starved by one gas.
      It shares the preparation snapshot: ``gas_used == cap``.
    - ``execution_halt``: the reservoir is sized *above* the
      authorizations' total state gas, so it survives the preparation
      and the settlement can distinguish the two charge classes. The
      precompile halts after the transfer: the recipient's leaf rolls
      back, so its ``NEW_ACCOUNT`` refills and returns with the
      reservoir remainder, while the persisting delegations keep their
      state gas consumed -- ``gas_used == cap + auth_state_total``
      exactly. (With a small reservoir the refill would be burned with
      ``gas_left`` and be unobservable, which is why the sizes differ
      per scenario.)

    In every scenario the transfer never sticks: the recipient's leaf
    is absent from the post state and the sender keeps the value,
    paying only the gas.
    """
    cap = fork.transaction_gas_limit_cap()
    assert cap is not None, "EIP-7825 cap expected on this fork"
    gas_costs = fork.gas_costs()

    value = 1
    sender = pre.fund_eoa()
    recipient = Address(0x08)

    delegation_target = pre.deploy_contract(code=Op.STOP)

    def creation_authorization(authority: EOA) -> AuthorizationTuple:
        """Authorization creating a fresh authority's account leaf."""
        return AuthorizationTuple(
            address=delegation_target,
            nonce=0,
            signer=authority,
            creates_account=True,
        )

    probe_authority = pre.fund_eoa(amount=0)
    probe = creation_authorization(probe_authority)
    base_intrinsic = _intrinsic_execution(
        fork,
        [],
        recipient_type=RecipientType.EMPTY_ACCOUNT,
        sends_value=True,
    )
    per_auth_intrinsic = (
        _intrinsic_execution(
            fork,
            [probe],
            recipient_type=RecipientType.EMPTY_ACCOUNT,
            sends_value=True,
        )
        - base_intrinsic
    )
    per_auth_charges = _auth_top_frame_charges(fork, [probe])
    per_auth_total = per_auth_intrinsic + per_auth_charges

    # The smallest authorization count whose starved-by-one gas limit
    # exceeds the cap, plus one more so the starved scenarios' reservoir
    # exceeds a full authorization's preparation charge.
    min_count = (cap + 1 - base_intrinsic) // per_auth_total + 1
    auth_count = min_count + 1

    authorities = [probe_authority] + [
        pre.fund_eoa(amount=0) for _ in range(auth_count - 1)
    ]
    authorization_list = [probe] + [
        creation_authorization(authority) for authority in authorities[1:]
    ]

    intrinsic_execution = base_intrinsic + auth_count * per_auth_intrinsic
    auth_charges = auth_count * per_auth_charges
    auth_state_total = fork.transaction_top_frame_state_gas(
        recipient_type=RecipientType.CONTRACT,
        authorizations=authorization_list,
    )

    data = b""
    if failure_point == "set_delegation_oog":
        # The final authorization's closing AUTH_BASE is starved by one.
        gas_limit = intrinsic_execution + auth_charges - 1
        expected_gas_used = cap
        delegations_persist = False
    elif failure_point == "dispatch_charge_oog":
        # All authorizations apply; the recipient's NEW_ACCOUNT state
        # charge is starved by one.
        gas_limit = (
            intrinsic_execution + auth_charges + gas_costs.NEW_ACCOUNT - 1
        )
        expected_gas_used = cap
        delegations_persist = False
    else:  # execution_halt
        # One byte: not a multiple of 192, so the pairing precompile
        # exceptionally halts after the value has moved. The reservoir
        # covers the authorizations' state gas and the recipient's
        # NEW_ACCOUNT with headroom, so no preparation charge spills
        # into gas_left and the refill is observable in the settlement.
        data = b"\x00"
        gas_limit = cap + auth_state_total + gas_costs.NEW_ACCOUNT + 100_000
        expected_gas_used = cap + auth_state_total
        delegations_persist = True

    reservoir = gas_limit - cap
    if delegations_persist:
        assert reservoir > auth_state_total, (
            "the reservoir must survive the persisted auth state gas"
        )
    else:
        assert reservoir > per_auth_charges, (
            "the reservoir must exceed one authorization's charges"
        )

    tx = Transaction(
        sender=sender,
        to=recipient,
        value=value,
        data=data,
        authorization_list=authorization_list,
        gas_limit=gas_limit,
        expected_receipt=TransactionReceipt(
            cumulative_gas_used=expected_gas_used,
        ),
    )

    applied_authority = Account(
        nonce=1,
        balance=0,
        code=Spec7702.delegation_designation(delegation_target),
    )
    post: dict[Address, Account | None] = {
        # The transfer never sticks; the recipient's leaf stays absent.
        recipient: None,
        **(
            dict.fromkeys(authorities, applied_authority)
            if delegations_persist
            else dict.fromkeys(authorities)
        ),
    }

    # The recipient is first loaded for its NEW_ACCOUNT alive-check, so
    # it is absent from the block access list only when the halt lands
    # inside set_delegation; afterwards it appears with no net change
    # (the transfer, if any, rolled back). The authorities' delegation
    # target is never read at all: writing a designation does not
    # access the designated account.
    if delegations_persist:
        authority_bal = BalAccountExpectation(
            nonce_changes=[BalNonceChange(block_access_index=1, post_nonce=1)],
            code_changes=[
                BalCodeChange(
                    block_access_index=1,
                    new_code=Spec7702.delegation_designation(
                        delegation_target
                    ),
                )
            ],
        )
    else:
        authority_bal = BalAccountExpectation.empty()
    recipient_bal = (
        None
        if failure_point == "set_delegation_oog"
        else BalAccountExpectation.empty()
    )
    expected_block_access_list = BlockAccessListExpectation(
        account_expectations={
            recipient: recipient_bal,
            delegation_target: None,
            **dict.fromkeys(authorities, authority_bal),
        }
    )

    state_test(
        pre=pre,
        tx=tx,
        post=post,
        expected_block_access_list=expected_block_access_list,
    )


@EIPChecklist.GasCostChanges.Test.OutOfGas()
@pytest.mark.parametrize(
    "value",
    [pytest.param(0, id="no_value"), pytest.param(1, id="with_value")],
)
def test_delegation_persists_on_execution_oog(
    fork: Fork,
    pre: Alloc,
    state_test: StateTestFiller,
    value: int,
) -> None:
    """
    Once the top-frame preparation completes, an out-of-gas in the
    dispatched call does NOT roll the applied delegations back.

    Two valid authorizations on third-party authorities are paid in
    full and the recipient (a plain contract, so it adds no top-frame
    charge) is dispatched with only enough execution budget for a single
    opcode. The recipient runs that opcode and then runs out of gas on
    the next, so the frame halts during execution and consumes the full
    ``gas_limit``.

    The execution snapshot is taken after preparation, so the applied
    delegations survive the halt -- matching the EIP-7702 "dispatch
    reverts, delegation remains" rule -- while the recipient is
    unchanged.

    With ``value`` set, the transfer to the recipient happens inside
    the execution snapshot, so the halt that keeps the delegations in
    place reverses the transfer: the recipient stays at balance zero
    and the sender pays only the gas.

    The block access list mirrors this split: both authorities carry
    their persisted nonce bump and delegation-code write, while the
    recipient -- accessed for dispatch but whose (reverted) value
    transfer leaves no net change -- appears with no recorded changes.
    """
    sender = pre.fund_eoa()

    auth_a = build_authorization(pre, AuthorizationAction.CREATES_ACCOUNT)
    auth_b = build_authorization(pre, AuthorizationAction.SETS_NEW_DELEGATION)
    authorization_list = [auth_a.authorization, auth_b.authorization]
    auth_charges = _auth_top_frame_charges(fork, authorization_list)

    intrinsic_execution = _intrinsic_execution(
        fork,
        authorization_list,
        recipient_type=RecipientType.CONTRACT,
        sends_value=bool(value),
    )

    # Two VERYLOW pushes: the budget covers one, so the frame enters
    # execution and then runs out on the second, consuming all gas.
    recipient_code = Op.PUSH1(0) + Op.PUSH1(0)
    one_opcode = Op.PUSH1(0).gas_cost(fork)
    gas_limit = intrinsic_execution + auth_charges + one_opcode

    recipient = pre.deploy_contract(code=recipient_code)

    tx = Transaction(
        sender=sender,
        to=recipient,
        value=value,
        authorization_list=authorization_list,
        gas_limit=gas_limit,
        expected_receipt=TransactionReceipt(
            cumulative_gas_used=gas_limit,
        ),
    )

    post = {
        auth_a.authority: auth_a.applied_account,
        auth_b.authority: auth_b.applied_account,
        recipient: Account(code=recipient_code, balance=0),
    }

    expected_block_access_list = BlockAccessListExpectation(
        account_expectations={
            auth_a.authority: _applied_delegation_bal(auth_a),
            auth_b.authority: _applied_delegation_bal(auth_b),
            recipient: BalAccountExpectation.empty(),
        }
    )

    state_test(
        pre=pre,
        tx=tx,
        post=post,
        expected_block_access_list=expected_block_access_list,
    )


@EIPChecklist.GasCostChanges.Test.GasUpdatesMeasurement()
@pytest.mark.parametrize(
    "auth_action",
    [
        AuthorizationAction.CREATES_ACCOUNT,
        AuthorizationAction.SETS_NEW_DELEGATION,
    ],
    ids=lambda a: a.name.lower(),
)
def test_auth_state_charges_survive_dispatch_revert(
    fork: Fork,
    pre: Alloc,
    state_test: StateTestFiller,
    auth_action: AuthorizationAction,
) -> None:
    """
    The state gas charged for an applied authorization stays consumed
    when the dispatched call reverts, because the delegation persists.

    A single authorization is applied in full, then the recipient (a
    plain contract) reverts immediately. Per EIP-7702 the applied
    delegation survives the revert, so the state it created -- the
    authority's account leaf (``NEW_ACCOUNT``) and delegation indicator
    (``AUTH_BASE``) -- remains, and the state gas that paid for it must
    remain consumed. Only the dispatched frame's unused budget is
    returned.

    A regression that refills the authorization's state gas with the
    frame's rollback would refund the sender 218,790
    (``NEW_ACCOUNT + AUTH_BASE``) or 35,190 (``AUTH_BASE``) gas for
    state that persists; the receipt's exact gas used pins this.

    The same persistence must show in the block access list: the
    authority carries its nonce bump and delegation-code write even
    though the dispatched frame reverted, while the recipient appears
    with no recorded changes.
    """
    sender = pre.fund_eoa()

    revert_code = Op.REVERT(0, 0)
    recipient = pre.deploy_contract(code=revert_code)

    auth = build_authorization(pre, auth_action)
    authorization_list = [auth.authorization]

    intrinsic_execution = _intrinsic_execution(
        fork, authorization_list, recipient_type=RecipientType.CONTRACT
    )
    auth_charges = _auth_top_frame_charges(fork, authorization_list)
    revert_exec_gas = revert_code.gas_cost(fork)

    # The authorization's execution and state charges and the two PUSH
    # opcodes feeding the REVERT stay paid; only the unused execution
    # budget returns.
    gas_used = intrinsic_execution + auth_charges + revert_exec_gas

    tx = Transaction(
        sender=sender,
        to=recipient,
        value=0,
        authorization_list=authorization_list,
        expected_receipt=TransactionReceipt(
            cumulative_gas_used=gas_used,
        ),
    )

    post = {
        auth.authority: auth.applied_account,
        recipient: Account(code=revert_code, balance=0),
    }

    expected_block_access_list = BlockAccessListExpectation(
        account_expectations={
            auth.authority: _applied_delegation_bal(auth),
            recipient: BalAccountExpectation.empty(),
        }
    )

    state_test(
        pre=pre,
        tx=tx,
        post=post,
        expected_block_access_list=expected_block_access_list,
    )


@EIPChecklist.GasCostChanges.Test.GasUpdatesMeasurement()
def test_auth_state_charges_survive_dispatch_halt_with_reservoir(
    fork: Fork,
    pre: Alloc,
    state_test: StateTestFiller,
) -> None:
    """
    The state gas charged for an applied authorization stays consumed
    when the dispatched call exceptionally halts, observed through the
    state-gas reservoir.

    With an ordinary gas limit the reservoir is zero and a halt
    consumes all of ``gas_left`` anyway, masking any wrongly-refilled
    state gas. Here the gas limit exceeds the EIP-7825 cap (allowed --
    the cap binds only the execution dimension), so the excess forms a
    state-gas reservoir that covers the authorization's ``NEW_ACCOUNT``
    + ``AUTH_BASE``. The dispatched call hits ``INVALID``, consuming
    all execution gas; the *unused* reservoir returns to the sender, but
    the portion consumed for the persisting delegation must not.

    A regression that refills the authorization's state gas with the
    frame's rollback would return the full reservoir, refunding the
    sender 218,790 gas for state that persists.
    """
    cap = fork.transaction_gas_limit_cap()
    assert cap is not None, "EIP-7825 cap expected on this fork"

    sender = pre.fund_eoa()

    halt_code = Op.INVALID
    recipient = pre.deploy_contract(code=halt_code)

    auth = build_authorization(pre, AuthorizationAction.CREATES_ACCOUNT)
    authorization_list = [auth.authorization]

    auth_state_gas = fork.transaction_top_frame_state_gas(
        recipient_type=RecipientType.CONTRACT,
        authorizations=authorization_list,
    )
    assert auth_state_gas > 0, (
        "the authorization must carry a state-gas charge"
    )

    # The reservoir covers the authorization's state charges with
    # headroom, so they draw from the reservoir rather than spilling
    # into gas_left.
    reservoir = auth_state_gas + 50_000

    # The halt consumes the full execution budget (the cap); of the
    # reservoir, only the authorization's state gas is consumed -- its
    # delegation persists -- and the unused remainder returns.
    gas_used = cap + auth_state_gas

    tx = Transaction(
        sender=sender,
        to=recipient,
        value=0,
        authorization_list=authorization_list,
        state_gas_reservoir=reservoir,
        expected_receipt=TransactionReceipt(
            cumulative_gas_used=gas_used,
        ),
    )

    post = {
        auth.authority: auth.applied_account,
        recipient: Account(code=halt_code, balance=0),
    }

    state_test(pre=pre, tx=tx, post=post)


@EIPChecklist.GasCostChanges.Test.GasUpdatesMeasurement()
def test_auth_state_gas_in_header_on_dispatch_revert(
    fork: Fork,
    pre: Alloc,
    blockchain_test: BlockchainTestFiller,
) -> None:
    """
    The state gas of an applied authorization is counted in the block's
    state dimension when the dispatched call reverts.

    The header ``gas_used`` is ``max(block_execution_gas,
    block_state_gas)``. The authorization creates and delegates a fresh
    authority (218,790 state gas), which dominates the small execution
    side (intrinsic + ``ACCOUNT_WRITE`` + the pre-revert execution), so
    a correct accounting yields ``gas_used == 218,790`` even though the
    dispatched call reverts -- the delegation, and the state it grew,
    persist.

    A regression that refills the authorization's state gas on the
    frame's rollback collapses ``tx_state_gas`` to zero and the header
    to the small execution sum, which balance-only state tests cannot
    distinguish from a correctly-split total.
    """
    sender = pre.fund_eoa()

    revert_code = Op.REVERT(0, 0)
    recipient = pre.deploy_contract(code=revert_code)

    auth = build_authorization(pre, AuthorizationAction.CREATES_ACCOUNT)
    authorization_list = [auth.authorization]

    intrinsic_execution = _intrinsic_execution(
        fork, authorization_list, recipient_type=RecipientType.CONTRACT
    )
    auth_execution = fork.transaction_top_frame_gas_calculator()(
        recipient_type=RecipientType.CONTRACT,
        authorizations=authorization_list,
    )
    auth_state = fork.transaction_top_frame_state_gas(
        recipient_type=RecipientType.CONTRACT,
        authorizations=authorization_list,
    )
    revert_exec_gas = revert_code.gas_cost(fork)

    execution_total = intrinsic_execution + auth_execution + revert_exec_gas
    assert auth_state > execution_total, (
        "the state dimension must dominate for the header to pin it"
    )
    expected_gas_used = max(execution_total, auth_state)

    tx = Transaction(
        sender=sender,
        to=recipient,
        value=0,
        authorization_list=authorization_list,
    )

    blockchain_test(
        pre=pre,
        blocks=[
            Block(
                txs=[tx],
                header_verify=Header(gas_used=expected_gas_used),
            ),
        ],
        post={
            sender: Account(nonce=1),
            auth.authority: auth.applied_account,
            recipient: Account(code=revert_code, balance=0),
        },
    )


@EIPChecklist.GasCostChanges.Test.GasUpdatesMeasurement()
@pytest.mark.inclusion_test
@pytest.mark.parametrize(
    "delta",
    [
        pytest.param(0, id="exact_fit"),
        pytest.param(1, id="exceeded", marks=pytest.mark.exception_test),
    ],
)
def test_reverted_dispatch_state_gas_counts_toward_block_limit(
    fork: Fork,
    pre: Alloc,
    blockchain_test: BlockchainTestFiller,
    delta: int,
) -> None:
    """
    The state gas persisted by a reverted transaction's authorization
    counts against the block's state dimension when including later
    transactions.

    The first transaction applies an account-creating authorization and
    its dispatched call reverts: the delegation, and the state gas that
    paid for it, persist. The last transaction is then sized to the
    remaining state capacity exactly (``exact_fit``: the inclusion
    check is strictly greater-than, so the block is valid) or one gas
    beyond it (``exceeded``: the per-transaction state check fires and
    the block is correctly rejected).

    The execution dimension is asserted to have room either way, pinning
    the rejection to the state dimension. An implementation that drops
    a reverted transaction's persisting state gas from the block's
    state total would accept the ``exceeded`` block and fork.
    """
    cap = fork.transaction_gas_limit_cap()
    assert cap is not None, "EIP-7825 cap expected on this fork"

    block_gas_limit = 100_000_000

    revert_code = Op.REVERT(0, 0)
    recipient = pre.deploy_contract(code=revert_code)

    auth = build_authorization(pre, AuthorizationAction.CREATES_ACCOUNT)
    authorization_list = [auth.authorization]

    intrinsic_execution = _intrinsic_execution(
        fork, authorization_list, recipient_type=RecipientType.CONTRACT
    )
    auth_execution = fork.transaction_top_frame_gas_calculator()(
        recipient_type=RecipientType.CONTRACT,
        authorizations=authorization_list,
    )
    auth_state = fork.transaction_top_frame_state_gas(
        recipient_type=RecipientType.CONTRACT,
        authorizations=authorization_list,
    )
    revert_exec_gas = revert_code.gas_cost(fork)

    first_tx_execution = intrinsic_execution + auth_execution + revert_exec_gas
    first_tx = Transaction(
        sender=pre.fund_eoa(),
        to=recipient,
        value=0,
        authorization_list=authorization_list,
        gas_limit=first_tx_execution + auth_state,
    )

    # The last transaction's worst-case state contribution is its full
    # ``tx.gas`` (the strict EIP-8037 inclusion rule), charged against
    # a state dimension that already carries the reverted first
    # transaction's persisting authorization state gas.
    state_available = block_gas_limit - auth_state
    last_tx_gas = state_available + delta

    # Pin the rejection (when delta > 0) to the state check: the
    # execution check must not fire.
    execution_available = block_gas_limit - first_tx_execution
    assert min(cap, last_tx_gas) < execution_available, (
        "the last tx would fail the execution check instead of the state check"
    )

    last_tx_error = (
        TransactionException.GAS_ALLOWANCE_EXCEEDED if delta > 0 else None
    )
    last_tx = Transaction(
        sender=pre.fund_eoa(),
        to=pre.deploy_contract(code=Op.STOP),
        value=0,
        gas_limit=last_tx_gas,
        error=last_tx_error,
    )

    # On rejection nothing in the block applies; on the exact fit the
    # reverted first transaction still leaves its delegation behind.
    post = {} if delta > 0 else {auth.authority: auth.applied_account}

    blockchain_test(
        genesis_environment=Environment(gas_limit=block_gas_limit),
        pre=pre,
        blocks=[
            Block(
                txs=[first_tx, last_tx],
                gas_limit=block_gas_limit,
                exception=last_tx_error,
            )
        ],
        post=post,
    )


@EIPChecklist.GasCostChanges.Test.GasUpdatesMeasurement()
def test_recipient_new_account_refilled_on_dispatch_halt_with_reservoir(
    fork: Fork,
    pre: Alloc,
    state_test: StateTestFiller,
) -> None:
    """
    The recipient ``NEW_ACCOUNT`` charge is refilled when the dispatch
    fails, because the recipient's account creation rolls back with it
    -- unlike an authorization's state gas, whose delegation persists.

    Value moves to an *empty precompile* (a recipient that is empty
    yet still executes): the top frame charges ``NEW_ACCOUNT``,
    dispatch moves the value -- materializing the leaf -- and the
    precompile then halts (the bn254 pairing rejects a 1-byte input),
    rolling the leaf back. The state did not grow, so the charge
    refills.

    The gas limit exceeds the EIP-7825 cap so the charge draws from a
    state-gas reservoir; the halt consumes the full execution budget (the
    cap) but the *entire* reservoir returns, pinning the refill in the
    receipt's gas used. This is the counterpart of
    ``test_auth_state_charges_survive_dispatch_halt_with_reservoir``,
    which pins that an authorization's state gas does NOT return.
    """
    cap = fork.transaction_gas_limit_cap()
    assert cap is not None, "EIP-7825 cap expected on this fork"

    sender = pre.fund_eoa()
    pairing_precompile = Address(0x08)

    value = 1
    new_account_state_gas = fork.transaction_top_frame_state_gas(
        sends_value=True,
        recipient_type=RecipientType.EMPTY_ACCOUNT,
    )
    assert new_account_state_gas > 0, (
        "an empty recipient receiving value must charge NEW_ACCOUNT"
    )

    reservoir = new_account_state_gas + 50_000

    # The halt consumes the full execution budget; the NEW_ACCOUNT drawn
    # from the reservoir is refilled (the account creation rolled
    # back), so the whole reservoir returns to the sender.
    gas_used = cap

    tx = Transaction(
        sender=sender,
        to=pairing_precompile,
        value=value,
        # One byte: not a multiple of 192, so the pairing precompile
        # exceptionally halts after the value has moved.
        data=b"\x00",
        state_gas_reservoir=reservoir,
        expected_receipt=TransactionReceipt(
            cumulative_gas_used=gas_used,
        ),
    )

    post = {
        pairing_precompile: None,
    }

    state_test(pre=pre, tx=tx, post=post)


@EIPChecklist.GasCostChanges.Test.GasUpdatesMeasurement()
def test_dispatched_frame_state_gas_still_refills_on_revert(
    fork: Fork,
    pre: Alloc,
    state_test: StateTestFiller,
) -> None:
    """
    State gas charged *inside* the dispatched call is still refilled
    when that call reverts, in the same transaction whose authorization
    state gas must stay consumed.

    The authorization sets a delegation on an existing EOA
    (``AUTH_BASE``, persists across the revert). The recipient then
    ``SSTORE``s a fresh slot -- charging ``STORAGE_SET`` state gas --
    and reverts, rolling the slot back, so that state gas is refilled.

    This brackets the rollback boundary from both sides: refilling the
    ``AUTH_BASE`` along with the frame's rollback would underpay by
    35,190, while an over-correction that stops refilling frame state
    gas altogether would overcharge by the 97,920 ``STORAGE_SET``.
    """
    sender = pre.fund_eoa()

    sstore_revert_code = Op.SSTORE(
        0, 1, original_value=0, new_value=1
    ) + Op.REVERT(0, 0)
    recipient = pre.deploy_contract(code=sstore_revert_code)

    auth = build_authorization(pre, AuthorizationAction.SETS_NEW_DELEGATION)
    authorization_list = [auth.authorization]

    intrinsic_execution = _intrinsic_execution(
        fork, authorization_list, recipient_type=RecipientType.CONTRACT
    )
    auth_charges = _auth_top_frame_charges(fork, authorization_list)
    evm_execution = sstore_revert_code.execution_cost(fork)
    exec_state = sstore_revert_code.state_cost(fork)
    assert exec_state > 0, (
        "the dispatched SSTORE must carry a state-gas charge"
    )

    # The SSTORE's state gas is charged and then refilled by the
    # revert (the slot rolls back), so the sender pays only the
    # authorization charges and the execution gas.
    gas_used = intrinsic_execution + auth_charges + evm_execution

    tx = Transaction(
        sender=sender,
        to=recipient,
        value=0,
        authorization_list=authorization_list,
        expected_receipt=TransactionReceipt(
            cumulative_gas_used=gas_used,
        ),
    )

    post = {
        auth.authority: auth.applied_account,
        recipient: Account(code=sstore_revert_code, balance=0, storage={0: 0}),
    }

    state_test(pre=pre, tx=tx, post=post)
