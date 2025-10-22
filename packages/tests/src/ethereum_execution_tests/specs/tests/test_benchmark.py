"""
Tests for the BenchmarkTest class and its
transaction splitting functionality.
"""

import pytest

from ethereum_test_base_types import HexNumber
from ethereum_test_specs.benchmark import BenchmarkTest
from ethereum_test_types import Alloc, Environment, Transaction


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
        f"Expected {expected_splits} transactions for {gas_benchmark_value_millions}M gas, "
        f"got {len(split_txs)}"
    )

    # Verify total gas equals the benchmark value
    total_gas = sum(tx.gas_limit for tx in split_txs)
    assert total_gas == gas_benchmark_value, (
        f"Total gas {total_gas} doesn't match benchmark value {gas_benchmark_value}"
    )

    # Verify no transaction exceeds the cap
    for i, tx in enumerate(split_txs):
        assert tx.gas_limit <= gas_limit_cap, (
            f"Transaction {i} gas limit {tx.gas_limit} exceeds cap {gas_limit_cap}"
        )

    # Verify nonces increment correctly
    for i, tx in enumerate(split_txs):
        assert tx.nonce == i, f"Transaction {i} has incorrect nonce {tx.nonce}"

    # Verify gas distribution
    for i, tx in enumerate(split_txs[:-1]):  # All but last should be at cap
        assert tx.gas_limit == gas_limit_cap, (
            f"Transaction {i} should have gas limit {gas_limit_cap}, got {tx.gas_limit}"
        )

    # Last transaction should have the remainder
    if expected_splits > 1:
        expected_last_gas = gas_benchmark_value - (
            gas_limit_cap * (expected_splits - 1)
        )
        assert split_txs[-1].gas_limit == expected_last_gas, (
            f"Last transaction should have {expected_last_gas} gas, got {split_txs[-1].gas_limit}"
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
    benchmark_test = BenchmarkTest(
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
        assert split_txs[0].gas_limit == min(
            benchmark_test.tx.gas_limit, gas_benchmark_value
        )
