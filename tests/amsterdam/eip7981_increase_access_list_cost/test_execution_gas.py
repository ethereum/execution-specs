"""Test execution gas after the EIP-7981 access list surcharge."""

from typing import Literal

import pytest
from execution_testing import (
    AccessList,
    Account,
    Alloc,
    EIPChecklist,
    Fork,
    GasConsumer,
    Hash,
    Header,
    Op,
    StateTestFiller,
    Storage,
    Transaction,
    TransactionReceipt,
)

from .spec import ref_spec_7981

REFERENCE_SPEC_GIT_PATH = ref_spec_7981.git_path
REFERENCE_SPEC_VERSION = ref_spec_7981.version

pytestmark = pytest.mark.valid_at("EIP7981")


@EIPChecklist.GasCostChanges.Test.OutOfGas()
@EIPChecklist.GasCostChanges.Test.GasUpdatesMeasurement()
@pytest.mark.with_all_tx_types(selector=lambda tx_type: tx_type in (1, 2))
@pytest.mark.parametrize("gas_delta", [-1, 0, 1])
def test_execution_gas_after_access_list_surcharge(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    tx_type: int,
    gas_delta: int,
) -> None:
    """Pin the execution OOG boundary after deducting the surcharge."""
    code = Op.SSTORE(
        0, 2, key_warm=True, original_value=1, current_value=1, new_value=2
    )
    contract = pre.deploy_contract(code=code, storage={0: 1})
    access_list = [AccessList(address=contract, storage_keys=[Hash(0)])]
    intrinsic = fork.transaction_intrinsic_cost_calculator()(
        access_list=access_list, return_cost_deducted_prior_execution=True
    )
    required_gas = intrinsic + code.gas_cost(fork)
    # With empty calldata the floor carries only terms the intrinsic side
    # also pays, so the boundary below is set by execution alone.
    floor = fork.transaction_data_floor_cost_calculator()(
        data=b"", access_list=access_list
    )
    assert required_gas > floor
    succeeds = gas_delta >= 0
    tx = Transaction(
        ty=tx_type,
        sender=pre.fund_eoa(),
        to=contract,
        access_list=access_list,
        gas_limit=required_gas + gas_delta,
        expected_receipt=TransactionReceipt(
            status=int(succeeds),
            gas_used=required_gas if succeeds else required_gas - 1,
        ),
    )
    state_test(
        pre=pre,
        post={contract: Account(storage={0: 2 if succeeds else 1})},
        tx=tx,
    )


@EIPChecklist.GasCostChanges.Test.GasUpdatesMeasurement()
@pytest.mark.with_all_tx_types(selector=lambda tx_type: tx_type in (1, 2))
@pytest.mark.parametrize("reverts", [False, True])
@pytest.mark.parametrize("floor_dominates", [False, True])
def test_access_list_surcharge_with_refund(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    tx_type: int,
    reverts: bool,
    floor_dominates: bool,
) -> None:
    """Apply the surcharged floor after refunds; discard refunds on revert."""
    clear = Op.SSTORE(
        0, 0, key_warm=True, original_value=1, current_value=1, new_value=0
    )
    code = clear + (Op.REVERT(0, 0) if reverts else Op.STOP)
    contract = pre.deploy_contract(code=code, storage={0: 1})
    access_list = [AccessList(address=contract, storage_keys=[Hash(0)])]
    data = b"\x00" * (1000 if floor_dominates else 0)
    intrinsic = fork.transaction_intrinsic_cost_calculator()(
        calldata=data,
        access_list=access_list,
        return_cost_deducted_prior_execution=True,
    )
    before_refund = intrinsic + code.gas_cost(fork)
    refund_counter = 0 if reverts else clear.refund(fork)
    refund = min(refund_counter, before_refund // fork.max_refund_quotient())
    floor = fork.transaction_data_floor_cost_calculator()(
        data=data, access_list=access_list
    )
    assert (floor > before_refund - refund) == floor_dominates
    tx = Transaction(
        ty=tx_type,
        sender=pre.fund_eoa(),
        to=contract,
        data=data,
        access_list=access_list,
        gas_limit=max(before_refund, floor) + 1000,
        expected_receipt=TransactionReceipt(
            status=0 if reverts else 1,
            gas_used=max(before_refund - refund, floor),
        ),
    )
    state_test(
        pre=pre,
        post={contract: Account(storage={0: 1 if reverts else 0})},
        tx=tx,
    )


@EIPChecklist.GasCostChanges.Test.GasUpdatesMeasurement()
@pytest.mark.with_all_tx_types(selector=lambda tx_type: tx_type in (1, 2))
@pytest.mark.parametrize(
    "gas_dominance",
    [
        pytest.param("floor_binds_total", id="floor_binds_total"),
        pytest.param("state_gas_lifts_total", id="state_gas_lifts_total"),
        pytest.param("execution_dominates", id="execution_dominates"),
    ],
)
def test_access_list_surcharge_in_block_execution_gas(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    tx_type: int,
    gas_dominance: Literal[
        "floor_binds_total", "state_gas_lifts_total", "execution_dominates"
    ],
) -> None:
    """
    Pin the surcharged floor and execution branches of block gas accounting.

    An over-cap reservoir funds the state gas of a storage set. The block's
    execution dimension applies the floor to execution gas; the receipt
    applies it to the sum of execution and state gas.
    """
    storage = Storage()
    code = Op.SSTORE(storage.store_next(1), 1, new_value=1, key_warm=True)
    state_cost = code.state_cost(fork)
    assert state_cost > 0
    if gas_dominance == "execution_dominates":
        code += GasConsumer(gas=state_cost, fork=fork)
    contract = pre.deploy_contract(code=code)
    access_list = [AccessList(address=contract, storage_keys=[Hash(0)])]
    intrinsic_calculator = fork.transaction_intrinsic_cost_calculator()
    floor_calculator = fork.transaction_data_floor_cost_calculator()

    def bill(data: bytes) -> tuple[int, int]:
        """Return the floor and the pre-floor execution bill for `data`."""
        floor = floor_calculator(data=data, access_list=access_list)
        tx_execution = intrinsic_calculator(
            calldata=data,
            access_list=access_list,
            return_cost_deducted_prior_execution=True,
        ) + code.execution_cost(fork)
        return floor, tx_execution

    if gas_dominance == "execution_dominates":
        data = b""
        floor, tx_execution = bill(data)
        assert tx_execution > max(floor, state_cost)
        expected_header_gas = tx_execution
    elif gas_dominance in ("floor_binds_total", "state_gas_lifts_total"):
        # Size calldata in word increments until the floor clears the target.
        size = 0
        while True:
            data = b"\x00" * size
            floor, tx_execution = bill(data)
            target = state_cost
            if gas_dominance == "floor_binds_total":
                target += tx_execution
            if floor > target:
                break
            size += 32
        if gas_dominance == "floor_binds_total":
            assert floor > tx_execution + state_cost
        else:
            assert tx_execution < floor < tx_execution + state_cost
        assert floor > state_cost
        expected_header_gas = floor
    else:
        raise ValueError(f"Unknown gas dominance: {gas_dominance}")
    tx_total = tx_execution + state_cost

    tx = Transaction(
        ty=tx_type,
        sender=pre.fund_eoa(),
        to=contract,
        data=data,
        access_list=access_list,
        state_gas_reservoir=state_cost,
        expected_receipt=TransactionReceipt(
            cumulative_gas_used=max(tx_total, floor)
        ),
    )
    state_test(
        pre=pre,
        post={contract: Account(storage=storage)},
        tx=tx,
        blockchain_test_header_verify=Header(gas_used=expected_header_gas),
    )
