"""
Test EIP-8037 spill-refund accounting across call frames.

With the transaction gas limit below the EIP-7825 cap the reservoir is
empty, so every state charge spills from `gas_left`. A restoration
refund credited in a re-entered frame is an advance against an
ancestor's spilled sets and must discharge through the intermediate
merges; a reverted or halted frame refills its own spill locally and
must not export it; a top-level exceptional halt burns spilled state
gas in the regular dimension while the intrinsic authorization state
gas stays in the state dimension.

Tests for [EIP-8037: State Creation Gas Cost Increase]
(https://eips.ethereum.org/EIPS/eip-8037).
"""

import pytest
from execution_testing import (
    Account,
    Address,
    Alloc,
    AuthorizationTuple,
    Conditional,
    Fork,
    Header,
    Op,
    StateTestFiller,
    Storage,
    Transaction,
)

from tests.prague.eip7702_set_code_tx.spec import Spec as Spec7702

from .spec import ref_spec_8037

REFERENCE_SPEC_GIT_PATH = ref_spec_8037.git_path
REFERENCE_SPEC_VERSION = ref_spec_8037.version


def _revoked_advance_call_tree(pre: Alloc) -> Address:
    """
    Deploy a call tree whose entry sets two slots (both spilled), and
    whose middle frame — holding one spilled set of its own — value
    calls back into the entry, which imports a reverted child call and
    then clears both slots. The two-clear advance is only partially
    dischargeable against the middle frame's usage; the entry then
    exceptionally halts, revoking the rest.

    Returns the entry contract's address.
    """
    reverting = pre.deploy_contract(code=Op.SSTORE(0, 1) + Op.REVERT(0, 0))
    middle = pre.deploy_contract(
        code=(
            Op.SSTORE(0, 1)
            + Op.POP(Op.CALL(gas=Op.GAS, address=Op.CALLER, value=1))
            + Op.STOP
        ),
        balance=1,
    )
    return pre.deploy_contract(
        code=Conditional(
            condition=Op.CALLVALUE,
            if_true=(
                Op.POP(Op.CALL(gas=Op.GAS, address=reverting))
                + Op.SSTORE(0, 0)
                + Op.SSTORE(1, 0)
                + Op.STOP
            ),
            if_false=(
                Op.SSTORE(0, 1)
                + Op.SSTORE(1, 1)
                + Op.POP(Op.CALL(gas=Op.GAS, address=middle))
                + Op.INVALID
            ),
        ),
    )


@pytest.mark.parametrize(
    "ending",
    [
        pytest.param("success", id="all_frames_succeed"),
        pytest.param("top_revert", id="top_level_reverts"),
        pytest.param("middle_revert", id="middle_reverts_after_clear"),
    ],
)
@pytest.mark.valid_from("EIP8037")
def test_cross_frame_refund_advance(
    state_test: StateTestFiller,
    pre: Alloc,
    ending: str,
) -> None:
    """
    Verify a restoration refund credited in a re-entered frame (an
    advance against the entry frame's spilled sets) discharges through
    the middle frame's merge on success, is void when the top level
    reverts, and is revoked when the middle frame reverts after the
    clear — leaving both slots set and the sender paying their full
    state gas.
    """
    middle_ending = Op.REVERT(0, 0) if ending == "middle_revert" else Op.STOP
    middle = pre.deploy_contract(
        code=(
            Op.POP(Op.CALL(gas=Op.GAS, address=Op.CALLER, args_size=1))
            + middle_ending
        ),
    )

    entry_ending = Op.REVERT(0, 0) if ending == "top_revert" else Op.STOP
    entry = pre.deploy_contract(
        code=Conditional(
            condition=Op.CALLDATASIZE,
            # Re-entered: clear both slots; each refund is credited
            # here as an advance.
            if_true=Op.SSTORE(0, 0) + Op.SSTORE(1, 0) + Op.STOP,
            if_false=(
                Op.SSTORE(0, 1)
                + Op.SSTORE(1, 1)
                + Op.SSTORE(2, Op.CALL(gas=Op.GAS, address=middle))
                + entry_ending
            ),
        ),
    )

    tx = Transaction(
        to=entry,
        gas_limit=1_000_000,
        sender=pre.fund_eoa(),
    )

    if ending == "success":
        storage = {0: 0, 1: 0, 2: 1}
    elif ending == "top_revert":
        storage = {}
    else:
        storage = {0: 1, 1: 1, 2: 0}

    post = {entry: Account(storage=storage)}
    state_test(pre=pre, post=post, tx=tx)


@pytest.mark.valid_from("EIP8037")
def test_reverted_grandchild_spill_through_child_halt(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """
    Verify a grandchild's reverted spill does not ride through the
    child's exceptional halt into the caller's accounting: the sender
    pays the halted child's forwarded budget exactly once, not the
    grandchild's refilled spill on top.
    """
    grandchild = pre.deploy_contract(code=Op.SSTORE(0, 1) + Op.REVERT(0, 0))
    child = pre.deploy_contract(
        code=Op.POP(Op.CALL(gas=Op.GAS, address=grandchild)) + Op.INVALID,
    )

    storage = Storage()
    caller = pre.deploy_contract(
        code=(
            Op.SSTORE(
                storage.store_next(0, "child_halted"),
                Op.CALL(gas=400_000, address=child),
            )
            + Op.SSTORE(storage.store_next(1, "caller_completed"), 1)
        ),
    )

    tx = Transaction(
        to=caller,
        gas_limit=1_000_000,
        sender=pre.fund_eoa(),
    )

    post = {
        caller: Account(storage=storage),
        grandchild: Account(storage={0: 0}),
    }
    state_test(pre=pre, post=post, tx=tx)


@pytest.mark.valid_from("EIP8037")
def test_soft_failed_value_call_refund_through_child_halt(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """
    Verify a same-frame NEW_ACCOUNT charge-and-refund (a value CALL
    soft-failing the balance check) performed after a reverted child
    call, merged into a frame with its own spilled set that then
    exceptionally halts, charges the sender the halted frame's budget
    exactly once.
    """
    grandchild = pre.deploy_contract(code=Op.SSTORE(0, 1) + Op.REVERT(0, 0))
    fresh = pre.nonexistent_account()
    # Zero balance: the value CALL soft-fails its balance check after
    # the up-front NEW_ACCOUNT state charge, refunded in-frame.
    middle = pre.deploy_contract(
        code=(
            Op.POP(Op.CALL(gas=Op.GAS, address=grandchild))
            + Op.POP(Op.CALL(gas=Op.GAS, address=fresh, value=1))
            + Op.STOP
        ),
    )
    child = pre.deploy_contract(
        code=(
            Op.SSTORE(0, 1)
            + Op.POP(Op.CALL(gas=Op.GAS, address=middle))
            + Op.INVALID
        ),
    )

    storage = Storage()
    caller = pre.deploy_contract(
        code=(
            Op.SSTORE(
                storage.store_next(0, "child_halted"),
                Op.CALL(gas=600_000, address=child),
            )
            + Op.SSTORE(storage.store_next(1, "caller_completed"), 1)
        ),
    )

    tx = Transaction(
        to=caller,
        gas_limit=1_000_000,
        sender=pre.fund_eoa(),
    )

    post = {
        caller: Account(storage=storage),
        child: Account(storage={0: 0}),
        fresh: Account.NONEXISTENT,
    }
    state_test(pre=pre, post=post, tx=tx)


@pytest.mark.valid_from("EIP8037")
def test_partially_discharged_advance_revoked_by_halt(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """
    Verify an advance only partially dischargeable in the middle frame
    (two clears against one middle set) is fully revoked when the entry
    frame exceptionally halts, so the sender pays the entry's whole
    forwarded budget and the caller's accounting is undisturbed.
    """
    entry = _revoked_advance_call_tree(pre)

    storage = Storage()
    caller = pre.deploy_contract(
        code=(
            Op.SSTORE(
                storage.store_next(0, "entry_halted"),
                Op.CALL(gas=600_000, address=entry),
            )
            + Op.SSTORE(storage.store_next(1, "caller_completed"), 1)
        ),
    )

    tx = Transaction(
        to=caller,
        gas_limit=1_000_000,
        sender=pre.fund_eoa(),
    )

    post = {
        caller: Account(storage=storage),
        entry: Account(storage={0: 0, 1: 0}),
    }
    state_test(pre=pre, post=post, tx=tx)


@pytest.mark.parametrize(
    "inner_shape",
    [
        pytest.param("burned_child_spill", id="burned_child_spill"),
        pytest.param("revoked_advance", id="revoked_advance"),
    ],
)
@pytest.mark.valid_from("EIP8037")
def test_top_level_halt_keeps_intrinsic_auth_state_gas(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    inner_shape: str,
) -> None:
    """
    Verify a top-level exceptional halt keeps the full authorization
    state gas in the state dimension while the burned child spill stays
    in the regular dimension: the header reports
    ``max(gas_limit - auth_state, auth_state)`` regardless of the
    spill shape burned inside the halted frame.
    """
    gas_limit = 1_000_000

    if inner_shape == "burned_child_spill":
        inner = pre.deploy_contract(code=Op.SSTORE(0, 1) + Op.INVALID)
    else:
        inner = _revoked_advance_call_tree(pre)

    recipient = pre.deploy_contract(
        code=Op.POP(Op.CALL(gas=Op.GAS, address=inner)) + Op.INVALID,
    )

    delegate = pre.deploy_contract(code=Op.STOP)
    signer = pre.fund_eoa(amount=0)
    authorization_list = [
        AuthorizationTuple(
            address=delegate,
            nonce=0,
            signer=signer,
            creates_account=True,
            writes_delegation=True,
        ),
    ]
    auth_state_gas = fork.transaction_top_frame_state_gas(
        authorizations=authorization_list,
    )

    tx = Transaction(
        ty=4,
        to=recipient,
        gas_limit=gas_limit,
        authorization_list=authorization_list,
        sender=pre.fund_eoa(),
    )

    post = {
        signer: Account(code=Spec7702.delegation_designation(delegate)),
    }
    state_test(
        pre=pre,
        post=post,
        tx=tx,
        blockchain_test_header_verify=Header(
            gas_used=max(gas_limit - auth_state_gas, auth_state_gas)
        ),
    )
