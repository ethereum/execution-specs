"""
Tests for CREATE2 state restoration after reverted sub-calls.
"""

import pytest
from execution_testing import (
    Account,
    Alloc,
    Environment,
    Initcode,
    Op,
    StateTestFiller,
    Storage,
    Transaction,
    compute_create2_address,
)

from .spec import ref_spec_1014

REFERENCE_SPEC_GIT_PATH = ref_spec_1014.git_path
REFERENCE_SPEC_VERSION = ref_spec_1014.version


@pytest.mark.valid_from("Constantinople")
@pytest.mark.pre_alloc_mutable
def test_create2_revert_preserves_balance(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """
    Test that CREATE2 revert preserves pre-existing balance at target.

    Address X has a pre-existing balance but no code. CREATE2 targets X
    with init code that reverts. After the revert, X must still have its
    original balance, nonce=0, and no code or storage.
    """
    env = Environment()
    factory_storage = Storage()
    salt = 0
    pre_balance = 1

    # Init code that writes storage then reverts.
    initcode = Op.SSTORE(0, 1) + Op.REVERT(offset=0, size=0)

    # Factory receives initcode via calldata, does CREATE2.
    factory = pre.deploy_contract(
        Op.CALLDATACOPY(0, 0, Op.CALLDATASIZE)
        + Op.SSTORE(
            factory_storage.store_next(0, "create2_result"),
            Op.CREATE2(
                value=0,
                offset=0,
                size=Op.CALLDATASIZE,
                salt=salt,
            ),
        )
        + Op.STOP,
        storage=factory_storage.canary(),
    )

    target = compute_create2_address(factory, salt, initcode)

    # Pre-allocate target with balance only.
    pre[target] = Account(balance=pre_balance)

    sender = pre.fund_eoa()

    state_test(
        env=env,
        pre=pre,
        post={
            # CREATE2 returns 0 on failure.
            factory: Account(storage=factory_storage),
            # Target keeps its balance, no code deployed.
            target: Account(balance=pre_balance, nonce=0, code=b""),
        },
        tx=Transaction(
            sender=sender,
            to=factory,
            gas_limit=1_000_000,
            data=initcode,
        ),
    )


@pytest.mark.valid_from("Constantinople")
def test_create2_succeeds_after_reverted_create2(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """
    Test that CREATE2 succeeds after a previous CREATE2 at the same address
    was reverted.

    Inner call does CREATE2 then REVERTs. Outer call then does the same
    CREATE2 which should succeed since the first was rolled back.
    """
    env = Environment()
    storage = Storage()
    salt = 1

    runtime_code = Op.SSTORE(0, 1) + Op.STOP
    initcode = Initcode(deploy_code=runtime_code)

    # The "creator" contract that does CREATE2 when called.
    creator_code = (
        Op.CALLDATACOPY(0, 0, Op.CALLDATASIZE)
        + Op.SSTORE(
            0,
            Op.CREATE2(
                value=0,
                offset=0,
                size=Op.CALLDATASIZE,
                salt=salt,
            ),
        )
        + Op.STOP
    )
    creator = pre.deploy_contract(creator_code)

    expected_address = compute_create2_address(creator, salt, initcode)

    # Outer contract:
    # 1. Call creator wrapped in a sub-call that reverts.
    # 2. Call creator again (should succeed).
    #
    # Use a "reverter" contract that calls creator then reverts.
    reverter_code = (
        Op.CALLDATACOPY(0, 0, Op.CALLDATASIZE)
        + Op.POP(
            Op.CALL(
                gas=200_000,
                address=creator,
                args_size=Op.CALLDATASIZE,
            )
        )
        + Op.REVERT(offset=0, size=0)
    )
    reverter = pre.deploy_contract(reverter_code)

    outer_code = (
        Op.CALLDATACOPY(0, 0, Op.CALLDATASIZE)
        # First attempt: call reverter (which calls creator then reverts)
        + Op.SSTORE(
            storage.store_next(0, "reverter_call_result"),
            Op.CALL(
                gas=300_000,
                address=reverter,
                args_size=Op.CALLDATASIZE,
            ),
        )
        # Second attempt: call creator directly (should succeed)
        + Op.SSTORE(
            storage.store_next(1, "creator_call_result"),
            Op.CALL(
                gas=300_000,
                address=creator,
                args_size=Op.CALLDATASIZE,
            ),
        )
        + Op.STOP
    )
    outer = pre.deploy_contract(outer_code, storage=storage.canary())

    sender = pre.fund_eoa()

    state_test(
        env=env,
        pre=pre,
        post={
            outer: Account(storage=storage),
            # The creator stored the CREATE2 result.
            creator: Account(storage={0: expected_address}),
            # The contract was deployed.
            expected_address: Account(code=runtime_code),
        },
        tx=Transaction(
            sender=sender,
            to=outer,
            gas_limit=2_000_000,
            data=initcode,
        ),
    )
