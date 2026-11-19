"""
The gas limits the spec accepts for a transaction, against the framework.

The framework computes the least gas a transaction needs and the caps on
its gas, so each limit is pinned on both sides: the last valid value and the
first invalid one.
"""

from dataclasses import replace
from types import ModuleType
from typing import Callable

import pytest
from ethereum_types.numeric import U256, Uint
from execution_testing import Transaction, TransactionType
from execution_testing.base_types import AccessList
from execution_testing.forks import Fork
from hypothesis import given
from hypothesis import strategies as st

from ethereum.exceptions import InsufficientTransactionGasError
from ethereum_spec_tools.forks import Hardfork

from .forks import requires
from .spec_api import (
    spec_transaction,
    validate_tx,
)
from .strategies import (
    aim_at,
    bytes_data,
    framework_tx,
    framework_tx_fields,
    framework_txs,
    ints,
    minimum_gas_limit,
    signed,
)

BOUNDARY_SIDES = ["at_cap", "above_cap"]

with_state_gas_reservoir = requires(
    lambda fork: fork.state_gas_reservoir_enabled()
)

# From EIP-8037 a separate cap bounds the gas limit, and the EIP-7825 cap
# bounds the intrinsic execution gas and the calldata floor instead.
with_intrinsic_gas_cap = requires(
    lambda fork: fork.transaction_total_gas_limit_cap() is not None
)


def validate(transactions: ModuleType, framework: Transaction) -> None:
    """Validate the spec's copy of a framework transaction."""
    assert framework.sender is not None
    tx = spec_transaction(transactions, framework)
    validate_tx(transactions, tx, framework.sender)


@pytest.mark.parametrize(
    "creation",
    [pytest.param(False, id="call"), pytest.param(True, id="creation")],
)
@given(data=st.data())
def test_minimum_gas_limit_boundary(
    fork: Fork, transactions: ModuleType, data: st.DataObject, creation: bool
) -> None:
    """
    Validation accepts a gas limit of exactly the framework's intrinsic
    cost, for any transaction type, recipient, value, calldata, access list
    and authorization count, and rejects one gas less.
    """
    if creation:
        # Init code is charged per word, so the creation deploys some.
        fields = data.draw(
            framework_tx_fields(fork, fork.contract_creating_tx_types())
        )
        framework = signed(
            {**fields, "to": None, "data": data.draw(bytes_data(min_size=1))}
        )
    else:
        framework = data.draw(framework_txs(fork))
    minimum = minimum_gas_limit(fork, framework)
    # Calldata heavy enough for the EIP-7623 floor to set the minimum.
    aim_at(
        fork.transaction_data_floor_cost_calculator()(data=framework.data),
        minimum,
        "calldata floor near the intrinsic cost",
    )
    assert framework.sender is not None
    tx = spec_transaction(transactions, framework)

    validate_tx(transactions, replace(tx, gas=Uint(minimum)), framework.sender)
    below = replace(tx, gas=Uint(minimum - 1))
    with pytest.raises(InsufficientTransactionGasError):
        validate_tx(transactions, below, framework.sender)


@requires(lambda fork: fork.transaction_gas_limit_cap() is not None)
@pytest.mark.parametrize("side", BOUNDARY_SIDES)
def test_gas_limit_cap_boundary(
    fork: Fork, spec: Hardfork, transactions: ModuleType, side: str
) -> None:
    """
    A gas limit of exactly the cap is valid for every transaction type and
    one more is not.
    """
    cap = (
        fork.transaction_total_gas_limit_cap()
        or fork.transaction_gas_limit_cap()
    )
    assert cap is not None
    exceptions = spec.module("exceptions")
    for ty in fork.tx_types():
        if side == "at_cap":
            validate(transactions, framework_tx(ty, gas_limit=cap))
        elif side == "above_cap":
            above = framework_tx(ty, gas_limit=cap + 1)
            with pytest.raises(exceptions.TransactionGasLimitExceededError):
                validate(transactions, above)
        else:
            raise ValueError(f"unknown boundary side: {side}")


def largest_size_within(cap: int, cost_of: Callable[[int], int]) -> int:
    """
    Return the largest size whose cost fits `cap`, for a cost that grows by
    a fixed step per unit of size.
    """
    step = cost_of(1) - cost_of(0)
    assert step > 0
    return (cap - cost_of(0)) // step


@with_intrinsic_gas_cap
@pytest.mark.parametrize("side", BOUNDARY_SIDES)
def test_intrinsic_execution_gas_cap_boundary(
    fork: Fork, transactions: ModuleType, side: str
) -> None:
    """
    Intrinsic execution gas of exactly the cap is valid and one zero byte
    more is not.

    Access list slots bring the cost near the cap and zero calldata bytes
    close the gap, keeping the calldata floor well below the cap.
    """
    cap = fork.transaction_gas_limit_cap()
    gas_limit = fork.transaction_total_gas_limit_cap()
    assert cap is not None and gas_limit is not None
    intrinsic_cost = fork.transaction_intrinsic_cost_calculator()
    floor_cost = fork.transaction_data_floor_cost_calculator()

    def tx_with(slots: int, zero_bytes: int) -> Transaction:
        access = AccessList(address=0xCC, storage_keys=[0] * slots)
        return framework_tx(
            TransactionType.BASE_FEE,
            gas_limit=gas_limit,
            access_list=[access],
            data=b"\x00" * zero_bytes,
        )

    def execution_gas(tx: Transaction) -> int:
        return intrinsic_cost(
            calldata=tx.data,
            access_list=tx.access_list,
            return_cost_deducted_prior_execution=True,
        )

    slots = largest_size_within(cap, lambda n: execution_gas(tx_with(n, 0)))
    zero_bytes = largest_size_within(
        cap, lambda n: execution_gas(tx_with(slots, n))
    )
    at_cap = tx_with(slots, zero_bytes)
    above_cap = tx_with(slots, zero_bytes + 1)
    assert execution_gas(at_cap) == cap, (
        "zero bytes and access list slots no longer add up to the cap"
    )
    assert (
        floor_cost(data=above_cap.data, access_list=above_cap.access_list)
        < cap
    )

    if side == "at_cap":
        validate(transactions, at_cap)
    elif side == "above_cap":
        with pytest.raises(InsufficientTransactionGasError):
            validate(transactions, above_cap)
    else:
        raise ValueError(f"unknown boundary side: {side}")


@with_intrinsic_gas_cap
@pytest.mark.parametrize("side", BOUNDARY_SIDES)
def test_calldata_floor_cap_boundary(
    fork: Fork, transactions: ModuleType, side: str
) -> None:
    """
    The longest calldata whose floor fits the cap is valid and one more
    byte is not.

    The floor grows in steps of many gas per byte and cannot land on the
    cap exactly, so the two sides are one byte apart.
    """
    cap = fork.transaction_gas_limit_cap()
    gas_limit = fork.transaction_total_gas_limit_cap()
    assert cap is not None and gas_limit is not None
    floor_cost = fork.transaction_data_floor_cost_calculator()
    intrinsic_cost = fork.transaction_intrinsic_cost_calculator()

    def floor(data_bytes: int) -> int:
        return floor_cost(data=b"\xff" * data_bytes)

    data_bytes = largest_size_within(cap, floor)
    assert floor(data_bytes) <= cap < floor(data_bytes + 1)
    execution = intrinsic_cost(
        calldata=b"\xff" * (data_bytes + 1),
        return_cost_deducted_prior_execution=True,
    )
    assert execution < cap

    def tx_with(data_bytes: int) -> Transaction:
        return framework_tx(
            TransactionType.LEGACY,
            gas_limit=gas_limit,
            data=b"\xff" * data_bytes,
        )

    if side == "at_cap":
        validate(transactions, tx_with(data_bytes))
    elif side == "above_cap":
        with pytest.raises(InsufficientTransactionGasError):
            validate(transactions, tx_with(data_bytes + 1))
    else:
        raise ValueError(f"unknown boundary side: {side}")


@pytest.mark.spec_unit
@with_state_gas_reservoir
@given(data=st.data())
def test_evm_gas_splits_at_the_cap(
    fork: Fork, gas: ModuleType, spec: Hardfork, data: st.DataObject
) -> None:
    """
    After the intrinsic cost, EIP-8037 grants execution gas up to the
    EIP-7825 cap and puts the rest in the state gas reservoir, which is
    empty exactly when the gas limit fits the cap.
    """
    cap = fork.transaction_gas_limit_cap()
    assert cap is not None
    tx_gas = data.draw(
        st.one_of(
            st.sampled_from([cap - 1, cap, cap + 1]),
            ints(fork.transaction_total_gas_limit_cap() or 2 * cap),
        )
    )
    intrinsic = data.draw(ints(min(tx_gas, cap)))
    cost = spec.module("transactions").IntrinsicGasCost(
        execution=gas.ExecutionGas(Uint(intrinsic)),
        calldata_floor=gas.ExecutionGas(Uint(0)),
    )

    allocation = gas.allocate_evm_gas(Uint(tx_gas), cost)

    execution, reservoir = (
        int(allocation.execution_gas),
        int(allocation.state_gas_reservoir),
    )
    assert execution + reservoir == tx_gas - intrinsic
    assert execution == min(tx_gas, cap) - intrinsic
    assert (reservoir == 0) == (tx_gas <= cap)


@pytest.mark.spec_unit
@with_state_gas_reservoir
@given(data=st.data())
def test_settlement_refunds_and_floors(
    fork: Fork, gas: ModuleType, data: st.DataObject
) -> None:
    """
    The sender pays the gas used less a refund of at most a fifth of it
    (EIP-3529), never below the calldata floor (EIP-7623), and gets the
    rest back. The block counts state gas above zero apart and execution
    gas before the refund, also never below the floor (EIP-7778). The
    model follows EIP-8037's "Transaction gas used" and "Block-level gas
    accounting" sections.
    """
    tx_gas = data.draw(ints(fork.transaction_total_gas_limit_cap() or 2**32))
    returned = data.draw(ints(tx_gas))
    reservoir_left = data.draw(ints(tx_gas - returned))
    used = tx_gas - returned - reservoir_left
    floor = data.draw(st.one_of(st.sampled_from([0, used]), ints(tx_gas)))
    refund_counter = data.draw(
        st.one_of(
            st.sampled_from(
                [used // fork.max_refund_quotient() + k for k in (-1, 0, 1)]
            ).filter(lambda r: r >= 0),
            ints(2 * used),
        )
    )
    state_gas = data.draw(st.integers(-used, used))

    settled = gas.settle_transaction_gas(
        Uint(tx_gas),
        Uint(floor),
        gas.ExecutionGas(Uint(returned)),
        gas.StateGas(Uint(reservoir_left)),
        U256(refund_counter),
        state_gas,
    )

    refund = min(used // fork.max_refund_quotient(), refund_counter)
    assert int(settled.gas_used) == max(used - refund, floor)
    assert int(settled.gas_used) + int(settled.gas_left) == tx_gas
    assert int(settled.state_gas_used) == max(state_gas, 0)
    assert int(settled.execution_gas_used) == max(
        used - max(state_gas, 0), floor
    )
