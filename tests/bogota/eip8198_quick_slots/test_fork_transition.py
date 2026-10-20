"""
Fork transition tests for
[EIP-8198: Quick Slots](https://eips.ethereum.org/EIPS/eip-8198).

Blocks are spaced twelve seconds apart before the fork and ten seconds after
it, as on a network that shortens its slots. The execution layer does not
depend on the spacing.
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
    Header,
    TransitionFork,
)

from .helpers import (
    BLOCK_GAS_LIMIT,
    gas_spending_transactions,
)
from .spec import Spec, ref_spec_8198

REFERENCE_SPEC_GIT_PATH = ref_spec_8198.git_path
REFERENCE_SPEC_VERSION = ref_spec_8198.version

pytestmark = pytest.mark.valid_at_transition_to("EIP8198")

FORK_TIMESTAMP = 15_000
BLOCK_TIMESTAMPS = [
    FORK_TIMESTAMP - 24,
    FORK_TIMESTAMP - 12,
    FORK_TIMESTAMP,
    FORK_TIMESTAMP + 10,
]
"""Two blocks before the fork, the fork block, and one block after it."""

FORK_BLOCK_INDEX = BLOCK_TIMESTAMPS.index(FORK_TIMESTAMP)

GENESIS_BASE_FEE_PER_GAS = 10**9


def expected_base_fees(
    fork: TransitionFork, gas_used: int, block_count: int
) -> List[int]:
    """
    Return the base fees of `block_count` blocks built on an empty genesis
    block, each block but the last using `gas_used` gas.

    Blocks before the fork follow the parent fork's update rule, and blocks
    from the fork onward the new rule.
    """
    base_fees = []
    parent_base_fee = GENESIS_BASE_FEE_PER_GAS
    parent_gas_used = 0
    for timestamp in BLOCK_TIMESTAMPS[:block_count]:
        block_fork = fork.fork_at(timestamp=timestamp)
        parent_base_fee = block_fork.base_fee_per_gas_calculator()(
            parent_base_fee_per_gas=parent_base_fee,
            parent_gas_used=parent_gas_used,
            parent_gas_limit=BLOCK_GAS_LIMIT,
        )
        base_fees.append(parent_base_fee)
        parent_gas_used = gas_used
    return base_fees


@pytest.mark.parametrize_by_fork(
    "gas_used",
    lambda fork: [
        pytest.param(0, id="empty"),
        pytest.param(
            BLOCK_GAS_LIMIT
            // fork.transitions_to().base_fee_elasticity_multiplier(),
            id="at_target",
        ),
        pytest.param(BLOCK_GAS_LIMIT, id="full"),
    ],
)
@EIPChecklist.GasCostChanges.Test.ForkTransition.Before()
@EIPChecklist.GasCostChanges.Test.ForkTransition.After()
def test_base_fee_across_fork(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    fork: TransitionFork,
    gas_used: int,
) -> None:
    """
    Check that blocks before the fork use the parent fork's base fee update
    rule and that the fork block and its successor use the new rule.
    """
    sender = pre.fund_eoa()
    base_fees = expected_base_fees(fork, gas_used, len(BLOCK_TIMESTAMPS))
    blocks = []
    for i, timestamp in enumerate(BLOCK_TIMESTAMPS):
        block_fork = fork.fork_at(block_number=i + 1, timestamp=timestamp)
        last = i == len(BLOCK_TIMESTAMPS) - 1
        blocks.append(
            Block(
                txs=(
                    []
                    if last
                    else gas_spending_transactions(
                        pre=pre, sender=sender, fork=block_fork, gas=gas_used
                    )
                ),
                timestamp=timestamp,
                header_verify=Header(base_fee_per_gas=base_fees[i]),
            )
        )
    blockchain_test(
        pre=pre,
        post={},
        blocks=blocks,
        genesis_environment=Environment(
            gas_limit=BLOCK_GAS_LIMIT,
            base_fee_per_gas=GENESIS_BASE_FEE_PER_GAS,
        ),
    )


@pytest.mark.parametrize(
    "gas_used",
    [
        pytest.param(0, id="empty"),
        pytest.param(BLOCK_GAS_LIMIT, id="full"),
    ],
)
@pytest.mark.parametrize(
    "invalid_block_index",
    [
        pytest.param(FORK_BLOCK_INDEX - 1, id="last_pre_fork_block_new_rule"),
        pytest.param(FORK_BLOCK_INDEX, id="fork_block_old_rule"),
    ],
)
@pytest.mark.exception_test
def test_base_fee_wrong_rule_across_fork(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    fork: TransitionFork,
    gas_used: int,
    invalid_block_index: int,
) -> None:
    """
    Reject the last block before the fork when its base fee follows the new
    rule, and the fork block when its base fee follows the parent fork's
    rule.
    """
    sender = pre.fund_eoa()
    base_fees = expected_base_fees(fork, gas_used, invalid_block_index + 1)
    if invalid_block_index >= FORK_BLOCK_INDEX:
        wrong_fork = fork.transitions_from()
    else:
        wrong_fork = fork.transitions_to()
    wrong_base_fee = wrong_fork.base_fee_per_gas_calculator()(
        parent_base_fee_per_gas=base_fees[invalid_block_index - 1],
        parent_gas_used=gas_used,
        parent_gas_limit=BLOCK_GAS_LIMIT,
    )
    assert wrong_base_fee != base_fees[invalid_block_index]

    blocks = []
    for i, timestamp in enumerate(BLOCK_TIMESTAMPS[:invalid_block_index]):
        block_fork = fork.fork_at(block_number=i + 1, timestamp=timestamp)
        blocks.append(
            Block(
                txs=gas_spending_transactions(
                    pre=pre, sender=sender, fork=block_fork, gas=gas_used
                ),
                timestamp=timestamp,
            )
        )
    blocks.append(
        Block(
            timestamp=BLOCK_TIMESTAMPS[invalid_block_index],
            rlp_modifier=Header(base_fee_per_gas=wrong_base_fee),
            exception=BlockException.INVALID_BASEFEE_PER_GAS,
        )
    )
    blockchain_test(
        pre=pre,
        post={},
        blocks=blocks,
        genesis_environment=Environment(
            gas_limit=BLOCK_GAS_LIMIT,
            base_fee_per_gas=GENESIS_BASE_FEE_PER_GAS,
        ),
    )


@pytest.mark.parametrize(
    "adjusted_block_index",
    [
        pytest.param(FORK_BLOCK_INDEX - 1, id="last_pre_fork_block"),
        pytest.param(FORK_BLOCK_INDEX, id="fork_block"),
        pytest.param(FORK_BLOCK_INDEX + 1, id="post_fork_block"),
    ],
)
@pytest.mark.parametrize(
    "direction",
    [pytest.param(1, id="increase"), pytest.param(-1, id="decrease")],
)
@pytest.mark.parametrize(
    "beyond_bound",
    [
        pytest.param(False, id="largest_allowed"),
        pytest.param(True, id="one_beyond", marks=pytest.mark.exception_test),
    ],
)
def test_gas_limit_adjustment_unchanged(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    adjusted_block_index: int,
    direction: int,
    beyond_bound: bool,
) -> None:
    """
    Check that the gas limit adjustment rule is unchanged across the fork,
    with no one-time gas limit change at the fork block.
    """
    max_change = BLOCK_GAS_LIMIT // Spec.GAS_LIMIT_ADJUSTMENT_FACTOR
    change = max_change if beyond_bound else max_change - 1
    gas_limit = BLOCK_GAS_LIMIT + direction * change

    blocks = [
        Block(timestamp=timestamp)
        for timestamp in BLOCK_TIMESTAMPS[:adjusted_block_index]
    ]
    timestamp = BLOCK_TIMESTAMPS[adjusted_block_index]
    if beyond_bound:
        blocks.append(
            Block(
                timestamp=timestamp,
                rlp_modifier=Header(gas_limit=gas_limit),
                exception=BlockException.INVALID_GASLIMIT,
            )
        )
    else:
        blocks.append(
            Block(
                timestamp=timestamp,
                gas_limit=gas_limit,
                header_verify=Header(gas_limit=gas_limit),
            )
        )
        # The next block may again move by the largest allowed change.
        next_gas_limit = gas_limit + direction * (
            gas_limit // Spec.GAS_LIMIT_ADJUSTMENT_FACTOR - 1
        )
        blocks.append(
            Block(
                timestamp=timestamp + 10,
                gas_limit=next_gas_limit,
                header_verify=Header(gas_limit=next_gas_limit),
            )
        )
    blockchain_test(
        pre=pre,
        post={},
        blocks=blocks,
        genesis_environment=Environment(gas_limit=BLOCK_GAS_LIMIT),
    )
