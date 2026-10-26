"""
State gas tests for EVM calls inside a frame of
[EIP-8141: Frame Transaction](https://eips.ethereum.org/EIPS/eip-8141).

A frame's `state_gas_left` is one pool for every call depth: a call
forwards none of it, a child's state charge draws from it directly, and
a failed child returns what it and its call charged. A `CALL` carrying
value to an account that does not exist charges the account creation
before the call checks the caller's balance, while a value-carrying
frame checks the balance first. `GAS` and the `SSTORE` stipend check
see the execution pool alone.
"""

import pytest
from execution_testing import (
    Account,
    Address,
    Alloc,
    Bytecode,
    Fork,
    Op,
    StateTestFiller,
)
from execution_testing.base_types import StorageRootType

from .helpers import (
    CANARY,
    FrameTransaction,
    Outcome,
    account_creation_cost,
    default_frame,
    overwrite,
    record_pool,
    sender_frame,
    sponsored_signatures,
    storage_set_cost,
    verify_frame,
)
from .spec import Spec, ref_spec_8141

REFERENCE_SPEC_GIT_PATH = ref_spec_8141.git_path
REFERENCE_SPEC_VERSION = ref_spec_8141.version

pytestmark = pytest.mark.valid_from("Bogota")

SLOT_RESULT = 0x01
"""
Caller slot recording a call's result plus one, so a failed call's zero
is distinguishable from a slot never written.
"""

SLOT_POOL = 0x02
"""
Caller slot recording the frame's remaining state gas pool plus one, so
an empty pool is distinguishable from a slot never written.
"""

SLOT_CHILD = 0x05
"""Fresh slot a child call writes, creating storage."""

SLOT_PARENT = 0x09
"""Fresh slot a parent writes after its child returns."""

CANARIES: StorageRootType = {SLOT_RESULT: CANARY, SLOT_POOL: CANARY}
"""Pre-state storage of a recording caller."""

CHILD_GAS = 30_000
"""Execution gas a parent forwards to its child."""

ECRECOVER = Address(0x01)
"""A precompile that holds no balance and fails on a call's stipend."""

SHA256 = Address(0x02)
"""A precompile that holds no balance and accepts empty input."""


def recorder(call: Bytecode) -> Bytecode:
    """
    Return code recording `call`'s result and then the remaining pool,
    each plus one, over the canaries.
    """
    return (
        overwrite(SLOT_RESULT, Op.ADD(1, call))
        + record_pool(SLOT_POOL)
        + Op.STOP
    )


@pytest.mark.parametrize(
    "state_gas_limit_delta",
    [
        pytest.param(0, id="exact_budget"),
        pytest.param(-1, id="one_below"),
    ],
)
def test_call_value_to_new_account(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    state_gas_limit_delta: int,
) -> None:
    """
    Charge the account creation of a `CALL` sending value to an absent
    account to the executing frame's pool.

    EIP-8141 "Charge points follow EIP-8037 unchanged. ... the
    conditional account-creation charge of the `CALL*` and
    `CREATE`/`CREATE2` families in the creating frame", and "A charge
    exceeding its remaining pool is an exceptional halt of the current
    callframe, with ordinary out-of-gas semantics."

    The caller holds one wei and sends it to an absent account. With a
    budget of exactly the account creation the call succeeds, the
    recorded pool is empty and the receipt reports the creation. One
    unit below, the charge halts the frame: its receipt reports its
    whole execution budget and no state gas, the canaries stay, and the
    wei stays with the caller.
    """
    sender = pre.fund_eoa()
    fresh = pre.nonexistent_account()
    code = recorder(
        Op.CALL(
            gas=0,
            address=fresh,
            value=1,
            value_transfer=True,
            account_new=True,
        )
    )
    assert code.state_cost(fork) == account_creation_cost(fork)
    caller = pre.deploy_contract(code=code, balance=1, storage=CANARIES)
    succeeds = state_gas_limit_delta >= 0

    tx = FrameTransaction.build(
        fork=fork,
        sender=sender,
        frames=[
            verify_frame(),
            default_frame(
                target=caller,
                code=code,
                # The empty account spends none of the call's stipend,
                # which returns to the caller.
                execution_gas=code.execution_cost(fork)
                - fork.gas_costs().CALL_STIPEND,
                state_gas_limit_delta=state_gas_limit_delta,
                outcome=Outcome.SUCCESS if succeeds else Outcome.HALT,
            ),
        ],
    )

    state_test(
        pre=pre,
        tx=tx,
        post={
            sender: Account(nonce=1),
            caller: (
                Account(balance=0, storage={SLOT_RESULT: 2, SLOT_POOL: 1})
                if succeeds
                else Account(balance=1, storage=CANARIES)
            ),
            fresh: Account(balance=1) if succeeds else Account.NONEXISTENT,
        },
    )


def test_call_value_charge_precedes_balance_check(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    Halt a frame on the account-creation charge of a `CALL` whose caller
    cannot even pay the value.

    EIP-8141 "Charge points follow EIP-8037 unchanged", and EIP-8037
    (`CALL*` family): the charge "is applied *conditionally* right
    before entering the child frame ... If the operation is
    unsuccessful before entering the call frame (e.g., due to
    insufficient balance ...), the charged state-gas is refilled". The
    charge is taken before the balance check that makes the call fail.

    The caller holds no balance and sends one wei to an absent account,
    in a frame with an empty state pool. The charge fails first and
    halts the frame, so the canaries stay. A client that checks the
    balance first returns zero from the call and lets the frame record
    it; contrast `test_frame_value_balance_check_precedes_account_charge`,
    where a frame's own value is checked first.
    """
    sender = pre.fund_eoa()
    fresh = pre.nonexistent_account()
    code = recorder(
        Op.CALL(
            gas=0,
            address=fresh,
            value=1,
            value_transfer=True,
            account_new=True,
        )
    )
    caller = pre.deploy_contract(code=code, balance=0, storage=CANARIES)

    tx = FrameTransaction.build(
        fork=fork,
        sender=sender,
        frames=[
            verify_frame(),
            default_frame(
                target=caller,
                code=code,
                state_gas_limit=0,
                outcome=Outcome.HALT,
            ),
        ],
    )

    state_test(
        pre=pre,
        tx=tx,
        post={
            sender: Account(nonce=1),
            caller: Account(balance=0, storage=CANARIES),
            fresh: Account.NONEXISTENT,
        },
    )


def test_callcode_value_charges_no_account(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    Charge no account creation to a `CALLCODE` sending value, whatever
    its code address.

    EIP-8141 "Charge points follow EIP-8037 unchanged", and EIP-8037
    charges a `CALL*` "only when the target account does not exist and
    a positive value is transferred". A `CALLCODE` transfers its value
    to the caller itself, which exists, so it never charges.

    The caller holds no balance and `CALLCODE`s an absent address with
    one wei, in a frame with an empty state pool. The call fails on the
    balance alone and returns zero; the frame records that and its
    untouched pool and succeeds with zero state gas.
    """
    sender = pre.fund_eoa()
    fresh = pre.nonexistent_account()
    code = recorder(
        Op.CALLCODE(gas=0, address=fresh, value=1, value_transfer=True)
    )
    assert code.state_cost(fork) == 0
    caller = pre.deploy_contract(code=code, balance=0, storage=CANARIES)

    tx = FrameTransaction.build(
        fork=fork,
        sender=sender,
        frames=[
            verify_frame(),
            default_frame(
                target=caller,
                code=code,
                # The failed balance check hands the call's stipend
                # straight back to the caller.
                execution_gas=code.execution_cost(fork)
                - fork.gas_costs().CALL_STIPEND,
                state_gas_limit=0,
            ),
        ],
    )

    state_test(
        pre=pre,
        tx=tx,
        post={
            sender: Account(nonce=1),
            caller: Account(storage={SLOT_RESULT: 1, SLOT_POOL: 1}),
            fresh: Account.NONEXISTENT,
        },
    )


@pytest.mark.parametrize(
    "state_gas_limit_delta",
    [
        pytest.param(0, id="exact_budget"),
        pytest.param(-1, id="one_below"),
    ],
)
def test_call_value_child_failure_refills_account_charge(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    state_gas_limit_delta: int,
) -> None:
    """
    Refill the account creation of a `CALL` whose child fails.

    EIP-8141 "When an EVM call frame reverts or halts exceptionally,
    restore the state-gas journal and the active frame's
    `state_gas_left` to the checkpoint covering that call and any
    associated pre-call state charge", and EIP-8037: "if the child
    frame reverts or halts exceptionally, the charged state-gas is
    refilled".

    The caller sends one wei to the `ecrecover` precompile, which holds
    no balance and so does not exist, forwarding no gas: the precompile
    costs more than the call's stipend and fails. With a budget of
    exactly the account creation, the charge is taken, the child fails,
    and the charge comes back: the call returns zero, the recorded pool
    is the whole budget, and the receipt reports no state gas. One unit
    below, the charge itself halts the frame, which shows the call was
    charged at all.
    """
    gas_costs = fork.gas_costs()
    assert gas_costs.PRECOMPILE_ECRECOVER > gas_costs.CALL_STIPEND
    sender = pre.fund_eoa()
    code = recorder(
        Op.CALL(
            gas=0,
            address=ECRECOVER,
            value=1,
            # The precompiles seed the warm set.
            address_warm=True,
            value_transfer=True,
            account_new=True,
        )
    )
    account_creation = account_creation_cost(fork)
    caller = pre.deploy_contract(code=code, balance=1, storage=CANARIES)
    succeeds = state_gas_limit_delta >= 0

    tx = FrameTransaction.build(
        fork=fork,
        sender=sender,
        frames=[
            verify_frame(),
            default_frame(
                target=caller,
                code=code,
                state_gas_limit=account_creation + state_gas_limit_delta,
                state_gas_used=0,
                outcome=Outcome.SUCCESS if succeeds else Outcome.HALT,
            ),
        ],
    )

    state_test(
        pre=pre,
        tx=tx,
        post={
            sender: Account(nonce=1),
            caller: Account(
                balance=1,
                storage=(
                    {SLOT_RESULT: 1, SLOT_POOL: account_creation + 1}
                    if succeeds
                    else CANARIES
                ),
            ),
            ECRECOVER: Account.NONEXISTENT,
        },
    )


def test_frame_value_balance_check_precedes_account_charge(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    Revert a frame whose value exceeds the sender's balance before its
    absent target's account creation is charged.

    EIP-8141 "Behavior": "if the caller does not have sufficient
    balance to transfer `frame.value`, the frame reverts, consuming the
    gas charged so far", and "If `frame.value > 0` and
    `resolved_target` does not exist, `STATE_BYTES_PER_NEW_ACCOUNT *
    CPSB` state gas is charged after the balance check".

    A sponsor pays, and the sender holds one wei less than the value
    its `SENDER` frame sends to an absent target, with an empty state
    pool. The balance check fails first: the frame reverts, its receipt
    reports only the target's cold access, and no state gas. A client
    charging the account creation first halts the frame on its empty
    pool, reporting its whole execution budget instead; contrast
    `test_call_value_charge_precedes_balance_check`.
    """
    value = 2
    sender = pre.fund_eoa(amount=value - 1)
    payer = pre.fund_eoa()
    fresh = pre.nonexistent_account()

    tx = FrameTransaction.build(
        fork=fork,
        sender=sender,
        payer=payer,
        frames=[
            verify_frame(flags=Spec.APPROVE_EXECUTION),
            verify_frame(flags=Spec.APPROVE_PAYMENT, target=payer),
            sender_frame(
                target=fresh,
                value=value,
                state_gas_limit=0,
                outcome=Outcome.REVERT,
            ),
        ],
        signatures=sponsored_signatures(sender, payer),
    )

    state_test(
        pre=pre,
        tx=tx,
        post={
            sender: Account(nonce=1, balance=value - 1),
            fresh: Account.NONEXISTENT,
        },
    )


@pytest.mark.parametrize(
    "state_gas_limit_delta",
    [
        pytest.param(0, id="exact_budget"),
        pytest.param(-1, id="one_below"),
    ],
)
def test_frame_value_to_precompile_charges_account(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    state_gas_limit_delta: int,
) -> None:
    """
    Charge the account creation of a frame sending value to a precompile
    that holds no balance, then dispatch the precompile.

    EIP-8141 "Behavior": "If `frame.value > 0` and `resolved_target`
    does not exist, `STATE_BYTES_PER_NEW_ACCOUNT * CPSB` state gas is
    charged after the balance check and before the frame's code
    executes", then "If `resolved_target` is an active precompile at
    the current fork, the frame dispatches it as an ordinary call
    would." A precompile without balance, nonce or code has no account
    (EIP-8037: "an account is *existent* if it already has a leaf in
    the state trie").

    The `SENDER` frame sends one wei to the `sha256` precompile with
    empty input. With a budget of exactly the account creation the
    frame succeeds, runs the precompile, and the precompile holds the
    wei. One unit below, the frame halts before the precompile runs and
    the precompile stays absent.
    """
    sender = pre.fund_eoa()
    gas_costs = fork.gas_costs()
    succeeds = state_gas_limit_delta >= 0

    tx = FrameTransaction.build(
        fork=fork,
        sender=sender,
        frames=[
            verify_frame(),
            sender_frame(
                target=SHA256,
                value=1,
                # The precompiles seed the warm set.
                warm=True,
                # An empty input hashes no words.
                execution_gas=gas_costs.PRECOMPILE_SHA256_BASE,
                state_gas_limit=account_creation_cost(fork)
                + state_gas_limit_delta,
                state_gas_used=account_creation_cost(fork) if succeeds else 0,
                outcome=Outcome.SUCCESS if succeeds else Outcome.HALT,
            ),
        ],
    )

    state_test(
        pre=pre,
        tx=tx,
        post={
            sender: Account(nonce=1),
            SHA256: Account(balance=1) if succeeds else Account.NONEXISTENT,
        },
    )


def test_subcall_draws_frame_pool(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    Pay a child call's storage creation from the whole frame pool.

    EIP-8141 "Frame gas pools": "`state_gas_left` is frame-scoped. EVM
    call frames at any depth within the frame draw from it directly. It
    is not forwarded, split, or divided per callframe like execution
    gas."

    The frame's budget is exactly one storage write. The parent
    forwards the child a small execution grant, and the child creates a
    slot from the frame pool. The parent then records the pool as
    empty, and the receipt reports the write. A client handing the
    child 63/64 of the pool halts the child, and the parent records the
    whole budget.
    """
    sender = pre.fund_eoa()
    child_code = Op.SSTORE(SLOT_CHILD, 1) + Op.STOP
    child = pre.deploy_contract(code=child_code)
    parent_code = (
        Op.POP(Op.CALL(gas=CHILD_GAS, address=child))
        + record_pool(SLOT_POOL)
        + Op.STOP
    )
    parent = pre.deploy_contract(code=parent_code, storage=CANARIES)
    storage_set = storage_set_cost(fork)

    tx = FrameTransaction.build(
        fork=fork,
        sender=sender,
        frames=[
            verify_frame(),
            default_frame(
                target=parent,
                execution_gas=parent_code.execution_cost(fork)
                + child_code.execution_cost(fork),
                state_gas_limit=storage_set,
                state_gas_used=storage_set,
            ),
        ],
    )

    state_test(
        pre=pre,
        tx=tx,
        post={
            sender: Account(nonce=1),
            child: Account(storage={SLOT_CHILD: 1}),
            parent: Account(storage={SLOT_RESULT: CANARY, SLOT_POOL: 1}),
        },
    )


def test_subcall_state_shortfall_halts_only_child(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    Halt only the child call whose storage creation the pool cannot pay.

    EIP-8141 "Frame gas pools": "A charge exceeding its remaining pool
    is an exceptional halt of the current callframe, with ordinary
    out-of-gas semantics." The current call frame is the child; the
    frame goes on.

    The frame's budget is one unit short of a storage write. The
    child's write halts it, consuming its whole execution grant, and
    the call returns zero to the parent, which records that and its
    untouched pool and succeeds. The receipt reports the parent's code
    plus the child's whole grant, and no state gas. A client halting
    the whole frame on the shortfall leaves both canaries in place.
    """
    sender = pre.fund_eoa()
    child_code = Op.SSTORE(SLOT_CHILD, 1) + Op.STOP
    child = pre.deploy_contract(code=child_code)
    parent_code = recorder(Op.CALL(gas=CHILD_GAS, address=child))
    parent = pre.deploy_contract(code=parent_code, storage=CANARIES)
    state_budget = storage_set_cost(fork) - 1

    tx = FrameTransaction.build(
        fork=fork,
        sender=sender,
        frames=[
            verify_frame(),
            default_frame(
                target=parent,
                execution_gas=parent_code.execution_cost(fork) + CHILD_GAS,
                state_gas_limit=state_budget,
                state_gas_used=0,
            ),
        ],
    )

    state_test(
        pre=pre,
        tx=tx,
        post={
            sender: Account(nonce=1),
            child: Account(storage={}),
            parent: Account(
                storage={SLOT_RESULT: 1, SLOT_POOL: state_budget + 1}
            ),
        },
    )


def test_reverted_subcall_returns_state_gas(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    Return a reverted child's storage creation to the frame pool, for
    the parent to spend.

    EIP-8141 "When an EVM call frame reverts or halts exceptionally,
    restore the state-gas journal and the active frame's
    `state_gas_left` to the checkpoint covering that call".

    The frame's budget is exactly one storage write. The child creates
    a slot and reverts; the parent then creates a slot of its own,
    which fits only because the child's charge came back, and records
    the pool as empty. The receipt reports one storage write.
    """
    sender = pre.fund_eoa()
    child_code = Op.SSTORE(SLOT_CHILD, 1) + Op.REVERT(0, 0)
    child = pre.deploy_contract(code=child_code)
    parent_code = (
        Op.POP(Op.CALL(gas=Op.GAS, address=child))
        + Op.SSTORE(SLOT_PARENT, 1)
        + record_pool(SLOT_POOL)
        + Op.STOP
    )
    parent = pre.deploy_contract(code=parent_code, storage=CANARIES)
    storage_set = storage_set_cost(fork)

    tx = FrameTransaction.build(
        fork=fork,
        sender=sender,
        frames=[
            verify_frame(),
            default_frame(
                target=parent,
                execution_gas=parent_code.execution_cost(fork)
                + child_code.execution_cost(fork),
                state_gas_limit=storage_set,
                state_gas_used=storage_set,
            ),
        ],
    )

    state_test(
        pre=pre,
        tx=tx,
        post={
            sender: Account(nonce=1),
            child: Account(storage={}),
            parent: Account(
                storage={
                    SLOT_RESULT: CANARY,
                    SLOT_POOL: 1,
                    SLOT_PARENT: 1,
                }
            ),
        },
    )


GAS_PROBE_LIMIT = 100_000
"""Execution budget of a frame whose code reads `GAS`."""

GAS_PROBE_STATE_LIMIT = 1_000_000
"""State budget of that frame, far above its execution budget."""


@pytest.mark.parametrize(
    "depth",
    [
        pytest.param(0, id="frame_top_level"),
        pytest.param(1, id="child_call"),
    ],
)
def test_gas_opcode_excludes_state_pool(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    depth: int,
) -> None:
    """
    Report through `GAS` the current call frame's execution gas only.

    EIP-8141 "Frame gas pools": "The `GAS` instruction returns the
    current callframe's `gas_left` and never observes
    `state_gas_left`."

    `GAS` is the first instruction run, at the frame's top level or as
    the first instruction of a child granted `CHILD_GAS`, and its value
    overwrites a canary. It reads the execution budget less the frame's
    entry access, or the child's grant, each less `GAS`'s own cost,
    with a state pool ten times the execution budget left out.
    """
    sender = pre.fund_eoa()
    record_gas = overwrite(SLOT_RESULT, Op.GAS) + Op.STOP
    gas_cost = fork.gas_costs().BASE
    entry = fork.frame_entry_gas_calculator()(target_warm=False)
    if depth == 0:
        target = pre.deploy_contract(code=record_gas, storage=CANARIES)
        recorder_account = target
        execution_gas = record_gas.execution_cost(fork)
        expected = GAS_PROBE_LIMIT - entry - gas_cost
    else:
        recorder_account = pre.deploy_contract(
            code=record_gas, storage=CANARIES
        )
        parent_code = (
            Op.POP(Op.CALL(gas=CHILD_GAS, address=recorder_account)) + Op.STOP
        )
        target = pre.deploy_contract(code=parent_code)
        execution_gas = parent_code.execution_cost(
            fork
        ) + record_gas.execution_cost(fork)
        expected = CHILD_GAS - gas_cost

    tx = FrameTransaction.build(
        fork=fork,
        sender=sender,
        frames=[
            verify_frame(),
            default_frame(
                target=target,
                execution_gas=execution_gas,
                gas_limit=GAS_PROBE_LIMIT,
                state_gas_limit=GAS_PROBE_STATE_LIMIT,
                state_gas_used=0,
            ),
        ],
    )

    state_test(
        pre=pre,
        tx=tx,
        post={
            sender: Account(nonce=1),
            recorder_account: Account(
                storage={SLOT_RESULT: expected, SLOT_POOL: CANARY}
            ),
        },
    )


@pytest.mark.parametrize(
    "stipend_margin",
    [
        pytest.param(0, id="gas_left_at_stipend"),
        pytest.param(1, id="gas_left_above_stipend"),
    ],
)
def test_sstore_stipend_check_ignores_state_pool(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    stipend_margin: int,
) -> None:
    """
    Halt an `SSTORE` run with no more execution gas than the call
    stipend, however large the state pool.

    EIP-8141 "Frame gas pools": "The `GAS_CALL_STIPEND` pre-state check
    of EIP-8037 applies to `gas_left` only."

    The frame's target rewrites a slot with its current value, a write
    that creates nothing and costs less than the stipend, with a state
    pool of a million. When the write starts with exactly the stipend
    of execution gas left, the check fails and the frame halts,
    consuming its whole budget. One gas more and the write succeeds,
    the frame reporting only what it spent. A client counting the state
    pool toward the check lets the first case write.
    """
    sender = pre.fund_eoa()
    pushes = Op.PUSH1[1] + Op.PUSH1[1]
    code = (
        Op.SSTORE(
            1,
            1,
            key_warm=False,
            original_value=1,
            current_value=1,
            new_value=1,
        )
        + Op.STOP
    )
    target = pre.deploy_contract(code=code, storage={1: 1})
    entry = fork.frame_entry_gas_calculator()(target_warm=False)
    succeeds = stipend_margin > 0

    tx = FrameTransaction.build(
        fork=fork,
        sender=sender,
        frames=[
            verify_frame(),
            default_frame(
                target=target,
                code=code,
                gas_limit=entry
                + pushes.execution_cost(fork)
                + fork.gas_costs().CALL_STIPEND
                + stipend_margin,
                state_gas_limit=GAS_PROBE_STATE_LIMIT,
                outcome=Outcome.SUCCESS if succeeds else Outcome.HALT,
            ),
        ],
    )

    state_test(
        pre=pre,
        tx=tx,
        post={
            sender: Account(nonce=1),
            target: Account(storage={1: 1}),
        },
    )
