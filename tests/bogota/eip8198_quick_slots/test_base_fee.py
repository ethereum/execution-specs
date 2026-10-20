"""
Base fee update tests for
[EIP-8198: Quick Slots](https://eips.ethereum.org/EIPS/eip-8198).

From the fork onward, the maximum per-block base fee change follows the slot
duration read from the spacing of a block and its parent, up to twelve
seconds per slot, with the multiplication performed before the division. A
block's slot number must exceed its parent's.
"""

from typing import List

import pytest
from execution_testing import (
    Alloc,
    Block,
    BlockchainTestFiller,
    BlockException,
    EIPChecklist,
    Environment,
    Fork,
    Header,
    ParameterSet,
)

from .helpers import (
    BLOCK_GAS_LIMIT,
    block_with_invalid_slot_number,
    gas_spending_transactions,
)
from .spec import Spec, ref_spec_8198

REFERENCE_SPEC_GIT_PATH = ref_spec_8198.git_path
REFERENCE_SPEC_VERSION = ref_spec_8198.version

pytestmark = pytest.mark.valid_from("EIP8198")

SLOT_SECONDS = 10
"""Slot duration of the blocks in the base fee update tests."""


def gas_used_cases(fork: Fork) -> List[ParameterSet]:
    """Return the parent gas used values around the fork's gas target."""
    gas_target = BLOCK_GAS_LIMIT // fork.base_fee_elasticity_multiplier()
    return [
        pytest.param(0, id="empty"),
        pytest.param(gas_target - 1, id="target_minus_one"),
        pytest.param(gas_target, id="at_target"),
        pytest.param(gas_target + 1, id="target_plus_one"),
        pytest.param(BLOCK_GAS_LIMIT, id="full"),
        # At `first_larger_rise_after_full_block` these differ from a single
        # division by the combined denominator, which flooring once more
        # would round up.
        pytest.param(100_000, id="near_empty"),
        pytest.param(BLOCK_GAS_LIMIT - 100_000, id="near_full"),
    ]


def base_fee_cases(fork: Fork) -> List[ParameterSet]:
    """Return parent base fees on both sides of the fork's rounding edges."""
    numerator = fork.base_fee_max_change_numerator(
        seconds_elapsed=SLOT_SECONDS
    )
    denominator = fork.base_fee_max_change_denominator(
        seconds_elapsed=SLOT_SECONDS
    )
    full_block_numerator = numerator * (
        fork.base_fee_elasticity_multiplier() - 1
    )
    # An empty block lowers the base fee by
    # `base_fee * numerator // denominator`, which is zero up to here.
    last_unchanged_by_empty_block = (denominator - 1) // numerator
    # A full block raises it by
    # `max(base_fee * full_block_numerator // denominator, 1)`, which is one
    # wei up to here.
    last_one_wei_rise = (2 * denominator - 1) // full_block_numerator
    return [
        # The framework's default genesis base fee.
        pytest.param(7, id="base_fee_7"),
        pytest.param(
            last_unchanged_by_empty_block,
            id="last_unchanged_by_empty_block",
        ),
        pytest.param(
            last_unchanged_by_empty_block + 1,
            id="first_lowered_by_empty_block",
        ),
        pytest.param(
            last_one_wei_rise, id="last_one_wei_rise_after_full_block"
        ),
        pytest.param(
            last_one_wei_rise + 1, id="first_larger_rise_after_full_block"
        ),
        pytest.param(10**9, id="base_fee_1_gwei"),
        pytest.param(10**9 + 7, id="base_fee_1_gwei_plus_7"),
    ]


def genesis_base_fee_for(
    fork: Fork, base_fee_per_gas: int, slot_seconds: int = SLOT_SECONDS
) -> int:
    """
    Return a genesis base fee from which the first block, built on the empty
    genesis block `slot_seconds` later, has exactly `base_fee_per_gas`.
    """
    base_fee_per_gas_calculator = fork.base_fee_per_gas_calculator()
    numerator = fork.base_fee_max_change_numerator(
        seconds_elapsed=slot_seconds
    )
    denominator = fork.base_fee_max_change_denominator(
        seconds_elapsed=slot_seconds
    )
    lowest = base_fee_per_gas * denominator // (denominator - numerator)
    for candidate in range(max(lowest - 2, base_fee_per_gas), lowest + 50):
        if (
            base_fee_per_gas_calculator(
                parent_base_fee_per_gas=candidate,
                parent_gas_used=0,
                parent_gas_limit=BLOCK_GAS_LIMIT,
                seconds_elapsed=slot_seconds,
            )
            == base_fee_per_gas
        ):
            return candidate
    raise AssertionError(f"no genesis base fee yields {base_fee_per_gas}")


@pytest.mark.parametrize_by_fork("parent_gas_used", gas_used_cases)
@pytest.mark.parametrize_by_fork("parent_base_fee_per_gas", base_fee_cases)
def test_base_fee_update(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    fork: Fork,
    parent_base_fee_per_gas: int,
    parent_gas_used: int,
) -> None:
    """
    Check the base fee of a block after a parent that used `parent_gas_used`
    gas at `parent_base_fee_per_gas`.
    """
    sender = pre.fund_eoa()
    genesis_environment = Environment(
        gas_limit=BLOCK_GAS_LIMIT,
        base_fee_per_gas=genesis_base_fee_for(fork, parent_base_fee_per_gas),
    )
    expected_base_fee = fork.base_fee_per_gas_calculator()(
        parent_base_fee_per_gas=parent_base_fee_per_gas,
        parent_gas_used=parent_gas_used,
        parent_gas_limit=BLOCK_GAS_LIMIT,
        seconds_elapsed=SLOT_SECONDS,
    )
    blocks = [
        Block(
            txs=gas_spending_transactions(
                pre=pre, sender=sender, fork=fork, gas=parent_gas_used
            ),
            timestamp=SLOT_SECONDS,
            header_verify=Header(
                base_fee_per_gas=parent_base_fee_per_gas,
                gas_used=parent_gas_used,
            ),
        ),
        Block(
            timestamp=2 * SLOT_SECONDS,
            header_verify=Header(base_fee_per_gas=expected_base_fee),
        ),
    ]
    blockchain_test(
        pre=pre,
        post={},
        blocks=blocks,
        genesis_environment=genesis_environment,
    )


@pytest.mark.parametrize(
    "parent_gas_used",
    [
        pytest.param(0, id="empty"),
        pytest.param(BLOCK_GAS_LIMIT, id="full"),
    ],
)
@pytest.mark.parametrize(
    "base_fee_offset",
    [
        pytest.param(-1, id="one_below"),
        pytest.param(1, id="one_above"),
    ],
)
@pytest.mark.exception_test
def test_invalid_base_fee(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    fork: Fork,
    parent_gas_used: int,
    base_fee_offset: int,
) -> None:
    """
    Reject a block whose base fee is one wei away from the value the fork's
    update rule gives at the largest increase or decrease.
    """
    parent_base_fee_per_gas = 10**9
    sender = pre.fund_eoa()
    genesis_environment = Environment(
        gas_limit=BLOCK_GAS_LIMIT,
        base_fee_per_gas=genesis_base_fee_for(fork, parent_base_fee_per_gas),
    )
    expected_base_fee = fork.base_fee_per_gas_calculator()(
        parent_base_fee_per_gas=parent_base_fee_per_gas,
        parent_gas_used=parent_gas_used,
        parent_gas_limit=BLOCK_GAS_LIMIT,
        seconds_elapsed=SLOT_SECONDS,
    )
    blocks = [
        Block(
            txs=gas_spending_transactions(
                pre=pre, sender=sender, fork=fork, gas=parent_gas_used
            ),
            timestamp=SLOT_SECONDS,
        ),
        Block(
            timestamp=2 * SLOT_SECONDS,
            rlp_modifier=Header(
                base_fee_per_gas=expected_base_fee + base_fee_offset
            ),
            exception=BlockException.INVALID_BASEFEE_PER_GAS,
        ),
    ]
    blockchain_test(
        pre=pre,
        post={},
        blocks=blocks,
        genesis_environment=genesis_environment,
    )


def slot_spacing_cases(fork: Fork) -> List[ParameterSet]:
    """Return slot durations and slot gaps between a block and its parent."""
    # The smallest slot gap at which `96 * slots_elapsed` exceeds 64 bits.
    gap_beyond_64_bits = -(
        -(2**64) // fork.base_fee_max_change_denominator(slots_elapsed=1)
    )
    # Spacing beyond the reference duration per slot is capped.
    reference = Spec.BASE_FEE_REFERENCE_SLOT_SECONDS
    return [
        pytest.param(9, 1, id="9s"),
        pytest.param(9, 3, id="9s_two_missed_slots"),
        pytest.param(10, 1, id="10s"),
        pytest.param(10, 2, id="10s_missed_slot"),
        pytest.param(10, 5, id="10s_four_missed_slots"),
        pytest.param(reference - 1, 1, id=f"{reference - 1}s"),
        pytest.param(reference, 1, id=f"{reference}s"),
        pytest.param(reference, 2, id=f"{reference}s_missed_slot"),
        pytest.param(reference, 10, id=f"{reference}s_nine_missed_slots"),
        pytest.param(reference + 1, 1, id=f"{reference + 1}s"),
        pytest.param(reference + 1, 2, id=f"{reference + 1}s_missed_slot"),
        pytest.param(2**32, 1, id="long_gap"),
        pytest.param(
            reference,
            gap_beyond_64_bits - 1,
            id="slot_gap_product_within_64_bits",
        ),
        pytest.param(
            reference,
            gap_beyond_64_bits,
            id="slot_gap_product_beyond_64_bits",
        ),
    ]


@pytest.mark.parametrize(
    "slots_elapsed",
    [
        pytest.param(
            2,
            id="missed_slot",
            marks=EIPChecklist.BlockLevelConstraint.Test.Boundary.Under(),
        ),
        pytest.param(
            1,
            id="next_slot",
            marks=EIPChecklist.BlockLevelConstraint.Test.Boundary.Exact(),
        ),
        pytest.param(
            0,
            id="same_slot",
            marks=[
                pytest.mark.exception_test,
                EIPChecklist.BlockLevelConstraint.Test.Boundary.Over(),
            ],
        ),
        pytest.param(-1, id="earlier_slot", marks=pytest.mark.exception_test),
    ],
)
def test_slot_number_must_increase(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    fork: Fork,
    slots_elapsed: int,
) -> None:
    """
    Accept a block whose slot number exceeds its parent's, and reject one
    whose slot number equals or precedes it.
    """
    parent_base_fee_per_gas = 10**9
    parent_slot_number = 1
    slot_number = parent_slot_number + slots_elapsed
    parent = Block(timestamp=SLOT_SECONDS, slot_number=parent_slot_number)
    if slots_elapsed > 0:
        block = Block(
            timestamp=(1 + slots_elapsed) * SLOT_SECONDS,
            slot_number=slot_number,
            header_verify=Header(
                slot_number=slot_number,
                base_fee_per_gas=fork.base_fee_per_gas_calculator()(
                    parent_base_fee_per_gas=parent_base_fee_per_gas,
                    parent_gas_used=0,
                    parent_gas_limit=BLOCK_GAS_LIMIT,
                    seconds_elapsed=slots_elapsed * SLOT_SECONDS,
                    slots_elapsed=slots_elapsed,
                ),
            ),
        )
    else:
        block = block_with_invalid_slot_number(
            timestamp=2 * SLOT_SECONDS,
            parent_slot_number=parent_slot_number,
            slot_number=slot_number,
        )
    blockchain_test(
        pre=pre,
        post={},
        blocks=[parent, block],
        genesis_environment=Environment(
            gas_limit=BLOCK_GAS_LIMIT,
            base_fee_per_gas=genesis_base_fee_for(
                fork, parent_base_fee_per_gas
            ),
        ),
    )


@pytest.mark.parametrize_by_fork(
    "slot_seconds,slots_elapsed", slot_spacing_cases
)
@pytest.mark.parametrize(
    "parent_gas_used",
    [
        pytest.param(0, id="empty"),
        pytest.param(BLOCK_GAS_LIMIT, id="full"),
        pytest.param(BLOCK_GAS_LIMIT * 3 // 4, id="three_quarters"),
    ],
)
def test_base_fee_follows_slot_duration(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    fork: Fork,
    slot_seconds: int,
    slots_elapsed: int,
    parent_gas_used: int,
) -> None:
    """
    Check that the maximum base fee change follows the slot duration read
    from the block spacing up to twelve seconds per slot, and that missed
    slots between a block and its parent leave it unchanged.
    """
    parent_base_fee_per_gas = 10**9
    base_fee_per_gas_calculator = fork.base_fee_per_gas_calculator()
    expected_base_fee = base_fee_per_gas_calculator(
        parent_base_fee_per_gas=parent_base_fee_per_gas,
        parent_gas_used=parent_gas_used,
        parent_gas_limit=BLOCK_GAS_LIMIT,
        seconds_elapsed=slot_seconds * slots_elapsed,
        slots_elapsed=slots_elapsed,
    )
    capped_slot_seconds = min(
        slot_seconds, Spec.BASE_FEE_REFERENCE_SLOT_SECONDS
    )
    assert expected_base_fee == base_fee_per_gas_calculator(
        parent_base_fee_per_gas=parent_base_fee_per_gas,
        parent_gas_used=parent_gas_used,
        parent_gas_limit=BLOCK_GAS_LIMIT,
        seconds_elapsed=capped_slot_seconds,
    )
    sender = pre.fund_eoa()
    genesis_environment = Environment(
        gas_limit=BLOCK_GAS_LIMIT,
        base_fee_per_gas=genesis_base_fee_for(
            fork, parent_base_fee_per_gas, slot_seconds=slot_seconds
        ),
    )
    blocks = [
        Block(
            txs=gas_spending_transactions(
                pre=pre, sender=sender, fork=fork, gas=parent_gas_used
            ),
            timestamp=slot_seconds,
            slot_number=1,
            header_verify=Header(
                base_fee_per_gas=parent_base_fee_per_gas,
                gas_used=parent_gas_used,
            ),
        ),
        Block(
            timestamp=slot_seconds * (1 + slots_elapsed),
            slot_number=1 + slots_elapsed,
            header_verify=Header(base_fee_per_gas=expected_base_fee),
        ),
    ]
    blockchain_test(
        pre=pre,
        post={},
        blocks=blocks,
        genesis_environment=genesis_environment,
    )
