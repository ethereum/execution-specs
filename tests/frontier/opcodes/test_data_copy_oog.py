"""
Test data copy OOG regression.
"""

import pytest
from execution_testing import (
    Account,
    Alloc,
    Environment,
    Op,
    StateTestFiller,
    Storage,
    Transaction,
)

REFERENCE_SPEC_GIT_PATH = "EIPS/eip-211.md"
REFERENCE_SPEC_VERSION = "1.0.0"

pytestmark = pytest.mark.valid_from("Byzantium")

# Gas costs for data copy operations:
# - Static cost: 3 gas
# - Word copy cost: 3 * ceil(size/32) gas
# - Memory expansion: 3 * words + words^2/512

# For 0x400 (1024) bytes = 32 words:
# - Word copy cost: 3 * 32 = 96 gas
# - Memory expansion (from 0): 3 * 32 + 32^2/512 = 96 + 2 = 98 gas
# - Static cost: 3 gas
# - Total CALLDATACOPY: ~200 gas (with memory expansion)

# We give enough gas for memory expansion but not for word copy cost
# to trigger the bug.

COPY_SIZE = 0x400  # 1024 bytes = 32 words


@pytest.mark.parametrize(
    "subcall_gas,expect_success",
    [
        pytest.param(
            5000,
            True,
            id="sufficient_gas",
        ),
        pytest.param(
            # Enough for: MSTORE + memory expansion + static CALLDATACOPY
            # But NOT enough for word copy cost (3 gas per 32-byte word)
            150,
            False,
            id="insufficient_gas_for_word_copy_cost",
        ),
    ],
)
def test_calldatacopy_word_copy_oog(
    state_test: StateTestFiller,
    pre: Alloc,
    subcall_gas: int,
    expect_success: bool,
) -> None:
    """
    Test that CALLDATACOPY properly consumes gas for word copy cost.

    Uses a sub-call with controlled gas to isolate the test from intrinsic
    gas costs that vary across forks.
    """
    storage = Storage()
    storage_key = storage.store_next(1 if expect_success else 0)

    # Inner contract: performs CALLDATACOPY and stores success marker
    inner_code = (
        # Pre-expand memory to cover COPY_SIZE
        Op.MSTORE(COPY_SIZE - 0x20, 0)
        # CALLDATACOPY - should consume word copy gas
        + Op.CALLDATACOPY(dest_offset=0, offset=0, size=COPY_SIZE)
        # If we reach here, sufficient gas was available
        + Op.MSTORE8(0, 1)
        + Op.RETURN(0, 1)
    )
    inner_address = pre.deploy_contract(inner_code)

    # Outer contract: calls inner with controlled gas, stores call success
    # CALL pushes 1 on success, 0 on OOG/revert
    # Stack after CALL: [success]
    # PUSH key, then SSTORE pops [key, value] -> storage[key] = value
    outer_code = (
        Op.CALL(
            gas=subcall_gas,
            address=inner_address,
            value=0,
            args_offset=0,
            args_size=0,
            ret_offset=0,
            ret_size=1,
        )
        # Stack: [success (0 or 1)]
        + Op.PUSH1[storage_key]
        # Stack: [storage_key, success]
        + Op.SSTORE
        # Stores storage[storage_key] = success
        + Op.STOP
    )
    outer_address = pre.deploy_contract(outer_code)

    sender = pre.fund_eoa()

    tx = Transaction(
        to=outer_address,
        sender=sender,
        gas_limit=500_000,  # Plenty of gas for outer call
    )

    post = {outer_address: Account(storage=storage)}

    state_test(
        env=Environment(),
        pre=pre,
        post=post,
        tx=tx,
    )


@pytest.mark.parametrize(
    "subcall_gas,expect_success",
    [
        pytest.param(
            5000,
            True,
            id="sufficient_gas",
        ),
        pytest.param(
            150,
            False,
            id="insufficient_gas_for_word_copy_cost",
        ),
    ],
)
def test_codecopy_word_copy_oog(
    state_test: StateTestFiller,
    pre: Alloc,
    subcall_gas: int,
    expect_success: bool,
) -> None:
    """
    Test that CODECOPY properly consumes gas for word copy cost.
    """
    storage = Storage()
    storage_key = storage.store_next(1 if expect_success else 0)

    inner_code = (
        Op.MSTORE(COPY_SIZE - 0x20, 0)
        + Op.CODECOPY(dest_offset=0, offset=0, size=COPY_SIZE)
        + Op.MSTORE8(0, 1)
        + Op.RETURN(0, 1)
    )
    inner_address = pre.deploy_contract(inner_code)

    outer_code = (
        Op.CALL(
            gas=subcall_gas,
            address=inner_address,
            value=0,
            args_offset=0,
            args_size=0,
            ret_offset=0,
            ret_size=1,
        )
        + Op.PUSH1[storage_key]
        + Op.SSTORE
        + Op.STOP
    )
    outer_address = pre.deploy_contract(outer_code)

    sender = pre.fund_eoa()

    tx = Transaction(
        to=outer_address,
        sender=sender,
        gas_limit=500_000,
    )

    post = {outer_address: Account(storage=storage)}

    state_test(
        env=Environment(),
        pre=pre,
        post=post,
        tx=tx,
    )
