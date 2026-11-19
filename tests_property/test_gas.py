"""
The spec's gas formulas agree with the testing framework's calculators.

Each property draws random inputs and compares the spec function with the
framework's own calculator for the same fork, which is written apart from
`src/`. Where the framework has no calculator, the rule comes from its EIP.
"""

from types import ModuleType
from typing import Any, List, Tuple

from ethereum_types.numeric import U64, U256, Uint
from execution_testing import TransactionType
from execution_testing.forks import Fork
from hypothesis import given
from hypothesis import strategies as st

from ethereum_spec_tools.forks import Hardfork

from .forks import requires
from .gas_meter import AMOUNT_BOUND, amounts, pools
from .spec_api import spec_transaction, zeroed
from .strategies import (
    MAX_U64,
    MAX_U256,
    aim_at,
    framework_txs,
    ints,
    uints,
)

# Blob pricing is an exponential, which the spec computes term by term, so
# excess blob gas stays far below the U64 limit to keep it fast.
BLOB_GAS_BOUND = 1 << 30
GAS_LIMIT_BOUND = 1 << 40
# EIP-150: a parent keeps one 64th of its gas when it makes a call.
RETAINED_FRACTION = 64

with_blobs = requires(lambda fork: fork.supports_blobs())


def ceil32(value: int) -> int:
    """Round up to the next multiple of 32."""
    return (value + 31) // 32 * 32


@given(size=uints(MAX_U64))
def test_memory_gas_cost(gas: ModuleType, fork: Fork, size: Uint) -> None:
    """The cost of memory of a given size matches the framework."""
    aim_at(int(size), MAX_U64, "size near 2**64")
    expected = fork.memory_expansion_gas_calculator()(new_bytes=int(size))
    assert gas.calculate_memory_gas_cost(size) == expected


# An empty range grows nothing, even one that starts past the end, so
# empty ranges are drawn more often than their share of sizes.
range_sizes = st.one_of(st.just(0), ints(MAX_U256))


@given(
    initial_words=ints(64),
    extensions=st.lists(st.tuples(ints(MAX_U256), range_sizes), max_size=8),
)
def test_memory_extension(
    gas: ModuleType,
    fork: Fork,
    initial_words: int,
    extensions: List[Tuple[int, int]],
) -> None:
    """
    Extending memory by several ranges at once grows it to the end of the
    furthest non-empty range and costs what the framework charges for
    that growth.
    """
    memory = bytearray(initial_words * 32)
    final_size = len(memory)
    for start, size in extensions:
        if size > 0:
            final_size = max(final_size, ceil32(start + size))
    # Offsets and sizes are stack words, so their sum can pass 2**256.
    aim_at(final_size, 2**256, "end of memory near 2**256")

    result = gas.calculate_gas_extend_memory(
        memory, [(U256(start), U256(size)) for start, size in extensions]
    )

    assert len(memory) + int(result.expand_by) == final_size
    assert result.cost == fork.memory_expansion_gas_calculator()(
        new_bytes=final_size, previous_bytes=len(memory)
    )


with_call_gas_cap = requires(lambda fork: fork.is_eip_enabled(150))


@with_call_gas_cap
@given(
    request=amounts(),
    gas_left=pools(),
    memory_cost=amounts(),
    extra_gas=amounts(),
    big_value=st.integers(min_value=2, max_value=MAX_U256),
)
def test_value_adds_only_the_stipend_to_the_child_grant(
    gas: ModuleType,
    fork: Fork,
    request: int,
    gas_left: int,
    memory_cost: int,
    extra_gas: int,
    big_value: int,
) -> None:
    """
    A value-bearing call gives the child exactly the call stipend more
    than the same call without value, costs the caller the same, and does
    not depend on how much value is sent.
    """
    aim_at(big_value, MAX_U256, "value near 2**256")
    without_value, with_one, with_big = (
        gas.calculate_message_call_gas(
            U256(value),
            Uint(request),
            Uint(gas_left),
            Uint(memory_cost),
            Uint(extra_gas),
        )
        for value in (0, 1, big_value)
    )
    assert with_one.cost == without_value.cost
    assert int(with_one.sub_call) - int(without_value.sub_call) == (
        fork.call_value_stipend()
    )
    assert with_big == with_one


@with_call_gas_cap
@given(
    request=amounts(),
    memory_cost=amounts(),
    extra_gas=amounts(),
    value=st.sampled_from([0, 1]),
    delta=st.integers(min_value=-AMOUNT_BOUND, max_value=AMOUNT_BOUND),
)
def test_call_runs_out_of_gas_only_on_its_own_costs(
    gas: ModuleType,
    fork: Fork,
    request: int,
    memory_cost: int,
    extra_gas: int,
    value: int,
    delta: int,
) -> None:
    """
    A call costs more than `gas_left` exactly when `gas_left` cannot cover
    the call's own costs; a large gas request never does. Otherwise the
    child gets its request, capped at all but a 64th of the rest, and the
    parent keeps at least that 64th.
    """
    aim_at(delta, 0, "gas left near the call's own costs")
    gas_left = max(extra_gas + memory_cost + delta, 0)

    result = gas.calculate_message_call_gas(
        U256(value),
        Uint(request),
        Uint(gas_left),
        Uint(memory_cost),
        Uint(extra_gas),
    )

    charged = int(result.cost) + memory_cost
    if gas_left < extra_gas + memory_cost:
        assert charged > gas_left
    else:
        remaining = gas_left - memory_cost - extra_gas
        stipend = fork.call_value_stipend() if value else 0
        assert int(result.sub_call) - stipend == min(
            request, remaining - remaining // RETAINED_FRACTION
        )
        assert gas_left - charged >= remaining // RETAINED_FRACTION


@requires(lambda fork: fork.header_base_fee_required())
@given(data=st.data())
def test_base_fee_per_gas(
    spec: Hardfork, fork: Fork, data: st.DataObject
) -> None:
    """The next block's base fee matches the framework."""
    minimum = fork.minimum_block_gas_limit()
    gas_limit = data.draw(
        st.one_of(st.just(minimum), st.integers(minimum, GAS_LIMIT_BOUND))
    )
    gas_target = gas_limit // fork.base_fee_elasticity_multiplier()
    gas_used = data.draw(
        st.one_of(
            st.sampled_from([0, gas_target - 1, gas_target, gas_target + 1]),
            ints(gas_limit),
        )
    )
    base_fee = data.draw(ints(MAX_U256))
    aim_at(gas_used, gas_target, "gas used near the target")
    aim_at(base_fee, MAX_U256, "base fee near 2**256")

    # A block that keeps its parent's gas limit is always valid.
    actual = spec.module("fork").calculate_base_fee_per_gas(
        Uint(gas_limit), Uint(gas_limit), Uint(gas_used), Uint(base_fee)
    )
    assert actual == fork.base_fee_per_gas_calculator()(
        parent_base_fee_per_gas=base_fee,
        parent_gas_used=gas_used,
        parent_gas_limit=gas_limit,
    )


@with_blobs
@given(excess=ints(BLOB_GAS_BOUND))
def test_blob_gas_price(gas: ModuleType, fork: Fork, excess: int) -> None:
    """The blob gas price at any excess blob gas matches the framework."""
    expected = fork.blob_gas_price_calculator()(excess_blob_gas=excess)
    assert gas.calculate_blob_gas_price(U64(excess)) == expected


def parent_header(
    blocks: ModuleType, excess: int, used: int, base_fee: int
) -> Any:
    """Return a parent header whose only set fields drive blob pricing."""
    return zeroed(
        blocks.Header,
        excess_blob_gas=U64(excess),
        blob_gas_used=U64(used),
        base_fee_per_gas=Uint(base_fee),
    )


@with_blobs
@given(data=st.data())
def test_excess_blob_gas(
    gas: ModuleType, fork: Fork, blocks: ModuleType, data: st.DataObject
) -> None:
    """
    The next block's excess blob gas matches the framework, around the
    blob target and, where EIP-7918 applies, around its reserve price.
    """
    blob_gas_per_blob = fork.blob_gas_per_blob()
    target = fork.target_blobs_per_block() * blob_gas_per_blob
    # Only a parent at or past the target reaches the reserve price rule.
    excess = data.draw(
        st.one_of(
            st.sampled_from([0, target - 1, target]),
            ints(4 * target),
            st.integers(target, 4 * target),
            # Far past the target, where the blob price is above 1.
            ints(BLOB_GAS_BOUND),
        )
    )
    used = data.draw(
        st.integers(0, fork.max_blobs_per_block()).map(
            lambda blobs: blobs * blob_gas_per_blob
        )
    )
    base_fees = ints(MAX_U64)
    if fork.blob_reserve_price_active():
        # The reserve applies once the base fee times `BLOB_BASE_COST`
        # outprices one blob at the current blob gas price.
        blob_price = fork.blob_gas_price_calculator()(excess_blob_gas=excess)
        lowest_reserve_fee = (
            blob_gas_per_blob * blob_price // fork.blob_base_cost() + 1
        )
        base_fees = st.one_of(
            st.sampled_from([lowest_reserve_fee - 1, lowest_reserve_fee]),
            base_fees,
        )
    base_fee = data.draw(base_fees)
    # Excess blob gas bottoms out at zero where the parent's excess plus
    # its usage meets the target.
    aim_at(excess + used, target, "excess plus usage near the target")

    parent = parent_header(blocks, excess, used, base_fee)
    assert gas.calculate_excess_blob_gas(parent) == (
        fork.excess_blob_gas_calculator()(
            parent_excess_blob_gas=excess,
            parent_blob_gas_used=used,
            parent_base_fee_per_gas=base_fee,
        )
    )


@with_blobs
@given(excess=ints(BLOB_GAS_BOUND), data=st.data())
def test_blob_fee(
    gas: ModuleType,
    fork: Fork,
    transactions: ModuleType,
    excess: int,
    data: st.DataObject,
) -> None:
    """
    A transaction uses blob gas only for its blobs, and pays the blob gas
    price for each unit of it.
    """
    # Blob transactions are one type of several, so draw them more often.
    framework = data.draw(
        st.one_of(
            framework_txs(fork, [TransactionType.BLOB_TRANSACTION]),
            framework_txs(fork),
        )
    )
    tx = spec_transaction(transactions, framework)

    blob_count = len(framework.blob_versioned_hashes or [])
    blob_gas = blob_count * fork.blob_gas_per_blob()
    blob_price = fork.blob_gas_price_calculator()(excess_blob_gas=excess)
    assert gas.calculate_total_blob_gas(tx) == blob_gas
    assert gas.calculate_data_fee(U64(excess), tx) == blob_gas * blob_price
