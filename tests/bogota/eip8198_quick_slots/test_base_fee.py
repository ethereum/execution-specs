"""
Base fee update tests for
[EIP-8198: Quick Slots](https://eips.ethereum.org/EIPS/eip-8198).

From the fork onward, the maximum per-block base fee change is
`BASE_FEE_MAX_CHANGE_NUMERATOR / BASE_FEE_MAX_CHANGE_DENOMINATOR`, with the
multiplication performed before the division.
"""

import pytest
from execution_testing import (
    Alloc,
    Block,
    BlockchainTestFiller,
    BlockException,
    Environment,
    Fork,
    Header,
)

from .helpers import BLOCK_GAS_LIMIT, gas_spending_transactions
from .spec import Spec, ref_spec_8198

REFERENCE_SPEC_GIT_PATH = ref_spec_8198.git_path
REFERENCE_SPEC_VERSION = ref_spec_8198.version

pytestmark = pytest.mark.valid_from("EIP8198")

GAS_TARGET = BLOCK_GAS_LIMIT // Spec.ELASTICITY_MULTIPLIER

GAS_USED_CASES = [
    pytest.param(0, id="empty"),
    pytest.param(GAS_TARGET - 1, id="target_minus_one"),
    pytest.param(GAS_TARGET, id="at_target"),
    pytest.param(GAS_TARGET + 1, id="target_plus_one"),
    pytest.param(BLOCK_GAS_LIMIT, id="full"),
]

BASE_FEE_CASES = [
    # At or below 9 wei an empty block no longer lowers the base fee.
    pytest.param(7, id="base_fee_7"),
    pytest.param(9, id="base_fee_9"),
    pytest.param(10, id="base_fee_10"),
    # Up to 19 wei a full block raises the base fee by exactly one wei.
    pytest.param(19, id="base_fee_19"),
    pytest.param(20, id="base_fee_20"),
    pytest.param(10**9, id="base_fee_1_gwei"),
    pytest.param(10**9 + 7, id="base_fee_1_gwei_plus_7"),
]


def next_base_fee(
    parent_base_fee_per_gas: int,
    parent_gas_used: int,
    parent_gas_limit: int = BLOCK_GAS_LIMIT,
) -> int:
    """Return the base fee of a block under the fork's update rule."""
    return Spec.next_base_fee(
        parent_base_fee_per_gas=parent_base_fee_per_gas,
        parent_gas_used=parent_gas_used,
        parent_gas_limit=parent_gas_limit,
        numerator=Spec.BASE_FEE_MAX_CHANGE_NUMERATOR,
        denominator=Spec.BASE_FEE_MAX_CHANGE_DENOMINATOR,
    )


def genesis_base_fee_for(base_fee_per_gas: int) -> int:
    """
    Return a genesis base fee from which the first block, built on the empty
    genesis block, has exactly `base_fee_per_gas`.
    """
    lowest = (
        base_fee_per_gas
        * Spec.BASE_FEE_MAX_CHANGE_DENOMINATOR
        // (
            Spec.BASE_FEE_MAX_CHANGE_DENOMINATOR
            - Spec.BASE_FEE_MAX_CHANGE_NUMERATOR
        )
    )
    for candidate in range(max(lowest - 2, base_fee_per_gas), lowest + 50):
        if next_base_fee(candidate, 0) == base_fee_per_gas:
            return candidate
    raise AssertionError(f"no genesis base fee yields {base_fee_per_gas}")


@pytest.mark.parametrize("parent_gas_used", GAS_USED_CASES)
@pytest.mark.parametrize("parent_base_fee_per_gas", BASE_FEE_CASES)
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

    The cases cover the largest increase (full parent), the largest decrease
    (empty parent), no change (parent at target), the smallest changes either
    side of the target, and small base fees where the one-wei floor on
    increases and the truncation of decreases apply.
    """
    sender = pre.fund_eoa()
    genesis_environment = Environment(
        gas_limit=BLOCK_GAS_LIMIT,
        base_fee_per_gas=genesis_base_fee_for(parent_base_fee_per_gas),
    )
    expected_base_fee = next_base_fee(parent_base_fee_per_gas, parent_gas_used)
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
        base_fee_per_gas=genesis_base_fee_for(parent_base_fee_per_gas),
    )
    expected_base_fee = next_base_fee(parent_base_fee_per_gas, parent_gas_used)
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
