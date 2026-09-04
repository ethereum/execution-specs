"""
EIP-2780 invariants for transaction-level account charges.

Two distinct charges are exercised here, and they treat warmth
differently:

- The recipient's intrinsic ``COLD_ACCOUNT_ACCESS`` is charged in the
  intrinsic phase, without reading state, so it is *always cold*:
  listing ``tx.to`` in the access list pays the access-list cost but
  does not waive it, and the protocol-warmed coinbase is still charged
  cold when it is the recipient. The same holds for the authority
  access folded into ``EXECUTION_PER_AUTH_BASE_COST``.
- A delegated recipient's delegation-target access is a *top-frame*
  charge that reads state, so it follows normal warm/cold accounting:
  ``WARM_ACCESS`` when the target is already warm -- the sender, the
  coinbase, a precompile, the recipient itself, or an access-list
  entry -- and ``COLD_ACCOUNT_ACCESS`` otherwise. The dispatched EVM
  frame then runs whatever code lives at the target, including the
  degenerate cases of empty code (EOA, precompile address) or a
  delegation prefix that itself decodes as the ``INVALID`` opcode.
"""

import pytest
from execution_testing import (
    AccessList,
    Account,
    Address,
    Alloc,
    AuthorizationTuple,
    BalAccountExpectation,
    BalBalanceChange,
    BlockAccessListExpectation,
    ChainConfig,
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
from .helpers import (
    AuthorizationAction,
    authorization_transaction_cost,
    build_authorization,
)
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
def test_intrinsic_charges_recipient_in_access_list(
    fork: Fork,
    pre: Alloc,
    state_test: StateTestFiller,
    value: int,
) -> None:
    """
    Recipient is listed in the access list. The intrinsic charge still
    includes ``COLD_ACCOUNT_ACCESS`` for the recipient on top of the
    access-list cost itself.
    """
    sender_initial_balance = 10**18
    sender = pre.fund_eoa(sender_initial_balance)

    target_initial_balance = 100
    target = pre.fund_eoa(amount=target_initial_balance)
    access_list = [AccessList(address=target, storage_keys=[])]

    intrinsic_gas = fork.transaction_intrinsic_cost_calculator()(
        access_list=access_list,
        sends_value=bool(value),
        recipient_type=RecipientType.EOA,
        return_cost_deducted_prior_execution=True,
    )

    gas_price = 1_000_000_000
    gas_limit = intrinsic_gas + 1000

    tx = Transaction(
        ty=1,
        sender=sender,
        to=target,
        value=value,
        access_list=access_list,
        gas_limit=gas_limit,
        gas_price=gas_price,
    )

    sender_final_balance = (
        sender_initial_balance - value - intrinsic_gas * gas_price
    )

    post = {
        sender: Account(nonce=1, balance=sender_final_balance),
        target: Account(balance=target_initial_balance + value),
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
def test_intrinsic_charges_recipient_is_coinbase(
    env: Environment,
    fork: Fork,
    pre: Alloc,
    state_test: StateTestFiller,
    value: int,
) -> None:
    """
    Recipient is the block coinbase, which is implicitly warm before
    transaction execution. The intrinsic charge still includes
    ``COLD_ACCOUNT_ACCESS`` for the recipient.
    """
    sender_initial_balance = 10**18
    sender = pre.fund_eoa(sender_initial_balance)
    target = Address(env.fee_recipient)
    # Pre-fund coinbase so it is alive at top-frame check time; this
    # isolates the test to the intrinsic charge invariant and avoids
    # the orthogonal ``NEW_ACCOUNT`` top-frame state charge that would
    # otherwise fire for value transfer to an empty recipient.
    pre.fund_address(target, amount=1)

    intrinsic_gas = fork.transaction_intrinsic_cost_calculator()(
        sends_value=bool(value),
        recipient_type=RecipientType.EOA,
        return_cost_deducted_prior_execution=True,
    )

    gas_price = 1_000_000_000
    gas_limit = intrinsic_gas + 1000

    tx = Transaction(
        sender=sender,
        to=target,
        value=value,
        gas_limit=gas_limit,
        gas_price=gas_price,
    )

    # Coinbase also receives miner fees, so its post-tx balance is not
    # asserted exactly; verifying the sender balance is sufficient to
    # pin the intrinsic charge.
    sender_final_balance = (
        sender_initial_balance - value - intrinsic_gas * gas_price
    )

    post = {
        sender: Account(nonce=1, balance=sender_final_balance),
    }

    state_test(pre=pre, tx=tx, post=post)


@EIPChecklist.GasCostChanges.Test.GasUpdatesMeasurement()
def test_intrinsic_charges_authority_in_access_list(
    fork: Fork,
    pre: Alloc,
    state_test: StateTestFiller,
) -> None:
    """
    Authority is listed in the access list. The intrinsic charge still
    includes the full ``EXECUTION_PER_AUTH_BASE_COST``, whose folded-in
    authority access is charged at the cold rate.
    """
    sender = pre.fund_eoa()
    recipient = pre.deploy_contract(code=Op.STOP)

    scenario = build_authorization(
        pre, AuthorizationAction.SETS_NEW_DELEGATION
    )
    authorization_list = [scenario.authorization]
    access_list = [AccessList(address=scenario.authority, storage_keys=[])]

    total_gas_cost = authorization_transaction_cost(
        fork, authorization_list, access_list=access_list
    )

    tx = Transaction(
        ty=4,
        sender=sender,
        to=recipient,
        value=0,
        access_list=access_list,
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


@EIPChecklist.GasCostChanges.Test.OutOfGas()
@EIPChecklist.GasCostChanges.Test.GasUpdatesMeasurement()
@pytest.mark.parametrize("outcome", ["oog", "success"])
@pytest.mark.parametrize(
    "value",
    [
        pytest.param(0, id="zero_value"),
        pytest.param(1, id="non-zero_value"),
    ],
)
def test_top_frame_charges_delegation_in_access_list(
    fork: Fork,
    pre: Alloc,
    state_test: StateTestFiller,
    value: int,
    outcome: str,
) -> None:
    """
    Recipient holds a pre-existing EIP-7702 delegation; the delegation
    target is listed in the access list, which warms it, so the
    top-frame charges ``WARM_ACCESS`` (100) for the delegation target --
    not ``COLD_ACCOUNT_ACCESS`` (3000) -- on top of the access-list cost
    itself.

    Parametrized over the outcome to also pin the exact warm charge at
    the gas boundary:

    - ``success``: ``gas_limit = intrinsic + WARM_ACCESS`` (exact)
      passes, proving the charge is the 100-gas warm access -- a cold
      charge would need far more headroom and out-of-gas here. The
      delegated ``STOP`` runs and any value transfer lands.
    - ``oog``: ``gas_limit = intrinsic + WARM_ACCESS - 1`` runs out at
      ``charge_gas(WARM_ACCESS)`` before the delegated code runs; the
      sender pays the full ``gas_limit``, no value moves, and the
      recipient keeps its delegation unchanged.
    """
    sender_initial_balance = 10**18
    sender = pre.fund_eoa(sender_initial_balance)

    delegated_to = pre.deploy_contract(code=Op.STOP)
    target_code = Spec7702.delegation_designation(delegated_to)
    target = pre.deploy_contract(code=target_code)
    access_list = [AccessList(address=delegated_to, storage_keys=[])]

    intrinsic_gas = fork.transaction_intrinsic_cost_calculator()(
        access_list=access_list,
        sends_value=bool(value),
        recipient_type=RecipientType.DELEGATION_7702,
        return_cost_deducted_prior_execution=True,
    )
    top_frame_gas = fork.transaction_top_frame_execution_gas(
        sends_value=bool(value),
        recipient_type=RecipientType.DELEGATION_7702,
        delegation_warm=True,
    )

    total_gas_cost = intrinsic_gas + top_frame_gas
    gas_price = 1_000_000_000

    delegated_to_bal: BalAccountExpectation | None
    if outcome == "oog":
        # Runs out one gas short of the warm charge, before dispatch:
        # no value moves and the sender pays the full gas_limit.
        gas_limit = total_gas_cost - 1
        sender_final_balance = sender_initial_balance - gas_limit * gas_price
        target_balance = 0
        # The access-list entry warmed the delegation target but never
        # read it, and the starved charge is the one access that would
        # have: the target must be absent from the block access list.
        delegated_to_bal = None
        target_bal = BalAccountExpectation.empty()
    else:
        # Exact gas: the delegated STOP costs nothing, so the warm
        # charge is the last gas spent and the value transfer lands.
        gas_limit = total_gas_cost
        sender_final_balance = (
            sender_initial_balance - value - total_gas_cost * gas_price
        )
        target_balance = value
        # The paid warm access loads the target's code for dispatch, so
        # it enters the block access list, unchanged.
        delegated_to_bal = BalAccountExpectation.empty()
        target_bal = (
            BalAccountExpectation(
                balance_changes=[
                    BalBalanceChange(block_access_index=1, post_balance=value)
                ]
            )
            if value
            else BalAccountExpectation.empty()
        )

    tx = Transaction(
        ty=1,
        sender=sender,
        to=target,
        value=value,
        access_list=access_list,
        gas_limit=gas_limit,
        gas_price=gas_price,
    )

    post = {
        sender: Account(nonce=1, balance=sender_final_balance),
        target: Account(balance=target_balance, code=target_code),
    }

    state_test(
        pre=pre,
        tx=tx,
        post=post,
        expected_block_access_list=BlockAccessListExpectation(
            account_expectations={
                target: target_bal,
                delegated_to: delegated_to_bal,
            }
        ),
    )


@EIPChecklist.GasCostChanges.Test.GasUpdatesMeasurement()
@pytest.mark.parametrize(
    "value",
    [
        pytest.param(0, id="zero_value"),
        pytest.param(1, id="non-zero_value"),
    ],
)
def test_top_frame_charges_delegation_is_coinbase(
    env: Environment,
    fork: Fork,
    pre: Alloc,
    state_test: StateTestFiller,
    value: int,
) -> None:
    """
    Recipient holds a pre-existing EIP-7702 delegation whose target is
    the block coinbase. Coinbase is implicitly warm before execution,
    so the top-frame charges ``WARM_ACCESS`` for the delegation target.
    """
    sender_initial_balance = 10**18
    sender = pre.fund_eoa(sender_initial_balance)

    delegated_to = Address(env.fee_recipient)
    target_code = Spec7702.delegation_designation(delegated_to)
    target = pre.deploy_contract(code=target_code)

    intrinsic_gas = fork.transaction_intrinsic_cost_calculator()(
        sends_value=bool(value),
        recipient_type=RecipientType.DELEGATION_7702,
        return_cost_deducted_prior_execution=True,
    )
    top_frame_gas = fork.transaction_top_frame_execution_gas(
        sends_value=bool(value),
        recipient_type=RecipientType.DELEGATION_7702,
        delegation_warm=True,
    )

    total_gas_cost = intrinsic_gas + top_frame_gas
    gas_price = 1_000_000_000
    gas_limit = total_gas_cost + 1000

    tx = Transaction(
        sender=sender,
        to=target,
        value=value,
        gas_limit=gas_limit,
        gas_price=gas_price,
    )

    # Coinbase also receives miner fees, so its post-tx balance is not
    # asserted exactly.
    sender_final_balance = (
        sender_initial_balance - value - total_gas_cost * gas_price
    )

    post = {
        sender: Account(nonce=1, balance=sender_final_balance),
        target: Account(balance=value, code=target_code),
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
def test_sender_is_coinbase(
    fork: Fork,
    pre: Alloc,
    state_test: StateTestFiller,
    value: int,
) -> None:
    """
    Sender is the block coinbase. The intrinsic charge is unchanged
    by sender identity, but the priority-fee payment loops back to
    the sender, so the net gas cost reduces to ``gas_used *
    base_fee_per_gas``.

    The coinbase override is wired via a custom ``Environment`` whose
    ``fee_recipient`` matches the sender's address.
    """
    sender_initial_balance = 10**18
    sender = pre.fund_eoa(sender_initial_balance)

    target_initial_balance = 100
    target = pre.fund_eoa(amount=target_initial_balance)

    intrinsic_gas = fork.transaction_intrinsic_cost_calculator()(
        sends_value=bool(value),
        recipient_type=RecipientType.EOA,
        return_cost_deducted_prior_execution=True,
    )

    base_fee = 7
    gas_price = 1_000_000_000
    gas_limit = intrinsic_gas + 1000
    # Sender pays the full gas fee upfront and is credited the
    # priority fee back as the coinbase: net cost is
    # ``gas_used * base_fee``.
    sender_final_balance = (
        sender_initial_balance - value - intrinsic_gas * base_fee
    )

    tx = Transaction(
        sender=sender,
        to=target,
        value=value,
        gas_limit=gas_limit,
        gas_price=gas_price,
    )

    post = {
        sender: Account(nonce=1, balance=sender_final_balance),
        target: Account(balance=target_initial_balance + value),
    }

    state_test(
        pre=pre,
        tx=tx,
        post=post,
        env=Environment(fee_recipient=sender, base_fee_per_gas=base_fee),
    )


@EIPChecklist.GasCostChanges.Test.GasUpdatesMeasurement()
@pytest.mark.parametrize(
    "value",
    [
        pytest.param(0, id="zero_value"),
        pytest.param(1, id="non-zero_value"),
    ],
)
def test_top_frame_charges_delegation_is_sender(
    fork: Fork,
    pre: Alloc,
    state_test: StateTestFiller,
    value: int,
) -> None:
    """
    Recipient holds a pre-existing EIP-7702 delegation whose target is
    the sender (``tx.origin``), which is warm, so the top-frame charges
    ``WARM_ACCESS`` for the delegation target; the dispatched EVM frame
    finds the sender's empty EOA code and exits immediately.
    """
    sender_initial_balance = 10**18
    sender = pre.fund_eoa(sender_initial_balance)

    delegated_to = sender
    target_code = Spec7702.delegation_designation(delegated_to)
    target = pre.deploy_contract(code=target_code)

    intrinsic_gas = fork.transaction_intrinsic_cost_calculator()(
        sends_value=bool(value),
        recipient_type=RecipientType.DELEGATION_7702,
        return_cost_deducted_prior_execution=True,
    )
    top_frame_gas = fork.transaction_top_frame_execution_gas(
        sends_value=bool(value),
        recipient_type=RecipientType.DELEGATION_7702,
        delegation_warm=True,
    )

    total_gas_cost = intrinsic_gas + top_frame_gas
    gas_price = 1_000_000_000
    gas_limit = total_gas_cost + 1000

    tx = Transaction(
        sender=sender,
        to=target,
        value=value,
        gas_limit=gas_limit,
        gas_price=gas_price,
    )

    sender_final_balance = (
        sender_initial_balance - value - total_gas_cost * gas_price
    )

    post = {
        sender: Account(nonce=1, balance=sender_final_balance),
        target: Account(balance=value, code=target_code),
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
def test_top_frame_charges_delegation_is_recipient(
    fork: Fork,
    pre: Alloc,
    state_test: StateTestFiller,
    value: int,
) -> None:
    """
    Recipient holds a pre-existing EIP-7702 delegation pointing back
    at itself. The delegation target is the recipient, which is warm,
    so the top-frame charges ``WARM_ACCESS``, and then the dispatched
    EVM frame runs the recipient's code -- which *is* the delegation
    prefix ``0xef 01 00 <addr>``. The leading ``0xef`` decodes as the
    ``INVALID`` opcode, consuming the remaining EVM budget. The
    intrinsic and top-frame gas remain paid; the value transfer is
    rolled back.
    """
    sender_initial_balance = 10**18
    sender = pre.fund_eoa(sender_initial_balance)

    # Pre-allocate an EOA that delegates to itself. The 1-wei balance
    # keeps the account alive at top-frame check time so the
    # ``NEW_ACCOUNT`` charge does not fire.
    target = pre.fund_eoa(amount=1, delegation="Self")
    target_code = Spec7702.delegation_designation(target)

    intrinsic_gas = fork.transaction_intrinsic_cost_calculator()(
        sends_value=bool(value),
        recipient_type=RecipientType.DELEGATION_7702,
        return_cost_deducted_prior_execution=True,
    )
    top_frame_gas = fork.transaction_top_frame_execution_gas(
        sends_value=bool(value),
        recipient_type=RecipientType.DELEGATION_7702,
        delegation_warm=True,
    )

    # The dispatched frame burns the entire EVM budget on the
    # ``INVALID`` opcode and the value transfer is rolled back, so the
    # sender pays the full ``gas_limit``.
    gas_price = 1_000_000_000
    gas_limit = intrinsic_gas + top_frame_gas + 50_000

    tx = Transaction(
        sender=sender,
        to=target,
        value=value,
        gas_limit=gas_limit,
        gas_price=gas_price,
    )

    sender_final_balance = sender_initial_balance - gas_limit * gas_price

    post = {
        sender: Account(nonce=1, balance=sender_final_balance),
        # Value transfer rolled back by the ``INVALID``; the pre-tx
        # 1-wei balance is preserved.
        target: Account(balance=1, code=target_code),
    }

    state_test(pre=pre, tx=tx, post=post)


@EIPChecklist.GasCostChanges.Test.OutOfGas()
@pytest.mark.parametrize(
    "value",
    [
        pytest.param(0, id="zero_value"),
        pytest.param(1, id="non-zero_value"),
    ],
)
def test_top_frame_charges_self_delegation_oog(
    fork: Fork,
    pre: Alloc,
    state_test: StateTestFiller,
    value: int,
) -> None:
    """
    Recipient holds a pre-existing EIP-7702 delegation pointing back at
    itself, and the transaction is one gas short of the delegation
    target's ``WARM_ACCESS`` charge.

    The target of the resolution is the recipient itself, which is warm
    as ``tx.to``, so the starved charge is the warm access --
    a cold charge here would be a self-delegation warmth bug. The halt
    lands before dispatch, so the delegation prefix (whose leading
    ``0xef`` decodes as ``INVALID``) never runs; the sender pays the
    full ``gas_limit`` and no value moves.

    Unlike a delegation to a distinct never-accessed account, the
    delegated address here *is* the recipient, whose code was already
    read to discover the delegation: per EIP-7928 it must appear in the
    block access list exactly once, with no recorded changes.
    """
    sender = pre.fund_eoa()

    # Pre-allocate an EOA that delegates to itself. The 1-wei balance
    # keeps the account alive at top-frame check time so the
    # ``NEW_ACCOUNT`` charge does not fire.
    target = pre.fund_eoa(amount=1, delegation="Self")
    target_code = Spec7702.delegation_designation(target)

    intrinsic_gas = fork.transaction_intrinsic_cost_calculator()(
        sends_value=bool(value),
        recipient_type=RecipientType.DELEGATION_7702,
        return_cost_deducted_prior_execution=True,
    )
    top_frame_gas = fork.transaction_top_frame_execution_gas(
        sends_value=bool(value),
        recipient_type=RecipientType.DELEGATION_7702,
        delegation_warm=True,
    )

    # One gas short of the warm self-access: the frame halts before
    # dispatching the (self-)delegated code. The receipt pins the full
    # ``gas_limit`` as consumed -- the out-of-gas signature (receipt
    # ``status`` is not verified by the filler).
    gas_limit = intrinsic_gas + top_frame_gas - 1

    tx = Transaction(
        sender=sender,
        to=target,
        value=value,
        gas_limit=gas_limit,
        expected_receipt=TransactionReceipt(
            cumulative_gas_used=gas_limit,
        ),
    )

    post = {
        sender: Account(nonce=1),
        target: Account(balance=1, code=target_code),
    }

    state_test(
        pre=pre,
        tx=tx,
        post=post,
        expected_block_access_list=BlockAccessListExpectation(
            account_expectations={
                target: BalAccountExpectation.empty(),
            }
        ),
    )


@EIPChecklist.GasCostChanges.Test.GasUpdatesMeasurement()
@pytest.mark.parametrize(
    "value",
    [
        pytest.param(0, id="zero_value"),
        pytest.param(1, id="non-zero_value"),
    ],
)
def test_top_frame_charges_delegation_is_precompile(
    fork: Fork,
    pre: Alloc,
    state_test: StateTestFiller,
    value: int,
) -> None:
    """
    Recipient holds a pre-existing EIP-7702 delegation pointing at a
    precompile address (``IDENTITY``, ``0x04``), which is warm, so the
    top-frame charges ``WARM_ACCESS``; the dispatched EVM frame sets
    ``disable_precompiles = True`` for delegated calls, so the
    precompile body does not run. The code lookup at the precompile
    address returns the empty byte string and the frame exits
    immediately.
    """
    sender_initial_balance = 10**18
    sender = pre.fund_eoa(sender_initial_balance)

    delegated_to = Address(0x04)
    target_code = Spec7702.delegation_designation(delegated_to)
    target = pre.deploy_contract(code=target_code)

    intrinsic_gas = fork.transaction_intrinsic_cost_calculator()(
        sends_value=bool(value),
        recipient_type=RecipientType.DELEGATION_7702,
        return_cost_deducted_prior_execution=True,
    )
    top_frame_gas = fork.transaction_top_frame_execution_gas(
        sends_value=bool(value),
        recipient_type=RecipientType.DELEGATION_7702,
        delegation_warm=True,
    )

    total_gas_cost = intrinsic_gas + top_frame_gas
    gas_price = 1_000_000_000
    gas_limit = total_gas_cost + 1000

    tx = Transaction(
        sender=sender,
        to=target,
        value=value,
        gas_limit=gas_limit,
        gas_price=gas_price,
    )

    sender_final_balance = (
        sender_initial_balance - value - total_gas_cost * gas_price
    )

    post = {
        sender: Account(nonce=1, balance=sender_final_balance),
        target: Account(balance=value, code=target_code),
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
    "invalid_reason",
    [
        "stale_nonce",
        pytest.param("account_code", marks=pytest.mark.pre_alloc_mutable),
        "chain_id",
        "nonce_limit",
        "signature",
    ],
)
def test_top_frame_charges_delegation_is_authority(
    fork: Fork,
    pre: Alloc,
    state_test: StateTestFiller,
    value: int,
    invalid_reason: str,
    chain_config: ChainConfig,
) -> None:
    """
    Charge delegation access according to whether a skipped authorization
    recovered its authority: only failures after recovery warm it.
    """
    sender = pre.fund_eoa()
    authority_code = Op.STOP if invalid_reason == "account_code" else None
    authority = pre.fund_eoa(amount=1, code=authority_code)
    original_account = pre[authority]

    authorization = AuthorizationTuple(
        address=pre.deploy_contract(code=Op.STOP),
        nonce=(
            2**64 - 1
            if invalid_reason == "nonce_limit"
            else 99
            if invalid_reason == "stale_nonce"
            else 0
        ),
        chain_id=chain_config.chain_id + 1
        if invalid_reason == "chain_id"
        else 0,
        signer=authority,
        creates_account=False,
        writes_delegation=False,
        first_write=False,
    )
    if invalid_reason == "signature":
        authorization = authorization.model_copy(update={"r": 0, "s": 0})
    authorization_list = [authorization]
    delegation_warm = invalid_reason in ("stale_nonce", "account_code")
    target = pre.fund_eoa(amount=0, delegation=authority)
    target_code = Spec7702.delegation_designation(authority)

    intrinsic_gas = fork.transaction_intrinsic_cost_calculator()(
        sends_value=bool(value),
        recipient_type=RecipientType.DELEGATION_7702,
        authorization_list_or_count=authorization_list,
        return_cost_deducted_prior_execution=True,
    )
    top_frame_gas = fork.transaction_top_frame_execution_gas(
        sends_value=bool(value),
        recipient_type=RecipientType.DELEGATION_7702,
        delegation_warm=delegation_warm,
        authorizations=authorization_list,
    )
    top_frame_state_gas = fork.transaction_top_frame_state_gas(
        sends_value=bool(value),
        recipient_type=RecipientType.DELEGATION_7702,
        authorizations=authorization_list,
    )
    assert top_frame_state_gas == 0, (
        "a skipped authorization must not carry a state-gas charge"
    )
    total_gas_cost = intrinsic_gas + top_frame_gas

    # A cold charge in a warm case halts and spends the spare gas; a
    # warm charge in a cold case spends less than the expected receipt.
    tx = Transaction(
        sender=sender,
        to=target,
        value=value,
        authorization_list=authorization_list,
        gas_limit=total_gas_cost + 1,
        expected_receipt=TransactionReceipt(
            cumulative_gas_used=total_gas_cost,
        ),
    )

    post = {
        sender: Account(nonce=1),
        target: Account(balance=value, code=target_code),
        authority: original_account,
    }

    state_test(pre=pre, tx=tx, post=post)


@EIPChecklist.GasCostChanges.Test.GasUpdatesMeasurement()
def test_intrinsic_accounts_warm_for_execution(
    fork: Fork,
    pre: Alloc,
    state_test: StateTestFiller,
) -> None:
    """
    The sender, the recipient and a processed authority are warm for
    execution-level touches once the intrinsic phase has charged them.

    The recipient's code reads each of the three balances once. Every
    read costs ``WARM_ACCESS``: the intrinsic already charged the
    accesses at the cold rate and the accounts sit in
    ``accessed_addresses`` when the frame starts. A client that charged
    the recipient touch unconditionally but left the recipient out of
    the warm set would pay ``COLD_ACCOUNT_ACCESS`` on the read and run
    out of gas here. One spare gas distinguishes that halt from
    successful execution, even though the balance reads change no state
    and the applied authorization persists after an execution halt.
    """
    sender = pre.fund_eoa()
    scenario = build_authorization(
        pre, AuthorizationAction.SETS_NEW_DELEGATION
    )
    authorization_list = [scenario.authorization]

    warm_balance = Op.BALANCE.with_metadata(address_warm=True)
    code = (
        Op.POP(warm_balance(Op.ORIGIN))
        + Op.POP(warm_balance(Op.ADDRESS))
        + Op.POP(warm_balance(scenario.authority))
        + Op.STOP
    )
    recipient = pre.deploy_contract(code=code)

    intrinsic_gas = fork.transaction_intrinsic_cost_calculator()(
        recipient_type=RecipientType.CONTRACT,
        authorization_list_or_count=authorization_list,
        return_cost_deducted_prior_execution=True,
    )
    top_frame_gas = fork.transaction_top_frame_execution_gas(
        recipient_type=RecipientType.CONTRACT,
        authorizations=authorization_list,
    )
    top_frame_state_gas = fork.transaction_top_frame_state_gas(
        recipient_type=RecipientType.CONTRACT,
        authorizations=authorization_list,
    )
    total_gas_cost = (
        intrinsic_gas
        + top_frame_gas
        + top_frame_state_gas
        + code.gas_cost(fork)
    )

    tx = Transaction(
        sender=sender,
        to=recipient,
        authorization_list=authorization_list,
        gas_limit=total_gas_cost + 1,
        expected_receipt=TransactionReceipt(
            cumulative_gas_used=total_gas_cost,
        ),
    )

    post = {
        sender: Account(nonce=1),
        recipient: Account(code=code),
        scenario.authority: scenario.applied_account,
    }

    state_test(pre=pre, tx=tx, post=post)
