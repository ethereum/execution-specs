"""
State gas pool tests for
[EIP-8141: Frame Transaction](https://eips.ethereum.org/EIPS/eip-8141).

Each frame's state gas pool is seeded from its declared budget and
shared by every call depth within the frame. An `SSTORE` returning a
slot created earlier in the transaction to its transaction-start value
refills the charge to the frame that paid it: the executing frame's
pool when the owner is still executing, the owner's receipt otherwise.
A charge exceeding the pool halts exceptionally, and `APPROVE` charges
the sender's account creation to the approving frame's pool.

Calls inside a frame forward none of the pool: a child's state charge
draws on it directly, a charge the pool cannot cover halts only the
current call, and a failed call returns what it and its pre-call charge
took. A `CALL` carrying value to an absent account charges the account
creation before checking the caller's balance, while a frame carrying
value checks the balance first. `GAS` and the `SSTORE` stipend check
see the execution pool alone.
"""

from typing import Any, Dict, List, Tuple

import pytest
from execution_testing import (
    DEFAULT_FRAME_STATE_GAS_LIMIT,
    EOA,
    Account,
    Address,
    Alloc,
    Bytecode,
    Bytes,
    Conditional,
    Environment,
    Fork,
    FrameSignature,
    Op,
    StateTestFiller,
    Transaction,
    TransactionException,
)
from execution_testing.base_types import StorageRootType

from .helpers import (
    CANARY,
    FrameCase,
    FrameTransaction,
    Outcome,
    default_frame,
    overwrite,
    record_pool,
    sender_frame,
    sponsored_signatures,
    verify_frame,
)
from .spec import Spec, ref_spec_8141

REFERENCE_SPEC_GIT_PATH = ref_spec_8141.git_path
REFERENCE_SPEC_VERSION = ref_spec_8141.version

pytestmark = pytest.mark.valid_from("Bogota")

SLOT_CREATED = 0x01
"""Storage slot created — and possibly cleared again — under test."""

SLOT_USED_BEFORE = 0x02
"""Slot recording the owner frame's attributed state gas pre-refill."""

SLOT_USED_AFTER = 0x03
"""Slot recording the owner frame's attributed state gas post-refill."""

SLOT_POOL = 0x04
"""Slot recording the executing frame's remaining state gas pool."""

SLOT_OWNER_USED = 0x06
"""Probe slot recording the creating frame's attributed state gas."""

SLOT_EDITOR_USED = 0x07
"""
Probe slot recording the refilling frame's attributed state gas, plus
one so the expected zero readback is distinguishable from a slot never
written.
"""

SLOT_STATUS = 0x08
"""
Probe slot recording a frame's receipt status, plus one so the
expected `FAILURE` readback is distinguishable from a slot never
written.
"""

SLOT_SECOND = 0x09
"""Second storage slot a frame creates from its own state gas pool."""

SLOT_RESULT = 0x01
"""
Caller slot recording a call's result plus one, so a failed call's zero
is distinguishable from a slot never written.
"""

SLOT_POOL_PLUS_ONE = 0x02
"""
Caller slot recording the frame's remaining state gas pool plus one, so
an empty pool is distinguishable from a slot never written.
"""

SLOT_CHILD = 0x05
"""Fresh slot a child call writes, creating storage."""

CANARIES: StorageRootType = {SLOT_RESULT: CANARY, SLOT_POOL_PLUS_ONE: CANARY}
"""Pre-state storage of a recording caller."""

CHILD_GAS = 30_000
"""Execution gas a parent forwards to its child."""

ECRECOVER = Address(0x01)
"""A precompile that holds no balance and fails on a call's stipend."""

SHA256 = Address(0x02)
"""A precompile that holds no balance and accepts empty input."""

SPENT_SENDER_BALANCE = 10**15
"""Balance a sender transfers away before its payment is approved."""

GAS_PROBE_LIMIT = 100_000
"""Execution budget of a frame whose code reads `GAS`."""

GAS_PROBE_STATE_LIMIT = 1_000_000
"""State budget of that frame, far above its execution budget."""

UNFUNDED_SENDERS = pytest.mark.parametrize(
    "sender_state",
    [
        pytest.param("absent", id="sender_absent"),
        pytest.param("emptied", id="sender_emptied_by_earlier_frame"),
    ],
)
"""
The two ways a sender has no account when its payment is approved:
none in the pre-state, or one an earlier frame spent down to empty —
present in the state but empty, so `APPROVE` still creates it.
"""


def unfunded_sender(
    pre: Alloc, sender_state: str
) -> Tuple[EOA, List[FrameCase], Address | None]:
    """
    Return the sender, the frames that run between its execution and
    payment approvals, and the account those frames pay, if any.
    """
    if sender_state == "absent":
        return pre.fund_eoa(amount=0), [], None
    elif sender_state == "emptied":
        sender = pre.fund_eoa(amount=SPENT_SENDER_BALANCE)
        recipient = pre.fund_eoa(amount=1)
        spend = sender_frame(target=recipient, value=SPENT_SENDER_BALANCE)
        return sender, [spend], recipient
    else:
        raise ValueError(f"unknown sender state: {sender_state}")


def recorder(call: Bytecode) -> Bytecode:
    """
    Return code recording `call`'s result and then the remaining pool,
    each plus one, over the canaries.
    """
    return (
        overwrite(SLOT_RESULT, Op.ADD(1, call))
        + record_pool(SLOT_POOL_PLUS_ONE)
        + Op.STOP
    )


def test_same_frame_refill(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    Refill a state charge within the frame that paid it.

    The frame creates a slot, clears it back to its transaction-start
    value, and then records its pool: the refill credits the pool, so
    the recording — itself a fresh write — reads the full budget back,
    and the frame's receipt attributes only the recording's charge.
    """
    sender = pre.fund_eoa()
    create = Op.SSTORE(SLOT_CREATED, 1)
    clear = Op.SSTORE(
        SLOT_CREATED,
        0,
        key_warm=True,
        original_value=0,
        current_value=1,
        new_value=0,
    )
    observe_pool = Op.SSTORE(
        SLOT_POOL, Op.TXPARAM(Spec.TXPARAM_STATE_GAS_LEFT)
    )
    worker_code = create + clear + observe_pool + Op.STOP
    worker = pre.deploy_contract(code=worker_code)

    tx = FrameTransaction.build(
        fork=fork,
        sender=sender,
        # The clearing write refunds execution gas this test does not
        # price, so the transaction total is left unpinned.
        settle=False,
        frames=[
            verify_frame(),
            default_frame(
                target=worker,
                code=worker_code,
                state_gas_used=observe_pool.state_cost(fork),
            ),
        ],
    )

    state_test(
        pre=pre,
        tx=tx,
        post={
            sender: Account(nonce=1),
            worker: Account(
                storage={
                    SLOT_CREATED: 0,
                    SLOT_POOL: DEFAULT_FRAME_STATE_GAS_LIMIT,
                }
            ),
        },
    )


def test_cross_frame_refill(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    Refill a state charge from a later frame than the one that paid it.

    A first frame creates a slot; a second frame clears it back to its
    transaction-start value. The refill lowers the owner frame's
    receipt — observed live through `FRAMEPARAM` before and after —
    and credits nothing to the executing frame's pool.
    """
    sender = pre.fund_eoa()
    fresh_write_state_cost = Op.SSTORE(SLOT_CREATED, 1).state_cost(fork)

    observe_before = Op.SSTORE(
        SLOT_USED_BEFORE,
        Op.FRAMEPARAM(1, Spec.FRAMEPARAM_STATE_GAS_USED),
    )
    refill = Op.SSTORE(
        SLOT_CREATED,
        0,
        key_warm=True,
        original_value=0,
        current_value=1,
        new_value=0,
    )
    # Recorded with one added, so the expected zero readback is
    # distinguishable from a slot never written.
    observe_after = Op.SSTORE(
        SLOT_USED_AFTER,
        Op.ADD(1, Op.FRAMEPARAM(1, Spec.FRAMEPARAM_STATE_GAS_USED)),
    )
    observe_pool = Op.SSTORE(
        SLOT_POOL, Op.TXPARAM(Spec.TXPARAM_STATE_GAS_LEFT)
    )
    worker_code = Conditional(
        condition=Op.ISZERO(Op.CALLDATALOAD(0)),
        if_true=Op.SSTORE(SLOT_CREATED, 1) + Op.STOP,
        if_false=observe_before
        + refill
        + observe_after
        + observe_pool
        + Op.STOP,
    )
    worker = pre.deploy_contract(code=worker_code)

    tx = FrameTransaction.build(
        fork=fork,
        sender=sender,
        frames=[
            verify_frame(),
            # The owner's attribution is gone: the refill returned its
            # charge at settlement.
            default_frame(
                target=worker,
                pin_gas=False,
                state_gas_used=0,
            ),
            # The refilling frame pays only for its three fresh
            # recording slots; the refill credits it nothing.
            default_frame(
                target=worker,
                data=b"\x01",
                pin_gas=False,
                state_gas_used=3 * fresh_write_state_cost,
            ),
        ],
    )

    state_test(
        pre=pre,
        tx=tx,
        post={
            sender: Account(nonce=1),
            worker: Account(
                storage={
                    SLOT_CREATED: 0,
                    SLOT_USED_BEFORE: fresh_write_state_cost,
                    SLOT_USED_AFTER: 1,
                    SLOT_POOL: DEFAULT_FRAME_STATE_GAS_LIMIT
                    - 2 * fresh_write_state_cost,
                }
            ),
        },
    )


@pytest.mark.parametrize(
    "state_gas_limit_delta",
    [
        pytest.param(0, id="exact_budget"),
        pytest.param(-1, id="one_below"),
    ],
)
def test_state_gas_exhaustion(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    state_gas_limit_delta: int,
) -> None:
    """
    Drive a frame's state gas budget across the exact cost of its one
    storage creation.

    The exact budget succeeds and consumes the whole pool; one unit
    below halts the frame exceptionally — the write is rolled back,
    the receipt reports the whole execution budget and zero state gas,
    and the transaction stays valid.
    """
    sender = pre.fund_eoa()
    worker_code = Op.SSTORE(SLOT_CREATED, 1) + Op.STOP
    worker = pre.deploy_contract(code=worker_code)

    succeeds = state_gas_limit_delta >= 0

    tx = FrameTransaction.build(
        fork=fork,
        sender=sender,
        frames=[
            verify_frame(),
            default_frame(
                target=worker,
                code=worker_code,
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
            worker: Account(storage={SLOT_CREATED: 1 if succeeds else 0}),
        },
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
    caller = pre.deploy_contract(code=code, balance=1, storage=CANARIES)
    if state_gas_limit_delta == 0:
        succeeds = True
    elif state_gas_limit_delta == -1:
        succeeds = False
    else:
        raise ValueError(
            f"unknown state_gas_limit_delta: {state_gas_limit_delta!r}"
        )

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
                - fork.call_value_stipend(),
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
                Account(
                    balance=0,
                    storage={SLOT_RESULT: 2, SLOT_POOL_PLUS_ONE: 1},
                )
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
                - fork.call_value_stipend(),
                state_gas_limit=0,
            ),
        ],
    )

    state_test(
        pre=pre,
        tx=tx,
        post={
            sender: Account(nonce=1),
            caller: Account(storage={SLOT_RESULT: 1, SLOT_POOL_PLUS_ONE: 1}),
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
    # The premise: the precompile costs more than the call's stipend.
    assert fork.gas_costs().PRECOMPILE_ECRECOVER > fork.call_value_stipend()
    sender = pre.fund_eoa()
    call = Op.CALL(
        gas=0,
        address=ECRECOVER,
        value=1,
        # The precompiles seed the warm set.
        address_warm=True,
        value_transfer=True,
        account_new=True,
    )
    code = recorder(call)
    account_creation = call.state_cost(fork)
    caller = pre.deploy_contract(code=code, balance=1, storage=CANARIES)
    if state_gas_limit_delta == 0:
        succeeds = True
    elif state_gas_limit_delta == -1:
        succeeds = False
    else:
        raise ValueError(
            f"unknown state_gas_limit_delta: {state_gas_limit_delta!r}"
        )

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
                    {SLOT_RESULT: 1, SLOT_POOL_PLUS_ONE: account_creation + 1}
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
    `resolved_target` does not exist", the new account's state gas "is
    charged after the balance check".

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
    does not exist", the new account's state gas "is charged after the
    balance check and before the frame's code executes", then "If
    `resolved_target` is an active precompile at the current fork, the
    frame dispatches it as an ordinary call would." A precompile
    without balance, nonce or code has no account (EIP-8037: "an
    account is *existent* if it already has a leaf in the state
    trie").

    The `SENDER` frame sends one wei to the `sha256` precompile with
    empty input. With a budget of exactly the account creation the
    frame succeeds, runs the precompile, and the precompile holds the
    wei. One unit below, the frame halts before the precompile runs and
    the precompile stays absent.
    """
    sender = pre.fund_eoa()
    # No opcode makes the charge: the frame entry charges the new
    # account's state gas for a value-bearing frame to a dead target.
    account_creation = fork.gas_costs().NEW_ACCOUNT
    if state_gas_limit_delta == 0:
        succeeds = True
    elif state_gas_limit_delta == -1:
        succeeds = False
    else:
        raise ValueError(
            f"unknown state_gas_limit_delta: {state_gas_limit_delta!r}"
        )

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
                # An empty input hashes no words; the framework does not
                # price precompiles, so the fork's base cost is read.
                execution_gas=fork.gas_costs().PRECOMPILE_SHA256_BASE,
                state_gas_limit=account_creation + state_gas_limit_delta,
                state_gas_used=account_creation if succeeds else 0,
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
        + record_pool(SLOT_POOL_PLUS_ONE)
        + Op.STOP
    )
    parent = pre.deploy_contract(code=parent_code, storage=CANARIES)
    storage_set = child_code.state_cost(fork)

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
            parent: Account(
                storage={SLOT_RESULT: CANARY, SLOT_POOL_PLUS_ONE: 1}
            ),
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
    state_budget = child_code.state_cost(fork) - 1

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
                storage={SLOT_RESULT: 1, SLOT_POOL_PLUS_ONE: state_budget + 1}
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
        + Op.SSTORE(SLOT_SECOND, 1)
        + record_pool(SLOT_POOL_PLUS_ONE)
        + Op.STOP
    )
    parent = pre.deploy_contract(code=parent_code, storage=CANARIES)
    # The parent's own write costs what the child's reverted one did.
    storage_set = parent_code.state_cost(fork)

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
                    SLOT_POOL_PLUS_ONE: 1,
                    SLOT_SECOND: 1,
                }
            ),
        },
    )


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
    gas_cost = Op.GAS.gas_cost(fork)
    entry = fork.frame_entry_gas_calculator()(target_warm=False)
    if depth == 0:
        target = pre.deploy_contract(code=record_gas, storage=CANARIES)
        recorder_account = target
        execution_gas = record_gas.execution_cost(fork)
        expected = GAS_PROBE_LIMIT - entry - gas_cost
    elif depth == 1:
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
    else:
        raise ValueError(f"unknown depth: {depth!r}")

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
                storage={SLOT_RESULT: expected, SLOT_POOL_PLUS_ONE: CANARY}
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
    pool of `GAS_PROBE_STATE_LIMIT`. When the write starts with exactly
    the stipend of execution gas left, the check fails and the frame
    halts, consuming its whole budget. One gas more and the write
    succeeds, the frame reporting only what it spent. A client counting
    the state pool toward the check lets the first case write.
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
    if stipend_margin == 0:
        succeeds = False
    elif stipend_margin == 1:
        succeeds = True
    else:
        raise ValueError(f"unknown stipend_margin: {stipend_margin!r}")
    # The premise: the write itself costs no more than the stipend, so
    # only the stipend check can halt the frame at exactly the stipend.
    assert (
        code.execution_cost(fork) - pushes.execution_cost(fork)
        <= fork.call_value_stipend()
    )

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
                + fork.call_value_stipend()
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


@UNFUNDED_SENDERS
def test_approve_creates_sender(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    sender_state: str,
) -> None:
    """
    Approve payment for a sender whose account does not exist.

    Incrementing the nonce creates the sender account, and `APPROVE`
    charges the account creation to the approving frame's state gas
    pool — here inside the payer's protocol default code, whose only
    execution charge is the payer's cold access at frame entry. The
    pool holds exactly the charge; the unaffordable test below is the
    same transaction one unit short.
    """
    sender, spend_frames, recipient = unfunded_sender(pre, sender_state)
    payer = pre.fund_eoa()
    sender_creation = fork.gas_costs().NEW_ACCOUNT

    tx = FrameTransaction.build(
        fork=fork,
        sender=sender,
        payer=payer,
        frames=[
            verify_frame(flags=Spec.APPROVE_EXECUTION),
            *spend_frames,
            verify_frame(
                flags=Spec.APPROVE_PAYMENT,
                target=payer,
                state_gas_limit=sender_creation,
                state_gas_used=sender_creation,
            ),
        ],
        signatures=[
            FrameSignature(scheme=Spec.SCHEME_SECP256K1, signer=Bytes(sender)),
            FrameSignature(
                scheme=Spec.SCHEME_SECP256K1,
                signer=Bytes(payer),
                secret_key=payer.key,
            ),
        ],
    )

    post: Dict[Address, Account] = {sender: Account(nonce=1, balance=0)}
    if recipient is not None:
        post[recipient] = Account(balance_change=SPENT_SENDER_BALANCE)
    state_test(pre=pre, tx=tx, post=post)


@UNFUNDED_SENDERS
@pytest.mark.exception_test
def test_approve_sender_creation_unaffordable(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    sender_state: str,
) -> None:
    """
    Reject a frame transaction whose payment approval cannot cover the
    sender's account creation.

    The approving `VERIFY` frame declares one unit of state gas less
    than the account creation, so the `APPROVE` inside the payer's
    protocol default code halts the frame exceptionally, with no
    approval effects — and a failing `VERIFY` frame invalidates the
    transaction.
    """
    sender, spend_frames, recipient = unfunded_sender(pre, sender_state)
    payer = pre.fund_eoa()

    tx = Transaction(
        sender=sender,
        frames=[
            verify_frame(flags=Spec.APPROVE_EXECUTION),
            *spend_frames,
            verify_frame(
                flags=Spec.APPROVE_PAYMENT,
                target=payer,
                state_gas_limit=fork.gas_costs().NEW_ACCOUNT - 1,
            ),
        ],
        signatures=[
            FrameSignature(scheme=Spec.SCHEME_SECP256K1, signer=Bytes(sender)),
            FrameSignature(
                scheme=Spec.SCHEME_SECP256K1,
                signer=Bytes(payer),
                secret_key=payer.key,
            ),
        ],
        error=TransactionException.TYPE_6_INVALID_FRAME_EXECUTION,
    )

    post: Dict[Address, Account] = {}
    if recipient is not None:
        post = {
            sender: Account(nonce_change=0, balance_change=0),
            recipient: Account(balance_change=0),
        }
    state_test(pre=pre, tx=tx, post=post)


def test_refill_after_intermediate_modification(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    Return a slot to its transaction-start value after an intermediate
    modification by another frame.

    The second frame's write changes an already-dirty slot: it charges
    no state gas and leaves the outstanding charge's owner untouched.
    The third frame's return to the transaction-start value therefore
    still refills the creating frame, although the third frame never
    observed the value that frame wrote.
    """
    sender = pre.fund_eoa()
    fresh_write_state_cost = Op.SSTORE(SLOT_CREATED, 1).state_cost(fork)

    modify = Op.SSTORE(
        SLOT_CREATED,
        2,
        key_warm=True,
        original_value=0,
        current_value=1,
        new_value=2,
    )
    clear = Op.SSTORE(
        SLOT_CREATED,
        0,
        key_warm=True,
        original_value=0,
        current_value=2,
        new_value=0,
    )
    observe_owner = Op.SSTORE(
        SLOT_USED_AFTER,
        Op.ADD(1, Op.FRAMEPARAM(1, Spec.FRAMEPARAM_STATE_GAS_USED)),
    )
    worker_code = Conditional(
        condition=Op.ISZERO(Op.CALLDATALOAD(0)),
        if_true=Op.SSTORE(SLOT_CREATED, 1) + Op.STOP,
        if_false=Conditional(
            condition=Op.EQ(Op.CALLDATALOAD(0), 1),
            if_true=modify + Op.STOP,
            if_false=clear + observe_owner + Op.STOP,
        ),
    )
    worker = pre.deploy_contract(code=worker_code)

    tx = FrameTransaction.build(
        fork=fork,
        sender=sender,
        frames=[
            # Frame 0: approve execution and payment.
            verify_frame(),
            # Frame 1: create the slot (0 -> 1). The creation's
            # attribution is gone: the third frame's refill returned it
            # at settlement.
            default_frame(
                target=worker,
                pin_gas=False,
                state_gas_used=0,
            ),
            # Frame 2: modify the dirty slot (1 -> 2), which charges no
            # state gas.
            default_frame(
                target=worker,
                data=(1).to_bytes(32, "big"),
                pin_gas=False,
                state_gas_used=0,
            ),
            # Frame 3: return the slot to its start value (2 -> 0) and
            # record frame 1's attribution. Only the recording write is
            # charged; the refill credits the owner, not this frame.
            default_frame(
                target=worker,
                data=(2).to_bytes(32, "big"),
                pin_gas=False,
                state_gas_used=fresh_write_state_cost,
            ),
        ],
    )

    state_test(
        pre=pre,
        tx=tx,
        post={
            sender: Account(nonce=1),
            worker: Account(storage={SLOT_CREATED: 0, SLOT_USED_AFTER: 1}),
        },
    )


def test_batch_unroll_restores_refilled_receipt(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    Unroll an atomic batch whose frame refilled a pre-batch receipt.

    A batch frame returns a slot created before the batch to its
    transaction-start value, lowering the creating frame's receipt.
    The batch's terminating frame reverts, and the unroll restores the
    receipt edit together with the state: a later frame reads the
    creating frame's full attribution back, while the unrolled frame's
    re-appended receipt keeps its status with its state gas zeroed.
    """
    sender = pre.fund_eoa()
    fresh_write_state_cost = Op.SSTORE(SLOT_CREATED, 1).state_cost(fork)

    modify = Op.SSTORE(
        SLOT_CREATED,
        2,
        key_warm=True,
        original_value=0,
        current_value=1,
        new_value=2,
    )
    clear = Op.SSTORE(
        SLOT_CREATED,
        0,
        key_warm=True,
        original_value=0,
        current_value=2,
        new_value=0,
    )
    worker_code = Conditional(
        condition=Op.ISZERO(Op.CALLDATALOAD(0)),
        if_true=Op.SSTORE(SLOT_CREATED, 1) + Op.STOP,
        if_false=Conditional(
            condition=Op.EQ(Op.CALLDATALOAD(0), 1),
            if_true=modify + Op.STOP,
            if_false=clear + Op.STOP,
        ),
    )
    worker = pre.deploy_contract(code=worker_code)
    reverter = pre.deploy_contract(code=Op.REVERT(0, 0))
    probe = pre.deploy_contract(
        code=Op.SSTORE(
            SLOT_OWNER_USED,
            Op.FRAMEPARAM(1, Spec.FRAMEPARAM_STATE_GAS_USED),
        )
        + Op.SSTORE(
            SLOT_EDITOR_USED,
            Op.ADD(1, Op.FRAMEPARAM(3, Spec.FRAMEPARAM_STATE_GAS_USED)),
        )
        + Op.SSTORE(
            SLOT_STATUS,
            Op.ADD(1, Op.FRAMEPARAM(4, Spec.FRAMEPARAM_STATUS)),
        )
        + Op.STOP
    )

    tx = FrameTransaction.build(
        fork=fork,
        sender=sender,
        frames=[
            # Frame 0: approve execution and payment.
            verify_frame(),
            # Frame 1: create the slot (0 -> 1). The unroll restored
            # the refill the batch frame applied to this receipt.
            default_frame(
                target=worker,
                pin_gas=False,
                state_gas_used=fresh_write_state_cost,
            ),
            # Frame 2: modify the dirty slot (1 -> 2).
            default_frame(
                target=worker,
                data=(1).to_bytes(32, "big"),
                pin_gas=False,
                state_gas_used=0,
            ),
            # Frame 3: open the batch and return the slot to its
            # start value (2 -> 0), refilling frame 1's receipt.
            default_frame(
                flags=Spec.ATOMIC_BATCH_FLAG,
                target=worker,
                data=(2).to_bytes(32, "big"),
                outcome=Outcome.UNROLLED,
                pin_gas=False,
            ),
            # Frame 4: terminate the batch with a revert, unrolling it.
            default_frame(
                target=reverter,
                outcome=Outcome.REVERT,
                pin_gas=False,
            ),
            # Frame 5: record frame 1's and frame 3's attributions and
            # frame 4's status after the unroll.
            default_frame(
                target=probe,
                pin_gas=False,
                state_gas_used=3 * fresh_write_state_cost,
            ),
        ],
    )

    state_test(
        pre=pre,
        tx=tx,
        post={
            sender: Account(nonce=1),
            # The unroll undid the batch frame's clearing write, so
            # the intermediate modification survives.
            worker: Account(storage={SLOT_CREATED: 2}),
            probe: Account(
                storage={
                    SLOT_OWNER_USED: fresh_write_state_cost,
                    SLOT_EDITOR_USED: 1,
                    SLOT_STATUS: 1,
                }
            ),
        },
    )


def test_frame_revert_restores_refilled_receipt(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    Revert a frame that refilled an earlier frame's receipt.

    A reverting frame's rollback extends over the edits it made to
    earlier receipts: the creating frame's attribution is restored,
    and the reverting frame's own receipt reports zero state gas.
    """
    sender = pre.fund_eoa()
    fresh_write_state_cost = Op.SSTORE(SLOT_CREATED, 1).state_cost(fork)

    clear = Op.SSTORE(
        SLOT_CREATED,
        0,
        key_warm=True,
        original_value=0,
        current_value=1,
        new_value=0,
    )
    worker_code = Conditional(
        condition=Op.ISZERO(Op.CALLDATALOAD(0)),
        if_true=Op.SSTORE(SLOT_CREATED, 1) + Op.STOP,
        if_false=clear + Op.REVERT(0, 0),
    )
    worker = pre.deploy_contract(code=worker_code)
    probe = pre.deploy_contract(
        code=Op.SSTORE(
            SLOT_OWNER_USED,
            Op.FRAMEPARAM(1, Spec.FRAMEPARAM_STATE_GAS_USED),
        )
        + Op.SSTORE(
            SLOT_EDITOR_USED,
            Op.ADD(1, Op.FRAMEPARAM(2, Spec.FRAMEPARAM_STATE_GAS_USED)),
        )
        + Op.SSTORE(
            SLOT_STATUS,
            Op.ADD(1, Op.FRAMEPARAM(2, Spec.FRAMEPARAM_STATUS)),
        )
        + Op.STOP
    )

    tx = FrameTransaction.build(
        fork=fork,
        sender=sender,
        frames=[
            # Frame 0: approve execution and payment.
            verify_frame(),
            # Frame 1: create the slot (0 -> 1). The revert restored
            # the refill the failing frame applied to this receipt.
            default_frame(
                target=worker,
                pin_gas=False,
                state_gas_used=fresh_write_state_cost,
            ),
            # Frame 2: return the slot to its start value (1 -> 0),
            # refilling frame 1's receipt, then revert.
            default_frame(
                target=worker,
                data=b"\x01",
                outcome=Outcome.REVERT,
                pin_gas=False,
            ),
            # Frame 3: record frame 1's and frame 2's attributions and
            # frame 2's status after the revert.
            default_frame(
                target=probe,
                pin_gas=False,
                state_gas_used=3 * fresh_write_state_cost,
            ),
        ],
    )

    state_test(
        pre=pre,
        tx=tx,
        post={
            sender: Account(nonce=1),
            # The revert undid the clearing write.
            worker: Account(storage={SLOT_CREATED: 1}),
            probe: Account(
                storage={
                    SLOT_OWNER_USED: fresh_write_state_cost,
                    SLOT_EDITOR_USED: 1,
                    SLOT_STATUS: 1,
                }
            ),
        },
    )


def test_call_revert_restores_refilled_receipt(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    Revert a call that refilled an earlier frame's receipt, inside a
    frame that succeeds.

    A call's rollback extends over the edits it made to earlier
    receipts, as a frame's does: the creating frame's attribution is
    restored. The refill never reached the executing frame's pool, so
    the rollback leaves that pool whole, and the frame can still create
    a slot from a budget of exactly one slot creation.
    """
    sender = pre.fund_eoa()
    fresh_write_state_cost = Op.SSTORE(SLOT_CREATED, 1).state_cost(fork)

    clear = Op.SSTORE(
        SLOT_CREATED,
        0,
        key_warm=True,
        original_value=0,
        current_value=1,
        new_value=0,
    )
    worker_code = Conditional(
        condition=Op.ISZERO(Op.CALLDATALOAD(0)),
        if_true=Op.SSTORE(SLOT_CREATED, 1) + Op.STOP,
        if_false=Conditional(
            condition=Op.EQ(Op.CALLDATALOAD(0), 1),
            # Call this contract to clear the slot and revert, then
            # create a second slot.
            if_true=Op.MSTORE(0, 2)
            + Op.POP(
                Op.CALL(
                    gas=Op.GAS,
                    address=Op.ADDRESS,
                    args_offset=0,
                    args_size=32,
                )
            )
            + Op.SSTORE(SLOT_SECOND, 1)
            + Op.STOP,
            if_false=clear + Op.REVERT(0, 0),
        ),
    )
    worker = pre.deploy_contract(code=worker_code)

    tx = FrameTransaction.build(
        fork=fork,
        sender=sender,
        frames=[
            # Frame 0: approve execution and payment.
            verify_frame(),
            # Frame 1: create the slot (0 -> 1). The call's revert
            # restored the refill it applied to this receipt.
            default_frame(
                target=worker,
                pin_gas=False,
                state_gas_used=fresh_write_state_cost,
            ),
            # Frame 2: a call returns the slot to its start value
            # (1 -> 0), refilling frame 1's receipt, and reverts; the
            # frame then creates a second slot from its own pool.
            default_frame(
                target=worker,
                state_gas_limit=fresh_write_state_cost,
                data=(1).to_bytes(32, "big"),
                pin_gas=False,
                state_gas_used=fresh_write_state_cost,
            ),
        ],
    )

    state_test(
        pre=pre,
        tx=tx,
        post={
            sender: Account(nonce=1),
            # The revert undid the clearing write.
            worker: Account(storage={SLOT_CREATED: 1, SLOT_SECOND: 1}),
        },
    )


@pytest.mark.parametrize(
    "reversion",
    ["reverted_call", "reverted_frame", "unrolled_batch"],
)
def test_reversion_restores_charge_ownership(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    reversion: str,
) -> None:
    """
    Restore a slot's charge ownership record that a reverted clearing
    write consumed.

    Returning a slot to its transaction-start value consumes the record
    of the frame that paid for its creation. When the clearing write is
    reverted, by its call, its frame or its atomic batch, the record
    comes back with it, so a later frame that clears the slot for good
    refills the frame that paid, not its own pool. That later frame
    then creates a second slot from a budget of exactly one slot
    creation, which its pool covers only if the refill went to the
    owner.
    """
    sender = pre.fund_eoa()
    fresh_write_state_cost = Op.SSTORE(SLOT_CREATED, 1).state_cost(fork)

    clear = Op.SSTORE(
        SLOT_CREATED,
        0,
        key_warm=True,
        original_value=0,
        current_value=1,
        new_value=0,
    )
    worker_code = Conditional(
        condition=Op.ISZERO(Op.CALLDATALOAD(0)),
        if_true=Op.SSTORE(SLOT_CREATED, 1) + Op.STOP,
        if_false=Conditional(
            condition=Op.EQ(Op.CALLDATALOAD(0), 1),
            # Clear the slot for good and create a second one.
            if_true=clear + Op.SSTORE(SLOT_SECOND, 1) + Op.STOP,
            if_false=Conditional(
                condition=Op.EQ(Op.CALLDATALOAD(0), 2),
                # Clear the slot and revert.
                if_true=clear + Op.REVERT(0, 0),
                if_false=Conditional(
                    condition=Op.EQ(Op.CALLDATALOAD(0), 3),
                    # Clear the slot and return.
                    if_true=clear + Op.STOP,
                    # Call this contract to clear the slot and revert.
                    if_false=Op.MSTORE(0, 2)
                    + Op.POP(
                        Op.CALL(
                            gas=Op.GAS,
                            address=Op.ADDRESS,
                            args_offset=0,
                            args_size=32,
                        )
                    )
                    + Op.STOP,
                ),
            ),
        ),
    )
    worker = pre.deploy_contract(code=worker_code)
    reverter = pre.deploy_contract(code=Op.REVERT(0, 0))

    def worker_frame(selector: int, **overrides: Any) -> FrameCase:
        return default_frame(
            target=worker,
            data=selector.to_bytes(32, "big"),
            pin_gas=False,
            **overrides,
        )

    if reversion == "reverted_call":
        reverting_frames = [
            worker_frame(4, state_gas_limit=0, state_gas_used=0)
        ]
    elif reversion == "reverted_frame":
        reverting_frames = [
            worker_frame(2, state_gas_limit=0, outcome=Outcome.REVERT)
        ]
    else:
        reverting_frames = [
            worker_frame(
                3,
                flags=Spec.ATOMIC_BATCH_FLAG,
                state_gas_limit=0,
                outcome=Outcome.UNROLLED,
            ),
            # Terminate the batch with a revert, unrolling it.
            default_frame(
                target=reverter,
                outcome=Outcome.REVERT,
                pin_gas=False,
            ),
        ]

    tx = FrameTransaction.build(
        fork=fork,
        sender=sender,
        frames=[
            # Frame 0: approve execution and payment.
            verify_frame(),
            # Frame 1: create the slot (0 -> 1). The final clear
            # refilled this receipt.
            worker_frame(0, state_gas_used=0),
            # The reverted clearing write.
            *reverting_frames,
            # Clear the slot for good, refilling frame 1, and create a
            # second slot from exactly one slot creation of budget.
            worker_frame(
                1,
                state_gas_limit=fresh_write_state_cost,
                state_gas_used=fresh_write_state_cost,
            ),
        ],
    )

    state_test(
        pre=pre,
        tx=tx,
        post={
            sender: Account(nonce=1),
            worker: Account(storage={SLOT_CREATED: 0, SLOT_SECOND: 1}),
        },
    )


@pytest.mark.parametrize(
    "cleared_again",
    [
        pytest.param(True, id="recreation_refilled"),
        pytest.param(False, id="recreation_kept"),
    ],
)
def test_recreation_after_refill_charges_recreating_frame(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    cleared_again: bool,
) -> None:
    """
    Attribute a slot created again after a cross-frame refill to the
    frame that creates it again.

    EIP-8141 "State-gas attribution and refills": "In both cases the
    storage slot's ownership entry is cleared, so a subsequent creation
    there is charged and attributed to whichever frame performs it."

    Frame 1 creates the slot and frame 2 clears it, refilling frame 1.
    Frame 3 creates it again, from exactly one storage write of budget.
    In `recreation_refilled`, frame 4 clears it once more: the refill
    goes to frame 3, the new owner, so both creating frames read back
    zero. In `recreation_kept`, frame 3 keeps its charge. A client that
    keeps frame 1 as the owner refills frame 1 a second time instead of
    frame 3.
    """
    sender = pre.fund_eoa()
    # The probe's records of frame 1's and frame 3's attributed state
    # gas, each plus one so the expected zero readback is
    # distinguishable from a slot never written.
    frame_1_used, frame_3_used = 0x02, 0x03

    def write(**pricing: Any) -> Bytecode:
        """Return the worker's write of its frame's data word."""
        return Op.SSTORE(SLOT_CREATED, Op.CALLDATALOAD(0), **pricing) + Op.STOP

    worker_code = write(
        key_warm=False, original_value=0, current_value=0, new_value=1
    )
    worker = pre.deploy_contract(code=worker_code)
    # Every creation is charged the state gas of the worker's first write.
    storage_set = worker_code.state_cost(fork)
    clear_code = write(
        key_warm=True, original_value=0, current_value=1, new_value=0
    )
    # A clear refills the creation's state charge to its owner frame;
    # only its execution refund reaches the transaction refund.
    clear_refund = clear_code.refund(fork) - clear_code.state_refund(fork)
    probe_code = (
        Op.SSTORE(
            frame_1_used,
            Op.ADD(1, Op.FRAMEPARAM(1, Spec.FRAMEPARAM_STATE_GAS_USED)),
        )
        + Op.SSTORE(
            frame_3_used,
            Op.ADD(1, Op.FRAMEPARAM(3, Spec.FRAMEPARAM_STATE_GAS_USED)),
        )
        + Op.STOP
    )
    probe = pre.deploy_contract(code=probe_code)

    def create(*, key_warm: bool, **overrides: Any) -> FrameCase:
        """Return a frame creating the slot (0 -> 1)."""
        return default_frame(
            target=worker,
            code=write(
                key_warm=key_warm,
                original_value=0,
                current_value=0,
                new_value=1,
            ),
            data=(1).to_bytes(32, "big"),
            state_gas_limit=storage_set,
            **overrides,
        )

    def clear() -> FrameCase:
        """Return a frame clearing the slot (1 -> 0), refilling it."""
        return default_frame(
            target=worker,
            code=clear_code,
            data=(0).to_bytes(32, "big"),
            warm=True,
            state_gas_limit=0,
        )

    frames = [
        verify_frame(),
        # Frame 1: create the slot; frame 2 refills it.
        create(key_warm=False, state_gas_used=0),
        # Frame 2: clear it, refilling frame 1.
        clear(),
        # Frame 3: create it again, now owning the charge.
        create(
            key_warm=True,
            warm=True,
            state_gas_used=0 if cleared_again else storage_set,
        ),
    ]
    if cleared_again:
        # Frame 4: clear it again, refilling frame 3.
        frames.append(clear())
    frames.append(default_frame(target=probe, code=probe_code))
    clears = 2 if cleared_again else 1

    tx = FrameTransaction.build(
        fork=fork,
        sender=sender,
        refund=clears * clear_refund,
        frames=frames,
    )

    state_test(
        pre=pre,
        tx=tx,
        post={
            sender: Account(nonce=1),
            worker: Account(storage={SLOT_CREATED: 0 if cleared_again else 1}),
            probe: Account(
                storage={
                    frame_1_used: 1,
                    frame_3_used: 1 if cleared_again else storage_set + 1,
                }
            ),
        },
    )


@pytest.mark.parametrize(
    "outcome",
    [
        pytest.param(Outcome.REVERT, id="frame_reverts"),
        pytest.param(Outcome.HALT, id="frame_halts"),
    ],
)
def test_failed_frame_discards_own_state_charge(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    outcome: Outcome,
) -> None:
    """
    Report no state gas for a frame that created a slot and then failed.

    EIP-8141 "State-gas attribution and refills": "When a frame
    reverts, restore the journal and `state_gas_left` to frame entry.
    Its final `gas_used.state` is therefore zero ... Both remaining
    pools count toward `tx_unused_gas`", and "When a frame halts
    exceptionally, perform the same state-gas restoration, but consume
    its entire execution-gas pool. Its final `gas_used.state` is zero."

    The frame's slot creation succeeds and is charged, from a state
    budget of exactly that charge, then the frame reverts or halts. Its
    receipt reports zero state gas and the transaction settles without
    the charge; the slot stays empty. A halting frame's receipt cannot
    tell a halt at `INVALID` from running out of gas before the
    creation; the reverting case pins the gas of the whole path, which
    fits the frame's budget.
    """
    sender = pre.fund_eoa()
    if outcome is Outcome.REVERT:
        ending = Op.REVERT(0, 0)
    elif outcome is Outcome.HALT:
        ending = Op.INVALID
    else:
        raise ValueError(f"unknown outcome: {outcome!r}")
    # The worker's slot starts empty.
    create = Op.SSTORE(SLOT_CREATED, 1)
    code = create + ending
    worker = pre.deploy_contract(code=code)
    failing = default_frame(
        target=worker,
        code=code,
        state_gas_limit_delta=0,
        outcome=outcome,
    )

    tx = FrameTransaction.build(
        fork=fork, sender=sender, frames=[verify_frame(), failing]
    )
    # The premises: the frame's state budget is exactly its charge, and
    # the whole path fits its execution budget.
    assert int(failing.state_gas_limit) == create.state_cost(fork)
    assert failing.entry_gas(fork) + failing.code_gas(fork) < int(
        failing.gas_limit
    )

    state_test(
        pre=pre,
        tx=tx,
        post={sender: Account(nonce=1), worker: Account(storage={})},
    )


@pytest.mark.state_test_only
@pytest.mark.parametrize(
    "state_gas_limit_delta",
    [
        pytest.param(0, id="exact_budget"),
        pytest.param(-1, id="one_below", marks=pytest.mark.exception_test),
    ],
)
def test_approve_both_scopes_creates_sender_at_zero_cost(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    state_gas_limit_delta: int,
) -> None:
    """
    Charge the account creation of an absent sender that approves both
    execution and payment of a transaction costing nothing.

    EIP-8141 `APPROVE` (`APPROVE_EXECUTION_AND_PAYMENT`): "If
    `resolved_target` has insufficient balance, revert the current call
    frame" and "Immediately before incrementing the sender's nonce, if
    `tx.sender` does not exist under the existence rule of
    [EIP-8037](./eip-8037.md)", charge the state gas of one new account
    "from the current frame's `state_gas_left`. If the pool cannot
    cover the charge, halt the current call frame exceptionally without
    applying any approval effects."

    An absent sender holds no balance, so this path is only reachable
    when `max_cost` is zero: a block with a zero base fee and a
    transaction with a zero `max_fee`. The sender's single `VERIFY`
    frame approves both scopes through its default code. With exactly
    the account creation of state budget the transaction is valid, the
    sender exists with nonce one, and the receipt reports the creation;
    one unit short, the frame halts and the transaction is invalid.

    Only a state test is filled: the blocks of the blockchain fixtures
    generated from it do not carry the zero base fee.
    """
    sender = pre.fund_eoa(amount=0)
    # No opcode prices the sender's creation: approving payment charges
    # it to the frame's state gas as the fork's new-account cost.
    account_creation = fork.gas_costs().NEW_ACCOUNT
    if state_gas_limit_delta == 0:
        succeeds = True
    elif state_gas_limit_delta == -1:
        succeeds = False
    else:
        raise ValueError(
            f"unknown state_gas_limit_delta: {state_gas_limit_delta!r}"
        )
    frame = verify_frame(
        state_gas_limit=account_creation + state_gas_limit_delta,
        state_gas_used=account_creation,
    )
    tx: Transaction
    if succeeds:
        tx = FrameTransaction.build(
            fork=fork,
            sender=sender,
            frames=[frame],
            max_fee=0,
            max_priority_fee_per_gas=0,
        )
    else:
        tx = Transaction(
            sender=sender,
            frames=[frame],
            max_fee=0,
            max_priority_fee_per_gas=0,
            error=TransactionException.TYPE_6_INVALID_FRAME_EXECUTION,
        )

    state_test(
        env=Environment(base_fee_per_gas=0),
        pre=pre,
        tx=tx,
        post={
            sender: (
                Account(nonce=1, balance=0)
                if succeeds
                else Account.NONEXISTENT
            )
        },
    )
