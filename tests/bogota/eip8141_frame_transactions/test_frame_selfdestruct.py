"""
`SELFDESTRUCT` state gas tests for
[EIP-8141: Frame Transaction](https://eips.ethereum.org/EIPS/eip-8141).

EIP-8037 assigns no state gas refill to `SELFDESTRUCT`, even when it
deletes a contract created earlier in the same transaction, so the
creation's charges stay attributed to the frame that paid them — in the
executing frame's pool and in an earlier frame's receipt alike. The
only state gas `SELFDESTRUCT` itself moves is the account creation it
charges, to the executing frame's pool, when its balance funds a new
beneficiary.

Bogota runs `SELFDESTRUCT` under EIP-6780: a contract created in the
same transaction is deleted, any other keeps its code.
"""

from typing import Dict, List, Tuple

import pytest
from execution_testing import (
    Account,
    Address,
    Alloc,
    Fork,
    Initcode,
    Op,
    StateTestFiller,
)

from .helpers import (
    FACTORY_NONCE,
    FrameCase,
    FrameTransaction,
    Outcome,
    account_creation_cost,
    created_address,
    default_frame,
    frame_data_copy,
    frame_data_create,
    storage_set_cost,
    verify_frame,
)
from .spec import Spec, ref_spec_8141

REFERENCE_SPEC_GIT_PATH = ref_spec_8141.git_path
REFERENCE_SPEC_VERSION = ref_spec_8141.version

pytestmark = pytest.mark.valid_from("Bogota")

SLOT_POOL = 0x01
"""Driver slot recording the frame's remaining state gas pool."""

SLOT_CREATOR_STATE_USED = 0x02
"""Probe slot recording the creating frame's attributed state gas."""

SLOT_DESTROYER_STATE_USED = 0x03
"""
Probe slot recording the self-destructing frame's attributed state gas,
plus one so the expected zero readback is distinguishable from a slot
never written.
"""

SELFDESTRUCT_CODE = Op.SELFDESTRUCT(Op.ADDRESS, address_warm=True)
"""
Code destroying its own account, with itself as the beneficiary of its
zero balance, so the opcode charges no state gas of its own.
"""

VICTIM_CODE = bytes(SELFDESTRUCT_CODE).ljust(32, b"\x00")
"""
`SELFDESTRUCT_CODE` padded to 32 bytes, so the code deposit of a
victim created in the transaction is a state charge of its own size.
"""

INIT_CODE = Initcode(deploy_code=VICTIM_CODE)
"""Init code deploying `VICTIM_CODE`."""


def creation_state_gas(fork: Fork) -> int:
    """
    Return the state gas a creation of the victim charges, derived from
    the EIP-8037 constants and checked against the framework's pricing:
    the account creation (STATE_BYTES_PER_NEW_ACCOUNT * CPSB) plus the
    code deposit (CPSB per deployed byte).
    """
    account_creation = account_creation_cost(fork)
    code_deposit = len(VICTIM_CODE) * fork.cost_per_state_byte()
    assert fork.code_deposit_state_gas(code_size=len(VICTIM_CODE)) == (
        code_deposit
    )
    assert INIT_CODE.state_cost(fork) == code_deposit
    return account_creation + code_deposit


@pytest.mark.parametrize(
    "victim_kind",
    [
        pytest.param("created_in_frame", id="created_in_same_frame"),
        pytest.param("pre_existing", id="pre_existing"),
    ],
)
def test_selfdestruct_no_state_gas_refill(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    victim_kind: str,
) -> None:
    """
    Self-destruct a contract from inside a frame and observe that the
    frame's pool is not refilled.

    EIP-8141 "EIP-8037 assigns no state-gas refill to `SELFDESTRUCT`,
    including when it deletes a contract created earlier in the
    transaction" (State-gas attribution and refills), and "account
    creation and code-deposit charges are only undone by rolling back
    the frame that made them" (Rationale: Cross-frame state-gas
    refills).

    The frame's driver contract calls the victim, which destroys
    itself, then records the frame's remaining pool. Either the driver
    created the victim earlier in the same frame — paying its account
    creation and code deposit from the pool, a budget of exactly that
    plus the recording write — or the victim is in the pre-state and
    the budget is only the recording write. Both record one storage
    write left: the deletion of the created victim gives nothing back,
    and the receipt keeps the creation's charges.

    Under EIP-6780 the created victim is deleted and the pre-existing
    one keeps its code.
    """
    sender = pre.fund_eoa()
    storage_set = storage_set_cost(fork)
    record_pool = Op.SSTORE(SLOT_POOL, Op.TXPARAM(Spec.TXPARAM_STATE_GAS_LEFT))

    post: Dict[Address, Account | None] = {sender: Account(nonce=1)}
    if victim_kind == "created_in_frame":
        driver_code = (
            frame_data_copy(INIT_CODE)
            + Op.POP(
                Op.CALL(
                    gas=Op.GAS,
                    # The creation warmed the address it returns.
                    address=frame_data_create(Op.CREATE, INIT_CODE),
                    address_warm=True,
                )
            )
            + record_pool
            + Op.STOP
        )
        driver = pre.deploy_contract(code=driver_code)
        victim = created_address(driver, Op.CREATE, INIT_CODE)
        data = bytes(INIT_CODE)
        creation = creation_state_gas(fork)
        execution_gas = (
            driver_code.execution_cost(fork)
            + INIT_CODE.execution_cost(fork)
            + SELFDESTRUCT_CODE.execution_cost(fork)
        )
        post[driver] = Account(
            nonce=FACTORY_NONCE + 1, storage={SLOT_POOL: storage_set}
        )
        # EIP-6780 deletes an account created in the same transaction.
        post[victim] = Account.NONEXISTENT
    elif victim_kind == "pre_existing":
        victim = pre.deploy_contract(code=VICTIM_CODE)
        driver_code = (
            Op.POP(Op.CALL(gas=Op.GAS, address=victim)) + record_pool + Op.STOP
        )
        driver = pre.deploy_contract(code=driver_code)
        data = b""
        creation = 0
        execution_gas = driver_code.execution_cost(
            fork
        ) + SELFDESTRUCT_CODE.execution_cost(fork)
        post[driver] = Account(storage={SLOT_POOL: storage_set})
        # EIP-6780 deletes only accounts created in the transaction.
        post[victim] = Account(code=VICTIM_CODE)
    else:
        raise ValueError(f"unknown victim kind: {victim_kind}")

    state_budget = creation + storage_set
    tx = FrameTransaction.build(
        fork=fork,
        sender=sender,
        frames=[
            verify_frame(),
            default_frame(
                target=driver,
                data=data,
                execution_gas=execution_gas,
                state_gas_limit=state_budget,
                state_gas_used=state_budget,
            ),
        ],
    )

    state_test(pre=pre, tx=tx, post=post)


def created_then_destroyed(
    pre: Alloc, fork: Fork
) -> Tuple[Address, Address, List[FrameCase]]:
    """
    Return a factory, the victim it creates and the frames of a
    transaction in which frame 0 approves, frame 1 creates the victim
    from exactly its creation's state gas, and frame 2 runs the
    victim's code, destroying it.
    """
    factory_code = (
        frame_data_copy(INIT_CODE)
        + Op.POP(frame_data_create(Op.CREATE, INIT_CODE))
        + Op.STOP
    )
    factory = pre.deploy_contract(code=factory_code)
    victim = created_address(factory, Op.CREATE, INIT_CODE)
    creation = creation_state_gas(fork)
    frames = [
        # Frame 0: approve execution and payment.
        verify_frame(),
        # Frame 1: create the victim from exactly its creation's state
        # gas.
        default_frame(
            target=factory,
            data=bytes(INIT_CODE),
            execution_gas=factory_code.execution_cost(fork)
            + INIT_CODE.execution_cost(fork),
            state_gas_limit=creation,
            state_gas_used=creation,
        ),
        # Frame 2: run the victim's code, destroying it. Frame 1's
        # creation left the victim's address warm.
        default_frame(
            target=victim,
            code=SELFDESTRUCT_CODE,
            warm=True,
            state_gas_limit=0,
        ),
    ]
    return factory, victim, frames


def test_selfdestruct_keeps_creator_frame_attribution(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    Self-destruct, in a later frame, a contract an earlier frame created.

    EIP-8141 "EIP-8037 assigns no state-gas refill to `SELFDESTRUCT`,
    including when it deletes a contract created earlier in the
    transaction. Such an operation therefore does not modify the
    creating frame's `gas_used.state`."

    Frame 1 creates the victim, attributing the account creation and
    the code deposit to its receipt. Frame 2 targets the victim
    directly and destroys it. Frame 3 reads frame 1's attribution back
    unchanged and frame 2's as zero, and both receipts settle that way.
    Whether the victim is deleted is pinned separately, in
    `test_selfdestruct_deletes_account_created_in_earlier_frame`.
    """
    sender = pre.fund_eoa()
    factory, _victim, frames = created_then_destroyed(pre, fork)
    probe_code = (
        Op.SSTORE(
            SLOT_CREATOR_STATE_USED,
            Op.FRAMEPARAM(1, Spec.FRAMEPARAM_STATE_GAS_USED),
        )
        + Op.SSTORE(
            SLOT_DESTROYER_STATE_USED,
            Op.ADD(1, Op.FRAMEPARAM(2, Spec.FRAMEPARAM_STATE_GAS_USED)),
        )
        + Op.STOP
    )
    probe = pre.deploy_contract(code=probe_code)

    tx = FrameTransaction.build(
        fork=fork,
        sender=sender,
        frames=[
            *frames,
            # Frame 3: record frame 1's and frame 2's attributions.
            default_frame(target=probe, code=probe_code),
        ],
    )

    state_test(
        pre=pre,
        tx=tx,
        post={
            sender: Account(nonce=1),
            factory: Account(nonce=FACTORY_NONCE + 1),
            probe: Account(
                storage={
                    SLOT_CREATOR_STATE_USED: creation_state_gas(fork),
                    SLOT_DESTROYER_STATE_USED: 1,
                }
            ),
        },
    )


def test_selfdestruct_deletes_account_created_in_earlier_frame(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    Self-destruct, in a later frame, a contract an earlier frame created,
    and observe that the contract is deleted.

    EIP-8141 does not say whether "created in the same transaction"
    spans frames. This test follows EIP-6780, which tracks creations per
    transaction: `SELFDESTRUCT` deletes the account when it "is executed
    in the same transaction as the contract was created", and every
    frame belongs to the one frame transaction. A client that tracks
    creations per frame keeps the victim's code and fails this test.

    Frame 1 creates the victim and frame 2 destroys it, as in
    `test_selfdestruct_keeps_creator_frame_attribution`.
    """
    sender = pre.fund_eoa()
    factory, victim, frames = created_then_destroyed(pre, fork)
    tx = FrameTransaction.build(fork=fork, sender=sender, frames=frames)

    state_test(
        pre=pre,
        tx=tx,
        post={
            sender: Account(nonce=1),
            factory: Account(nonce=FACTORY_NONCE + 1),
            victim: Account.NONEXISTENT,
        },
    )


@pytest.mark.parametrize(
    "state_gas_limit_delta",
    [
        pytest.param(0, id="exact_budget"),
        pytest.param(-1, id="one_below"),
    ],
)
def test_selfdestruct_new_beneficiary_charges_frame_pool(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    state_gas_limit_delta: int,
) -> None:
    """
    Charge the account creation of a `SELFDESTRUCT` whose balance funds
    a new beneficiary to the executing frame's pool.

    EIP-8141 "Charge points follow EIP-8037 unchanged", and EIP-8037
    charges `STATE_BYTES_PER_NEW_ACCOUNT * CPSB` when a `SELFDESTRUCT`
    sends a non-zero balance to an account that does not exist; "A
    charge exceeding its remaining pool is an exceptional halt of the
    current callframe".

    The frame targets a pre-existing contract holding one wei, whose
    code destroys it in favour of an absent beneficiary. A budget of
    exactly the account creation succeeds: the beneficiary receives the
    wei, the receipt attributes the creation, and the victim keeps its
    code under EIP-6780. One unit below halts the frame exceptionally:
    the receipt reports the whole execution budget and zero state gas,
    and the wei stays with the victim.
    """
    sender = pre.fund_eoa()
    beneficiary = pre.fund_eoa(amount=0)
    victim_code = Op.SELFDESTRUCT(beneficiary, account_new=True)
    victim = pre.deploy_contract(code=victim_code, balance=1)
    assert victim_code.state_cost(fork) == account_creation_cost(fork)

    succeeds = state_gas_limit_delta >= 0

    tx = FrameTransaction.build(
        fork=fork,
        sender=sender,
        frames=[
            verify_frame(),
            default_frame(
                target=victim,
                code=victim_code,
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
            beneficiary: Account(balance=1)
            if succeeds
            else Account.NONEXISTENT,
            # The victim was not created in the transaction, so it keeps
            # its code.
            victim: Account(code=victim_code, balance=0 if succeeds else 1),
        },
    )


def test_selfdestruct_charge_refilled_on_call_revert(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    Refill the account creation a `SELFDESTRUCT` charged when a call
    frame above it reverts.

    EIP-8141 "When an EVM call frame reverts or halts exceptionally,
    restore the state-gas journal and the active frame's
    `state_gas_left` to the checkpoint covering that call and any
    associated pre-call state charge."

    The frame's driver calls a middle contract, which calls the victim
    and then reverts. The victim holds one wei and destroys itself in
    favour of an absent beneficiary, charging the account creation to
    the frame's pool two calls down. The middle contract's revert
    restores the pool, so the driver records the whole budget, the
    account creation plus its own recording write, and the receipt
    reports only that write. The beneficiary never receives the wei.
    """
    sender = pre.fund_eoa()
    beneficiary = pre.fund_eoa(amount=0)
    victim_code = Op.SELFDESTRUCT(beneficiary, account_new=True)
    victim = pre.deploy_contract(code=victim_code, balance=1)
    middle_code = Op.POP(Op.CALL(gas=Op.GAS, address=victim)) + Op.REVERT(0, 0)
    middle = pre.deploy_contract(code=middle_code)
    driver_code = (
        Op.POP(Op.CALL(gas=Op.GAS, address=middle))
        + Op.SSTORE(SLOT_POOL, Op.TXPARAM(Spec.TXPARAM_STATE_GAS_LEFT))
        + Op.STOP
    )
    driver = pre.deploy_contract(code=driver_code)
    account_creation = account_creation_cost(fork)
    assert victim_code.state_cost(fork) == account_creation
    storage_set = storage_set_cost(fork)
    state_budget = account_creation + storage_set

    tx = FrameTransaction.build(
        fork=fork,
        sender=sender,
        frames=[
            verify_frame(),
            default_frame(
                target=driver,
                execution_gas=driver_code.execution_cost(fork)
                + middle_code.execution_cost(fork)
                + victim_code.execution_cost(fork),
                state_gas_limit=state_budget,
                state_gas_used=storage_set,
            ),
        ],
    )

    state_test(
        pre=pre,
        tx=tx,
        post={
            sender: Account(nonce=1),
            driver: Account(storage={SLOT_POOL: state_budget}),
            beneficiary: Account.NONEXISTENT,
            victim: Account(code=victim_code, balance=1),
        },
    )
