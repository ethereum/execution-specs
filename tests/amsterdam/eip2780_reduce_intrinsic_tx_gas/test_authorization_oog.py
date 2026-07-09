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
  transaction is still included and consumes its full ``gas_limit``;
  the sender nonce (bumped at inclusion, before the snapshot) is not
  rolled back.
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
    Account,
    Address,
    Alloc,
    BalAccountExpectation,
    BalCodeChange,
    BalNonceChange,
    Block,
    BlockAccessListExpectation,
    BlockchainTestFiller,
    Fork,
    Header,
    Op,
    RecipientType,
    StateTestFiller,
    Transaction,
)

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

GAS_PRICE = 1_000_000_000


def _auth_top_frame_charges(fork: Fork, authorizations: list) -> int:
    """
    Return the top-frame regular + state gas attributable to the
    authorizations alone.

    Computed against a ``CONTRACT`` recipient, which contributes no
    top-frame charge, so the result is exactly the sum of each
    authorization's own ``ACCOUNT_WRITE`` / ``NEW_ACCOUNT`` /
    ``AUTH_BASE``. Under the zero state reservoir these all draw from
    ``gas_left``.
    """
    regular = fork.transaction_top_frame_gas_calculator()(
        recipient_type=RecipientType.CONTRACT,
        authorizations=authorizations,
    )
    state = fork.transaction_top_frame_state_gas(
        recipient_type=RecipientType.CONTRACT,
        authorizations=authorizations,
    )
    return regular + state


def _intrinsic_regular(
    fork: Fork,
    authorization_list: list,
    *,
    recipient_type: RecipientType,
    sends_value: bool = False,
) -> int:
    """Return the regular intrinsic gas deducted before execution."""
    return fork.transaction_intrinsic_cost_calculator()(
        recipient_type=recipient_type,
        sends_value=sends_value,
        authorization_list_or_count=authorization_list,
        return_cost_deducted_prior_execution=True,
    )


def _persisted_delegation_bal(
    scenario: AuthorizationScenario,
) -> BalAccountExpectation:
    """
    BAL entry for an authority whose applied delegation persists past a
    dispatch-phase failure.

    The nonce bump and delegation-code write are applied before the
    execution snapshot, so they survive the dispatched frame's revert or
    halt and must be recorded in the block access list.
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


@pytest.mark.parametrize(
    "oog_charge", ["new_account", "account_write", "auth_base"]
)
def test_set_delegation_oog_charge_point(
    fork: Fork,
    pre: Alloc,
    state_test: StateTestFiller,
    oog_charge: str,
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
      at the following ``ACCOUNT_WRITE`` regular charge.
    - ``auth_base``: the second (a delegation on an existing empty EOA)
      covers its first-write ``ACCOUNT_WRITE`` but runs out at the
      following ``AUTH_BASE`` state charge.

    In every case the transaction halts in ``set_delegation`` and both
    authorizations are rolled back -- the first, already applied, as
    well as the second -- so both authorities return to their pre-tx
    state. The sender pays the full ``gas_limit`` and its nonce is not
    rolled back.

    Both authorities are read during authorization validation before
    the halt, so per EIP-7928 they still appear in the block access
    list with no recorded changes. The recipient is only loaded by the
    top-frame dispatch, which the halt precedes, so it must be absent.
    """
    gas_costs = fork.gas_costs()
    sender_initial_balance = 10**18
    sender = pre.fund_eoa(sender_initial_balance)
    recipient = pre.deploy_contract(code=Op.STOP)

    first = build_authorization(pre, AuthorizationAction.CREATES_ACCOUNT)
    if oog_charge == "auth_base":
        second = build_authorization(
            pre, AuthorizationAction.SETS_NEW_DELEGATION
        )
    else:
        second = build_authorization(pre, AuthorizationAction.CREATES_ACCOUNT)

    authorization_list = [first.authorization, second.authorization]

    intrinsic_regular = _intrinsic_regular(
        fork, authorization_list, recipient_type=RecipientType.CONTRACT
    )
    first_auth_charges = _auth_top_frame_charges(fork, [first.authorization])

    # gas_left entering set_delegation is gas_limit - intrinsic_regular
    # (the state reservoir is zero). The first authorization is applied
    # in full; the second is starved by one gas at the target charge,
    # after covering any charges that precede it within that same
    # authorization.
    if oog_charge == "new_account":
        preceding = 0
        shortfall_charge = gas_costs.NEW_ACCOUNT
    elif oog_charge == "account_write":
        preceding = gas_costs.NEW_ACCOUNT
        shortfall_charge = gas_costs.ACCOUNT_WRITE
    else:  # auth_base
        preceding = gas_costs.ACCOUNT_WRITE
        shortfall_charge = gas_costs.AUTH_BASE

    gas_limit = (
        intrinsic_regular
        + first_auth_charges
        + preceding
        + shortfall_charge
        - 1
    )

    tx = Transaction(
        sender=sender,
        to=recipient,
        value=0,
        authorization_list=authorization_list,
        gas_limit=gas_limit,
        max_fee_per_gas=GAS_PRICE,
        max_priority_fee_per_gas=GAS_PRICE,
    )

    post = {
        sender: Account(
            nonce=1,
            balance=sender_initial_balance - gas_limit * GAS_PRICE,
        ),
        first.authority: first.original_account,
        second.authority: second.original_account,
    }

    # An implementation recording accesses only for dispatched frames
    # would drop the authority entries; one recording the recipient at
    # inclusion would add it. Either forks on the BAL hash.
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
    sender_initial_balance = 10**18
    sender = pre.fund_eoa(sender_initial_balance)
    recipient = pre.deploy_contract(code=Op.STOP)

    first = build_authorization(pre, first_action)
    second = build_authorization(pre, AuthorizationAction.CREATES_ACCOUNT)
    authorization_list = [first.authorization, second.authorization]

    intrinsic_regular = _intrinsic_regular(
        fork, authorization_list, recipient_type=RecipientType.CONTRACT
    )
    first_auth_charges = _auth_top_frame_charges(fork, [first.authorization])

    # The first authorization applies in full; the second (a creation)
    # runs out at its opening NEW_ACCOUNT state charge, rolling back the
    # whole authorization phase.
    gas_limit = (
        intrinsic_regular + first_auth_charges + gas_costs.NEW_ACCOUNT - 1
    )

    tx = Transaction(
        sender=sender,
        to=recipient,
        value=0,
        authorization_list=authorization_list,
        gas_limit=gas_limit,
        max_fee_per_gas=GAS_PRICE,
        max_priority_fee_per_gas=GAS_PRICE,
    )

    post = {
        sender: Account(
            nonce=1,
            balance=sender_initial_balance - gas_limit * GAS_PRICE,
        ),
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


@pytest.mark.parametrize(
    "recipient_charge", ["new_account", "delegation_access"]
)
def test_recipient_charge_oog_rolls_back_delegations(
    fork: Fork,
    pre: Alloc,
    state_test: StateTestFiller,
    recipient_charge: str,
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
    sender pays the full ``gas_limit``, and the recipient itself is
    unchanged.

    The recipient and both authorities were accessed before the halt,
    so per EIP-7928 all three must still appear in the block access
    list, with no recorded changes.
    """
    gas_costs = fork.gas_costs()
    sender_initial_balance = 10**18
    sender = pre.fund_eoa(sender_initial_balance)

    auth_a = build_authorization(pre, AuthorizationAction.CREATES_ACCOUNT)
    auth_b = build_authorization(pre, AuthorizationAction.SETS_NEW_DELEGATION)
    authorization_list = [auth_a.authorization, auth_b.authorization]
    auth_charges = _auth_top_frame_charges(fork, authorization_list)

    if recipient_charge == "new_account":
        recipient = pre.fund_eoa(amount=0)
        value = 1
        recipient_type = RecipientType.EMPTY_ACCOUNT
        shortfall_charge = gas_costs.NEW_ACCOUNT
        expected_recipient: Account | None = None
    else:  # delegation_access
        delegated_to = pre.deploy_contract(code=Op.STOP)
        recipient = pre.fund_eoa(
            amount=EOA_INITIAL_BALANCE, delegation=delegated_to
        )
        value = 0
        recipient_type = RecipientType.DELEGATION_7702
        shortfall_charge = gas_costs.COLD_ACCOUNT_ACCESS
        expected_recipient = Account(
            nonce=1,
            balance=EOA_INITIAL_BALANCE,
            code=Spec7702.delegation_designation(delegated_to),
        )

    intrinsic_regular = _intrinsic_regular(
        fork,
        authorization_list,
        recipient_type=recipient_type,
        sends_value=bool(value),
    )

    # Both authorizations apply, then the recipient's top-frame charge is
    # starved by one gas. That charge shares the preparation snapshot, so
    # its out-of-gas rolls the applied delegations back.
    gas_limit = intrinsic_regular + auth_charges + shortfall_charge - 1

    tx = Transaction(
        sender=sender,
        to=recipient,
        value=value,
        authorization_list=authorization_list,
        gas_limit=gas_limit,
        max_fee_per_gas=GAS_PRICE,
        max_priority_fee_per_gas=GAS_PRICE,
    )

    post = {
        sender: Account(
            nonce=1,
            balance=sender_initial_balance - gas_limit * GAS_PRICE,
        ),
        auth_a.authority: auth_a.original_account,
        auth_b.authority: auth_b.original_account,
        recipient: expected_recipient,
    }

    expected_block_access_list = BlockAccessListExpectation(
        account_expectations={
            recipient: BalAccountExpectation.empty(),
            auth_a.authority: BalAccountExpectation.empty(),
            auth_b.authority: BalAccountExpectation.empty(),
        }
    )

    state_test(
        pre=pre,
        tx=tx,
        post=post,
        expected_block_access_list=expected_block_access_list,
    )


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
    sender_initial_balance = 10**18
    sender = pre.fund_eoa(sender_initial_balance)

    auth_a = build_authorization(pre, AuthorizationAction.CREATES_ACCOUNT)
    auth_b = build_authorization(pre, AuthorizationAction.SETS_NEW_DELEGATION)
    authorization_list = [auth_a.authorization, auth_b.authorization]
    auth_charges = _auth_top_frame_charges(fork, authorization_list)

    intrinsic_regular = _intrinsic_regular(
        fork,
        authorization_list,
        recipient_type=RecipientType.CONTRACT,
        sends_value=bool(value),
    )

    # Two VERYLOW pushes: the budget covers one, so the frame enters
    # execution and then runs out on the second, consuming all gas.
    recipient_code = Op.PUSH1(0) + Op.PUSH1(0)
    one_opcode = Op.PUSH1(0).gas_cost(fork)
    gas_limit = intrinsic_regular + auth_charges + one_opcode
    sender_final_balance = sender_initial_balance - gas_limit * GAS_PRICE

    recipient = pre.deploy_contract(code=recipient_code)

    tx = Transaction(
        sender=sender,
        to=recipient,
        value=value,
        authorization_list=authorization_list,
        gas_limit=gas_limit,
        max_fee_per_gas=GAS_PRICE,
        max_priority_fee_per_gas=GAS_PRICE,
    )

    post = {
        sender: Account(nonce=1, balance=sender_final_balance),
        auth_a.authority: auth_a.applied_account,
        auth_b.authority: auth_b.applied_account,
        recipient: Account(code=recipient_code, balance=0),
    }

    expected_block_access_list = BlockAccessListExpectation(
        account_expectations={
            auth_a.authority: _persisted_delegation_bal(auth_a),
            auth_b.authority: _persisted_delegation_bal(auth_b),
            recipient: BalAccountExpectation.empty(),
        }
    )

    state_test(
        pre=pre,
        tx=tx,
        post=post,
        expected_block_access_list=expected_block_access_list,
    )


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
    state that persists; the exact sender balance pins this.

    The same persistence must show in the block access list: the
    authority carries its nonce bump and delegation-code write even
    though the dispatched frame reverted, while the recipient appears
    with no recorded changes.
    """
    sender_initial_balance = 10**18
    sender = pre.fund_eoa(sender_initial_balance)

    revert_code = Op.REVERT(0, 0)
    recipient = pre.deploy_contract(code=revert_code)

    auth = build_authorization(pre, auth_action)
    authorization_list = [auth.authorization]

    intrinsic_regular = _intrinsic_regular(
        fork, authorization_list, recipient_type=RecipientType.CONTRACT
    )
    auth_charges = _auth_top_frame_charges(fork, authorization_list)
    revert_exec_gas = revert_code.gas_cost(fork)

    # The authorization's regular and state charges and the two PUSH
    # opcodes feeding the REVERT stay paid; only the unused execution
    # budget returns.
    gas_used = intrinsic_regular + auth_charges + revert_exec_gas
    gas_limit = gas_used + 10_000

    tx = Transaction(
        sender=sender,
        to=recipient,
        value=0,
        authorization_list=authorization_list,
        gas_limit=gas_limit,
        max_fee_per_gas=GAS_PRICE,
        max_priority_fee_per_gas=GAS_PRICE,
    )

    post = {
        sender: Account(
            nonce=1,
            balance=sender_initial_balance - gas_used * GAS_PRICE,
        ),
        auth.authority: auth.applied_account,
        recipient: Account(code=revert_code, balance=0),
    }

    expected_block_access_list = BlockAccessListExpectation(
        account_expectations={
            auth.authority: _persisted_delegation_bal(auth),
            recipient: BalAccountExpectation.empty(),
        }
    )

    state_test(
        pre=pre,
        tx=tx,
        post=post,
        expected_block_access_list=expected_block_access_list,
    )


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
    the cap binds only the regular dimension), so the excess forms a
    state-gas reservoir that covers the authorization's ``NEW_ACCOUNT``
    + ``AUTH_BASE``. The dispatched call hits ``INVALID``, consuming
    all regular gas; the *unused* reservoir returns to the sender, but
    the portion consumed for the persisting delegation must not.

    A regression that refills the authorization's state gas with the
    frame's rollback would return the full reservoir, refunding the
    sender 218,790 gas for state that persists.
    """
    cap = fork.transaction_gas_limit_cap()
    assert cap is not None, "EIP-7825 cap expected on this fork"

    sender_initial_balance = 10**18
    sender = pre.fund_eoa(sender_initial_balance)

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
    gas_limit = cap + reservoir

    # The halt consumes the full regular budget (the cap); of the
    # reservoir, only the authorization's state gas is consumed -- its
    # delegation persists -- and the unused remainder returns.
    gas_used = cap + auth_state_gas

    tx = Transaction(
        sender=sender,
        to=recipient,
        value=0,
        authorization_list=authorization_list,
        gas_limit=gas_limit,
        max_fee_per_gas=GAS_PRICE,
        max_priority_fee_per_gas=GAS_PRICE,
    )

    post = {
        sender: Account(
            nonce=1,
            balance=sender_initial_balance - gas_used * GAS_PRICE,
        ),
        auth.authority: auth.applied_account,
        recipient: Account(code=halt_code, balance=0),
    }

    state_test(pre=pre, tx=tx, post=post)


def test_auth_state_gas_in_header_on_dispatch_revert(
    fork: Fork,
    pre: Alloc,
    blockchain_test: BlockchainTestFiller,
) -> None:
    """
    The state gas of an applied authorization is counted in the block's
    state dimension when the dispatched call reverts.

    The header ``gas_used`` is ``max(block_regular_gas,
    block_state_gas)``. The authorization creates and delegates a fresh
    authority (218,790 state gas), which dominates the small regular
    side (intrinsic + ``ACCOUNT_WRITE`` + the pre-revert execution), so
    a correct accounting yields ``gas_used == 218,790`` even though the
    dispatched call reverts -- the delegation, and the state it grew,
    persist.

    A regression that refills the authorization's state gas on the
    frame's rollback collapses ``tx_state_gas`` to zero and the header
    to the small regular sum, which balance-only state tests cannot
    distinguish from a correctly-split total.
    """
    sender_initial_balance = 10**18
    sender = pre.fund_eoa(sender_initial_balance)

    revert_code = Op.REVERT(0, 0)
    recipient = pre.deploy_contract(code=revert_code)

    auth = build_authorization(pre, AuthorizationAction.CREATES_ACCOUNT)
    authorization_list = [auth.authorization]

    intrinsic_regular = _intrinsic_regular(
        fork, authorization_list, recipient_type=RecipientType.CONTRACT
    )
    auth_regular = fork.transaction_top_frame_gas_calculator()(
        recipient_type=RecipientType.CONTRACT,
        authorizations=authorization_list,
    )
    auth_state = fork.transaction_top_frame_state_gas(
        recipient_type=RecipientType.CONTRACT,
        authorizations=authorization_list,
    )
    revert_exec_gas = revert_code.gas_cost(fork)

    regular_total = intrinsic_regular + auth_regular + revert_exec_gas
    assert auth_state > regular_total, (
        "the state dimension must dominate for the header to pin it"
    )
    expected_gas_used = max(regular_total, auth_state)

    gas_used = regular_total + auth_state
    gas_limit = gas_used + 10_000

    tx = Transaction(
        sender=sender,
        to=recipient,
        value=0,
        authorization_list=authorization_list,
        gas_limit=gas_limit,
        max_fee_per_gas=GAS_PRICE,
        max_priority_fee_per_gas=GAS_PRICE,
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


def test_recipient_new_account_refilled_on_dispatch_halt_with_reservoir(
    fork: Fork,
    pre: Alloc,
    state_test: StateTestFiller,
) -> None:
    """
    The recipient ``NEW_ACCOUNT`` charge is refilled when the dispatch
    fails, because the recipient's account creation rolls back with it
    -- unlike an authorization's state gas, whose delegation persists.

    Value moves to an *empty precompile* (the one recipient that is
    empty yet still executes): the top frame charges ``NEW_ACCOUNT``,
    dispatch moves the value -- materializing the leaf -- and the
    precompile then halts (the bn254 pairing rejects a 1-byte input),
    rolling the leaf back. The state did not grow, so the charge
    refills.

    The gas limit exceeds the EIP-7825 cap so the charge draws from a
    state-gas reservoir; the halt consumes the full regular budget (the
    cap) but the *entire* reservoir returns, pinning the refill in the
    sender balance. This is the counterpart of
    ``test_auth_state_charges_survive_dispatch_halt_with_reservoir``,
    which pins that an authorization's state gas does NOT return.
    """
    cap = fork.transaction_gas_limit_cap()
    assert cap is not None, "EIP-7825 cap expected on this fork"

    sender_initial_balance = 10**18
    sender = pre.fund_eoa(sender_initial_balance)
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
    gas_limit = cap + reservoir

    # The halt consumes the full regular budget; the NEW_ACCOUNT drawn
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
        gas_limit=gas_limit,
        max_fee_per_gas=GAS_PRICE,
        max_priority_fee_per_gas=GAS_PRICE,
    )

    post = {
        sender: Account(
            nonce=1,
            balance=sender_initial_balance - gas_used * GAS_PRICE,
        ),
        pairing_precompile: None,
    }

    state_test(pre=pre, tx=tx, post=post)


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

    This brackets the rollback boundary from both sides: the current
    over-refill (returning the ``AUTH_BASE`` too) underpays by 35,190,
    while an over-correction that stops refilling frame state gas
    altogether would overcharge by the 97,920 ``STORAGE_SET``.
    """
    sender_initial_balance = 10**18
    sender = pre.fund_eoa(sender_initial_balance)

    sstore_revert_code = Op.SSTORE(
        0, 1, original_value=0, new_value=1
    ) + Op.REVERT(0, 0)
    recipient = pre.deploy_contract(code=sstore_revert_code)

    auth = build_authorization(pre, AuthorizationAction.SETS_NEW_DELEGATION)
    authorization_list = [auth.authorization]

    intrinsic_regular = _intrinsic_regular(
        fork, authorization_list, recipient_type=RecipientType.CONTRACT
    )
    auth_charges = _auth_top_frame_charges(fork, authorization_list)
    exec_regular = sstore_revert_code.regular_cost(fork)
    exec_state = sstore_revert_code.state_cost(fork)
    assert exec_state > 0, (
        "the dispatched SSTORE must carry a state-gas charge"
    )

    # The SSTORE's state gas is charged and then refilled by the
    # revert (the slot rolls back), so the sender pays only the
    # authorization charges and the regular execution gas. The gas
    # limit must still cover the state charge while it is outstanding.
    gas_used = intrinsic_regular + auth_charges + exec_regular
    gas_limit = gas_used + exec_state + 10_000

    tx = Transaction(
        sender=sender,
        to=recipient,
        value=0,
        authorization_list=authorization_list,
        gas_limit=gas_limit,
        max_fee_per_gas=GAS_PRICE,
        max_priority_fee_per_gas=GAS_PRICE,
    )

    post = {
        sender: Account(
            nonce=1,
            balance=sender_initial_balance - gas_used * GAS_PRICE,
        ),
        auth.authority: auth.applied_account,
        recipient: Account(code=sstore_revert_code, balance=0, storage={0: 0}),
    }

    state_test(pre=pre, tx=tx, post=post)
