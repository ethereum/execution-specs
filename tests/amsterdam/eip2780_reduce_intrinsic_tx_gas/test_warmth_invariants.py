"""
EIP-2780 invariants for transaction-level account charges.

The recipient and any EIP-7702 delegation target referenced at the
top-level transaction frame always pay the cold access rate, even when
the address is otherwise warm, identical to the sender, or refers to
itself:

- The access list does not warm transaction-level accounts. Listing
  ``tx.to`` (or a delegation target) pays the access-list cost but
  does not waive the cold charge.
- The block coinbase is pre-warmed by the protocol before transaction
  execution, but tx-level cold charges still fire when ``tx.to`` or a
  delegation target happens to be the coinbase.
- Precompile addresses still pay the cold charge.
- Self-referential delegations (delegation target equal to the
  sender, the recipient itself, or a precompile) all pay the cold
  charge; the dispatched EVM frame then runs whatever code lives at
  the target, including the degenerate cases of empty code (EOA,
  precompile address) or a delegation prefix that itself decodes as
  the ``INVALID`` opcode.
"""

import pytest
from execution_testing import (
    AccessList,
    Account,
    Address,
    Alloc,
    Environment,
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
) -> None:
    """
    Recipient holds a pre-existing EIP-7702 delegation; the delegation
    target is listed in the access list. The top-frame still charges
    ``COLD_ACCOUNT_ACCESS`` for the delegation target on top of the
    access-list cost itself.
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
    top_frame_gas = fork.transaction_top_frame_gas_calculator()(
        sends_value=bool(value),
        recipient_type=RecipientType.DELEGATION_7702,
    )

    total_gas_cost = intrinsic_gas + top_frame_gas
    gas_price = 1_000_000_000
    gas_limit = total_gas_cost + 1000

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
        sender_initial_balance - value - total_gas_cost * gas_price
    )

    post = {
        sender: Account(nonce=1, balance=sender_final_balance),
        target: Account(balance=value, code=target_code),
    }

    state_test(pre=pre, tx=tx, post=post)


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
    the block coinbase. Coinbase is implicitly warm before execution;
    the top-frame still charges ``COLD_ACCOUNT_ACCESS`` for the
    delegation target.
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
    top_frame_gas = fork.transaction_top_frame_gas_calculator()(
        sends_value=bool(value),
        recipient_type=RecipientType.DELEGATION_7702,
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
    the sender (``tx.origin``). The top-frame still charges
    ``COLD_ACCOUNT_ACCESS`` for the delegation target; the dispatched
    EVM frame finds the sender's empty EOA code and exits immediately.
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
    top_frame_gas = fork.transaction_top_frame_gas_calculator()(
        sends_value=bool(value),
        recipient_type=RecipientType.DELEGATION_7702,
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
    at itself. The top-frame charges ``COLD_ACCOUNT_ACCESS`` for the
    delegation target (the recipient itself), and then the dispatched
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
    top_frame_gas = fork.transaction_top_frame_gas_calculator()(
        sends_value=bool(value),
        recipient_type=RecipientType.DELEGATION_7702,
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
    precompile address (``IDENTITY``, ``0x04``). The top-frame charges
    ``COLD_ACCOUNT_ACCESS``; the dispatched EVM frame sets
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
    top_frame_gas = fork.transaction_top_frame_gas_calculator()(
        sends_value=bool(value),
        recipient_type=RecipientType.DELEGATION_7702,
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
