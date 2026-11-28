"""
A touch made in a frame that reverts must not delete an empty account.

EIP-161 deletes an empty account touched by a transaction. The touch is part
of the frame's state changes, so it is discarded when the frame reverts, and
only a touch that survives to the end of the transaction deletes the account.
"""

from typing import Callable

import pytest
from execution_testing import (
    Account,
    Address,
    Alloc,
    Bytecode,
    Macros,
    Op,
    StateTestFiller,
    Storage,
    Transaction,
)

from .spec import ref_spec_161

REFERENCE_SPEC_GIT_PATH = ref_spec_161.git_path
REFERENCE_SPEC_VERSION = ref_spec_161.version

LEGACY_URL = (
    "https://github.com/ethereum/legacytests/blob/master"
    "/src/LegacyTests/Cancun/GeneralStateTestsFiller/stRevertTest"
)
STATIC_URL = "state_tests/stRevertTest"

pytestmark = pytest.mark.valid_from("SpuriousDragon")

target_kinds = pytest.mark.parametrize(
    "target_kind",
    [
        # EIP-7523 rules out empty accounts in the state from the Merge on.
        pytest.param("empty", marks=pytest.mark.valid_until("London")),
        pytest.param("funded"),
    ],
)


def make_target(pre: Alloc, target_kind: str) -> Address:
    """Add the touched account to the pre-state."""
    if target_kind == "empty":
        return pre.empty_account()
    elif target_kind == "funded":
        return pre.fund_eoa(amount=1)
    else:
        raise ValueError(f"unknown target kind: {target_kind}")


def expected_target(target_kind: str, deleted: bool) -> Account | None:
    """Return the post-state of the touched account."""
    if target_kind == "empty":
        return Account.NONEXISTENT if deleted else Account(balance=0)
    elif target_kind == "funded":
        return Account(balance=1)
    else:
        raise ValueError(f"unknown target kind: {target_kind}")


@pytest.mark.ported_from(
    [
        f"{LEGACY_URL}/TouchToEmptyAccountRevertFiller.json",
        f"{STATIC_URL}/TouchToEmptyAccountRevert_ParisFiller.json",
    ],
    pr=["https://github.com/ethereum/execution-specs/pull/2388"],
)
@target_kinds
def test_touch_reverted_by_failed_transaction(
    state_test: StateTestFiller,
    pre: Alloc,
    target_kind: str,
) -> None:
    """
    Test that a touch two frames deep is discarded when the transaction
    runs out of gas in its top frame.
    """
    target = make_target(pre, target_kind)
    toucher = pre.deploy_contract(Op.CALL(gas=Op.GAS, address=target))
    entry = pre.deploy_contract(
        Op.POP(Op.CALL(gas=Op.GAS, address=toucher)) + Macros.OOG
    )

    state_test(
        pre=pre,
        post={target: expected_target(target_kind, deleted=False)},
        tx=Transaction(sender=pre.fund_eoa(), to=entry),
    )


def touch_then_revert(
    pre: Alloc,
    touch: Callable[[], Bytecode],
    persisted_touch: bool,
) -> tuple[Address, Storage]:
    """
    Deploy a contract that calls a helper running `touch()` and then
    running out of gas, after running `touch()` itself when
    `persisted_touch` is set. `touch()` must push one value.
    """
    storage = Storage()
    code = Bytecode()
    if persisted_touch:
        code += Op.SSTORE(storage.store_next(1), touch())
    reverted = pre.deploy_contract(Op.POP(touch()) + Macros.OOG)
    code += Op.SSTORE(
        storage.store_next(0), Op.CALL(gas=100_000, address=reverted)
    )
    entry = pre.deploy_contract(code, storage=storage.canary())
    return entry, storage


@pytest.mark.ported_from(
    [
        f"{LEGACY_URL}/TouchToEmptyAccountRevert2Filler.json",
        f"{STATIC_URL}/TouchToEmptyAccountRevert2_ParisFiller.json",
    ],
    pr=["https://github.com/ethereum/execution-specs/pull/2388"],
)
@pytest.mark.parametrize("persisted_touch", [True, False])
@target_kinds
def test_call_touch_then_reverted_call_touch(
    state_test: StateTestFiller,
    pre: Alloc,
    target_kind: str,
    persisted_touch: bool,
) -> None:
    """
    Test that a zero-value CALL touch deletes the account unless the frame
    that made it reverted.
    """
    target = make_target(pre, target_kind)
    entry, storage = touch_then_revert(
        pre, lambda: Op.CALL(gas=Op.GAS, address=target), persisted_touch
    )

    state_test(
        pre=pre,
        post={
            entry: Account(storage=storage),
            target: expected_target(target_kind, deleted=persisted_touch),
        },
        tx=Transaction(sender=pre.fund_eoa(), to=entry),
    )


@pytest.mark.ported_from(
    [
        f"{LEGACY_URL}/TouchToEmptyAccountRevert3Filler.json",
        f"{STATIC_URL}/TouchToEmptyAccountRevert3_ParisFiller.json",
    ],
    pr=["https://github.com/ethereum/execution-specs/pull/2388"],
)
@pytest.mark.parametrize("persisted_touch", [True, False])
@target_kinds
def test_selfdestruct_touch_then_reverted_selfdestruct_touch(
    state_test: StateTestFiller,
    pre: Alloc,
    target_kind: str,
    persisted_touch: bool,
) -> None:
    """
    Test that naming the account as a zero-balance SELFDESTRUCT beneficiary
    deletes it unless the frame that did so reverted.
    """
    target = make_target(pre, target_kind)
    # Each touch calls a contract of its own, so the reverted SELFDESTRUCT
    # does not repeat one on an account already destroyed.
    entry, storage = touch_then_revert(
        pre,
        lambda: Op.CALL(
            gas=Op.GAS,
            address=pre.deploy_contract(Op.SELFDESTRUCT(target)),
        ),
        persisted_touch,
    )

    state_test(
        pre=pre,
        post={
            entry: Account(storage=storage),
            target: expected_target(target_kind, deleted=persisted_touch),
        },
        tx=Transaction(sender=pre.fund_eoa(), to=entry),
    )
