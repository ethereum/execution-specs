"""
Dedicated tests for the EIP-2780 top-frame charge layer.

The top-frame layer applies *after* intrinsic gas is deducted but
*before* the EVM dispatches at the transaction's outermost frame. Two
charges may fire there, depending on the recipient:

- ``NEW_ACCOUNT`` (state gas) when the recipient is empty and the
  transaction transfers value.
- ``COLD_ACCOUNT_ACCESS`` (regular gas) when the recipient holds an
  EIP-7702 delegation.

Each test parametrizes over the interesting outcomes for that charge:
running out of gas at the boundary, succeeding through the charge and
into the EVM, and (for the regular charge) succeeding through the
charge but reverting from the delegated code.
"""

import pytest
from execution_testing import (
    Account,
    Address,
    Alloc,
    Block,
    BlockchainTestFiller,
    Fork,
    Header,
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


@pytest.mark.parametrize("outcome", ["oog", "success"])
def test_top_frame_state_charge(
    fork: Fork,
    pre: Alloc,
    state_test: StateTestFiller,
    outcome: str,
) -> None:
    """
    Recipient is empty and the transaction transfers a non-zero value,
    so the top-frame fires the ``NEW_ACCOUNT`` state-gas charge.

    - ``oog``: gas limit is one short of covering the state charge.
      The transaction passes the intrinsic check, enters
      ``process_message``, and out-of-gases on
      ``charge_state_gas(NEW_ACCOUNT)`` before any EVM bytecode runs.
      The sender pays the full ``gas_limit`` and no value is
      transferred.
    - ``success``: gas limit covers the state charge. The value
      transfer brings the recipient into existence and the recipient
      ends the transaction holding the transferred balance.
    """
    sender_initial_balance = 10**18
    sender = pre.fund_eoa(sender_initial_balance)
    target = pre.fund_eoa(amount=0)

    value = 1
    intrinsic_gas = fork.transaction_intrinsic_cost_calculator()(
        sends_value=True,
        recipient_type=RecipientType.EMPTY_ACCOUNT,
        return_cost_deducted_prior_execution=True,
    )
    top_frame_state_gas = fork.transaction_top_frame_state_gas(
        sends_value=True,
        recipient_type=RecipientType.EMPTY_ACCOUNT,
    )
    assert top_frame_state_gas > 0, (
        "top-frame state gas must be non-zero for this scenario"
    )

    gas_price = 1_000_000_000
    if outcome == "oog":
        gas_limit = intrinsic_gas + top_frame_state_gas - 1
        sender_final_balance = sender_initial_balance - gas_limit * gas_price
        expected_target: Account | None = None
    else:
        total_gas_cost = intrinsic_gas + top_frame_state_gas
        gas_limit = total_gas_cost + 1000
        sender_final_balance = (
            sender_initial_balance - value - total_gas_cost * gas_price
        )
        expected_target = Account(balance=value)

    tx = Transaction(
        sender=sender,
        to=target,
        value=value,
        gas_limit=gas_limit,
        gas_price=gas_price,
    )

    post = {
        sender: Account(nonce=1, balance=sender_final_balance),
        target: expected_target,
    }

    state_test(pre=pre, tx=tx, post=post)


def test_top_frame_state_charge_empty_precompile(
    fork: Fork,
    pre: Alloc,
    state_test: StateTestFiller,
) -> None:
    """
    An empty precompile recipient is still empty per EIP-161, so a
    value-moving transaction to it must pay the top-frame
    ``NEW_ACCOUNT`` state-gas charge.

    The gas limit is one short of covering that state charge. Without
    the charge, the transaction would reach the identity precompile and
    transfer value, which makes this a direct regression test for a
    precompile carve-out.
    """
    sender_initial_balance = 10**18
    sender = pre.fund_eoa(sender_initial_balance)
    identity_precompile = Address(0x04)

    value = 1
    intrinsic_gas = fork.transaction_intrinsic_cost_calculator()(
        sends_value=True,
        recipient_type=RecipientType.PRECOMPILE,
        return_cost_deducted_prior_execution=True,
    )
    top_frame_state_gas = fork.transaction_top_frame_state_gas(
        sends_value=True,
        recipient_type=RecipientType.EMPTY_ACCOUNT,
    )
    assert top_frame_state_gas > 0, (
        "top-frame state gas must be non-zero for empty recipients"
    )

    gas_price = 1_000_000_000
    gas_limit = intrinsic_gas + top_frame_state_gas - 1
    tx = Transaction(
        sender=sender,
        to=identity_precompile,
        value=value,
        gas_limit=gas_limit,
        gas_price=gas_price,
    )

    post = {
        sender: Account(
            nonce=1,
            balance=sender_initial_balance - gas_limit * gas_price,
        ),
        identity_precompile: None,
    }

    state_test(pre=pre, tx=tx, post=post)


def test_top_frame_new_account_charged_as_state_gas(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    The top-frame ``NEW_ACCOUNT`` charge for a value transfer to an
    empty recipient is *state* gas, not regular gas. This pins the
    dimension via the block header ``gas_used``, which the spec
    computes as ``max(block_regular_gas, block_state_gas)``.

    Correctly attributed, the ``NEW_ACCOUNT`` state gas dominates the
    small regular intrinsic, so ``gas_used == NEW_ACCOUNT``. A
    regression mis-classifying the charge as regular gas would instead
    yield ``intrinsic_regular + NEW_ACCOUNT``.

    ``state_test``-based balance assertions (e.g.
    ``test_top_frame_state_charge``) only observe the *sum* of the two
    dimensions, so they cannot distinguish this; a block-level
    ``gas_used`` assertion is required.
    """
    sender = pre.fund_eoa(10**18)
    target = pre.fund_eoa(amount=0)
    value = 1

    intrinsic_regular = fork.transaction_intrinsic_cost_calculator()(
        sends_value=True,
        recipient_type=RecipientType.EMPTY_ACCOUNT,
        return_cost_deducted_prior_execution=True,
    )
    new_account_state_gas = fork.transaction_top_frame_state_gas(
        sends_value=True,
        recipient_type=RecipientType.EMPTY_ACCOUNT,
    )
    # The state charge must dominate the regular intrinsic for the
    # header ``gas_used`` to distinguish a state vs regular
    # mis-classification.
    assert new_account_state_gas > intrinsic_regular, (
        "test only distinguishes the dimension when NEW_ACCOUNT "
        f"({new_account_state_gas}) dominates the regular intrinsic "
        f"({intrinsic_regular})"
    )

    # No EVM bytecode runs (empty recipient), so the only regular gas
    # is the intrinsic and the only state gas is the top-frame
    # ``NEW_ACCOUNT`` charge.
    expected_gas_used = max(intrinsic_regular, new_account_state_gas)

    gas_price = 10**9
    tx = Transaction(
        sender=sender,
        to=target,
        value=value,
        gas_limit=intrinsic_regular + new_account_state_gas + 1000,
        gas_price=gas_price,
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
            target: Account(balance=value),
        },
    )


@pytest.mark.pre_alloc_mutable
def test_top_frame_new_account_skipped_for_nonce_only_recipient(
    fork: Fork,
    pre: Alloc,
    state_test: StateTestFiller,
) -> None:
    """
    A recipient that is alive only by its nonce (``nonce=1``, zero
    balance, no code) is not empty per EIP-161, so a value transfer to
    it does *not* incur the top-frame ``NEW_ACCOUNT`` charge. This pins
    that the gate keys on ``is_account_alive``, not ``balance == 0``.

    Such an account is reachable on-chain: any EOA that has sent a
    transaction (nonce bumped) and been fully drained sits at
    ``nonce>0, balance=0, no code``.

    The gas limit is pinned to exactly the intrinsic, leaving no room
    for any extra charge: an implementation that wrongly charged
    ``NEW_ACCOUNT`` (keying on the zero balance) would out-of-gas
    rather than succeed. The recipient has no code, so no EVM runs and
    the intrinsic is fully consumed with nothing to refund.
    """
    sender_initial_balance = 10**18
    sender = pre.fund_eoa(sender_initial_balance)
    # Alive via nonce only: not empty per EIP-161 because nonce != 0.
    target = pre.fund_eoa(amount=0, nonce=1)
    value = 1

    intrinsic_gas = fork.transaction_intrinsic_cost_calculator()(
        sends_value=True,
        recipient_type=RecipientType.EOA,
        return_cost_deducted_prior_execution=True,
    )
    top_frame_state_gas = fork.transaction_top_frame_state_gas(
        sends_value=True,
        recipient_type=RecipientType.EOA,
    )
    assert top_frame_state_gas == 0, (
        "a nonce-only-alive recipient must not incur the NEW_ACCOUNT charge"
    )

    gas_price = 1_000_000_000
    gas_limit = intrinsic_gas
    tx = Transaction(
        sender=sender,
        to=target,
        value=value,
        gas_limit=gas_limit,
        gas_price=gas_price,
    )

    sender_final_balance = (
        sender_initial_balance - value - intrinsic_gas * gas_price
    )
    post = {
        sender: Account(nonce=1, balance=sender_final_balance),
        target: Account(nonce=1, balance=value),
    }

    state_test(pre=pre, tx=tx, post=post)


@pytest.mark.parametrize("outcome", ["oog", "success", "evm_reverts"])
@pytest.mark.parametrize(
    "value",
    [
        pytest.param(0, id="zero_value"),
        pytest.param(1, id="non-zero_value"),
    ],
)
def test_top_frame_regular_charge(
    fork: Fork,
    pre: Alloc,
    state_test: StateTestFiller,
    outcome: str,
    value: int,
) -> None:
    """
    Recipient is an existing EIP-7702 delegation, so the top-frame
    fires the ``COLD_ACCOUNT_ACCESS`` regular-gas charge regardless of
    whether the transaction transfers value.

    - ``oog``: gas limit is one short of covering the regular charge
      (plus the value-transfer charge when ``value > 0``). The
      transaction OOGs at ``charge_gas(COLD_ACCOUNT_ACCESS)`` before
      the delegated code runs. The sender pays the full ``gas_limit``
      and the recipient keeps its pre-tx state.
    - ``success``: gas limit covers the regular charge; the delegated
      code is a ``STOP`` and the transaction lands the value transfer.
    - ``evm_reverts``: the delegated code reverts immediately. The
      top-frame charge is consumed before dispatch and the two
      ``PUSH`` opcodes that feed the ``REVERT`` are paid before the
      revert; the value transfer is rolled back, the unused EVM
      budget is returned, and the intrinsic and top-frame gas remain
      paid.
    """
    sender_initial_balance = 10**18
    sender = pre.fund_eoa(sender_initial_balance)

    revert_code = Op.REVERT(0, 0)
    if outcome == "evm_reverts":
        delegated_to = pre.deploy_contract(code=revert_code)
    else:
        delegated_to = pre.deploy_contract(code=Op.STOP)
    target_code = Spec7702.delegation_designation(delegated_to)
    target = pre.deploy_contract(code=target_code)

    intrinsic_gas = fork.transaction_intrinsic_cost_calculator()(
        sends_value=bool(value),
        recipient_type=RecipientType.DELEGATION_7702,
        return_cost_deducted_prior_execution=True,
    )
    top_frame_gas = fork.transaction_top_frame_gas_calculator()(
        sends_value=bool(value),
        recipient_type=RecipientType.DELEGATION_7702,
    )
    assert top_frame_gas > 0, (
        "top-frame regular gas must be non-zero for this scenario"
    )

    gas_price = 1_000_000_000
    if outcome == "oog":
        gas_limit = intrinsic_gas + top_frame_gas - 1
        sender_final_balance = sender_initial_balance - gas_limit * gas_price
        target_balance = 0
    elif outcome == "success":
        total_gas_cost = intrinsic_gas + top_frame_gas
        gas_limit = total_gas_cost + 1000
        sender_final_balance = (
            sender_initial_balance - value - total_gas_cost * gas_price
        )
        target_balance = value
    else:
        # Two ``PUSH`` opcodes feed ``REVERT`` before it halts.
        revert_exec_gas = revert_code.gas_cost(fork)
        gas_used = intrinsic_gas + top_frame_gas + revert_exec_gas
        gas_limit = gas_used + 1000
        # Value transfer is rolled back, so the sender keeps the
        # would-be transferred value. The intrinsic, top-frame, and
        # pre-revert EVM gas stay paid.
        sender_final_balance = sender_initial_balance - gas_used * gas_price
        target_balance = 0

    tx = Transaction(
        sender=sender,
        to=target,
        value=value,
        gas_limit=gas_limit,
        gas_price=gas_price,
    )

    post = {
        sender: Account(nonce=1, balance=sender_final_balance),
        target: Account(balance=target_balance, code=target_code),
    }

    state_test(pre=pre, tx=tx, post=post)
