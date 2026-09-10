"""
Test EIP-161 empty account cleanup with reverted touches.

Verify that empty accounts are correctly deleted (or preserved) when
touched via CALL or SELFDESTRUCT, including cases where a sub-call
that touches the account reverts due to out-of-gas.
"""

import pytest
from execution_testing import (
    Account,
    Address,
    Alloc,
    Macros,
    Op,
    StateTestFiller,
    Storage,
    Transaction,
)

REFERENCE_SPEC_GIT_PATH = "EIPS/eip-161.md"
REFERENCE_SPEC_VERSION = "96523ef4d76ca440f73f0403ddb5c9cb3b24dcae"

STATIC_URL = (
    "https://github.com/ethereum/tests/blob/v13.3"
    "/src/GeneralStateTestsFiller/stRevertTest"
)
LEGACY_URL = (
    "https://github.com/ethereum/tests/blob/v13.3"
    "/LegacyTests/Cancun/GeneralStateTestsFiller/stRevertTest"
)

pytestmark = [
    pytest.mark.valid_from("Istanbul"),
    pytest.mark.pre_alloc_mutable,
]


@pytest.mark.ported_from(
    [
        f"{LEGACY_URL}/TouchToEmptyAccountRevertFiller.json",
        f"{STATIC_URL}/TouchToEmptyAccountRevertFiller.json",
        f"{STATIC_URL}/TouchToEmptyAccountRevert_ParisFiller.json",
    ],
    pr=["https://github.com/ethereum/execution-specs/pull/2388"],
)
@pytest.mark.parametrize(
    "target_balance",
    [
        pytest.param(0, id="empty"),
        pytest.param(1, id="funded"),
    ],
)
def test_touch_empty_account_call_chain(
    state_test: StateTestFiller,
    pre: Alloc,
    target_balance: int,
) -> None:
    """
    Test EIP-161 deletion of an account touched by zero-value CALL
    through a call chain.

    Call chain: tx -> entry -> intermediary -> target.
    An empty target is deleted; a funded target survives.
    """
    storage = Storage()
    target = pre.nonexistent_account()
    pre.fund_address(target, target_balance)

    intermediary_code = Op.CALL(gas=Op.GAS, address=target) + Op.POP
    intermediary = pre.deploy_contract(intermediary_code)

    entry_code = Op.SSTORE(
        storage.store_next(1),
        Op.CALL(gas=Op.GAS, address=intermediary),
    ) + Op.SSTORE(storage.store_next(1), 1)
    entry = pre.deploy_contract(entry_code, storage=storage.canary())

    tx = Transaction(
        sender=pre.fund_eoa(),
        to=entry,
        gas_limit=200_000,
    )

    post: dict[Address, Account | None] = {
        entry: Account(storage=storage),
    }
    if target_balance > 0:
        post[target] = Account(balance=target_balance)
    else:
        # EIP-161: empty account touched by zero-value CALL is deleted.
        post[target] = Account.NONEXISTENT

    state_test(pre=pre, post=post, tx=tx)


@pytest.mark.ported_from(
    [
        f"{LEGACY_URL}/TouchToEmptyAccountRevert2Filler.json",
        f"{STATIC_URL}/TouchToEmptyAccountRevert2Filler.json",
        f"{STATIC_URL}/TouchToEmptyAccountRevert2_ParisFiller.json",
    ],
    pr=["https://github.com/ethereum/execution-specs/pull/2388"],
)
@pytest.mark.parametrize(
    "target_balance",
    [
        pytest.param(0, id="empty"),
        pytest.param(1, id="funded"),
    ],
)
def test_touch_empty_account_call_then_oog(
    state_test: StateTestFiller,
    pre: Alloc,
    target_balance: int,
) -> None:
    """
    Test empty account deletion when touched by CALL then a sub-call
    reverts due to out-of-gas.

    The entry contract CALLs the target directly (touch persists),
    then CALLs a helper that also touches the target but runs OOG.
    For an empty target, the non-reverted touch triggers EIP-161
    deletion. A funded target survives.
    """
    storage = Storage()
    target = pre.nonexistent_account()
    pre.fund_address(target, target_balance)

    # Helper that CALLs the target then runs OOG.
    oog_helper_code = (
        Op.CALL(gas=100_000, address=target) + Op.POP + Macros.OOG
    )
    oog_helper = pre.deploy_contract(oog_helper_code)

    entry_code = Op.SSTORE(
        storage.store_next(1),
        Op.CALL(gas=200_000, address=target),
    ) + Op.SSTORE(
        storage.store_next(0),
        Op.CALL(gas=200_000, address=oog_helper),
    )
    entry = pre.deploy_contract(entry_code, storage=storage.canary())

    tx = Transaction(
        sender=pre.fund_eoa(),
        to=entry,
        gas_limit=1_000_000,
    )

    post: dict[Address, Account | None] = {
        entry: Account(storage=storage),
    }
    if target_balance > 0:
        post[target] = Account(balance=target_balance)
    else:
        post[target] = Account.NONEXISTENT

    state_test(pre=pre, post=post, tx=tx)


@pytest.mark.ported_from(
    [
        f"{LEGACY_URL}/TouchToEmptyAccountRevert3Filler.json",
        f"{STATIC_URL}/TouchToEmptyAccountRevert3Filler.json",
        f"{STATIC_URL}/TouchToEmptyAccountRevert3_ParisFiller.json",
    ],
    pr=["https://github.com/ethereum/execution-specs/pull/2388"],
)
@pytest.mark.parametrize(
    "target_balance",
    [
        pytest.param(0, id="empty"),
        pytest.param(1, id="funded"),
    ],
)
def test_touch_empty_account_selfdestruct_then_oog(
    state_test: StateTestFiller,
    pre: Alloc,
    target_balance: int,
) -> None:
    """
    Test empty account deletion when touched as SELFDESTRUCT beneficiary
    then a sub-call reverts due to out-of-gas.

    The entry contract CALLs a contract that SELFDESTRUCTs to the
    target (touch persists), then CALLs a helper where another
    SELFDESTRUCT to the target is followed by OOG. For an empty
    target, the non-reverted touch triggers EIP-161 deletion.
    """
    storage = Storage()
    target = pre.nonexistent_account()
    pre.fund_address(target, target_balance)

    sd_code = Op.SELFDESTRUCT(target)
    sd1 = pre.deploy_contract(sd_code)

    # Helper that triggers SELFDESTRUCT to target then runs OOG.
    sd2 = pre.deploy_contract(sd_code)
    oog_helper_code = Op.CALL(gas=100_000, address=sd2) + Op.POP + Macros.OOG
    oog_helper = pre.deploy_contract(oog_helper_code)

    entry_code = Op.SSTORE(
        storage.store_next(1),
        Op.CALL(gas=200_000, address=sd1),
    ) + Op.SSTORE(
        storage.store_next(0),
        Op.CALL(gas=200_000, address=oog_helper),
    )
    entry = pre.deploy_contract(entry_code, storage=storage.canary())

    tx = Transaction(
        sender=pre.fund_eoa(),
        to=entry,
        gas_limit=1_000_000,
    )

    post: dict[Address, Account | None] = {
        entry: Account(storage=storage),
    }
    if target_balance > 0:
        post[target] = Account(balance=target_balance)
    else:
        post[target] = Account.NONEXISTENT

    state_test(pre=pre, post=post, tx=tx)
