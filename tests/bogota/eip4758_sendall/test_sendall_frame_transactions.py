"""
Tests for how [EIP-4758: Deactivate SELFDESTRUCT](https://eips.ethereum.org/EIPS/eip-4758)
composes with [EIP-8141](https://eips.ethereum.org/EIPS/eip-8141) frame
transactions.

A frame sweeps like any other call: the balance moves and the account
keeps its code, even when an earlier frame of the same transaction
created it. These tests pin the sweep in each frame mode, its rollback
with an atomic batch, and the state gas it draws from the frame.
"""

from typing import Any, Callable, List, Tuple

import pytest
from execution_testing import (
    Account,
    Address,
    Alloc,
    Bytecode,
    Fork,
    Initcode,
    Op,
    StateTestFiller,
    TransactionException,
    compute_create_address,
)
from execution_testing import (
    Macros as Om,
)

from tests.amsterdam.eip7708_eth_transfer_logs.spec import transfer_log
from tests.bogota.eip8141_frame_transactions.helpers import (
    FrameCase,
    FrameTransaction,
    Outcome,
    default_frame,
    sender_frame,
    verify_frame,
)
from tests.bogota.eip8141_frame_transactions.spec import Spec as Spec8141

from .spec import ref_spec_4758

REFERENCE_SPEC_GIT_PATH = ref_spec_4758.git_path
REFERENCE_SPEC_VERSION = ref_spec_4758.version

pytestmark = pytest.mark.valid_from("EIP4758")

VICTIM_BALANCE = 0x1234


def require_frame_transactions(fork: Fork) -> None:
    """Skip a fork without EIP-8141 frame transactions."""
    if not fork.is_eip_enabled(8141):
        pytest.skip("frame transactions need EIP-8141")


def deploy_factory(
    pre: Alloc, child_code: Bytecode, *, call_child: bool = False
) -> Tuple[Address, Address]:
    """
    Deploy a factory that creates a child running `child_code`, funded
    with `VICTIM_BALANCE`, and calls it when `call_child` is set.
    """
    initcode = Initcode(deploy_code=child_code)
    create = Op.CREATE(value=VICTIM_BALANCE, size=len(initcode))
    factory = pre.deploy_contract(
        code=Om.MSTORE(initcode, 0)
        + (Op.CALL(address=create) if call_child else create),
        balance=VICTIM_BALANCE,
    )
    return factory, compute_create_address(address=factory, nonce=1)


def factory_frame(
    fork: Fork, child_code: Bytecode, **overrides: Any
) -> FrameCase:
    """
    Return a `SENDER` frame running a factory, which pays the child's
    creation from its state budget.
    """
    return sender_frame(
        # The initcode's execution is not priced by the factory code.
        pin_gas=False,
        state_gas_used=fork.create_state_gas(code_size=len(child_code)),
        **overrides,
    )


@pytest.mark.parametrize(
    "frame",
    [
        pytest.param(default_frame, id="default_frame"),
        pytest.param(sender_frame, id="sender_frame"),
    ],
)
def test_sendall_in_frame(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    frame: Callable[..., FrameCase],
) -> None:
    """
    Sweep a contract from a frame: the balance moves to the beneficiary
    and the contract keeps its code and storage.
    """
    require_frame_transactions(fork)
    beneficiary = pre.fund_eoa(amount=1)
    victim_code = Op.SELFDESTRUCT(beneficiary)
    victim = pre.deploy_contract(
        code=victim_code, storage={0: 1}, balance=VICTIM_BALANCE
    )

    tx = FrameTransaction.build(
        fork=fork,
        sender=pre.fund_eoa(),
        frames=[
            verify_frame(),
            frame(
                target=victim,
                code=victim_code,
                logs=[transfer_log(victim, beneficiary, VICTIM_BALANCE)],
            ),
        ],
    )

    state_test(
        pre=pre,
        tx=tx,
        post={
            victim: Account(code=victim_code, storage={0: 1}, balance=0),
            beneficiary: Account(balance_change=VICTIM_BALANCE),
        },
    )


@pytest.mark.exception_test
def test_sendall_in_verify_frame(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    Reject a frame transaction whose `VERIFY` frame sweeps. The frame is
    static, so SENDALL halts it, and a failed `VERIFY` frame invalidates
    the transaction. `test_sendall_in_frame` sweeps the same contract.
    """
    require_frame_transactions(fork)
    sender = pre.fund_eoa()
    beneficiary = pre.fund_eoa(amount=1)
    victim = pre.deploy_contract(
        code=Op.SELFDESTRUCT(beneficiary), balance=VICTIM_BALANCE
    )

    tx = FrameTransaction.build(
        fork=fork,
        sender=sender,
        frames=[
            verify_frame(),
            verify_frame(target=victim, flags=Spec8141.APPROVE_NONE),
        ],
        error=TransactionException.TYPE_6_INVALID_FRAME_EXECUTION,
    )

    state_test(
        pre=pre,
        tx=tx,
        post={
            sender: Account(nonce_change=0),
            victim: Account(balance_change=0),
            beneficiary: Account(balance_change=0),
        },
    )


@pytest.mark.parametrize("sweep", ["same_frame", "later_frame"])
def test_created_account_swept_in_frame_survives(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    sweep: str,
) -> None:
    """
    Sweep an account a frame of the same transaction created. With no
    same-transaction deletion the account keeps its nonce and code once
    the transaction ends, whether the sweep runs in the creating frame
    or in a later one.
    """
    require_frame_transactions(fork)
    beneficiary = pre.fund_eoa(amount=1)
    child_code = Op.SELFDESTRUCT(beneficiary)
    factory, child = deploy_factory(
        pre, child_code, call_child=sweep == "same_frame"
    )
    funding = transfer_log(factory, child, VICTIM_BALANCE)
    swept = transfer_log(child, beneficiary, VICTIM_BALANCE)

    if sweep == "same_frame":
        frames = [
            factory_frame(
                fork, child_code, target=factory, logs=[funding, swept]
            )
        ]
    else:
        frames = [
            factory_frame(fork, child_code, target=factory, logs=[funding]),
            # The creation warmed the child for the frames after it.
            sender_frame(
                target=child, code=child_code, warm=True, logs=[swept]
            ),
        ]

    tx = FrameTransaction.build(
        fork=fork,
        sender=pre.fund_eoa(),
        frames=[verify_frame(), *frames],
    )

    state_test(
        pre=pre,
        tx=tx,
        post={
            factory: Account(nonce=2, balance=0),
            child: Account(nonce=1, code=child_code, balance=0),
            beneficiary: Account(balance_change=VICTIM_BALANCE),
        },
    )


@pytest.mark.parametrize(
    "victim_origin", ["pre_existing", "created_by_earlier_frame"]
)
def test_sendall_unrolled_with_atomic_batch(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    victim_origin: str,
) -> None:
    """
    Unroll an atomic batch whose first frame swept an account: the
    balance returns to the account and the transfer log is dropped.
    """
    require_frame_transactions(fork)
    beneficiary = pre.fund_eoa(amount=1)
    victim_code = Op.SELFDESTRUCT(beneficiary)
    reverter_code = Op.REVERT(0, 0)
    reverter = pre.deploy_contract(code=reverter_code)

    frames: List[FrameCase] = []
    if victim_origin == "pre_existing":
        victim = pre.deploy_contract(code=victim_code, balance=VICTIM_BALANCE)
        victim_post = Account(code=victim_code, balance_change=0)
    else:
        factory, victim = deploy_factory(pre, victim_code)
        frames.append(
            factory_frame(
                fork,
                victim_code,
                target=factory,
                logs=[transfer_log(factory, victim, VICTIM_BALANCE)],
            )
        )
        victim_post = Account(
            nonce=1, code=victim_code, balance=VICTIM_BALANCE
        )

    frames += [
        sender_frame(
            flags=Spec8141.ATOMIC_BATCH_FLAG,
            target=victim,
            code=victim_code,
            warm=victim_origin != "pre_existing",
            outcome=Outcome.UNROLLED,
        ),
        sender_frame(
            target=reverter, code=reverter_code, outcome=Outcome.REVERT
        ),
    ]

    tx = FrameTransaction.build(
        fork=fork,
        sender=pre.fund_eoa(),
        frames=[verify_frame(), *frames],
    )

    state_test(
        pre=pre,
        tx=tx,
        post={
            victim: victim_post,
            beneficiary: Account(balance_change=0),
        },
    )


@pytest.mark.parametrize(
    "state_gas_limit_delta",
    [pytest.param(0, id="exact"), pytest.param(-1, id="one_short")],
)
def test_sendall_to_new_account_draws_frame_state_gas(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    state_gas_limit_delta: int,
) -> None:
    """
    Sweep to an account that does not exist yet. The frame running the
    sweep pays the account's creation from its own state budget, so a
    budget one short halts the frame and nothing moves.
    """
    require_frame_transactions(fork)
    beneficiary = pre.nonexistent_account()
    victim_code = Op.SELFDESTRUCT(beneficiary, account_new=True)
    victim = pre.deploy_contract(code=victim_code, balance=VICTIM_BALANCE)
    swept = state_gas_limit_delta >= 0

    tx = FrameTransaction.build(
        fork=fork,
        sender=pre.fund_eoa(),
        frames=[
            verify_frame(),
            sender_frame(
                target=victim,
                code=victim_code,
                state_gas_limit_delta=state_gas_limit_delta,
                outcome=Outcome.SUCCESS if swept else Outcome.HALT,
                logs=(
                    [transfer_log(victim, beneficiary, VICTIM_BALANCE)]
                    if swept
                    else None
                ),
            ),
        ],
    )

    state_test(
        pre=pre,
        tx=tx,
        post={
            victim: Account(balance=0 if swept else VICTIM_BALANCE),
            beneficiary: (
                Account(balance=VICTIM_BALANCE)
                if swept
                else Account.NONEXISTENT
            ),
        },
    )
