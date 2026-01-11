"""
Test data copy OOG regression.

This test is a regression test for:
https://github.com/NethermindEth/nethermind/pull/10116

The bug was in `ConsumeDataCopyGas` where `UpdateGas` (which returns a bool
indicating if sufficient gas is available) was called instead of `Consume`
(which actually consumes gas). Since the bool return value wasn't checked,
execution would continue even when there wasn't enough gas for the data
copy word cost.

Key insight: Memory expansion OOG is handled separately and correctly.
The bug triggers when:
1. Memory expansion check passes (enough gas for memory expansion)
2. But NOT enough gas for the data copy word cost (3 gas per 32-byte word)

This affects: CALLDATACOPY, CODECOPY, EXTCODECOPY, RETURNDATACOPY

Only CALLDATACOPY and CODECOPY are tested here. EXTCODECOPY and RETURNDATACOPY
are omitted because:
- EXTCODECOPY: Address access costs vary by fork (700 pre-Berlin, 2600 cold /
  100 warm in Berlin+ per EIP-2929), making gas calibration complex
- RETURNDATACOPY: Requires nested CALLs to populate return data, adding gas
  accounting complexity (63/64 rule, call overhead, etc.)
Since all four opcodes use the same ConsumeDataCopyGas function, testing
CALLDATACOPY and CODECOPY adequately covers the word copy cost bug.

Test approach: Use a sub-call with controlled gas to isolate the word copy
cost from intrinsic gas costs that vary across forks.

Why sub-calls work for isolation:
- Intrinsic gas (21000 base + calldata cost) only applies to top-level tx
- The 63/64 rule (EIP-150) doesn't reduce gas when passing small amounts
  with plenty of remaining gas (e.g., passing 150 with 500k remaining)
- CALL costs (base + address access) are paid by caller, not callee
- EIP-150 also ensures caller retains 1/64 of gas after CALL; with 500k gas
  and small subcall amounts, plenty remains for post-call SSTORE (~20k max)
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


@pytest.mark.ported_from(
    [
        "https://github.com/NethermindEth/nethermind/pull/10116",
    ],
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
            # Enough for: MSTORE + memory expansion to COPY_SIZE + static CALLDATACOPY
            # But NOT enough for word copy cost
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


@pytest.mark.ported_from(
    [
        "https://github.com/NethermindEth/nethermind/pull/10116",
    ],
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
