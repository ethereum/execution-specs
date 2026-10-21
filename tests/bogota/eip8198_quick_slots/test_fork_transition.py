"""
Fork transition tests for
[EIP-8198: Quick Slots](https://eips.ethereum.org/EIPS/eip-8198).

Blocks are spaced ten seconds apart, except for the fork block, which follows
its parent by one twelve-second slot as on a network that shortens its slots
at the fork. The fork block's base fee therefore follows the parent fork's
rule, and the shorter slots lower the maximum change from the next block on.
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
    Fork,
    Header,
    TransactionException,
    TransitionFork,
)

from .helpers import (
    BLOB_COUNT_ERRORS,
    BLOCK_GAS_LIMIT,
    blob_transactions,
    block_with_invalid_slot_number,
    gas_spending_transactions,
)
from .spec import Spec, ref_spec_8198

REFERENCE_SPEC_GIT_PATH = ref_spec_8198.git_path
REFERENCE_SPEC_VERSION = ref_spec_8198.version

pytestmark = pytest.mark.valid_at_transition_to("EIP8198")

FORK_TIMESTAMP = 15_000
BLOCK_TIMESTAMPS = [
    FORK_TIMESTAMP - 22,
    FORK_TIMESTAMP - 12,
    FORK_TIMESTAMP,
    FORK_TIMESTAMP + 10,
]
"""Two blocks before the fork, the fork block, and one block after it."""

FORK_BLOCK_INDEX = BLOCK_TIMESTAMPS.index(FORK_TIMESTAMP)

GENESIS_BASE_FEE_PER_GAS = 10**9

BLOB_BASE_FEE_PER_GAS = 7
"""
Base fee of every block in the blob tests. It keeps the blob base fee
reserve price inactive and does not move, since blocks stay well below
their gas target.
"""

GENESIS_EXCESS_BLOBS = 300
"""
Excess blobs at genesis, high enough that the blob base fee depends on the
update fraction.
"""


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
    parent_timestamp = 0
    for timestamp in BLOCK_TIMESTAMPS[:block_count]:
        block_fork = fork.fork_at(timestamp=timestamp)
        parent_base_fee = block_fork.base_fee_per_gas_calculator()(
            parent_base_fee_per_gas=parent_base_fee,
            parent_gas_used=parent_gas_used,
            parent_gas_limit=BLOCK_GAS_LIMIT,
            seconds_elapsed=timestamp - parent_timestamp,
        )
        base_fees.append(parent_base_fee)
        parent_gas_used = gas_used
        parent_timestamp = timestamp
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
    rule and that the fork block and its successor use the new rule, which
    at the fork block's twelve-second spacing is the parent fork's rule and
    at its successor's ten-second spacing lowers the maximum change.
    """
    sender = pre.fund_eoa()
    base_fees = expected_base_fees(fork, gas_used, len(BLOCK_TIMESTAMPS))
    assert base_fees[FORK_BLOCK_INDEX] == (
        fork.transitions_from().base_fee_per_gas_calculator()(
            parent_base_fee_per_gas=base_fees[FORK_BLOCK_INDEX - 1],
            parent_gas_used=gas_used,
            parent_gas_limit=BLOCK_GAS_LIMIT,
        )
    )
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
    "invalid_block_index,base_fee_offset",
    [
        pytest.param(FORK_BLOCK_INDEX - 1, 0, id="pre_fork_block_new_rule"),
        pytest.param(FORK_BLOCK_INDEX, 1, id="fork_block_one_wei_over"),
        pytest.param(FORK_BLOCK_INDEX, -1, id="fork_block_one_wei_under"),
        pytest.param(FORK_BLOCK_INDEX + 1, 0, id="post_fork_block_old_rule"),
    ],
)
@pytest.mark.exception_test
def test_base_fee_wrong_rule_across_fork(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    fork: TransitionFork,
    gas_used: int,
    invalid_block_index: int,
    base_fee_offset: int,
) -> None:
    """
    Reject a base fee one wei off the parent fork's rule at the fork block,
    and a base fee from the other fork's rule at a ten-second spacing on
    either side of it.
    """
    sender = pre.fund_eoa()
    base_fees = expected_base_fees(fork, gas_used, invalid_block_index + 1)
    if invalid_block_index == FORK_BLOCK_INDEX - 1:
        wrong_fork = fork.transitions_to()
    elif invalid_block_index in (FORK_BLOCK_INDEX, FORK_BLOCK_INDEX + 1):
        wrong_fork = fork.transitions_from()
    else:
        raise ValueError(f"Unexpected block index {invalid_block_index}")
    base_fee_per_gas_calculator = wrong_fork.base_fee_per_gas_calculator()
    wrong_base_fee = base_fee_offset + base_fee_per_gas_calculator(
        parent_base_fee_per_gas=base_fees[invalid_block_index - 1],
        parent_gas_used=gas_used,
        parent_gas_limit=BLOCK_GAS_LIMIT,
        seconds_elapsed=(
            BLOCK_TIMESTAMPS[invalid_block_index]
            - BLOCK_TIMESTAMPS[invalid_block_index - 1]
        ),
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
    "gas_used",
    [
        pytest.param(0, id="empty"),
        pytest.param(BLOCK_GAS_LIMIT, id="full"),
    ],
)
@pytest.mark.parametrize(
    "missed_slots",
    [
        pytest.param(1, id="one_missed_slot"),
        # The spacing per slot is not a whole number of seconds.
        pytest.param(2, id="two_missed_slots"),
    ],
)
def test_base_fee_fork_block_after_missed_slot(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    fork: TransitionFork,
    gas_used: int,
    missed_slots: int,
) -> None:
    """
    Check the base fee of a fork block that follows missed slots at the
    fork, so its spacing spans one slot of each duration or more.
    """
    parent_timestamp = BLOCK_TIMESTAMPS[FORK_BLOCK_INDEX - 1]
    pre_fork_slot_seconds = FORK_TIMESTAMP - parent_timestamp
    post_fork_slot_seconds = (
        BLOCK_TIMESTAMPS[FORK_BLOCK_INDEX + 1] - FORK_TIMESTAMP
    )
    fork_block_timestamp = (
        FORK_TIMESTAMP + missed_slots * post_fork_slot_seconds
    )
    parent_slot_number = 1
    slots_elapsed = 1 + missed_slots
    seconds_elapsed = fork_block_timestamp - parent_timestamp
    sender = pre.fund_eoa()
    parent_base_fee = fork.transitions_from().base_fee_per_gas_calculator()(
        parent_base_fee_per_gas=GENESIS_BASE_FEE_PER_GAS,
        parent_gas_used=0,
        parent_gas_limit=BLOCK_GAS_LIMIT,
    )
    base_fee_per_gas_calculator = (
        fork.transitions_to().base_fee_per_gas_calculator()
    )

    def base_fee_after(seconds_elapsed: int) -> int:
        return base_fee_per_gas_calculator(
            parent_base_fee_per_gas=parent_base_fee,
            parent_gas_used=gas_used,
            parent_gas_limit=BLOCK_GAS_LIMIT,
            seconds_elapsed=seconds_elapsed,
            slots_elapsed=slots_elapsed,
        )

    expected_base_fee = base_fee_after(seconds_elapsed)
    # The spacing lies between the two slot durations, so the base fee
    # matches neither duration's rule, nor a rule that rounds the spacing
    # per slot down to whole seconds first.
    assert expected_base_fee not in (
        base_fee_after(pre_fork_slot_seconds * slots_elapsed),
        base_fee_after(post_fork_slot_seconds * slots_elapsed),
    )
    if seconds_elapsed % slots_elapsed:
        assert expected_base_fee != base_fee_after(
            seconds_elapsed // slots_elapsed * slots_elapsed
        )
    blockchain_test(
        pre=pre,
        post={},
        blocks=[
            Block(
                txs=gas_spending_transactions(
                    pre=pre,
                    sender=sender,
                    fork=fork.fork_at(
                        block_number=1, timestamp=parent_timestamp
                    ),
                    gas=gas_used,
                ),
                timestamp=parent_timestamp,
                slot_number=parent_slot_number,
            ),
            Block(
                timestamp=fork_block_timestamp,
                slot_number=parent_slot_number + slots_elapsed,
                header_verify=Header(base_fee_per_gas=expected_base_fee),
            ),
        ],
        genesis_environment=Environment(
            gas_limit=BLOCK_GAS_LIMIT,
            base_fee_per_gas=GENESIS_BASE_FEE_PER_GAS,
        ),
    )


@pytest.mark.parametrize(
    "fork_block_slots_elapsed",
    [
        pytest.param(
            1,
            id="fork_block_next_slot",
            marks=EIPChecklist.BlockLevelConstraint.Test.ForkTransition.AcceptedAfterFork(),
        ),
        pytest.param(
            0,
            id="fork_block_same_slot",
            marks=[
                pytest.mark.exception_test,
                EIPChecklist.BlockLevelConstraint.Test.ForkTransition.RejectedAfterFork(),
            ],
        ),
    ],
)
@EIPChecklist.BlockLevelConstraint.Test.ForkTransition.AcceptedBeforeFork()
def test_slot_number_rule_starts_at_fork(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    fork_block_slots_elapsed: int,
) -> None:
    """
    Accept a block before the fork that repeats its parent's slot number,
    and require the slot number to increase from the fork block on.
    """
    slot_number = 1
    blocks = [
        Block(timestamp=BLOCK_TIMESTAMPS[0], slot_number=slot_number),
        Block(
            timestamp=BLOCK_TIMESTAMPS[1],
            slot_number=slot_number,
            header_verify=Header(slot_number=slot_number),
        ),
    ]
    fork_block_slot_number = slot_number + fork_block_slots_elapsed
    if fork_block_slots_elapsed > 0:
        blocks.append(
            Block(
                timestamp=FORK_TIMESTAMP,
                slot_number=fork_block_slot_number,
                header_verify=Header(slot_number=fork_block_slot_number),
            )
        )
    else:
        blocks.append(
            block_with_invalid_slot_number(
                timestamp=FORK_TIMESTAMP,
                parent_slot_number=slot_number,
                slot_number=fork_block_slot_number,
            )
        )
    blockchain_test(pre=pre, post={}, blocks=blocks)


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


def unchanged_blob_schedule(fork: TransitionFork) -> Fork:
    """
    Return the parent fork after asserting that the new fork keeps its blob
    target, maximum, and update fraction.
    """
    parent, child = fork.transitions_from(), fork.transitions_to()
    assert child.target_blobs_per_block() == parent.target_blobs_per_block()
    assert child.max_blobs_per_block() == parent.max_blobs_per_block()
    assert (
        child.blob_base_fee_update_fraction()
        == parent.blob_base_fee_update_fraction()
    )
    return parent


def next_excess_blob_gas(
    schedule: Fork, parent_excess_blob_gas: int, parent_blob_count: int
) -> int:
    """Return the next block's excess blob gas under `schedule`."""
    return schedule.excess_blob_gas_calculator()(
        parent_excess_blob_gas=parent_excess_blob_gas,
        parent_blob_count=parent_blob_count,
        parent_base_fee_per_gas=BLOB_BASE_FEE_PER_GAS,
    )


@pytest.mark.parametrize_by_fork(
    "pre_fork_blobs,fork_block_blobs",
    lambda fork: [
        pytest.param(
            fork.transitions_from().max_blobs_per_block(),
            fork.transitions_to().max_blobs_per_block(),
            id="max_blobs_before_and_after",
        ),
        pytest.param(
            fork.transitions_from().target_blobs_per_block(),
            fork.transitions_to().target_blobs_per_block(),
            id="target_blobs_before_and_after",
        ),
        pytest.param(
            0,
            fork.transitions_to().max_blobs_per_block(),
            id="no_blobs_before_and_max_blobs_after",
        ),
        pytest.param(
            fork.transitions_from().max_blobs_per_block(),
            0,
            id="max_blobs_before_and_no_blobs_after",
        ),
    ],
)
def test_blob_schedule_unchanged_across_fork(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    fork: TransitionFork,
    pre_fork_blobs: int,
    fork_block_blobs: int,
) -> None:
    """
    Check that the excess blob gas and blob base fee follow the parent fork's
    blob schedule on both sides of the fork.
    """
    schedule = unchanged_blob_schedule(fork)
    sender = pre.fund_eoa()
    destination = pre.fund_eoa(amount=0)
    blob_gas_per_blob = schedule.blob_gas_per_blob()
    get_blob_gas_price = schedule.blob_gas_price_calculator()
    timestamps = BLOCK_TIMESTAMPS[FORK_BLOCK_INDEX - 1 :]
    # A final one-blob block checks the excess left by the fork block.
    blob_counts = [pre_fork_blobs, fork_block_blobs, 1]
    genesis_excess_blob_gas = GENESIS_EXCESS_BLOBS * blob_gas_per_blob
    excess_blob_gas = next_excess_blob_gas(
        schedule, genesis_excess_blob_gas, 0
    )
    blocks = []
    tx_count = 0
    blob_index = 0
    for i, (timestamp, blob_count) in enumerate(
        zip(timestamps, blob_counts, strict=True)
    ):
        txs = blob_transactions(
            sender=sender,
            destination=destination,
            fork=fork.fork_at(block_number=i + 1, timestamp=timestamp),
            blob_count=blob_count,
            max_fee_per_blob_gas=get_blob_gas_price(
                excess_blob_gas=excess_blob_gas
            ),
            first_blob_index=blob_index,
        )
        blocks.append(
            Block(
                txs=txs,
                timestamp=timestamp,
                header_verify=Header(
                    excess_blob_gas=excess_blob_gas,
                    blob_gas_used=blob_count * blob_gas_per_blob,
                ),
            )
        )
        tx_count += len(txs)
        blob_index += blob_count
        excess_blob_gas = next_excess_blob_gas(
            schedule, excess_blob_gas, blob_count
        )
    blockchain_test(
        pre=pre,
        post={destination: Account(balance=tx_count)},
        blocks=blocks,
        genesis_environment=Environment(
            base_fee_per_gas=BLOB_BASE_FEE_PER_GAS,
            excess_blob_gas=genesis_excess_blob_gas,
            blob_gas_used=0,
        ),
    )


@pytest.mark.parametrize(
    "blob_offset",
    [
        pytest.param(0, id="parent_fork_max"),
        pytest.param(
            1,
            id="parent_fork_max_plus_one",
            marks=pytest.mark.exception_test,
        ),
    ],
)
def test_blob_count_limit_unchanged_at_fork(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    fork: TransitionFork,
    blob_offset: int,
) -> None:
    """
    Accept the parent fork's maximum blob count in the last block before the
    fork and in the fork block, and reject one more blob in the fork block.
    """
    schedule = unchanged_blob_schedule(fork)
    sender = pre.fund_eoa()
    destination = pre.fund_eoa(amount=0)
    max_blobs = schedule.max_blobs_per_block()
    blob_gas_per_blob = schedule.blob_gas_per_blob()
    get_blob_gas_price = schedule.blob_gas_price_calculator()
    fork_block_blobs = max_blobs + blob_offset
    if blob_offset == 0:
        error = None
    elif blob_offset == 1:
        error = BLOB_COUNT_ERRORS
    else:
        raise ValueError(f"Unexpected blob offset {blob_offset}")
    pre_fork_timestamp = BLOCK_TIMESTAMPS[FORK_BLOCK_INDEX - 1]
    pre_fork_txs = blob_transactions(
        sender=sender,
        destination=destination,
        fork=fork.fork_at(block_number=1, timestamp=pre_fork_timestamp),
        blob_count=max_blobs,
        max_fee_per_blob_gas=get_blob_gas_price(excess_blob_gas=0),
    )
    fork_block_txs = blob_transactions(
        sender=sender,
        destination=destination,
        fork=fork.fork_at(block_number=2, timestamp=FORK_TIMESTAMP),
        blob_count=fork_block_blobs,
        max_fee_per_blob_gas=get_blob_gas_price(
            excess_blob_gas=next_excess_blob_gas(schedule, 0, max_blobs)
        ),
        first_blob_index=max_blobs,
        error=error,
    )
    if error is None:
        fork_block = Block(
            txs=fork_block_txs,
            timestamp=FORK_TIMESTAMP,
            header_verify=Header(
                blob_gas_used=fork_block_blobs * blob_gas_per_blob
            ),
        )
        tx_count = len(pre_fork_txs) + len(fork_block_txs)
    else:
        fork_block = Block(
            txs=fork_block_txs,
            timestamp=FORK_TIMESTAMP,
            exception=error,
        )
        tx_count = len(pre_fork_txs)
    blockchain_test(
        pre=pre,
        post={destination: Account(balance=tx_count)},
        blocks=[
            Block(
                txs=pre_fork_txs,
                timestamp=pre_fork_timestamp,
                header_verify=Header(
                    blob_gas_used=max_blobs * blob_gas_per_blob
                ),
            ),
            fork_block,
        ],
        genesis_environment=Environment(
            base_fee_per_gas=BLOB_BASE_FEE_PER_GAS
        ),
    )


@pytest.mark.parametrize(
    "price_offset",
    [
        pytest.param(0, id="exact_price"),
        pytest.param(-1, id="one_wei_short", marks=pytest.mark.exception_test),
    ],
)
def test_blob_base_fee_unchanged_at_fork(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    fork: TransitionFork,
    price_offset: int,
) -> None:
    """
    Accept a fork block blob transaction offering exactly the blob base fee
    under the parent fork's update fraction, and reject one wei less.
    """
    schedule = unchanged_blob_schedule(fork)
    sender = pre.fund_eoa()
    destination = pre.fund_eoa(amount=0)
    pre_fork_timestamp = BLOCK_TIMESTAMPS[FORK_BLOCK_INDEX - 1]
    genesis_excess_blob_gas = (
        GENESIS_EXCESS_BLOBS * schedule.blob_gas_per_blob()
    )
    # Two blocks without blobs, the last before the fork and the fork block.
    excess_blob_gas = next_excess_blob_gas(
        schedule,
        next_excess_blob_gas(schedule, genesis_excess_blob_gas, 0),
        0,
    )
    blob_gas_price = schedule.blob_gas_price_calculator()(
        excess_blob_gas=excess_blob_gas
    )
    if price_offset == 0:
        error = None
        header_verify = Header(excess_blob_gas=excess_blob_gas)
        post = {destination: Account(balance=1)}
    elif price_offset == -1:
        error = TransactionException.INSUFFICIENT_MAX_FEE_PER_BLOB_GAS
        header_verify = None
        post = {}
    else:
        raise ValueError(f"Unexpected price offset {price_offset}")
    blockchain_test(
        pre=pre,
        post=post,
        blocks=[
            Block(timestamp=pre_fork_timestamp),
            Block(
                txs=blob_transactions(
                    sender=sender,
                    destination=destination,
                    fork=fork.fork_at(
                        block_number=2, timestamp=FORK_TIMESTAMP
                    ),
                    blob_count=1,
                    max_fee_per_blob_gas=blob_gas_price + price_offset,
                    error=error,
                ),
                timestamp=FORK_TIMESTAMP,
                exception=error,
                header_verify=header_verify,
            ),
        ],
        genesis_environment=Environment(
            base_fee_per_gas=BLOB_BASE_FEE_PER_GAS,
            excess_blob_gas=genesis_excess_blob_gas,
            blob_gas_used=0,
        ),
    )
