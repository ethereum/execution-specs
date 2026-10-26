"""
Contract creation tests for
[EIP-8141: Frame Transaction](https://eips.ethereum.org/EIPS/eip-8141).

A `CREATE` or `CREATE2` run by a frame's code charges its state gas to
that frame's pool: the account creation in the creating call frame
before the child is spawned, any storage the init code writes, and the
code deposit when the init code returns. A failed child refills its
own charges to the pool, while a reverting frame or an unrolled atomic
batch removes the creation together with its attribution.
"""

from typing import Tuple

import pytest
from execution_testing import (
    Account,
    Alloc,
    Bytecode,
    Fork,
    Initcode,
    Op,
    StateTestFiller,
    create_op,
)

from .helpers import (
    CANARY,
    FACTORY_NONCE,
    FrameTransaction,
    Outcome,
    account_creation_cost,
    created_address,
    default_frame,
    frame_data_copy,
    frame_data_create,
    overwrite,
    record_pool,
    storage_set_cost,
    verify_frame,
)
from .spec import Spec, ref_spec_8141

REFERENCE_SPEC_GIT_PATH = ref_spec_8141.git_path
REFERENCE_SPEC_VERSION = ref_spec_8141.version

pytestmark = [
    pytest.mark.valid_from("Bogota"),
    pytest.mark.with_all_create_opcodes,
]

SLOT_CREATE_RESULT = 0x01
"""
Factory slot recording the address `CREATE` returned, plus one so a
failed creation's zero is distinguishable from a slot never written.
"""

SLOT_POOL = 0x02
"""Factory slot recording the frame's remaining state gas pool."""

SLOT_INIT_WRITE = 0x00
"""Slot the init code writes in the account it creates."""

SLOT_CREATOR_STATE_USED = 0x03
"""
Probe slot recording the creating frame's attributed state gas, plus
one so the expected zero readback is distinguishable from a slot never
written.
"""

SLOT_CREATOR_STATUS = 0x04
"""
Probe slot recording the creating frame's receipt status, plus one so
a `FAILURE` readback is distinguishable from a slot never written.
"""

RUNTIME_CODE = Op.JUMPDEST * 31 + Op.STOP
"""
Code the init code deploys: 32 bytes, so its code deposit is a state
charge of its own size next to the account creation.
"""

INIT_CODE = Initcode(
    deploy_code=RUNTIME_CODE,
    initcode_prefix=Op.SSTORE(SLOT_INIT_WRITE, 1),
)
"""
Init code writing one storage slot in the account it creates, then
returning `RUNTIME_CODE`.
"""


def factory_code(
    create_opcode: Op, init_code: Bytecode = INIT_CODE
) -> Tuple[Bytecode, Bytecode]:
    """
    Return the factory code that creates a contract from the frame data,
    which holds `init_code`, and its prefix up to and including the
    `CREATE`.

    After the creation the factory records the address returned and the
    frame's remaining state gas pool, each a fresh storage write.
    """
    create_call = frame_data_create(create_opcode, init_code)
    copy = frame_data_copy(init_code)
    code = (
        copy
        + Op.SSTORE(SLOT_CREATE_RESULT, Op.ADD(1, create_call))
        + Op.SSTORE(SLOT_POOL, Op.TXPARAM(Spec.TXPARAM_STATE_GAS_LEFT))
        + Op.STOP
    )
    # `Op.ADD(1, create_call)` pushes its second operand first, so the
    # `CREATE` is the last instruction run before the rest of the code.
    return code, copy + create_call


def plain_factory_code(create_opcode: Op, ending: Bytecode) -> Bytecode:
    """
    Return factory code that creates a contract from the frame data,
    discards the address and ends with `ending`, writing nothing itself.
    """
    return (
        frame_data_copy(INIT_CODE)
        + Op.POP(frame_data_create(create_opcode, INIT_CODE))
        + ending
    )


def creation_state_costs(fork: Fork, create_opcode: Op) -> Tuple[int, int]:
    """
    Return the account creation's state gas and the init code's state
    gas (its storage write plus the code deposit), both checked against
    the EIP-8037 constants they derive from.
    """
    # STATE_BYTES_PER_NEW_ACCOUNT * CPSB, charged by the creating frame.
    account_creation = account_creation_cost(fork)
    create_call = create_op(create_opcode, init_code_size=len(INIT_CODE))
    assert create_call.state_cost(fork) == account_creation
    # STATE_BYTES_PER_STORAGE_SET * CPSB for the init code's write, plus
    # CPSB per deployed byte for the deposit.
    init_state = INIT_CODE.state_cost(fork)
    assert init_state == storage_set_cost(fork) + fork.code_deposit_state_gas(
        code_size=len(RUNTIME_CODE)
    )
    return account_creation, init_state


def test_create_charges_frame_pool(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    create_opcode: Op,
) -> None:
    """
    Charge a creation's state gas to the creating frame's pool.

    EIP-8141 "Charge points follow EIP-8037 unchanged ... the
    conditional account-creation charge of the `CALL*` and
    `CREATE`/`CREATE2` families in the creating frame, and code-deposit
    gas at deposit time", drawn from the frame's `state_gas_left`, which
    "EVM call frames at any depth within the frame draw from ...
    directly" (Gas Accounting: the pools are independent), and
    attributed to the frame's receipt (State-gas attribution and
    refills).

    The frame's state budget is exactly the account creation, the init
    code's storage write (at depth one), the code deposit and the
    factory's two recording writes. The recorded pool after the
    creation and the first recording write is therefore one storage
    write, and the receipt reports the whole budget. The created
    account holds the deployed code and the init code's storage.
    """
    sender = pre.fund_eoa()
    code, _ = factory_code(create_opcode)
    factory = pre.deploy_contract(code=code)
    created = created_address(factory, create_opcode, INIT_CODE)
    account_creation, init_state = creation_state_costs(fork, create_opcode)
    storage_set = storage_set_cost(fork)
    state_budget = account_creation + init_state + 2 * storage_set
    assert code.state_cost(fork) + init_state == state_budget

    tx = FrameTransaction.build(
        fork=fork,
        sender=sender,
        frames=[
            verify_frame(),
            default_frame(
                target=factory,
                data=bytes(INIT_CODE),
                execution_gas=code.execution_cost(fork)
                + INIT_CODE.execution_cost(fork),
                state_gas_limit=state_budget,
                state_gas_used=state_budget,
            ),
        ],
    )

    state_test(
        pre=pre,
        tx=tx,
        post={
            sender: Account(nonce=1),
            factory: Account(
                nonce=FACTORY_NONCE + 1,
                storage={
                    SLOT_CREATE_RESULT: int.from_bytes(created, "big") + 1,
                    SLOT_POOL: storage_set,
                },
            ),
            created: Account(
                nonce=1,
                code=RUNTIME_CODE,
                storage={SLOT_INIT_WRITE: 1},
            ),
        },
    )


def test_create_code_deposit_exceeds_frame_pool(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    create_opcode: Op,
) -> None:
    """
    Run a creation's init code out of state gas at the code deposit.

    The frame's pool, at the `CREATE`, is one unit short of the
    account creation, the init code's storage write and the code
    deposit. The account creation and the storage write fit; the code
    deposit does not, which halts the child exceptionally (EIP-8141 "A
    charge exceeding its remaining pool is an exceptional halt of the
    current callframe, with ordinary out-of-gas semantics"), consuming
    its whole execution-gas grant.

    EIP-8141 "When an EVM call frame reverts or halts exceptionally,
    restore the state-gas journal and the active frame's
    `state_gas_left` to the checkpoint covering that call and any
    associated pre-call state charge": the storage write and the
    account creation charged before the child are both refilled, so
    the factory records its full budget back, `CREATE` returns zero,
    and the frame goes on to succeed paying only for its two recording
    writes. Nothing of the creation survives.

    The frame's execution budget is sized so the one 64th the factory
    keeps across the child grant exactly covers the code after the
    `CREATE`: the frame then spends its whole budget and succeeds.
    """
    sender = pre.fund_eoa()
    code, up_to_create = factory_code(create_opcode)
    factory = pre.deploy_contract(code=code)
    created = created_address(factory, create_opcode, INIT_CODE)
    account_creation, init_state = creation_state_costs(fork, create_opcode)
    storage_set = storage_set_cost(fork)
    state_budget = account_creation + init_state - 1
    # The recording writes fit the budget once the creation is refilled.
    assert state_budget >= 2 * storage_set

    # The factory keeps one 64th of its gas across the child grant
    # (`max_message_call_gas`), and the code after the `CREATE` runs on
    # exactly that.
    after_create = code.execution_cost(fork) - up_to_create.execution_cost(
        fork
    )
    # The factory is cold at frame entry.
    entry = fork.frame_entry_gas_calculator()(
        target_warm=False, delegated=False, delegation_warm=False
    )
    gas_limit = entry + up_to_create.execution_cost(fork) + 64 * after_create

    tx = FrameTransaction.build(
        fork=fork,
        sender=sender,
        frames=[
            verify_frame(),
            default_frame(
                target=factory,
                data=bytes(INIT_CODE),
                gas_limit=gas_limit,
                gas_used=gas_limit,
                state_gas_limit=state_budget,
                state_gas_used=2 * storage_set,
            ),
        ],
    )

    state_test(
        pre=pre,
        tx=tx,
        post={
            sender: Account(nonce=1),
            # The child's rollback leaves the nonce the creating frame
            # bumped before dispatching it.
            factory: Account(
                nonce=FACTORY_NONCE + 1,
                storage={
                    SLOT_CREATE_RESULT: 1,
                    SLOT_POOL: state_budget - storage_set,
                },
            ),
            created: Account.NONEXISTENT,
        },
    )


def test_create_account_charge_exceeds_frame_pool(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    create_opcode: Op,
) -> None:
    """
    Halt the creating frame at the account creation charge.

    EIP-8141 places the account creation charge of `CREATE`/`CREATE2`
    "in the creating frame", and "A charge that exhausts either pool
    halts". With a pool one unit short of the account creation, the
    charge is taken by the factory's own call frame — the frame's top
    level — before any child exists, so the frame halts exceptionally:
    its receipt reports its whole execution budget and zero state gas,
    and the factory's nonce and the created account are both absent.

    The rest of the creation, the init code's write and the code
    deposit, would fit that pool, and the factory writes nothing after
    it: only the account creation charge can halt the frame.
    """
    sender = pre.fund_eoa()
    code = plain_factory_code(create_opcode, Op.STOP)
    factory = pre.deploy_contract(code=code)
    created = created_address(factory, create_opcode, INIT_CODE)
    account_creation, init_state = creation_state_costs(fork, create_opcode)
    assert init_state <= account_creation - 1

    tx = FrameTransaction.build(
        fork=fork,
        sender=sender,
        frames=[
            verify_frame(),
            default_frame(
                target=factory,
                data=bytes(INIT_CODE),
                state_gas_limit=account_creation - 1,
                outcome=Outcome.HALT,
            ),
        ],
    )

    state_test(
        pre=pre,
        tx=tx,
        post={
            sender: Account(nonce=1),
            factory: Account(nonce=FACTORY_NONCE),
            created: Account.NONEXISTENT,
        },
    )


@pytest.mark.parametrize(
    "outcome",
    [
        pytest.param(Outcome.REVERT, id="frame_reverts"),
        pytest.param(Outcome.HALT, id="frame_halts"),
    ],
)
def test_create_in_failing_frame(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    create_opcode: Op,
    outcome: Outcome,
) -> None:
    """
    Undo a creation whose frame reverts or halts after it succeeded.

    EIP-8141 "When a frame reverts, restore the journal and
    `state_gas_left` to frame entry. Its final `gas_used.state` is
    therefore zero ... Both remaining pools count toward
    `tx_unused_gas`", and "When a frame halts exceptionally, perform
    the same state-gas restoration, but consume its entire
    execution-gas pool."

    The creation succeeds inside the frame, then the factory reverts
    (or halts). The receipt reports zero state gas — the account
    creation, the init code's write and the code deposit are all
    removed — and the payer is charged none of it. The created account
    is absent and the factory's nonce is back at its pre-state value.
    """
    sender = pre.fund_eoa()
    ending = Op.REVERT(0, 0) if outcome is Outcome.REVERT else Op.INVALID
    code = plain_factory_code(create_opcode, ending)
    factory = pre.deploy_contract(code=code)
    created = created_address(factory, create_opcode, INIT_CODE)
    account_creation, init_state = creation_state_costs(fork, create_opcode)

    tx = FrameTransaction.build(
        fork=fork,
        sender=sender,
        frames=[
            verify_frame(),
            default_frame(
                target=factory,
                data=bytes(INIT_CODE),
                execution_gas=code.execution_cost(fork)
                + INIT_CODE.execution_cost(fork),
                # The creation fits the budget; only the frame's end
                # removes it.
                state_gas_limit=account_creation + init_state,
                outcome=outcome,
            ),
        ],
    )

    state_test(
        pre=pre,
        tx=tx,
        post={
            sender: Account(nonce=1),
            factory: Account(nonce=FACTORY_NONCE),
            created: Account.NONEXISTENT,
        },
    )


def test_create_in_unrolled_batch(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    create_opcode: Op,
) -> None:
    """
    Unroll an atomic batch whose first frame created a contract.

    EIP-8141 "When a frame in the batch fails, the state must be rolled
    back to the condition it was immediately before the atomic batch
    began", and "Changes to any frame receipt's `gas_used.state` during
    the batch are reverted ... Executed frame receipts retain their
    execution status and execution gas used, with empty logs and zero
    state gas used"; "When an atomic batch is unrolled, restore the
    state-gas journal to the batch-entry checkpoint. Charges attributed
    to frames in the batch are removed from their receipts".

    The batch's first frame creates a contract, its terminating frame
    reverts. The creating frame's receipt keeps `SUCCESS` and its
    execution gas, but reports zero state gas: the account creation,
    the init code's write and the code deposit are all charged to no
    one. A later frame reads that attribution and that status back
    live, and the created account and the factory's nonce bump are gone
    after the transaction.

    The later frame does not touch the created address: the creation
    warmed it, and the EIP does not say whether an unrolled batch's
    successful frames keep the addresses they warmed (it rolls warmth
    back only "If a frame reverts", Cross-frame interactions), so any
    access to it would price an unspecified rule.
    """
    sender = pre.fund_eoa()
    code, _ = factory_code(create_opcode)
    factory = pre.deploy_contract(code=code)
    created = created_address(factory, create_opcode, INIT_CODE)
    account_creation, init_state = creation_state_costs(fork, create_opcode)
    reverter = pre.deploy_contract(code=Op.REVERT(0, 0))
    probe_code = (
        Op.SSTORE(
            SLOT_CREATOR_STATE_USED,
            Op.ADD(1, Op.FRAMEPARAM(1, Spec.FRAMEPARAM_STATE_GAS_USED)),
        )
        + Op.SSTORE(
            SLOT_CREATOR_STATUS,
            Op.ADD(1, Op.FRAMEPARAM(1, Spec.FRAMEPARAM_STATUS)),
        )
        + Op.STOP
    )
    probe = pre.deploy_contract(code=probe_code)

    tx = FrameTransaction.build(
        fork=fork,
        sender=sender,
        frames=[
            # Frame 0: approve execution and payment.
            verify_frame(),
            # Frame 1: open the batch and create the contract, which
            # succeeds and is then unrolled.
            default_frame(
                flags=Spec.ATOMIC_BATCH_FLAG,
                target=factory,
                data=bytes(INIT_CODE),
                execution_gas=code.execution_cost(fork)
                + INIT_CODE.execution_cost(fork),
                state_gas_limit=account_creation
                + init_state
                + 2 * storage_set_cost(fork),
                outcome=Outcome.UNROLLED,
            ),
            # Frame 2: terminate the batch with a revert, unrolling it.
            default_frame(
                target=reverter,
                code=Op.REVERT(0, 0),
                outcome=Outcome.REVERT,
            ),
            # Frame 3: record frame 1's attribution and status after
            # the unroll.
            default_frame(target=probe, code=probe_code),
        ],
    )

    state_test(
        pre=pre,
        tx=tx,
        post={
            sender: Account(nonce=1),
            factory: Account(nonce=FACTORY_NONCE, storage={}),
            created: Account.NONEXISTENT,
            probe: Account(
                storage={
                    SLOT_CREATOR_STATE_USED: 1,
                    SLOT_CREATOR_STATUS: Spec.STATUS_SUCCESS + 1,
                }
            ),
        },
    )


def test_create_preflight_failure_charges_nothing(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    create_opcode: Op,
) -> None:
    """
    Charge no account creation to a `CREATE` that fails its endowment
    check, even with an empty state pool.

    EIP-8141 "Charge points follow EIP-8037 unchanged", and EIP-8037
    (`CREATE`/`CREATE2` family): "A creation failing those checks
    [sender balance for the endowment, nonce overflow, and the
    call-stack depth limit] never reads the destination, and no
    account-creation state-gas is charged."

    The factory holds no balance and creates with a 1-wei endowment in
    a frame whose state budget is zero. The creation fails before the
    account-creation charge, so `CREATE` returns zero and the frame
    goes on: it records the result and its untouched pool over two
    canary slots and succeeds with zero state gas. A client charging
    the account creation before the balance check halts the frame on
    its empty pool, leaving both canaries in place.
    """
    sender = pre.fund_eoa()
    create_call = create_op(
        create_opcode, value=1, account_new=False, init_code_size=0
    )
    code = (
        overwrite(SLOT_CREATE_RESULT, Op.ADD(1, create_call))
        + record_pool(SLOT_POOL)
        + Op.STOP
    )
    assert code.state_cost(fork) == 0
    factory = pre.deploy_contract(
        code=code, storage={SLOT_CREATE_RESULT: CANARY, SLOT_POOL: CANARY}
    )

    tx = FrameTransaction.build(
        fork=fork,
        sender=sender,
        frames=[
            verify_frame(),
            default_frame(target=factory, code=code, state_gas_limit=0),
        ],
    )

    state_test(
        pre=pre,
        tx=tx,
        post={
            sender: Account(nonce=1),
            # A failed endowment check leaves the nonce alone.
            factory: Account(
                nonce=FACTORY_NONCE,
                storage={SLOT_CREATE_RESULT: 1, SLOT_POOL: 1},
            ),
        },
    )


def test_create_at_funded_address_charges_no_account(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    create_opcode: Op,
) -> None:
    """
    Charge only the init code's state to a creation whose destination
    already holds a balance.

    EIP-8141 "Charge points follow EIP-8037 unchanged", and EIP-8037:
    "an address that holds a balance but has no code and a zero nonce
    is existent ... only the code-deposit cost (`L × CPSB`) applies and
    the `STATE_BYTES_PER_NEW_ACCOUNT × CPSB` account-creation charge
    does not", and "If the destination pre-exists (e.g., it holds a
    balance), nothing is charged."

    The destination holds one wei. The frame's state budget is exactly
    the init code's storage write, the code deposit and the factory's
    two recording writes, with nothing for an account creation: the
    creation succeeds, the recorded pool after the first recording
    write is one storage write, and the receipt reports the whole
    budget. A client charging the account creation halts the frame.
    """
    sender = pre.fund_eoa()
    code, _ = factory_code(create_opcode)
    factory = pre.deploy_contract(code=code)
    created = created_address(factory, create_opcode, INIT_CODE)
    pre.fund_address(created, 1)
    _, init_state = creation_state_costs(fork, create_opcode)
    storage_set = storage_set_cost(fork)
    state_budget = init_state + 2 * storage_set

    tx = FrameTransaction.build(
        fork=fork,
        sender=sender,
        frames=[
            verify_frame(),
            default_frame(
                target=factory,
                data=bytes(INIT_CODE),
                execution_gas=code.execution_cost(fork)
                + INIT_CODE.execution_cost(fork),
                state_gas_limit=state_budget,
                state_gas_used=state_budget,
            ),
        ],
    )

    state_test(
        pre=pre,
        tx=tx,
        post={
            sender: Account(nonce=1),
            factory: Account(
                nonce=FACTORY_NONCE + 1,
                storage={
                    SLOT_CREATE_RESULT: int.from_bytes(created, "big") + 1,
                    SLOT_POOL: storage_set,
                },
            ),
            created: Account(
                nonce=1,
                balance=1,
                code=RUNTIME_CODE,
                storage={SLOT_INIT_WRITE: 1},
            ),
        },
    )


def test_create_init_code_revert_refills_frame_pool(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    create_opcode: Op,
) -> None:
    """
    Refill a creation's account charge and its init code's storage
    write when the init code reverts.

    EIP-8141 "When an EVM call frame reverts or halts exceptionally,
    restore the state-gas journal and the active frame's
    `state_gas_left` to the checkpoint covering that call and any
    associated pre-call state charge", and EIP-8037: "If the create
    frame reverts or halts exceptionally ... any charged
    account-creation state-gas is refilled".

    The init code writes a fresh slot, then reverts. The frame's state
    budget is the account creation, that write and the factory's two
    recording writes. Both creation charges come back, so the recorded
    pool after the first recording write is the whole budget less one
    storage write and the receipt reports only the two recording
    writes. The reverting child returns its unused execution gas, so
    the frame is charged only what the factory and the init code ran.
    """
    sender = pre.fund_eoa()
    init_code = Op.SSTORE(SLOT_INIT_WRITE, 1) + Op.REVERT(0, 0)
    code, _ = factory_code(create_opcode, init_code)
    factory = pre.deploy_contract(code=code)
    created = created_address(factory, create_opcode, init_code)
    account_creation = account_creation_cost(fork)
    storage_set = storage_set_cost(fork)
    state_budget = account_creation + 3 * storage_set

    tx = FrameTransaction.build(
        fork=fork,
        sender=sender,
        frames=[
            verify_frame(),
            default_frame(
                target=factory,
                data=bytes(init_code),
                execution_gas=code.execution_cost(fork)
                + init_code.execution_cost(fork),
                state_gas_limit=state_budget,
                state_gas_used=2 * storage_set,
            ),
        ],
    )

    state_test(
        pre=pre,
        tx=tx,
        post={
            sender: Account(nonce=1),
            factory: Account(
                nonce=FACTORY_NONCE + 1,
                storage={
                    SLOT_CREATE_RESULT: 1,
                    SLOT_POOL: state_budget - storage_set,
                },
            ),
            created: Account.NONEXISTENT,
        },
    )


def test_create_at_depth_one_charges_frame_pool(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    create_opcode: Op,
) -> None:
    """
    Charge a creation run one call below the frame's top level to the
    frame's pool.

    EIP-8141 "`state_gas_left` is frame-scoped. EVM call frames at any
    depth within the frame draw from it directly. It is not forwarded,
    split, or divided per callframe like execution gas."

    The frame's target calls the factory, which creates the contract at
    depth one and records the pool. The budget is exactly the account
    creation, the init code's write at depth two, the code deposit and
    the factory's two recording writes: the recorded pool is one
    storage write and the receipt reports the whole budget. A client
    that hands a call only part of the pool halts the creation.
    """
    sender = pre.fund_eoa()
    code, _ = factory_code(create_opcode)
    factory = pre.deploy_contract(code=code)
    created = created_address(factory, create_opcode, INIT_CODE)
    account_creation, init_state = creation_state_costs(fork, create_opcode)
    storage_set = storage_set_cost(fork)
    state_budget = account_creation + init_state + 2 * storage_set
    driver_code = (
        frame_data_copy(INIT_CODE)
        + Op.POP(
            Op.CALL(
                gas=Op.GAS,
                address=factory,
                args_offset=0,
                args_size=Op.CALLDATASIZE,
            )
        )
        + Op.STOP
    )
    driver = pre.deploy_contract(code=driver_code)

    tx = FrameTransaction.build(
        fork=fork,
        sender=sender,
        frames=[
            verify_frame(),
            default_frame(
                target=driver,
                data=bytes(INIT_CODE),
                execution_gas=driver_code.execution_cost(fork)
                + code.execution_cost(fork)
                + INIT_CODE.execution_cost(fork),
                state_gas_limit=state_budget,
                state_gas_used=state_budget,
            ),
        ],
    )

    state_test(
        pre=pre,
        tx=tx,
        post={
            sender: Account(nonce=1),
            factory: Account(
                nonce=FACTORY_NONCE + 1,
                storage={
                    SLOT_CREATE_RESULT: int.from_bytes(created, "big") + 1,
                    SLOT_POOL: storage_set,
                },
            ),
            created: Account(
                nonce=1,
                code=RUNTIME_CODE,
                storage={SLOT_INIT_WRITE: 1},
            ),
        },
    )
