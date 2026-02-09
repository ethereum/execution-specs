"""Test suite for `IteratingBytecode` class."""

from typing import Self, Type

import pytest

from execution_testing.forks import Osaka
from execution_testing.vm import Op

from ..tools_code import FixedIterationsBytecode, IteratingBytecode

OSAKA_GAS_COSTS = Osaka.gas_costs()


class CustomOsaka(Osaka):
    """Custom Osaka fork with a custom transaction gas limit cap."""

    tx_gas_limit_cap: int | None = 1_000_000

    @classmethod
    def with_tx_gas_limit_cap(cls, tx_gas_limit_cap: int | None) -> Type[Self]:
        """
        Return a new CustomOsaka fork with the given transaction gas limit cap.
        """
        return type(
            cls.__name__, (cls,), {"tx_gas_limit_cap": tx_gas_limit_cap}
        )

    @classmethod
    def transaction_gas_limit_cap(
        cls, *, block_number: int = 0, timestamp: int = 0
    ) -> int | None:
        """Return the transaction gas limit cap."""
        del block_number, timestamp
        return cls.tx_gas_limit_cap


@pytest.mark.parametrize(
    "iterating_bytecode,iterations,expected_cost",
    [
        pytest.param(
            IteratingBytecode(iterating=Op.ADD(1, 2)),
            10,
            10 * (Op.ADD(1, 2).gas_cost(Osaka)),
            id="simple_code",
        ),
        pytest.param(
            IteratingBytecode(
                iterating=Op.CALL(address=1),
                warm_iterating=Op.CALL(address=1, address_warm=True),
            ),
            10,
            1 * (Op.CALL(address=1).gas_cost(Osaka))
            + 9 * (Op.CALL(address=1, address_warm=True).gas_cost(Osaka)),
            id="simple_code_with_warm_variation",
        ),
        pytest.param(
            IteratingBytecode(iterating=Op.ADD(1, 2)),
            0,
            0,
            id="zero_iterations",
        ),
        pytest.param(
            IteratingBytecode(
                setup=Op.PUSH1(0),
                iterating=Op.ADD(1, 2),
                cleanup=Op.STOP,
            ),
            5,
            Op.PUSH1(0).gas_cost(Osaka)
            + 5 * Op.ADD(1, 2).gas_cost(Osaka)
            + Op.STOP.gas_cost(Osaka),
            id="with_setup_and_cleanup",
        ),
        pytest.param(
            IteratingBytecode(
                iterating=Op.CALL(address=1),
                iterating_subcall=Op.RETURN(0, 0),
            ),
            3,
            3 * Op.CALL(address=1).gas_cost(Osaka)
            + 3 * Op.RETURN(0, 0).gas_cost(Osaka),
            id="with_subcall_bytecode",
        ),
        pytest.param(
            IteratingBytecode(
                iterating=Op.SSTORE(0, 1),
                iterating_subcall=10000,
            ),
            3,
            3 * Op.SSTORE(0, 1).gas_cost(Osaka) + 3 * 10000,
            id="with_subcall_int",
        ),
    ],
)
def test_iterating_bytecode_gas_cost(
    iterating_bytecode: IteratingBytecode, iterations: int, expected_cost: int
) -> None:
    """Test the gas cost calculating function of an iterating bytecode."""
    calculated_cost = iterating_bytecode.gas_cost_by_iteration_count(
        fork=Osaka, iteration_count=iterations
    )
    assert calculated_cost == expected_cost, (
        f"Gas cost for {iterations} iterations is {expected_cost}, "
        f"but got {calculated_cost}"
    )


def test_iterating_subcall_gas_cost() -> None:
    """Test iterating_subcall_gas_cost with both bytecode and int."""
    # Test with Bytecode
    bytecode = IteratingBytecode(
        iterating=Op.STOP,
        iterating_subcall=Op.CALL(address=1),
    )
    assert bytecode.iterating_subcall_gas_cost(fork=Osaka) == Op.CALL(
        address=1
    ).gas_cost(Osaka)

    # Test with int
    bytecode_int = IteratingBytecode(
        iterating=Op.STOP,
        iterating_subcall=5000,
    )
    assert bytecode_int.iterating_subcall_gas_cost(fork=Osaka) == 5000


def test_iterating_subcall_reserve() -> None:
    """Test the 63/64 rule gas reserve calculation."""
    bytecode = IteratingBytecode(
        iterating=Op.STOP,
        iterating_subcall=6300,
    )
    reserve = bytecode.iterating_subcall_reserve(fork=Osaka)
    # Reserve should be: (6300 * 64 / 63) - 6300 = 100
    assert reserve == 100


def test_with_fixed_iteration_count() -> None:
    """Test conversion to FixedIterationsBytecode."""
    iterating_bytecode = IteratingBytecode(
        setup=Op.PUSH1(0),
        iterating=Op.ADD(1, 2),
        cleanup=Op.STOP,
    )
    fixed = iterating_bytecode.with_fixed_iteration_count(iteration_count=10)

    assert isinstance(fixed, FixedIterationsBytecode)
    assert fixed.iteration_count == 10
    assert fixed.gas_cost(
        Osaka
    ) == iterating_bytecode.gas_cost_by_iteration_count(
        fork=Osaka, iteration_count=10
    )


def test_tx_gas_cost_by_iteration_count() -> None:
    """Test transaction gas cost calculation."""
    bytecode = IteratingBytecode(
        iterating=Op.ADD(1, 2),
    )
    intrinsic_gas_cost_calc = Osaka.transaction_intrinsic_cost_calculator()

    tx_gas = bytecode.tx_gas_cost_by_iteration_count(
        fork=Osaka,
        iteration_count=5,
    )

    expected = (
        bytecode.gas_cost_by_iteration_count(fork=Osaka, iteration_count=5)
        + intrinsic_gas_cost_calc()
    )
    assert tx_gas == expected

    # With calldata
    tx_gas = bytecode.tx_gas_cost_by_iteration_count(
        fork=Osaka,
        iteration_count=5,
        calldata=b"hello",
    )
    expected = bytecode.gas_cost_by_iteration_count(
        fork=Osaka, iteration_count=5
    ) + intrinsic_gas_cost_calc(
        calldata=b"hello", return_cost_deducted_prior_execution=True
    )
    assert tx_gas == expected


def test_tx_gas_limit_by_iteration_count() -> None:
    """Test transaction gas limit calculation includes 63/64 rule reserve."""
    bytecode = IteratingBytecode(
        iterating=Op.ADD(1, 2),
        iterating_subcall=6300,
    )

    tx_gas_limit = bytecode.tx_gas_limit_by_iteration_count(
        fork=Osaka,
        iteration_count=5,
    )
    tx_gas_cost = bytecode.tx_gas_cost_by_iteration_count(
        fork=Osaka,
        iteration_count=5,
    )
    reserve = bytecode.iterating_subcall_reserve(fork=Osaka)

    assert tx_gas_limit == tx_gas_cost + reserve


@pytest.mark.parametrize(
    "gas_limit,gas_limit_cap,expected_transactions",
    [
        pytest.param(
            500_000,
            None,
            1,
            id="single_tx_no_cap",
        ),
        pytest.param(
            500_000,
            100_000,
            6,
            id="split_across_multiple_txs",
        ),
        pytest.param(
            1_000_000,
            60_000,
            23,
            id="split_across_many_txs",
        ),
    ],
)
def test_tx_iterations_by_gas_limit(
    gas_limit: int, gas_limit_cap: int | None, expected_transactions: int
) -> None:
    """Test splitting iterations by target gas usage."""
    fork = CustomOsaka.with_tx_gas_limit_cap(gas_limit_cap)
    bytecode = IteratingBytecode(
        iterating=Op.ADD(1, 2) + Op.SSTORE(0, 1),
    )

    result = list(
        bytecode.tx_iterations_by_gas_limit(
            fork=fork,
            gas_limit=gas_limit,
        )
    )

    # Check we got the expected number of transactions
    assert len(result) == expected_transactions

    # Check total gas used is close to target
    total_gas = sum(
        bytecode.tx_gas_limit_by_iteration_count(
            fork=fork, iteration_count=iters
        )
        for iters in result
    )
    assert total_gas <= gas_limit

    # Check each transaction respects the gas limit cap
    if gas_limit_cap is not None:
        for iters in result:
            tx_gas = bytecode.tx_gas_limit_by_iteration_count(
                fork=fork, iteration_count=iters
            )
            assert tx_gas <= gas_limit_cap


@pytest.mark.parametrize(
    "total_iterations,gas_limit_cap,min_expected_txs",
    [
        pytest.param(
            100,
            None,
            1,
            id="single_tx_no_cap",
        ),
        pytest.param(
            10,
            100000,
            1,
            id="split_with_reasonable_cap",
        ),
        pytest.param(
            50,
            60000,
            40,
            id="many_txs_needed",
        ),
    ],
)
def test_tx_iterations_by_total_iteration_count(
    total_iterations: int, gas_limit_cap: int | None, min_expected_txs: int
) -> None:
    """Test splitting a fixed number of iterations across transactions."""
    bytecode = IteratingBytecode(
        iterating=Op.ADD(1, 2) + Op.SSTORE(0, 1),
    )

    result = list(
        bytecode.tx_iterations_by_total_iteration_count(
            fork=CustomOsaka.with_tx_gas_limit_cap(gas_limit_cap),
            total_iterations=total_iterations,
        )
    )

    # Check we got at least the expected number of transactions
    assert len(result) >= min_expected_txs

    # Check total iterations matches exactly
    assert sum(result) == total_iterations

    # Check each transaction respects the gas limit cap
    if gas_limit_cap is not None:
        for iters in result:
            tx_gas = bytecode.tx_gas_limit_by_iteration_count(
                fork=Osaka, iteration_count=iters
            )
            assert tx_gas <= gas_limit_cap


def test_tx_iterations_by_total_iteration_count_raises_on_impossible() -> None:
    """Test that ValueError is raised when gas limit is too low."""
    bytecode = IteratingBytecode(
        setup=Op.PUSH1(0) * 1000,  # Large setup to exceed small gas limit
        iterating=Op.ADD(1, 2),
    )

    with pytest.raises(
        ValueError,
        match="Single iteration gas cost is greater than gas limit.",
    ):
        list(
            bytecode.tx_iterations_by_total_iteration_count(
                fork=CustomOsaka.with_tx_gas_limit_cap(1000),
                total_iterations=10,
            )
        )
