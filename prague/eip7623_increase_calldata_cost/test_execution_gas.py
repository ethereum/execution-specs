"""
abstract: Test [EIP-7623: Increase calldata cost](https://eips.ethereum.org/EIPS/eip-7623)
    Test execution gas consumption after [EIP-7623: Increase calldata cost](https://eips.ethereum.org/EIPS/eip-7623).
"""  # noqa: E501

from typing import List

import pytest

from ethereum_test_forks import Fork, Prague
from ethereum_test_tools import (
    AccessList,
    Address,
    Alloc,
    AuthorizationTuple,
    Bytes,
    StateTestFiller,
    Transaction,
    TransactionReceipt,
)
from ethereum_test_tools import Opcodes as Op

from .helpers import DataTestType
from .spec import ref_spec_7623

REFERENCE_SPEC_GIT_PATH = ref_spec_7623.git_path
REFERENCE_SPEC_VERSION = ref_spec_7623.version

ENABLE_FORK = Prague
pytestmark = [pytest.mark.valid_from(str(ENABLE_FORK))]


@pytest.fixture
def data_test_type() -> DataTestType:
    """Return data test type."""
    return DataTestType.FLOOR_GAS_COST_GREATER_THAN_INTRINSIC_GAS


@pytest.fixture
def authorization_refund() -> bool:
    """
    Force the authority of the authorization tuple to be an existing authority in order
    to produce a refund.
    """
    return True


class TestGasRefunds:
    """Test gas refunds with EIP-7623 active."""

    @pytest.fixture
    def intrinsic_gas_data_floor_minimum_delta(self) -> int:
        """
        In this test we reset a storage key to zero to induce a refund,
        but we need to make sure that the floor is higher than the gas
        used during execution in order for the refund to be applied to
        the floor.
        """
        return 50_000

    @pytest.fixture
    def to(
        self,
        pre: Alloc,
    ) -> Address | None:
        """Return a contract that when executed results in refunds due to storage clearing."""
        return pre.deploy_contract(Op.SSTORE(0, 0) + Op.STOP, storage={0: 1})

    @pytest.fixture
    def refund(self, fork: Fork, ty: int) -> int:
        """Return the refund gas of the transaction."""
        gas_costs = fork.gas_costs()
        refund = gas_costs.R_STORAGE_CLEAR
        if ty == 4:
            refund += gas_costs.R_AUTHORIZATION_EXISTING_AUTHORITY
        return refund

    @pytest.mark.parametrize(
        "ty,protected,authorization_list",
        [
            pytest.param(0, False, None, id="type_0_unprotected"),
            pytest.param(0, True, None, id="type_0_protected"),
            pytest.param(1, True, None, id="type_1"),
            pytest.param(2, True, None, id="type_2"),
            pytest.param(
                3,
                True,
                None,
                id="type_3",
            ),
            pytest.param(
                4,
                True,
                [Address(1)],
                id="type_4_with_authorization_refund",
            ),
        ],
        indirect=["authorization_list"],
    )
    @pytest.mark.parametrize(
        "tx_gas_delta",
        [
            # Test with exact gas and extra gas, to verify that the refund is correctly applied up
            # to the floor data cost.
            pytest.param(1, id="extra_gas"),
            pytest.param(0, id="exact_gas"),
        ],
    )
    def test_gas_refunds_from_data_floor(
        self,
        state_test: StateTestFiller,
        pre: Alloc,
        tx: Transaction,
        tx_floor_data_cost: int,
        refund: int,
    ) -> None:
        """
        Test gas refunds deducted from the data floor.

        I.e. the used gas by the intrinsic gas cost plus the execution cost is less than the data
        floor, hence data floor is used, and then the gas refunds are applied to the data floor.
        """
        tx.expected_receipt = TransactionReceipt(gas_used=tx_floor_data_cost - refund)
        state_test(
            pre=pre,
            post={
                tx.to: {
                    "storage": {0: 0},  # Verify storage was cleared
                }
            },
            tx=tx,
        )


class TestGasConsumption:
    """Test gas consumption with EIP-7623 active."""

    @pytest.fixture
    def intrinsic_gas_data_floor_minimum_delta(self) -> int:
        """Force a minimum delta in order to have some gas to execute the invalid opcode."""
        return 50_000

    @pytest.fixture
    def to(
        self,
        pre: Alloc,
    ) -> Address | None:
        """Return a contract that consumes all gas when executed by calling an invalid opcode."""
        return pre.deploy_contract(Op.INVALID)

    @pytest.fixture
    def refund(
        self,
        fork: Fork,
        ty: int,
        authorization_refund: bool,
    ) -> int:
        """Return the refund gas of the transaction."""
        gas_costs = fork.gas_costs()
        refund = 0
        if ty == 4 and authorization_refund:
            refund += gas_costs.R_AUTHORIZATION_EXISTING_AUTHORITY
        return refund

    @pytest.mark.parametrize(
        "ty,protected,authorization_list",
        [
            pytest.param(0, False, None, id="type_0_unprotected"),
            pytest.param(0, True, None, id="type_0_protected"),
            pytest.param(1, True, None, id="type_1"),
            pytest.param(2, True, None, id="type_2"),
            pytest.param(
                3,
                True,
                None,
                id="type_3",
            ),
            pytest.param(
                4,
                True,
                [Address(1)],
                id="type_4_with_authorization_refund",
            ),
        ],
        indirect=["authorization_list"],
    )
    @pytest.mark.parametrize(
        "tx_gas_delta",
        [
            # Test with exact gas and extra gas, to verify that the refund is correctly applied
            # to the full consumed execution gas.
            pytest.param(1, id="extra_gas"),
            pytest.param(0, id="exact_gas"),
        ],
    )
    def test_full_gas_consumption(
        self,
        state_test: StateTestFiller,
        pre: Alloc,
        tx: Transaction,
        refund: int,
    ) -> None:
        """Test executing a transaction that fully consumes its execution gas allocation."""
        tx.expected_receipt = TransactionReceipt(gas_used=tx.gas_limit - refund)
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
    def refund(
        self,
        fork: Fork,
        ty: int,
        authorization_refund: bool,
    ) -> int:
        """Return the refund gas of the transaction."""
        gas_costs = fork.gas_costs()
        refund = 0
        if ty == 4 and authorization_refund:
            refund += gas_costs.R_AUTHORIZATION_EXISTING_AUTHORITY
        return refund

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
        intrinsic_gas_cost_calculator = fork.transaction_intrinsic_cost_calculator()
        execution_gas = tx_floor_data_cost - intrinsic_gas_cost_calculator(
            calldata=tx_data,
            contract_creation=False,
            access_list=access_list,
            authorization_list_or_count=authorization_list,
            return_cost_deducted_prior_execution=True,
        )
        assert execution_gas > 0

        return pre.deploy_contract((Op.JUMPDEST * (execution_gas - 1)) + Op.STOP)

    @pytest.mark.parametrize(
        "ty,protected,authorization_list,authorization_refund",
        [
            pytest.param(0, False, None, False, id="type_0_unprotected"),
            pytest.param(0, True, None, False, id="type_0_protected"),
            pytest.param(1, True, None, False, id="type_1"),
            pytest.param(2, True, None, False, id="type_2"),
            pytest.param(
                3,
                True,
                None,
                False,
                id="type_3",
            ),
            pytest.param(
                4,
                True,
                [Address(1)],
                False,
                id="type_4",
            ),
            pytest.param(
                4,
                True,
                [Address(1)],
                True,
                id="type_4_with_authorization_refund",
            ),
        ],
        indirect=["authorization_list"],
    )
    @pytest.mark.parametrize(
        "tx_gas_delta",
        [
            # Test with exact gas and extra gas, to verify that the refund is correctly applied
            # to the full consumed execution gas.
            pytest.param(0, id="exact_gas"),
        ],
    )
    def test_gas_consumption_below_data_floor(
        self,
        state_test: StateTestFiller,
        pre: Alloc,
        tx: Transaction,
        tx_floor_data_cost: int,
        refund: int,
    ) -> None:
        """Test executing a transaction that almost consumes the floor data cost."""
        tx.expected_receipt = TransactionReceipt(gas_used=tx_floor_data_cost - refund)
        state_test(
            pre=pre,
            post={},
            tx=tx,
        )
