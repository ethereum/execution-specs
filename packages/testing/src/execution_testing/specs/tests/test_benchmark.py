"""
Tests for the BenchmarkTest class and its
transaction splitting functionality.
"""

import pytest

from execution_testing.base_types import Bytes, HexNumber
from execution_testing.forks import Amsterdam, Osaka
from execution_testing.specs.benchmark import BenchmarkTest
from execution_testing.test_types import Alloc, Environment, Transaction


@pytest.mark.parametrize(
    "gas_benchmark_value_millions,expected_splits",
    [
        (1, 1),  # 1M / 16M = 1 transaction
        (10, 1),  # 10M / 16M = 1 transaction
        (30, 2),  # 30M / 16M = 2 transactions (16M + 14M)
        (45, 3),  # 45M / 16M = 3 transactions (16M + 16M + 13M)
        (60, 4),  # 60M / 16M = 4 transactions (16M + 16M + 16M + 12M)
        (100, 7),  # 100M / 16M = 7 transactions (6x16M + 4M)
        (150, 10),  # 150M / 16M = 10 transactions (9x16M + 6M)
    ],
)
def test_split_transaction(
    gas_benchmark_value_millions: int, expected_splits: int
) -> None:
    """
    Test that transaction splitting works
    correctly for Osaka fork gas cap.
    """
    gas_benchmark_value = gas_benchmark_value_millions * 1_000_000
    gas_limit_cap = 16_000_000  # Osaka's transaction gas limit cap

    # Create a minimal BenchmarkTest instance
    benchmark_test = BenchmarkTest(
        fork=Osaka,
        pre=Alloc(),
        post=Alloc(),
        tx=Transaction(sender=HexNumber(0), to=HexNumber(0), nonce=0),
        env=Environment(),
        gas_benchmark_value=gas_benchmark_value,
    )

    # Test the split_transaction method
    assert benchmark_test.tx is not None, "Transaction should not be None"
    split_txs = benchmark_test.split_transaction(
        benchmark_test.tx, gas_limit_cap
    )

    # Verify the number of transactions
    assert len(split_txs) == expected_splits, (
        f"Expected {expected_splits} transactions for "
        f"{gas_benchmark_value_millions}M gas, got {len(split_txs)}"
    )

    total_gas = 0
    for i, tx in enumerate(split_txs):
        tx_gas_limit = tx.gas_limit
        assert tx_gas_limit is not None, f"Unexpected `None` gas_limit: {tx}"
        total_gas += tx_gas_limit
        # Verify no tx exceeds the cap
        assert tx_gas_limit <= gas_limit_cap, (
            f"Transaction {i} gas limit {tx_gas_limit} "
            f"exceeds cap {gas_limit_cap}"
        )
        # Verify nonces increment correctly
        assert tx.nonce == i, f"Transaction {i} has incorrect nonce {tx.nonce}"

    # Gas is spread evenly rather than cap-cap-...-remainder, so the shares
    # differ by at most one wei of gas. The old scheme's tail could be
    # arbitrarily small, which made it unable to pay the floor data cost of the
    # calldata every split carries -- see
    # test_split_transaction_tail_covers_data_floor.
    gas_limits = [int(tx.gas_limit or 0) for tx in split_txs]
    assert max(gas_limits) - min(gas_limits) <= 1, (
        f"Gas should be spread evenly, got {gas_limits}"
    )
    # Verify total gas equals the benchmark value
    assert total_gas == gas_benchmark_value, (
        f"Total gas {total_gas} doesn't match benchmark "
        f"value {gas_benchmark_value}"
    )


@pytest.mark.parametrize(
    "gas_benchmark_value_millions",
    [100, 120, 140, 160, 180, 200, 220, 240, 260, 280, 300],
)
def test_split_transaction_tail_covers_data_floor(
    gas_benchmark_value_millions: int,
) -> None:
    """
    Every split must be able to pay the floor data cost of its calldata.

    Each split is a copy of the same transaction, so each carries identical
    calldata and owes identical floor data gas. Splitting gas as
    cap-cap-...-remainder left the final transaction with
    ``gas_benchmark_value % cap``, which is unrelated to that floor and could
    fall below it -- a 220M benchmark on Amsterdam gave its last transaction
    1,896,192 gas against a 2,374,296 floor, and clients reject it with
    "insufficient gas for floor data gas cost".

    36,864 bytes is the worst-case BLS12_G2MSM k=128 calldata that surfaced
    this.
    """
    gas_benchmark_value = gas_benchmark_value_millions * 1_000_000
    calldata = Bytes(b"\xab" * 36_864)
    fork = Amsterdam
    gas_limit_cap = fork.transaction_gas_limit_cap()
    assert gas_limit_cap is not None

    minimum_gas = max(
        fork.transaction_intrinsic_cost_calculator()(calldata=calldata),
        fork.transaction_data_floor_cost_calculator()(data=calldata),
    )

    benchmark_test = BenchmarkTest(
        fork=fork,
        pre=Alloc(),
        post=Alloc(),
        tx=Transaction(
            sender=HexNumber(0), to=HexNumber(0), nonce=0, data=calldata
        ),
        env=Environment(),
        gas_benchmark_value=gas_benchmark_value,
    )
    assert benchmark_test.tx is not None
    split_txs = benchmark_test.split_transaction(
        benchmark_test.tx, gas_limit_cap
    )

    for i, tx in enumerate(split_txs):
        assert tx.gas_limit is not None
        assert int(tx.gas_limit) >= minimum_gas, (
            f"Transaction {i} of {len(split_txs)} has gas limit "
            f"{int(tx.gas_limit)}, below the {minimum_gas} minimum its "
            f"{len(calldata)}-byte calldata requires"
        )

    # The total must stay exact: benchmark gas validation asserts the block
    # consumes precisely gas_benchmark_value.
    assert sum(int(tx.gas_limit or 0) for tx in split_txs) == (
        gas_benchmark_value
    )


@pytest.mark.parametrize(
    "gas_benchmark_value,gas_limit_cap",
    [
        (50_000_000, None),  # No cap - should return single transaction
        (50_000_000, 100_000_000),  # Cap higher than benchmark value
    ],
)
def test_split_transaction_edge_cases(
    gas_benchmark_value: int, gas_limit_cap: int | None
) -> None:
    """Test edge cases for transaction splitting."""
    fork = Osaka
    benchmark_test = BenchmarkTest(
        fork=fork,
        pre=Alloc(),
        post=Alloc(),
        tx=Transaction(
            sender=HexNumber(0),
            to=HexNumber(0),
            nonce=0,
            gas_limit=1_000_000_000,
        ),
        env=Environment(),
        gas_benchmark_value=gas_benchmark_value,
    )

    assert benchmark_test.tx is not None, "Transaction should not be None"
    split_txs = benchmark_test.split_transaction(
        benchmark_test.tx, gas_limit_cap
    )

    # Should return single transaction in both cases
    assert len(split_txs) == 1, f"Expected 1 transaction, got {len(split_txs)}"

    if gas_limit_cap is None:
        # When no cap, gas_limit should be benchmark value
        assert split_txs[0].gas_limit == gas_benchmark_value
    else:
        # When cap > benchmark, gas_limit should be
        # min of tx.gas_limit and benchmark
        assert benchmark_test.tx is not None, "Transaction should not be None"
        benchmark_test_tx_gas_limit = benchmark_test.tx.gas_limit
        assert benchmark_test_tx_gas_limit is not None, (
            "Transaction gas limit should not be None"
        )
        assert split_txs[0].gas_limit == min(
            benchmark_test_tx_gas_limit, gas_benchmark_value
        )
