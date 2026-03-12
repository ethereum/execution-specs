"""
Tests for correct state restoration after reverted sub-calls.

Target EIP-6780 (SELFDESTRUCT), EIP-2929 (warm/cold access),
EIP-1153 (transient storage), and CREATE2 interactions.
"""

import pytest
from execution_testing import (
    Account,
    Alloc,
    CodeGasMeasure,
    Conditional,
    Environment,
    Fork,
    Initcode,
    Op,
    StateTestFiller,
    Storage,
    Transaction,
    compute_create2_address,
)

REFERENCE_SPEC_GIT_PATH = "EIPS/eip-6780.md"
REFERENCE_SPEC_VERSION = "1b6a0e94cc47e859b9866e570391cf37dc55059a"


@pytest.mark.valid_from("Cancun")
def test_tstore_reverted_by_subcall(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """
    Test that TSTORE changes are rolled back when a sub-call reverts.

    Outer call sets TSTORE(0, 42). Inner call sets TSTORE(0, 99) and
    TSTORE(1, 77) then REVERTs. After revert, TLOAD(0) must return 42
    and TLOAD(1) must return 0.
    """
    env = Environment()
    storage = Storage()

    # Contract calls itself: first invocation is "outer", re-entry is
    # "inner" (distinguished by TLOAD(0) == 0).
    inner_code = (
        Op.TSTORE(0, 99) + Op.TSTORE(1, 77) + Op.REVERT(offset=0, size=0)
    )

    outer_code = (
        Op.TSTORE(0, 42)
        + Op.POP(Op.CALL(gas=100_000, address=Op.ADDRESS))
        + Op.SSTORE(
            storage.store_next(42, "tload_0_after_revert"),
            Op.TLOAD(0),
        )
        + Op.SSTORE(
            storage.store_next(0, "tload_1_after_revert"),
            Op.TLOAD(1),
        )
        + Op.STOP
    )

    # Distinguish outer vs inner call: outer has TLOAD(0) == 0.
    code = Conditional(
        condition=Op.TLOAD(0),
        if_true=inner_code,
        if_false=outer_code,
    )

    contract = pre.deploy_contract(code)
    sender = pre.fund_eoa()

    state_test(
        env=env,
        pre=pre,
        post={contract: Account(storage=storage)},
        tx=Transaction(
            sender=sender,
            to=contract,
            gas_limit=1_000_000,
        ),
    )


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
    salt = 0
    pre_balance = 3_000_000_000

    # Init code that writes storage then reverts.
    initcode = Op.SSTORE(0, 1) + Op.REVERT(offset=0, size=0)

    # Factory receives initcode via calldata, does CREATE2.
    factory = pre.deploy_contract(
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

    target = compute_create2_address(factory, salt, initcode)

    # Pre-allocate target with balance only.
    pre[target] = Account(balance=pre_balance)

    sender = pre.fund_eoa()

    state_test(
        env=env,
        pre=pre,
        post={
            # CREATE2 returns 0 on failure.
            factory: Account(storage={0: 0}),
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
    outer = pre.deploy_contract(outer_code)

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


@pytest.mark.valid_from("Cancun")
def test_selfdestruct_balance_transfer_reverted(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """
    Test that SELFDESTRUCT balance transfer is reverted on sub-call revert.

    Post-Cancun, SELFDESTRUCT does not destroy the contract but still
    transfers balance. When the sub-call containing SELFDESTRUCT reverts,
    the balance transfer must also be reverted.
    """
    env = Environment()
    storage = Storage()

    victim_balance = 10_000_000_000

    beneficiary_balance = 1
    beneficiary = pre.fund_eoa(amount=beneficiary_balance)

    victim = pre.deploy_contract(
        code=Op.SELFDESTRUCT(beneficiary),
        balance=victim_balance,
    )

    # Controller calls victim (triggers SELFDESTRUCT) then reverts.
    controller = pre.deploy_contract(
        Op.POP(Op.CALL(gas=100_000, address=victim))
        + Op.REVERT(offset=0, size=0)
    )

    # Outer calls controller, then checks beneficiary balance.
    outer = pre.deploy_contract(
        Op.POP(Op.CALL(gas=200_000, address=controller))
        + Op.SSTORE(
            storage.store_next(beneficiary_balance, "beneficiary_balance"),
            Op.BALANCE(beneficiary),
        )
        + Op.SSTORE(
            storage.store_next(victim_balance, "victim_balance"),
            Op.BALANCE(victim),
        )
        + Op.STOP
    )

    sender = pre.fund_eoa()

    state_test(
        env=env,
        pre=pre,
        post={
            outer: Account(storage=storage),
            # Beneficiary keeps only its initial balance (transfer reverted).
            beneficiary: Account(balance=beneficiary_balance),
            # Victim still has its balance.
            victim: Account(balance=victim_balance),
        },
        tx=Transaction(
            sender=sender,
            to=outer,
            gas_limit=1_000_000,
        ),
    )


@pytest.mark.valid_from("Berlin")
def test_storage_warm_status_reverted_by_subcall(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    Test that storage slot warm status is reverted when a sub-call reverts.

    Inner self-call does SLOAD(0) and SSTORE(0, 2) then REVERTs. After
    revert, SLOAD(0) must be a cold access and storage[0] must still
    hold its original value.
    """
    env = Environment()

    # Inner behavior (no calldata): warm slot 0 via SLOAD+SSTORE, revert.
    inner_code = (
        Op.POP(Op.SLOAD(0)) + Op.SSTORE(0, 2) + Op.REVERT(offset=0, size=0)
    )

    # Overhead: PUSH instructions for the SLOAD key argument.
    sload_push_cost = (Op.PUSH1(0) * len(Op.SLOAD.kwargs)).gas_cost(fork)
    cold_sload_cost = Op.SLOAD(key_warm=False).gas_cost(fork)

    # After revert, measure gas of SLOAD(0) — should be cold.
    sload_measure = CodeGasMeasure(
        code=Op.SLOAD(0),
        overhead_cost=sload_push_cost,
        extra_stack_items=1,
        sstore_key=1,
        stop=False,
    )

    # Also verify storage[0] value (should still be 1).
    verify_value = Op.SSTORE(2, Op.SLOAD(0))

    # Outer behavior (has calldata): call self (inner), measure, verify.
    outer_code = (
        Op.POP(Op.CALL(gas=100_000, address=Op.ADDRESS))
        + sload_measure
        + verify_value
        + Op.STOP
    )

    code = Conditional(
        condition=Op.CALLDATASIZE,
        if_true=outer_code,
        if_false=inner_code,
    )

    contract = pre.deploy_contract(code, storage={0: 1})
    sender = pre.fund_eoa()

    state_test(
        env=env,
        pre=pre,
        post={
            contract: Account(
                storage={0: 1, 1: cold_sload_cost, 2: 1},
            ),
        },
        tx=Transaction(
            sender=sender,
            to=contract,
            gas_limit=1_000_000,
            data=b"\x01",
        ),
    )


@pytest.mark.valid_from("Berlin")
def test_account_warm_status_reverted_by_subcall(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    Test that account warm status is reverted when a sub-call reverts.

    Inner call does BALANCE(target) then REVERTs. After revert,
    BALANCE(target) in the outer call must be a cold access.
    """
    env = Environment()

    target = pre.fund_eoa(amount=1)

    # Inner: BALANCE(target) warms target, then reverts.
    inner = pre.deploy_contract(
        Op.POP(Op.BALANCE(target)) + Op.REVERT(offset=0, size=0)
    )

    # Overhead: PUSH for the BALANCE address argument.
    balance_push_cost = (Op.PUSH1(0) * len(Op.BALANCE.kwargs)).gas_cost(fork)
    cold_balance_cost = Op.BALANCE(address_warm=False).gas_cost(fork)

    # Outer: call inner (reverts), then measure BALANCE(target) gas.
    outer = pre.deploy_contract(
        Op.POP(Op.CALL(gas=100_000, address=inner))
        + CodeGasMeasure(
            code=Op.BALANCE(target),
            overhead_cost=balance_push_cost,
            extra_stack_items=1,
            sstore_key=0,
        )
    )

    sender = pre.fund_eoa()

    state_test(
        env=env,
        pre=pre,
        post={outer: Account(storage={0: cold_balance_cost})},
        tx=Transaction(
            sender=sender,
            to=outer,
            gas_limit=1_000_000,
        ),
    )
