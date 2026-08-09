"""Test suite for `IteratingBytecode` class."""

from typing import Self, Type

import pytest

from execution_testing.forks import Amsterdam, Osaka
from execution_testing.vm import Op

from ..tools_code import (
    FixedIterationsBytecode,
    IteratingBytecode,
    TransactionWithCost,
    TxOutcome,
)

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
    def transaction_gas_limit_cap(cls) -> int | None:
        """Return the transaction gas limit cap."""
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
    calculated_cost = iterating_bytecode.execution_gas_cost_by_iteration_count(
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


def test_iterating_subcall_reserve_includes_state_gas() -> None:
    """
    The 63/64 reserve covers the subcall's state gas too: once the state
    reservoir is exhausted, the child pays its state charges (e.g. the
    EIP-8037 per-byte code deposit) from forwarded execution gas.
    """
    # Initcode depositing 2 bytes: tiny execution cost, 2 * 1530 state gas.
    initcode = Op.RETURN(0, 2, code_deposit_size=2)
    bytecode = IteratingBytecode(
        iterating=Op.CREATE2(offset=0, size=2, salt=0),
        iterating_subcall=initcode,
    )
    combined = initcode.execution_cost(fork=Amsterdam) + initcode.state_cost(
        fork=Amsterdam
    )
    assert initcode.state_cost(fork=Amsterdam) == 2 * 1530
    reserve = bytecode.iterating_subcall_reserve(fork=Amsterdam)
    assert reserve == (combined * 64 // 63) - combined
    assert reserve > 0, "state-charging subcall must have a reserve"


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
    ) == iterating_bytecode.execution_gas_cost_by_iteration_count(
        fork=Osaka, iteration_count=10
    )


def test_tx_gas_cost_by_iteration_count() -> None:
    """Test transaction gas cost calculation."""
    bytecode = IteratingBytecode(
        iterating=Op.ADD(1, 2),
    )
    intrinsic_gas_cost_calc = Osaka.transaction_intrinsic_cost_calculator()

    tx_gas = bytecode.tx_execution_gas_cost_by_iteration_count(
        fork=Osaka,
        iteration_count=5,
    )

    expected = (
        bytecode.execution_gas_cost_by_iteration_count(
            fork=Osaka, iteration_count=5
        )
        + intrinsic_gas_cost_calc()
    )
    assert tx_gas == expected

    # With calldata
    tx_gas = bytecode.tx_execution_gas_cost_by_iteration_count(
        fork=Osaka,
        iteration_count=5,
        calldata=b"hello",
    )
    expected = bytecode.execution_gas_cost_by_iteration_count(
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
        include_state_gas_reservoir=True,
    )
    tx_gas_cost = bytecode.tx_execution_gas_cost_by_iteration_count(
        fork=Osaka,
        iteration_count=5,
    )
    reserve = bytecode.iterating_subcall_reserve(fork=Osaka)

    # Osaka has no state-gas reservoir, so the limit is execution + reserve.
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
            fork=fork, iteration_count=iters, include_state_gas_reservoir=True
        )
        for iters in result
    )
    assert total_gas <= gas_limit

    # Check each transaction respects the gas limit cap
    if gas_limit_cap is not None:
        for iters in result:
            tx_gas = bytecode.tx_gas_limit_by_iteration_count(
                fork=fork,
                iteration_count=iters,
                include_state_gas_reservoir=True,
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
                fork=Osaka,
                iteration_count=iters,
                include_state_gas_reservoir=True,
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
        match="Single iteration gas cost is greater than gas constraints.",
    ):
        list(
            bytecode.tx_iterations_by_total_iteration_count(
                fork=CustomOsaka.with_tx_gas_limit_cap(1000),
                total_iterations=10,
            )
        )


class CustomAmsterdam(Amsterdam):
    """
    Amsterdam fork with a configurable EIP-7825 transaction gas limit cap.
    """

    tx_gas_limit_cap: int | None = 1_000_000

    @classmethod
    def with_tx_gas_limit_cap(cls, tx_gas_limit_cap: int | None) -> Type[Self]:
        """Return a new fork with the given transaction gas limit cap."""
        return type(
            cls.__name__, (cls,), {"tx_gas_limit_cap": tx_gas_limit_cap}
        )

    @classmethod
    def transaction_gas_limit_cap(cls) -> int | None:
        """Return the transaction gas limit cap."""
        return cls.tx_gas_limit_cap


def test_tx_gas_limit_includes_state_gas_reservoir() -> None:
    """
    Under EIP-8037 ``include_state_gas_reservoir`` adds the per-iteration
    state gas to the transaction gas limit; otherwise the limit is the
    execution gas plus the 63/64 subcall reserve only.
    """
    # SSTORE of a fresh slot from zero charges STORAGE_SET state gas.
    bytecode = IteratingBytecode(iterating=Op.SSTORE(0, 1))

    execution = bytecode.tx_execution_gas_cost_by_iteration_count(
        fork=Amsterdam, iteration_count=5
    )
    state = bytecode.state_gas_cost_by_iteration_count(
        fork=Amsterdam, iteration_count=5
    )
    reserve = bytecode.iterating_subcall_reserve(fork=Amsterdam)
    assert state > 0, "SSTORE-set should charge state gas under EIP-8037"

    without_state = bytecode.tx_gas_limit_by_iteration_count(
        fork=Amsterdam,
        iteration_count=5,
        include_state_gas_reservoir=False,
    )
    with_state = bytecode.tx_gas_limit_by_iteration_count(
        fork=Amsterdam,
        iteration_count=5,
        include_state_gas_reservoir=True,
    )

    assert without_state == execution + reserve
    assert with_state == execution + reserve + state


def test_state_reservoir_lets_tx_gas_exceed_execution_gas_limit_cap() -> None:
    """
    Under EIP-8037 the EIP-7825 transaction gas limit cap binds execution gas
    only. A state-heavy transaction can therefore pack more iterations than
    that cap alone would allow, because its state gas draws from a separate
    reservoir and the combined ``tx.gas`` grows past the cap.
    """
    cap = 5_000_000
    fork = CustomAmsterdam.with_tx_gas_limit_cap(cap)
    bytecode = IteratingBytecode(iterating=Op.SSTORE(0, 1))

    # Largest iteration count the tx splitter accepts for a single tx:
    # execution gas plus the subcall reserve must fit the cap, derived
    # from the helper's own (linear) cost model.
    cost_one = bytecode.tx_execution_gas_cost_by_iteration_count(
        fork=fork, iteration_count=1
    )
    per_iteration = (
        bytecode.tx_execution_gas_cost_by_iteration_count(
            fork=fork, iteration_count=2
        )
        - cost_one
    )
    reserve = bytecode.iterating_subcall_reserve(fork=fork)
    total_iterations = 1 + (cap - reserve - cost_one) // per_iteration
    counts = list(
        bytecode.tx_iterations_by_total_iteration_count(
            fork=fork, total_iterations=total_iterations
        )
    )

    # Execution gas stays under the cap, so all iterations fit in one tx even
    # though their combined (execution + state) gas far exceeds the cap.
    assert counts == [total_iterations]

    execution = bytecode.tx_execution_gas_cost_by_iteration_count(
        fork=fork, iteration_count=total_iterations
    )
    combined = bytecode.tx_gas_limit_by_iteration_count(
        fork=fork,
        iteration_count=total_iterations,
        include_state_gas_reservoir=True,
    )
    assert execution <= cap, "execution gas must respect the EIP-7825 cap"
    assert combined > cap, (
        "combined tx.gas exceeds the cap via state reservoir"
    )


@pytest.mark.parametrize(
    "outcome,expected_billed,expected_block",
    [
        pytest.param(TxOutcome.SUCCESS, 100_000, 60_000, id="success"),
        pytest.param(TxOutcome.REVERT, 60_000, 60_000, id="revert"),
        pytest.param(TxOutcome.OUT_OF_GAS, 150_000, 150_000, id="out_of_gas"),
    ],
)
def test_transaction_with_cost_billing_by_outcome(
    outcome: TxOutcome, expected_billed: int, expected_block: int
) -> None:
    """
    Billed gas and block-header contribution follow the expected outcome:
    combined execution + state on success, execution only on revert (state gas
    is refunded), and the whole gas limit on an exceptional halt.
    """
    tx = TransactionWithCost(
        gas_limit=150_000,
        execution_cost=60_000,
        state_cost=40_000,
        outcome=outcome,
    )
    assert tx.gas_cost == expected_billed
    assert tx.block_gas_cost == expected_block


def test_tx_iterations_by_gas_limit_outcome_packing() -> None:
    """
    The block budget is consumed according to the expected outcome: the
    max-dimension gas on success, the execution gas only on revert, and the
    whole gas limit (including the subcall reserve, without any state
    allowance) on out-of-gas.
    """
    budget = 1_000_000
    fork = CustomAmsterdam.with_tx_gas_limit_cap(16_777_216)
    # SSTORE of a fresh slot from zero: state gas dominates execution gas.
    bytecode = IteratingBytecode(
        iterating=Op.SSTORE(0, 1), iterating_subcall=6300
    )
    reserve = bytecode.iterating_subcall_reserve(fork=fork)
    assert reserve > 0

    def execution(iterations: int) -> int:
        return bytecode.tx_execution_gas_cost_by_iteration_count(
            fork=fork, iteration_count=iterations
        )

    def state(iterations: int) -> int:
        return bytecode.state_gas_cost_by_iteration_count(
            fork=fork, iteration_count=iterations
        )

    success = list(
        bytecode.tx_iterations_by_gas_limit(fork=fork, gas_limit=budget)
    )
    revert = list(
        bytecode.tx_iterations_by_gas_limit(
            fork=fork, gas_limit=budget, outcome=TxOutcome.REVERT
        )
    )
    out_of_gas = list(
        bytecode.tx_iterations_by_gas_limit(
            fork=fork, gas_limit=budget, outcome=TxOutcome.OUT_OF_GAS
        )
    )

    # Success packing is bound by the dominant (state) dimension.
    assert sum(max(execution(i), state(i)) for i in success) <= budget
    assert state(sum(success) + 1) > budget, (
        "one more iteration should overflow the state dimension"
    )

    # Revert packing bills execution gas only, so far more iterations fit.
    assert sum(revert) > sum(success)
    assert sum(execution(i) for i in revert) <= budget

    # Out-of-gas packing counts the whole gas limit, reserve included.
    assert sum(execution(i) + reserve for i in out_of_gas) <= budget
    assert execution(sum(out_of_gas) + 1) + reserve > budget, (
        "one more iteration should overflow the execution budget"
    )
