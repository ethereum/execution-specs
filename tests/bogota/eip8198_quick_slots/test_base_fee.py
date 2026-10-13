"""
Base fee update tests for
[EIP-8198: Quick Slots](https://eips.ethereum.org/EIPS/eip-8198).

From the fork onward, the maximum per-block base fee change is
`BASE_FEE_MAX_CHANGE_NUMERATOR / BASE_FEE_MAX_CHANGE_DENOMINATOR`, with the
multiplication performed before the division.
"""

from typing import List

import pytest
from execution_testing import (
    Alloc,
    Block,
    BlockchainTestFiller,
    BlockException,
    Environment,
    Fork,
    Header,
    ParameterSet,
)

from .helpers import BLOCK_GAS_LIMIT, gas_spending_transactions
from .spec import ref_spec_8198

REFERENCE_SPEC_GIT_PATH = ref_spec_8198.git_path
REFERENCE_SPEC_VERSION = ref_spec_8198.version

pytestmark = pytest.mark.valid_from("EIP8198")


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
    numerator = fork.base_fee_max_change_numerator()
    denominator = fork.base_fee_max_change_denominator()
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


def genesis_base_fee_for(fork: Fork, base_fee_per_gas: int) -> int:
    """
    Return a genesis base fee from which the first block, built on the empty
    genesis block, has exactly `base_fee_per_gas`.
    """
    base_fee_per_gas_calculator = fork.base_fee_per_gas_calculator()
    numerator = fork.base_fee_max_change_numerator()
    denominator = fork.base_fee_max_change_denominator()
    lowest = base_fee_per_gas * denominator // (denominator - numerator)
    for candidate in range(max(lowest - 2, base_fee_per_gas), lowest + 50):
        if (
            base_fee_per_gas_calculator(
                parent_base_fee_per_gas=candidate,
                parent_gas_used=0,
                parent_gas_limit=BLOCK_GAS_LIMIT,
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
    )
    blocks = [
        Block(
            txs=gas_spending_transactions(
                pre=pre, sender=sender, fork=fork, gas=parent_gas_used
            ),
            timestamp=10,
            header_verify=Header(
                base_fee_per_gas=parent_base_fee_per_gas,
                gas_used=parent_gas_used,
            ),
        ),
        Block(
            timestamp=20,
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
    )
    blocks = [
        Block(
            txs=gas_spending_transactions(
                pre=pre, sender=sender, fork=fork, gas=parent_gas_used
            ),
            timestamp=10,
        ),
        Block(
            timestamp=20,
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
