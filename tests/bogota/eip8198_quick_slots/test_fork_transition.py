"""
Fork transition tests for
[EIP-8198: Quick Slots](https://eips.ethereum.org/EIPS/eip-8198).

The fork changes the base fee update rule and the blob schedule, and leaves
the gas limit adjustment rule untouched. The first block of the fork already
follows the new rules, computed from its pre-fork parent.

Blocks before the fork are spaced twelve seconds apart and blocks from the
fork onward ten seconds apart, as on a network that shortens its slots. The
execution layer does not depend on the spacing.
"""

from typing import List

import pytest
from execution_testing import (
    Account,
    Alloc,
    Block,
    BlockchainTestFiller,
    BlockException,
    EIPChecklist,
    Environment,
    Header,
    TransactionException,
    TransitionFork,
)

from .helpers import (
    BLOCK_GAS_LIMIT,
    blob_transactions,
    gas_spending_transactions,
)
from .spec import Spec, ref_spec_8198

REFERENCE_SPEC_GIT_PATH = ref_spec_8198.git_path
REFERENCE_SPEC_VERSION = ref_spec_8198.version

pytestmark = pytest.mark.valid_at_transition_to("EIP8198")

FORK_TIMESTAMP = Spec.FORK_TIMESTAMP
BLOCK_TIMESTAMPS = [
    FORK_TIMESTAMP - 24,
    FORK_TIMESTAMP - 12,
    FORK_TIMESTAMP,
    FORK_TIMESTAMP + 10,
]
"""Two blocks before the fork, the fork block, and one block after it."""

FORK_BLOCK_INDEX = BLOCK_TIMESTAMPS.index(FORK_TIMESTAMP)

GAS_TARGET = BLOCK_GAS_LIMIT // Spec.ELASTICITY_MULTIPLIER

GENESIS_BASE_FEE_PER_GAS = 10**9

BLOB_BASE_FEE_PER_GAS = 7
"""
Base fee of every block in the blob tests. It keeps the blob base fee
reserve price inactive and does not move, since blocks stay well below
their gas target.
"""

GENESIS_EXCESS_BLOB_GAS = 300 * Spec.GAS_PER_BLOB
"""
Excess blob gas at genesis, high enough that the blob base fee depends on
the update fraction, and lower under the new fraction than under the old.
"""

BLOB_COUNT_ERRORS = [
    TransactionException.TYPE_3_TX_MAX_BLOB_GAS_ALLOWANCE_EXCEEDED,
    TransactionException.TYPE_3_TX_BLOB_COUNT_EXCEEDED,
]


def expected_base_fees(
    fork: TransitionFork, gas_used: int, block_count: int
) -> List[int]:
    """
    Return the base fees of `block_count` blocks built on an empty genesis
    block, each block but the last using `gas_used` gas.

    Blocks before the fork follow the parent fork's update rule, and blocks
    from the fork onward the new rule.
    """
    parent_fork = fork.transitions_from()
    base_fees = []
    parent_base_fee = GENESIS_BASE_FEE_PER_GAS
    parent_gas_used = 0
    for timestamp in BLOCK_TIMESTAMPS[:block_count]:
        if timestamp >= FORK_TIMESTAMP:
            numerator = Spec.BASE_FEE_MAX_CHANGE_NUMERATOR
            denominator = Spec.BASE_FEE_MAX_CHANGE_DENOMINATOR
        else:
            numerator = parent_fork.base_fee_max_change_numerator()
            denominator = parent_fork.base_fee_max_change_denominator()
        parent_base_fee = Spec.next_base_fee(
            parent_base_fee_per_gas=parent_base_fee,
            parent_gas_used=parent_gas_used,
            parent_gas_limit=BLOCK_GAS_LIMIT,
            numerator=numerator,
            denominator=denominator,
        )
        base_fees.append(parent_base_fee)
        parent_gas_used = gas_used
    return base_fees


@pytest.mark.parametrize(
    "gas_used",
    [
        pytest.param(0, id="empty"),
        pytest.param(GAS_TARGET, id="at_target"),
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
    parent_fork = fork.transitions_from()
    sender = pre.fund_eoa()
    base_fees = expected_base_fees(fork, gas_used, invalid_block_index + 1)
    if invalid_block_index >= FORK_BLOCK_INDEX:
        numerator = parent_fork.base_fee_max_change_numerator()
        denominator = parent_fork.base_fee_max_change_denominator()
    else:
        numerator = Spec.BASE_FEE_MAX_CHANGE_NUMERATOR
        denominator = Spec.BASE_FEE_MAX_CHANGE_DENOMINATOR
    wrong_base_fee = Spec.next_base_fee(
        parent_base_fee_per_gas=base_fees[invalid_block_index - 1],
        parent_gas_used=gas_used,
        parent_gas_limit=BLOCK_GAS_LIMIT,
        numerator=numerator,
        denominator=denominator,
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
    Check that the gas limit adjustment rule is unchanged across the fork.

    Each block's gas limit must stay strictly within `parent_gas_limit //
    GAS_LIMIT_ADJUSTMENT_FACTOR` of its parent's, before the fork, at the
    fork block, and after it. The fork applies no one-time gas limit change.
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


def blob_parameters(fork: TransitionFork, timestamp: int) -> dict[str, int]:
    """Return the blob schedule in effect at `timestamp`."""
    if timestamp >= FORK_TIMESTAMP:
        return {
            "target_blobs_per_block": Spec.TARGET_BLOBS_PER_BLOCK,
            "max_blobs_per_block": Spec.MAX_BLOBS_PER_BLOCK,
            "update_fraction": Spec.BLOB_BASE_FEE_UPDATE_FRACTION,
        }
    parent_fork = fork.transitions_from()
    return {
        "target_blobs_per_block": parent_fork.target_blobs_per_block(),
        "max_blobs_per_block": parent_fork.max_blobs_per_block(),
        "update_fraction": parent_fork.blob_base_fee_update_fraction(),
    }


@pytest.mark.parametrize_by_fork(
    "pre_fork_blobs,fork_block_blobs",
    lambda fork: [
        pytest.param(
            fork.transitions_from().max_blobs_per_block(),
            Spec.MAX_BLOBS_PER_BLOCK,
            id="max_blobs_before_and_after",
        ),
        pytest.param(
            fork.transitions_from().target_blobs_per_block(),
            Spec.TARGET_BLOBS_PER_BLOCK,
            id="target_blobs_before_and_after",
        ),
        pytest.param(
            0,
            Spec.MAX_BLOBS_PER_BLOCK,
            id="no_blobs_before_and_max_blobs_after",
        ),
        pytest.param(
            fork.transitions_from().max_blobs_per_block(),
            0,
            id="max_blobs_before_and_no_blobs_after",
        ),
    ],
)
@EIPChecklist.BlobCountChanges.Test.Eip4844BlobsChanges()
@EIPChecklist.BlockLevelConstraint.Test.ForkTransition.AcceptedAfterFork()
def test_blob_schedule_across_fork(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    fork: TransitionFork,
    pre_fork_blobs: int,
    fork_block_blobs: int,
) -> None:
    """
    Check the excess blob gas and blob base fee across the fork.

    The last block before the fork carries `pre_fork_blobs` blobs under the
    parent fork's schedule. The fork block computes its excess blob gas from
    that parent with the new target, and its blob transactions, offering
    exactly the blob base fee under the new update fraction, are accepted. A
    final block checks the excess blob gas left by the fork block.
    """
    sender = pre.fund_eoa()
    destination = pre.fund_eoa(amount=0)
    timestamps = BLOCK_TIMESTAMPS[FORK_BLOCK_INDEX - 1 :]
    blob_counts = [pre_fork_blobs, fork_block_blobs, 1]

    excess_blob_gas = Spec.next_excess_blob_gas(
        parent_excess_blob_gas=GENESIS_EXCESS_BLOB_GAS,
        parent_blob_gas_used=0,
        parent_base_fee_per_gas=BLOB_BASE_FEE_PER_GAS,
        **blob_parameters(fork, timestamps[0]),
    )
    blocks = []
    tx_count = 0
    blob_index = 0
    for i, (timestamp, blob_count) in enumerate(
        zip(timestamps, blob_counts, strict=True)
    ):
        parameters = blob_parameters(fork, timestamp)
        block_fork = fork.fork_at(block_number=i + 1, timestamp=timestamp)
        txs = blob_transactions(
            sender=sender,
            destination=destination,
            fork=block_fork,
            blob_count=blob_count,
            max_fee_per_blob_gas=Spec.blob_base_fee(
                excess_blob_gas=excess_blob_gas,
                update_fraction=parameters["update_fraction"],
            ),
            first_blob_index=blob_index,
        )
        blocks.append(
            Block(
                txs=txs,
                timestamp=timestamp,
                header_verify=Header(
                    excess_blob_gas=excess_blob_gas,
                    blob_gas_used=blob_count * Spec.GAS_PER_BLOB,
                ),
            )
        )
        tx_count += len(txs)
        blob_index += blob_count
        if i + 1 < len(timestamps):
            excess_blob_gas = Spec.next_excess_blob_gas(
                parent_excess_blob_gas=excess_blob_gas,
                parent_blob_gas_used=blob_count * Spec.GAS_PER_BLOB,
                parent_base_fee_per_gas=BLOB_BASE_FEE_PER_GAS,
                **blob_parameters(fork, timestamps[i + 1]),
            )
    blockchain_test(
        pre=pre,
        post={destination: Account(balance=tx_count)} if tx_count else {},
        blocks=blocks,
        genesis_environment=Environment(
            base_fee_per_gas=BLOB_BASE_FEE_PER_GAS,
            excess_blob_gas=GENESIS_EXCESS_BLOB_GAS,
            blob_gas_used=0,
        ),
    )


@pytest.mark.parametrize_by_fork(
    "fork_block_blobs",
    lambda fork: [
        pytest.param(Spec.MAX_BLOBS_PER_BLOCK + 1, id="max_plus_one"),
        pytest.param(
            fork.transitions_from().max_blobs_per_block(),
            id="parent_fork_max",
        ),
    ],
)
@pytest.mark.exception_test
@EIPChecklist.BlockLevelConstraint.Test.ForkTransition.AcceptedBeforeFork()
@EIPChecklist.BlockLevelConstraint.Test.ForkTransition.RejectedAfterFork()
def test_blob_count_limit_at_fork(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    fork: TransitionFork,
    fork_block_blobs: int,
) -> None:
    """
    Accept the parent fork's maximum blob count in the last block before the
    fork, and reject a fork block carrying more than `MAX_BLOBS_PER_BLOCK`
    blobs.
    """
    sender = pre.fund_eoa()
    destination = pre.fund_eoa(amount=0)
    pre_fork_timestamp = BLOCK_TIMESTAMPS[FORK_BLOCK_INDEX - 1]
    pre_fork_blobs = fork.transitions_from().max_blobs_per_block()
    blocks = [
        Block(
            txs=blob_transactions(
                sender=sender,
                destination=destination,
                fork=fork.fork_at(
                    block_number=1, timestamp=pre_fork_timestamp
                ),
                blob_count=pre_fork_blobs,
                max_fee_per_blob_gas=Spec.MIN_BLOB_BASE_FEE,
            ),
            timestamp=pre_fork_timestamp,
            header_verify=Header(
                blob_gas_used=pre_fork_blobs * Spec.GAS_PER_BLOB
            ),
        ),
        Block(
            txs=blob_transactions(
                sender=sender,
                destination=destination,
                fork=fork.fork_at(block_number=2, timestamp=FORK_TIMESTAMP),
                blob_count=fork_block_blobs,
                max_fee_per_blob_gas=10**6,
                first_blob_index=pre_fork_blobs,
                error=BLOB_COUNT_ERRORS,
            ),
            timestamp=FORK_TIMESTAMP,
            exception=BLOB_COUNT_ERRORS,
        ),
    ]
    blockchain_test(
        pre=pre,
        post={},
        blocks=blocks,
        genesis_environment=Environment(
            base_fee_per_gas=BLOB_BASE_FEE_PER_GAS
        ),
    )


@pytest.mark.exception_test
def test_insufficient_max_fee_per_blob_gas_at_fork(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    fork: TransitionFork,
) -> None:
    """
    Reject a fork-block blob transaction offering one wei less than the blob
    base fee under the new update fraction.
    """
    sender = pre.fund_eoa()
    destination = pre.fund_eoa(amount=0)
    pre_fork_timestamp = BLOCK_TIMESTAMPS[FORK_BLOCK_INDEX - 1]
    excess_blob_gas = GENESIS_EXCESS_BLOB_GAS
    for timestamp in (pre_fork_timestamp, FORK_TIMESTAMP):
        excess_blob_gas = Spec.next_excess_blob_gas(
            parent_excess_blob_gas=excess_blob_gas,
            parent_blob_gas_used=0,
            parent_base_fee_per_gas=BLOB_BASE_FEE_PER_GAS,
            **blob_parameters(fork, timestamp),
        )
    blob_base_fee = Spec.blob_base_fee(
        excess_blob_gas=excess_blob_gas,
        update_fraction=Spec.BLOB_BASE_FEE_UPDATE_FRACTION,
    )
    error = TransactionException.INSUFFICIENT_MAX_FEE_PER_BLOB_GAS
    blocks = [
        Block(timestamp=pre_fork_timestamp),
        Block(
            txs=blob_transactions(
                sender=sender,
                destination=destination,
                fork=fork.fork_at(block_number=2, timestamp=FORK_TIMESTAMP),
                blob_count=1,
                max_fee_per_blob_gas=blob_base_fee - 1,
                error=error,
            ),
            timestamp=FORK_TIMESTAMP,
            exception=error,
        ),
    ]
    blockchain_test(
        pre=pre,
        post={},
        blocks=blocks,
        genesis_environment=Environment(
            base_fee_per_gas=BLOB_BASE_FEE_PER_GAS,
            excess_blob_gas=GENESIS_EXCESS_BLOB_GAS,
            blob_gas_used=0,
        ),
    )
