"""
Test [EIP-7976: Increase calldata floor cost](https://eips.ethereum.org/EIPS/eip-7976).
"""

from typing import List

import pytest
from execution_testing import (
    AccessList,
    Account,
    Address,
    Alloc,
    AuthorizationTuple,
    Bytes,
    EIPChecklist,
    Fork,
    GasConsumer,
    Op,
    StateTestFiller,
    Transaction,
    TransactionReceipt,
)

from .helpers import DataTestType
from .spec import ref_spec_7976

REFERENCE_SPEC_GIT_PATH = ref_spec_7976.git_path
REFERENCE_SPEC_VERSION = ref_spec_7976.version

pytestmark = [pytest.mark.valid_from("EIP7976")]


@pytest.fixture
def data_test_type() -> DataTestType:
    """Return data test type."""
    return DataTestType.FLOOR_GAS_COST_GREATER_THAN_INTRINSIC_GAS


class TestGasConsumption:
    """Test gas consumption with EIP-7976 active."""

    @pytest.fixture
    def intrinsic_gas_data_floor_minimum_delta(self) -> int:
        """
        Force a minimum delta in order to have some gas to execute the invalid
        opcode.
        """
        return 50_000

    @pytest.fixture
    def to(
        self,
        pre: Alloc,
    ) -> Address | None:
        """
        Return a contract that consumes all gas when executed by calling an
        invalid opcode.
        """
        return pre.deploy_contract(Op.INVALID)

    @pytest.mark.parametrize(
        "ty,protected,authorization_list",
        [
            pytest.param(0, False, None, id="type_0_unprotected"),
            pytest.param(0, True, None, id="type_0_protected"),
            pytest.param(1, True, None, id="type_1"),
            pytest.param(2, True, None, id="type_2"),
            pytest.param(3, True, None, id="type_3"),
            pytest.param(4, True, [Address(1)], id="type_4"),
        ],
        indirect=["authorization_list"],
    )
    @pytest.mark.parametrize(
        "tx_gas_delta",
        [
            # Test with exact gas and extra gas.
            pytest.param(1, id="extra_gas"),
            pytest.param(0, id="exact_gas"),
        ],
    )
    @EIPChecklist.GasCostChanges.Test.GasUpdatesMeasurement()
    def test_full_gas_consumption(
        self,
        state_test: StateTestFiller,
        pre: Alloc,
        tx: Transaction,
    ) -> None:
        """
        Test executing a transaction that fully consumes its execution gas
        allocation.
        """
        tx.expected_receipt = TransactionReceipt(
            cumulative_gas_used=tx.gas_limit
        )
        state_test(
            pre=pre,
            post={},
            tx=tx,
        )


class TestGasConsumptionBelowDataFloor:
    """Test gas consumption barely below the floor data cost (1 gas below)."""

    @pytest.fixture
    def contract_creating_tx(self) -> bool:
        """Use a constant in order to avoid circular fixture dependencies."""
        return False

    @pytest.fixture
    def to(
        self,
        pre: Alloc,
        fork: Fork,
        tx_data: Bytes,
        access_list: List[AccessList] | None,
        authorization_list: List[AuthorizationTuple] | None,
        tx_floor_data_cost: int,
    ) -> Address | None:
        """
        Return a contract that consumes almost all the gas before reaching the
        floor data cost.
        """
        intrinsic_gas_cost_calculator = (
            fork.transaction_intrinsic_cost_calculator()
        )
        execution_gas = tx_floor_data_cost - intrinsic_gas_cost_calculator(
            calldata=tx_data,
            contract_creation=False,
            access_list=access_list,
            authorization_list_or_count=authorization_list,
            return_cost_deducted_prior_execution=True,
        )
        assert execution_gas > 0

        return pre.deploy_contract(
            GasConsumer(gas=execution_gas - 1, fork=fork) + Op.STOP
        )

    @pytest.mark.parametrize(
        "ty,protected,authorization_list",
        [
            pytest.param(0, False, None, id="type_0_unprotected"),
            pytest.param(0, True, None, id="type_0_protected"),
            pytest.param(1, True, None, id="type_1"),
            pytest.param(2, True, None, id="type_2"),
            pytest.param(3, True, None, id="type_3"),
            pytest.param(4, True, [Address(1)], id="type_4"),
        ],
        indirect=["authorization_list"],
    )
    @pytest.mark.parametrize(
        "tx_gas_delta",
        [
            # Test with exact gas and extra gas, to verify that the refund is
            # correctly applied to the full consumed execution gas.
            pytest.param(0, id="exact_gas"),
        ],
    )
    @EIPChecklist.GasCostChanges.Test.GasUpdatesMeasurement()
    def test_gas_consumption_below_data_floor(
        self,
        state_test: StateTestFiller,
        pre: Alloc,
        tx: Transaction,
        tx_floor_data_cost: int,
    ) -> None:
        """
        Test executing a transaction that almost consumes the floor data cost.
        """
        tx.expected_receipt = TransactionReceipt(
            cumulative_gas_used=tx_floor_data_cost
        )
        state_test(
            pre=pre,
            post={},
            tx=tx,
        )


@pytest.mark.with_all_tx_types(selector=lambda ty: ty < 3)
@pytest.mark.parametrize(
    "data",
    [
        pytest.param(b"\x00" * 32, id="zero_bytes"),
        pytest.param(b"\x00\x01" * 16, id="mixed_bytes"),
    ],
)
def test_standard_calldata_cost_above_floor(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    tx_type: int,
    data: bytes,
) -> None:
    """Pin zero-byte pricing for plain calldata with execution above floor."""
    code = Op.SSTORE(0, 2, original_value=1, current_value=1, new_value=2)
    contract = pre.deploy_contract(code=code, storage={0: 1})
    intrinsic = fork.transaction_intrinsic_cost_calculator()(
        calldata=data, return_cost_deducted_prior_execution=True
    )
    gas_used = intrinsic + code.gas_cost(fork)
    floor = fork.transaction_data_floor_cost_calculator()(data=data)
    assert gas_used > floor
    tx = Transaction(
        ty=tx_type,
        sender=pre.fund_eoa(),
        to=contract,
        data=data,
        gas_limit=gas_used + 1,
        expected_receipt=TransactionReceipt(cumulative_gas_used=gas_used),
    )
    state_test(pre=pre, tx=tx, post={contract: Account(storage={0: 2})})
