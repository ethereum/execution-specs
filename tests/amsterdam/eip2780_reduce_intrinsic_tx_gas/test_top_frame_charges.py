"""
Dedicated tests for the EIP-2780 top-frame charge layer.

The top-frame layer applies *after* intrinsic gas is deducted but
*before* the EVM dispatches at the transaction's outermost frame. Two
charges may fire there, depending on the recipient:

- ``NEW_ACCOUNT`` (state gas) when the recipient is empty and the
  transaction transfers value, or when a creation transaction's target
  leaf did not exist before the transaction.
- ``COLD_ACCOUNT_ACCESS`` (execution gas) when the recipient holds an
  EIP-7702 delegation.

Each test parametrizes over the interesting outcomes for that charge:
running out of gas at the boundary, succeeding through the charge and
into the EVM, and (for the execution charge) succeeding through the
charge but reverting from the delegated code. For creation
transactions, the charge keys on the *transaction pre-state* being
empty, and — being consumed on any successful halt — survives the
created account's own destruction.
"""

from enum import Enum, auto

import pytest
from execution_testing import (
    Account,
    Address,
    Alloc,
    Block,
    BlockchainTestFiller,
    Bytecode,
    Fork,
    Header,
    Op,
    RecipientType,
    StateTestFiller,
    Transaction,
    TransactionReceipt,
    compute_create_address,
)

from ...prague.eip7702_set_code_tx.spec import Spec as Spec7702
from .helpers import EOA_INITIAL_BALANCE
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
    fork: Fork,
    pre: Alloc,
    blockchain_test: BlockchainTestFiller,
) -> None:
    """
    The top-frame ``NEW_ACCOUNT`` charge for a value transfer to an
    empty recipient is *state* gas, not execution gas. This pins the
    dimension via the block header ``gas_used``, which the spec
    computes as ``max(block_execution_gas, block_state_gas)``.

    Correctly attributed, the ``NEW_ACCOUNT`` state gas dominates the
    small execution intrinsic, so ``gas_used == NEW_ACCOUNT``. A
    regression mis-classifying the charge as execution gas would instead
    yield ``intrinsic_execution + NEW_ACCOUNT``.

    ``state_test``-based balance assertions (e.g.
    ``test_top_frame_state_charge``) only observe the *sum* of the two
    dimensions, so they cannot distinguish this; a block-level
    ``gas_used`` assertion is required.
    """
    sender = pre.fund_eoa(10**18)
    target = pre.fund_eoa(amount=0)
    value = 1

    intrinsic_execution = fork.transaction_intrinsic_cost_calculator()(
        sends_value=True,
        recipient_type=RecipientType.EMPTY_ACCOUNT,
        return_cost_deducted_prior_execution=True,
    )
    new_account_state_gas = fork.transaction_top_frame_state_gas(
        sends_value=True,
        recipient_type=RecipientType.EMPTY_ACCOUNT,
    )
    # The state charge must dominate the execution intrinsic for the
    # header ``gas_used`` to distinguish a state vs execution
    # mis-classification.
    assert new_account_state_gas > intrinsic_execution, (
        "test only distinguishes the dimension when NEW_ACCOUNT "
        f"({new_account_state_gas}) dominates the execution intrinsic "
        f"({intrinsic_execution})"
    )

    # No EVM bytecode runs (empty recipient), so the only execution gas
    # is the intrinsic and the only state gas is the top-frame
    # ``NEW_ACCOUNT`` charge.
    expected_gas_used = max(intrinsic_execution, new_account_state_gas)

    gas_price = 1_000_000_000
    tx = Transaction(
        sender=sender,
        to=target,
        value=value,
        gas_limit=intrinsic_execution + new_account_state_gas + 1000,
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


def creation_tx_init_code(fork: Fork) -> tuple[Bytecode, int]:
    """
    Build init code for exact-gas creation-transaction tests and return
    it with its execution gas.

    The code deploys empty code (no deposit charges) and expands memory
    so that its execution gas lifts the transaction's exact total above
    the calldata floor, which would otherwise bind once the top-frame
    ``NEW_ACCOUNT`` charge is skipped.
    """
    memory_offset = 30_000
    init_code = (
        Op.MSTORE.with_metadata(
            new_memory_size=memory_offset + 32, old_memory_size=0
        )(memory_offset, 0)
        + Op.STOP
    )
    return init_code, init_code.gas_cost(fork)


@pytest.mark.parametrize(
    "value",
    [
        pytest.param(0, id="zero_value"),
        pytest.param(1, id="non-zero_value"),
    ],
)
def test_top_frame_new_account_skipped_for_prefunded_create_target(
    fork: Fork,
    pre: Alloc,
    state_test: StateTestFiller,
    value: int,
) -> None:
    """
    A creation transaction whose nonce-derived target address already
    holds a balance does not incur the top-frame ``NEW_ACCOUNT`` state
    charge.

    The create branch of ``prepare_dispatch`` keys the charge on the
    *transaction pre-state* being empty — a live check would always see
    the account, because ``process_create_message`` bumps the target's
    nonce before dispatch. Pre-funding the create address makes the
    pre-state leaf non-empty, so the charge must be skipped; a
    balance-only leaf does not trigger the create-collision check
    (only nonce or code do), so the deployment still succeeds.

    The gas limit carries headroom above the exact total so the
    transaction never runs out of gas, and the receipt pins
    ``cumulative_gas_used`` to exactly the intrinsic plus the init-code
    execution gas: a wrongly charged ``NEW_ACCOUNT`` for the
    pre-existing leaf (or a spurious refill) shifts the receipt by
    183,600 in either direction.
    """
    sender = pre.fund_eoa()
    created = compute_create_address(address=sender, nonce=sender.nonce)
    prefund = 1
    pre.fund_address(created, prefund)

    init_code, exec_gas = creation_tx_init_code(fork)

    intrinsic_gas = fork.transaction_intrinsic_cost_calculator()(
        calldata=init_code,
        contract_creation=True,
        sends_value=bool(value),
        return_cost_deducted_prior_execution=True,
    )
    # The amount a fresh create target would be charged at the top
    # frame -- the charge this test asserts is skipped.
    fresh_target_state_gas = fork.transaction_top_frame_state_gas(
        contract_creation=True,
    )
    assert fresh_target_state_gas > 0, (
        "a fresh create target must be charged top-frame state gas"
    )

    total_gas = intrinsic_gas + exec_gas
    calldata_floor = fork.transaction_data_floor_cost_calculator()(
        data=init_code,
        contract_creation=True,
        sends_value=bool(value),
    )
    assert total_gas > calldata_floor, (
        "The exact total must exceed the calldata floor for the "
        "gas pin to observe the skipped charge."
        "Lift memory expansion in `creation_tx_init_code` to fix."
    )

    tx = Transaction(
        sender=sender,
        to=None,
        data=init_code,
        value=value,
        gas_limit=total_gas,
        expected_receipt=TransactionReceipt(cumulative_gas_used=total_gas),
    )

    post = {
        sender: Account(nonce=1),
        created: Account(nonce=1, balance=prefund + value, code=b""),
    }

    state_test(pre=pre, tx=tx, post=post)


@pytest.mark.parametrize(
    "value",
    [
        pytest.param(0, id="zero_value"),
        pytest.param(1, id="non-zero_value"),
    ],
)
def test_top_frame_new_account_skipped_for_create_target_funded_same_block(
    fork: Fork,
    pre: Alloc,
    blockchain_test: BlockchainTestFiller,
    value: int,
) -> None:
    """
    A creation transaction whose target was funded by an *earlier
    transaction of the same block* does not incur the top-frame
    ``NEW_ACCOUNT`` state charge.

    This discriminates the transaction pre-state from the block
    pre-state: ``get_pre_state_account`` consults the block's
    accumulated same-block transaction writes before falling back to
    the block pre-state, so the funding transaction's new leaf counts
    as pre-existing for the creation transaction. An implementation
    snapshotting at block start would charge a second ``NEW_ACCOUNT``,
    shifting the creation transaction's receipt by 183,600 and
    doubling the state dimension pinned by the header.

    The funding transaction pays its own top-frame ``NEW_ACCOUNT`` for
    materializing the leaf, which the block header pins as the block's
    entire state-gas dimension: ``gas_used = max(execution, state)`` must
    equal exactly one ``NEW_ACCOUNT``.
    """
    funder = pre.fund_eoa()
    sender = pre.fund_eoa()
    created = compute_create_address(address=sender, nonce=sender.nonce)

    # Transaction 1: fund the future create address. The value transfer
    # to the not-yet-existing leaf pays the top-frame ``NEW_ACCOUNT``.
    prefund = 1
    fund_intrinsic = fork.transaction_intrinsic_cost_calculator()(
        sends_value=True,
        recipient_type=RecipientType.EMPTY_ACCOUNT,
        return_cost_deducted_prior_execution=True,
    )
    fund_state_gas = fork.transaction_top_frame_state_gas(
        sends_value=True,
        recipient_type=RecipientType.EMPTY_ACCOUNT,
    )
    assert fund_state_gas > 0, (
        "funding an empty leaf must charge top-frame state gas"
    )
    fund_total = fund_intrinsic + fund_state_gas
    fund_tx = Transaction(
        sender=funder,
        to=created,
        value=prefund,
        gas_limit=fund_total,
        expected_receipt=TransactionReceipt(cumulative_gas_used=fund_total),
    )

    # Transaction 2: the creation transaction, with gas headroom; the
    # receipt pins the consumed gas to exactly the ``NEW_ACCOUNT``-free
    # total.
    init_code, exec_gas = creation_tx_init_code(fork)
    create_intrinsic = fork.transaction_intrinsic_cost_calculator()(
        calldata=init_code,
        contract_creation=True,
        sends_value=bool(value),
        return_cost_deducted_prior_execution=True,
    )
    create_total = create_intrinsic + exec_gas
    calldata_floor = fork.transaction_data_floor_cost_calculator()(
        data=init_code,
        contract_creation=True,
        sends_value=bool(value),
    )
    assert create_total > calldata_floor, (
        "the exact total must exceed the calldata floor for the "
        "gas pin to observe the skipped charge."
        "Lift memory expansion in `creation_tx_init_code` to fix."
    )
    create_tx = Transaction(
        sender=sender,
        to=None,
        data=init_code,
        value=value,
        gas_limit=create_total,
        expected_receipt=TransactionReceipt(
            cumulative_gas_used=fund_total + create_total
        ),
    )

    # Header pin: the block's state dimension is exactly the funding
    # transaction's ``NEW_ACCOUNT``; both execution intrinsics sit at or
    # above their calldata floors, so no floor term enters the block's
    # execution dimension either.
    block_execution = fund_intrinsic + create_total
    assert fund_state_gas > block_execution, (
        "the state dimension must dominate for the header to pin it"
    )

    post = {
        funder: Account(nonce=1),
        sender: Account(nonce=1),
        created: Account(nonce=1, balance=prefund + value, code=b""),
    }

    blockchain_test(
        pre=pre,
        blocks=[
            Block(
                txs=[fund_tx, create_tx],
                header_verify=Header(gas_used=fund_state_gas),
            ),
        ],
        post=post,
    )


@pytest.mark.parametrize("outcome", ["oog", "success", "evm_reverts"])
@pytest.mark.parametrize(
    "value",
    [
        pytest.param(0, id="zero_value"),
        pytest.param(1, id="non-zero_value"),
    ],
)
def test_top_frame_execution_charge(
    fork: Fork,
    pre: Alloc,
    state_test: StateTestFiller,
    outcome: str,
    value: int,
) -> None:
    """
    Recipient is an existing EIP-7702 delegation, so the top-frame
    fires the ``COLD_ACCOUNT_ACCESS`` execution-gas charge regardless of
    whether the transaction transfers value.

    - ``oog``: gas limit is one short of covering the execution charge
      (plus the value-transfer charge when ``value > 0``). The
      transaction OOGs at ``charge_gas(COLD_ACCOUNT_ACCESS)`` before
      the delegated code runs. The sender pays the full ``gas_limit``
      and the recipient keeps its pre-tx state.
    - ``success``: gas limit covers the execution charge; the delegated
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
        "top-frame execution gas must be non-zero for this scenario"
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


@pytest.mark.parametrize(
    "beneficiary_kind",
    [
        pytest.param("self", id="self_beneficiary"),
        pytest.param("funded_external", id="funded_external_beneficiary"),
        pytest.param("empty_external", id="empty_external_beneficiary"),
    ],
)
@pytest.mark.parametrize(
    "value",
    [
        pytest.param(0, id="zero_value"),
        pytest.param(1, id="non-zero_value"),
    ],
)
@pytest.mark.valid_before("EIP4758")
def test_initcode_selfdestruct_keeps_top_frame_state_charge(
    fork: Fork,
    pre: Alloc,
    state_test: StateTestFiller,
    beneficiary_kind: str,
    value: int,
) -> None:
    """
    A creation transaction whose init code ``SELFDESTRUCT``s keeps the
    top-frame ``NEW_ACCOUNT`` state charge consumed.

    ``SELFDESTRUCT`` is a *successful* halt: the frame returns no
    output (an empty deposit, so no deposit charges) and no rollback
    runs, so the refill machinery that returns state gas on a revert or
    exceptional halt never triggers — even though the created account
    is destroyed at the end of the transaction (EIP-6780 same-tx
    deletion) and its leaf never persists. Deletion itself carries no
    state-gas credit: freeing state is not refunded.

    Where the endowment ends up follows EIP-8246: destruction preserves
    a nonzero balance, so a self beneficiary leaves a balance-only leaf
    behind, while sweeping to an external beneficiary (or a zero
    endowment) removes the account entirely. Sweeping value to a
    not-yet-existing beneficiary additionally pays the opcode-level
    ``NEW_ACCOUNT`` and ``ACCOUNT_WRITE`` for the beneficiary — both
    the destroyed target's top-frame charge and the sweep's charge stay
    paid.

    The receipt pins the exact total; a regression refilling the
    top-frame charge shows up as a 183,600 shortfall in
    ``cumulative_gas_used`` and a matching sender refund.
    """
    sender = pre.fund_eoa()
    created = compute_create_address(address=sender, nonce=sender.nonce)

    beneficiary: Address | None = None
    if beneficiary_kind == "self":
        # The created address is warmed for the create frame itself.
        init_code = Op.SELFDESTRUCT.with_metadata(
            address_warm=True, account_new=False
        )(Op.ADDRESS)
    elif beneficiary_kind == "funded_external":
        beneficiary = pre.fund_eoa(amount=EOA_INITIAL_BALANCE)
        init_code = Op.SELFDESTRUCT.with_metadata(
            address_warm=False, account_new=False
        )(beneficiary)
    else:
        beneficiary = pre.nonexistent_account()
        # Sweeping a non-zero balance into a non-existent leaf creates
        # the beneficiary, paying NEW_ACCOUNT (state) and ACCOUNT_WRITE
        # (execution) at the opcode.
        init_code = Op.SELFDESTRUCT.with_metadata(
            address_warm=False, account_new=bool(value)
        )(beneficiary)

    # Combined execution + state execution gas, including any sweep
    # charges modeled by the metadata above.
    exec_gas = init_code.gas_cost(fork)

    intrinsic_gas = fork.transaction_intrinsic_cost_calculator()(
        calldata=init_code,
        contract_creation=True,
        sends_value=bool(value),
        return_cost_deducted_prior_execution=True,
    )
    top_frame_state_gas = fork.transaction_top_frame_state_gas(
        contract_creation=True,
    )
    assert top_frame_state_gas > 0, (
        "a fresh create target must be charged top-frame state gas"
    )
    total_gas = intrinsic_gas + top_frame_state_gas + exec_gas

    tx = Transaction(
        sender=sender,
        to=None,
        data=init_code,
        value=value,
        gas_limit=total_gas,
        expected_receipt=TransactionReceipt(cumulative_gas_used=total_gas),
    )

    post: dict[Address, Account | None] = {sender: Account(nonce=1)}
    if beneficiary_kind == "self":
        # EIP-8246: destruction preserves the balance, so a non-zero
        # endowment survives as a balance-only leaf.
        post[created] = (
            Account(balance=value, nonce=0, code=b"") if value else None
        )
    elif beneficiary_kind == "funded_external":
        assert beneficiary is not None
        post[created] = None
        post[beneficiary] = Account(balance=EOA_INITIAL_BALANCE + value)
    else:
        assert beneficiary is not None
        post[created] = None
        # A zero-value sweep does not bring the beneficiary to life.
        post[beneficiary] = Account(balance=value) if value else None

    state_test(pre=pre, tx=tx, post=post)


@pytest.mark.valid_before("EIP4758")
def test_initcode_selfdestruct_state_gas_in_header(
    fork: Fork,
    pre: Alloc,
    blockchain_test: BlockchainTestFiller,
) -> None:
    """
    The top-frame ``NEW_ACCOUNT`` surviving an init-code
    ``SELFDESTRUCT`` stays in the *state* dimension after settlement.

    Receipts and balances only observe the sum of the two gas
    dimensions, so the sibling
    ``test_initcode_selfdestruct_keeps_top_frame_state_charge`` cannot
    distinguish which dimension the surviving charge settled into. The
    block header can: ``gas_used = max(block_execution, block_state)``,
    and with a zero endowment and a self beneficiary the whole created
    account vanishes while the state side (one ``NEW_ACCOUNT``,
    dominating the small execution side) must still show in the header.

    Bug signatures: a refill regression collapses the header to the
    small execution sum; an execution-gas mis-classification raises it to
    ``execution + NEW_ACCOUNT``.
    """
    sender = pre.fund_eoa()
    created = compute_create_address(address=sender, nonce=sender.nonce)

    init_code = Op.SELFDESTRUCT.with_metadata(
        address_warm=True, account_new=False
    )(Op.ADDRESS)
    evm_execution = init_code.execution_cost(fork)

    intrinsic_gas = fork.transaction_intrinsic_cost_calculator()(
        calldata=init_code,
        contract_creation=True,
        return_cost_deducted_prior_execution=True,
    )
    state_side = fork.transaction_top_frame_state_gas(
        contract_creation=True,
    )
    calldata_floor = fork.transaction_data_floor_cost_calculator()(
        data=init_code,
        contract_creation=True,
    )
    # Block accounting carries the calldata floor in the execution
    # dimension.
    execution_side = max(intrinsic_gas + evm_execution, calldata_floor)
    assert state_side > execution_side, (
        "the state dimension must dominate for the header to pin it"
    )

    total_gas = intrinsic_gas + state_side + evm_execution
    tx = Transaction(
        sender=sender,
        to=None,
        data=init_code,
        gas_limit=total_gas,
        expected_receipt=TransactionReceipt(cumulative_gas_used=total_gas),
    )

    blockchain_test(
        pre=pre,
        blocks=[
            Block(
                txs=[tx],
                header_verify=Header(gas_used=state_side),
            ),
        ],
        post={
            sender: Account(nonce=1),
            created: None,
        },
    )


class TopFrameFailureMode(Enum):
    """The top-frame charge the failing transaction out-of-gases on."""

    CREATE_STATE_OOG = auto()
    NEW_ACCOUNT_STATE_OOG = auto()
    DELEGATED_EXECUTION_OOG = auto()


@pytest.mark.parametrize(
    "failure_mode",
    [
        pytest.param(
            TopFrameFailureMode.CREATE_STATE_OOG,
            id="create_state_oog",
        ),
        pytest.param(
            TopFrameFailureMode.NEW_ACCOUNT_STATE_OOG,
            id="new_account_state_oog",
        ),
        pytest.param(
            TopFrameFailureMode.DELEGATED_EXECUTION_OOG,
            id="delegated_execution_oog",
        ),
    ],
)
def test_receipt_status_top_frame_oog_between_successful_txs(
    fork: Fork,
    pre: Alloc,
    blockchain_test: BlockchainTestFiller,
    failure_mode: TopFrameFailureMode,
) -> None:
    """
    Pin the failed receipt status of a top-frame OOG transaction that
    sits between two successful transactions in one block.

    A transaction that out-of-gases on a top-frame charge never
    dispatches into the EVM but is still included and must produce a
    ``succeeded=False`` receipt, committed to the header
    ``receiptsRoot``. The other top-frame OOG tests place the failing
    transaction alone in its block, so an implementation that derives
    the receipt status from stale shared per-block execution state
    still passes them: the stale value in a fresh block happens to be
    "failed". Sandwiching the failure between successful transactions
    makes the status byte load-bearing. (Regression: nimbus-eth1
    ``1f8dd2122`` receipted top-frame failures with the previous
    transaction's status and rejected finalized canonical blocks on
    glamsterdam-devnet-7 with ``receiptRoot mismatch``.)

    The middle transaction passes the intrinsic check but out-of-gases
    on a top-frame charge before any EVM bytecode runs:

    - ``create_state_oog``: contract creation; the created account's
      ``NEW_ACCOUNT`` state charge fires at the top frame and the gas
      limit is one short of covering it.
    - ``new_account_state_oog``: value transfer to an empty recipient;
      the ``NEW_ACCOUNT`` state charge fires and the gas limit is one
      short.
    - ``delegated_execution_oog``: recipient holds an EIP-7702
      delegation; the ``COLD_ACCOUNT_ACCESS`` execution charge fires and
      the gas limit is one short.

    The failing transaction burns its full gas limit, bumps the sender
    nonce, and must produce a ``succeeded=False`` receipt between two
    ``succeeded=True`` receipts.
    """
    gas_price = 1_000_000_000
    value = 1

    sender_initial_balance = 10**18
    ok_sender_1 = pre.fund_eoa(sender_initial_balance)
    ok_sender_2 = pre.fund_eoa(sender_initial_balance)
    fail_sender = pre.fund_eoa(sender_initial_balance)
    # Alive via balance, so the successful transfers to it incur no
    # top-frame charge and consume exactly their intrinsic gas.
    ok_recipient = pre.fund_eoa(amount=1)

    intrinsic_cost = fork.transaction_intrinsic_cost_calculator()

    fail_target: Address | None = None
    fail_target_post: Account | None = None
    if failure_mode is TopFrameFailureMode.CREATE_STATE_OOG:
        intrinsic_gas = intrinsic_cost(
            contract_creation=True,
            return_cost_deducted_prior_execution=True,
        )
        top_frame_state_gas = fork.transaction_top_frame_state_gas(
            contract_creation=True,
        )
        assert top_frame_state_gas > 0, (
            "contract creation must charge NEW_ACCOUNT at the top frame"
        )
        fail_gas_limit = intrinsic_gas + top_frame_state_gas - 1
        fail_to: Address | None = None
    elif failure_mode is TopFrameFailureMode.NEW_ACCOUNT_STATE_OOG:
        intrinsic_gas = intrinsic_cost(
            sends_value=True,
            recipient_type=RecipientType.EMPTY_ACCOUNT,
            return_cost_deducted_prior_execution=True,
        )
        top_frame_state_gas = fork.transaction_top_frame_state_gas(
            sends_value=True,
            recipient_type=RecipientType.EMPTY_ACCOUNT,
        )
        assert top_frame_state_gas > 0, (
            "value transfer to an empty recipient must charge "
            "NEW_ACCOUNT at the top frame"
        )
        fail_gas_limit = intrinsic_gas + top_frame_state_gas - 1
        fail_to = pre.fund_eoa(amount=0)
        fail_target = fail_to
        # The rolled-back transfer must not bring the recipient into
        # existence.
        fail_target_post = None
    elif failure_mode is TopFrameFailureMode.DELEGATED_EXECUTION_OOG:
        delegated_to = pre.deploy_contract(code=Op.STOP)
        target_code = Spec7702.delegation_designation(delegated_to)
        fail_to = pre.deploy_contract(code=target_code)
        intrinsic_gas = intrinsic_cost(
            recipient_type=RecipientType.DELEGATION_7702,
            return_cost_deducted_prior_execution=True,
        )
        top_frame_gas = fork.transaction_top_frame_gas_calculator()(
            recipient_type=RecipientType.DELEGATION_7702,
        )
        assert top_frame_gas > 0, (
            "a delegated recipient must charge COLD_ACCOUNT_ACCESS "
            "at the top frame"
        )
        fail_gas_limit = intrinsic_gas + top_frame_gas - 1
        fail_target = fail_to
        fail_target_post = Account(balance=0, code=target_code)
    else:
        raise ValueError(f"unhandled failure mode: {failure_mode}")

    # The successful transfers go to an alive EOA: no top-frame charge,
    # no EVM execution, so each consumes exactly its intrinsic gas.
    ok_intrinsic_gas = intrinsic_cost(
        sends_value=True,
        recipient_type=RecipientType.EOA,
        return_cost_deducted_prior_execution=True,
    )
    assert (
        fork.transaction_top_frame_state_gas(
            sends_value=True,
            recipient_type=RecipientType.EOA,
        )
        == 0
    ), "an alive recipient must not incur a top-frame state charge"

    ok_tx_1 = Transaction(
        sender=ok_sender_1,
        to=ok_recipient,
        value=value,
        gas_limit=ok_intrinsic_gas,
        gas_price=gas_price,
        expected_receipt=TransactionReceipt(
            status=1,
            cumulative_gas_used=ok_intrinsic_gas,
        ),
    )
    fail_tx = Transaction(
        sender=fail_sender,
        to=fail_to,
        value=(
            value
            if failure_mode is TopFrameFailureMode.NEW_ACCOUNT_STATE_OOG
            else 0
        ),
        gas_limit=fail_gas_limit,
        gas_price=gas_price,
        expected_receipt=TransactionReceipt(
            status=0,
            gas_used=fail_gas_limit,
            cumulative_gas_used=ok_intrinsic_gas + fail_gas_limit,
        ),
    )
    ok_tx_2 = Transaction(
        sender=ok_sender_2,
        to=ok_recipient,
        value=value,
        gas_limit=ok_intrinsic_gas,
        gas_price=gas_price,
        expected_receipt=TransactionReceipt(
            status=1,
            cumulative_gas_used=2 * ok_intrinsic_gas + fail_gas_limit,
        ),
    )

    ok_sender_final_balance = (
        sender_initial_balance - value - ok_intrinsic_gas * gas_price
    )
    post: dict[Address, Account | None] = {
        ok_sender_1: Account(nonce=1, balance=ok_sender_final_balance),
        ok_sender_2: Account(nonce=1, balance=ok_sender_final_balance),
        ok_recipient: Account(balance=1 + 2 * value),
        # The failing transaction is included: the nonce bumps and the
        # full gas limit is paid, but nothing else happens.
        fail_sender: Account(
            nonce=1,
            balance=sender_initial_balance - fail_gas_limit * gas_price,
        ),
    }
    if failure_mode is TopFrameFailureMode.CREATE_STATE_OOG:
        post[fail_tx.created_contract] = None
    else:
        assert fail_target is not None
        post[fail_target] = fail_target_post

    blockchain_test(
        pre=pre,
        blocks=[Block(txs=[ok_tx_1, fail_tx, ok_tx_2])],
        post=post,
    )
