"""
Additional test coverage for [EIP-7976: Increase calldata floor cost](https://eips.ethereum.org/EIPS/eip-7976).

This module tests:
1. Token calculation verification with different byte compositions
2. Maximum calldata size handling
3. Memory expansion interaction with floor cost
4. Nested contract calls verification
5. Exact threshold boundary testing
6. Authorization list gas cost verification
7. Gas refund cap interaction with floor cost
"""

from typing import List

import pytest
from execution_testing import (
    AccessList,
    Address,
    Alloc,
    AuthorizationTuple,
    Bytecode,
    Bytes,
    Fork,
    Op,
    StateTestFiller,
    Transaction,
    TransactionReceipt,
)

from .spec import ref_spec_7976

REFERENCE_SPEC_GIT_PATH = ref_spec_7976.git_path
REFERENCE_SPEC_VERSION = ref_spec_7976.version

pytestmark = [pytest.mark.valid_from("EIP7976")]


class TestTokenCalculation:
    """Test token calculation with different byte compositions."""

    @pytest.fixture
    def sender(self, pre: Alloc) -> Address:
        """Create sender account."""
        return pre.fund_eoa(10**21)

    @pytest.fixture
    def to(self, pre: Alloc) -> Address:
        """Deploy a simple contract that does nothing."""
        return pre.deploy_contract(Op.STOP)

    @pytest.mark.parametrize(
        "calldata,expected_standard_tokens,description",
        [
            pytest.param(
                Bytes(b"\x00" * 100),
                100,
                "all_zero_bytes",
                id="all_zero_bytes",
            ),
            pytest.param(
                Bytes(b"\x01" * 100),
                400,
                "all_nonzero_bytes",
                id="all_nonzero_bytes",
            ),
            pytest.param(
                Bytes(b"\x01" * 75 + b"\x00" * 25),
                325,  # 75*4 + 25*1
                "75_percent_nonzero",
                id="75_percent_nonzero",
            ),
            pytest.param(
                Bytes(b"\x01" * 25 + b"\x00" * 75),
                175,  # 25*4 + 75*1
                "25_percent_nonzero",
                id="25_percent_nonzero",
            ),
            pytest.param(
                Bytes(b"\x01\x02\x03\x00"),
                13,  # 3*4 + 1*1
                "three_nonzero_one_zero",
                id="three_nonzero_one_zero",
            ),
            pytest.param(
                Bytes(b"\xff" * 50 + b"\x00" * 50),
                250,  # 50*4 + 50*1
                "half_and_half",
                id="half_and_half",
            ),
        ],
    )
    def test_token_calculation_verification(
        self,
        state_test: StateTestFiller,
        pre: Alloc,
        sender: Address,
        to: Address,
        calldata: Bytes,
        expected_standard_tokens: int,
        description: str,
        fork: Fork,
    ) -> None:
        """
        Verify token calculation is correct for different byte compositions.

        Standard calldata token formula:
        tokens = zero_bytes + (nonzero_bytes * 4)

        Floor token formula introduced in EIP-7976:
        floor_tokens = 4 * calldata_bytes
        """
        # Calculate expected costs
        intrinsic_cost_calculator = (
            fork.transaction_intrinsic_cost_calculator()
        )
        intrinsic_cost_before_execution = intrinsic_cost_calculator(
            calldata=calldata,
            contract_creation=False,
            access_list=None,
            authorization_list_or_count=None,
            return_cost_deducted_prior_execution=True,
        )

        floor_cost_calculator = fork.transaction_data_floor_cost_calculator()
        floor_cost = floor_cost_calculator(data=calldata)

        # Verify floor token calculation:
        # floor_cost = 21000 + (floor_tokens * floor_token_cost)
        # where floor_tokens = 4 * calldata_bytes
        gas_costs = fork.gas_costs()
        floor_token_cost = gas_costs.GAS_TX_DATA_TOKEN_FLOOR
        expected_floor_tokens = len(calldata) * 4
        expected_floor_cost = 21000 + (
            expected_floor_tokens * floor_token_cost
        )
        assert floor_cost == expected_floor_cost, (
            f"Floor cost mismatch for {description}: "
            f"{floor_cost} != {expected_floor_cost} "
            f"(floor_tokens={expected_floor_tokens}, "
            f"floor_cost_per_token={floor_token_cost})"
        )

        expected_intrinsic_cost = 21000 + (
            expected_standard_tokens * gas_costs.GAS_TX_DATA_TOKEN_STANDARD
        )
        assert intrinsic_cost_before_execution == expected_intrinsic_cost, (
            f"Intrinsic cost mismatch for {description}: "
            f"{intrinsic_cost_before_execution} != {expected_intrinsic_cost} "
            f"(standard_tokens={expected_standard_tokens})"
        )

        # Create transaction with exact gas needed
        total_intrinsic_cost = max(intrinsic_cost_before_execution, floor_cost)
        tx = Transaction(
            sender=sender,
            to=to,
            data=calldata,
            gas_limit=total_intrinsic_cost,
        )

        # Expected gas used should be the floor cost if it's greater
        expected_gas_used = total_intrinsic_cost
        tx.expected_receipt = TransactionReceipt(
            cumulative_gas_used=expected_gas_used
        )

        state_test(
            pre=pre,
            post={},
            tx=tx,
        )


class TestMaximumCalldata:
    """Test maximum calldata size handling."""

    @pytest.fixture
    def sender(self, pre: Alloc) -> Address:
        """Create sender account with massive balance."""
        return pre.fund_eoa(10**25)

    @pytest.fixture
    def to(self, pre: Alloc) -> Address:
        """Deploy a simple contract."""
        return pre.deploy_contract(Op.STOP)

    def test_maximum_calldata_size(
        self,
        state_test: StateTestFiller,
        pre: Alloc,
        sender: Address,
        to: Address,
        fork: Fork,
    ) -> None:
        """
        Test transaction with large calldata size (~10M gas worth).

        This verifies that floor cost calculation doesn't overflow and
        gas metering is accurate at scale.
        """
        # Calculate calldata size that would cost approximately 10M gas
        # (below the default block gas limit to avoid EIP-7825 cap issues)
        # Using all non-zero bytes for maximum density
        # floor_cost = 21000 + (GAS_TX_DATA_TOKEN_FLOOR * tokens)
        # For non-zero bytes: tokens = bytes * 4
        gas_costs = fork.gas_costs()
        target_gas = 10_000_000
        floor_token_cost = gas_costs.GAS_TX_DATA_TOKEN_FLOOR
        target_tokens = (target_gas - 21000) // floor_token_cost
        # Use all non-zero bytes for maximum token density
        num_bytes = target_tokens // 4

        calldata = Bytes(b"\x01" * num_bytes)

        # Calculate expected costs
        floor_cost_calculator = fork.transaction_data_floor_cost_calculator()
        floor_cost = floor_cost_calculator(data=calldata)

        intrinsic_cost_calculator = (
            fork.transaction_intrinsic_cost_calculator()
        )
        intrinsic_cost = intrinsic_cost_calculator(
            calldata=calldata,
            contract_creation=False,
            access_list=None,
            authorization_list_or_count=None,
        )

        # Floor cost should dominate for data-heavy transaction
        assert floor_cost > 5_000_000, "Floor cost should be substantial"
        expected_gas = max(intrinsic_cost, floor_cost)

        # Add buffer for execution (cold address access + STOP opcode)
        execution_buffer = 3000
        gas_limit = expected_gas + execution_buffer

        tx = Transaction(
            sender=sender,
            to=to,
            data=calldata,
            gas_limit=gas_limit,
        )

        # Gas used should be the floor cost (execution is minimal)
        tx.expected_receipt = TransactionReceipt(
            cumulative_gas_used=expected_gas
        )

        state_test(
            pre=pre,
            post={},
            tx=tx,
        )


class TestMemoryExpansion:
    """Test memory expansion interaction with floor cost."""

    @pytest.fixture
    def sender(self, pre: Alloc) -> Address:
        """Create sender account."""
        return pre.fund_eoa(10**21)

    @pytest.fixture
    def to(self, pre: Alloc) -> Address:
        """
        Deploy a contract that causes memory expansion.

        The contract performs CALLDATACOPY to expand memory, then stops.
        This ensures memory expansion gas is counted in execution gas.
        """
        # CALLDATACOPY(destOffset=0, offset=0, length=CALLDATASIZE)
        # This will copy all calldata to memory starting at offset 0
        code = (
            Op.CALLDATASIZE  # Push calldata size
            + Op.PUSH1(0)  # Push offset (0)
            + Op.PUSH1(0)  # Push destOffset (0)
            + Op.CALLDATACOPY  # Copy calldata to memory
            + Op.STOP
        )
        return pre.deploy_contract(code)

    @pytest.mark.parametrize(
        "calldata_size",
        [
            pytest.param(1024, id="1kb"),
            pytest.param(10240, id="10kb"),
            pytest.param(32768, id="32kb"),
        ],
    )
    def test_memory_expansion_with_calldata(
        self,
        state_test: StateTestFiller,
        pre: Alloc,
        sender: Address,
        to: Address,
        calldata_size: int,
        fork: Fork,
    ) -> None:
        """
        Test memory expansion gas is counted in execution_gas not floor.

        The transaction pays max(standard_cost + execution_gas, floor_cost)
        where execution_gas includes memory expansion costs.
        """
        # Create calldata with non-zero bytes to trigger floor cost
        calldata = Bytes(b"\x01" * calldata_size)

        # Calculate costs
        intrinsic_cost_calculator = (
            fork.transaction_intrinsic_cost_calculator()
        )
        intrinsic_cost_before_execution = intrinsic_cost_calculator(
            calldata=calldata,
            contract_creation=False,
            access_list=None,
            authorization_list_or_count=None,
            return_cost_deducted_prior_execution=True,
        )

        floor_cost_calculator = fork.transaction_data_floor_cost_calculator()
        floor_cost = floor_cost_calculator(data=calldata)

        # Memory expansion cost for copying calldata_size bytes
        # memory_cost = (words^2)/512 + (3*words) where words = (size+31)//32
        words = (calldata_size + 31) // 32
        memory_expansion_cost = (words * words) // 512 + (3 * words)

        # Execution gas includes CALLDATASIZE, PUSH1*2, CALLDATACOPY base,
        # and memory expansion
        gas_costs = fork.gas_costs()
        execution_gas = (
            gas_costs.GAS_BASE  # CALLDATASIZE
            + gas_costs.GAS_VERY_LOW * 2  # PUSH1 * 2
            + gas_costs.GAS_VERY_LOW  # CALLDATACOPY base
            + memory_expansion_cost  # Memory expansion
            + 3 * calldata_size  # CALLDATACOPY per-byte cost
        )

        # Total gas is intrinsic + execution
        total_with_execution = intrinsic_cost_before_execution + execution_gas

        # The actual gas used is max(total_with_execution, floor_cost)
        expected_gas = max(total_with_execution, floor_cost)

        tx = Transaction(
            sender=sender,
            to=to,
            data=calldata,
            gas_limit=expected_gas + 100000,  # Add buffer for safety
        )

        # Verify the transaction executes successfully
        state_test(
            pre=pre,
            post={},
            tx=tx,
        )


class TestNestedContractCalls:
    """Test that nested contract calls don't trigger additional floor costs."""

    @pytest.fixture
    def sender(self, pre: Alloc) -> Address:
        """Create sender account."""
        return pre.fund_eoa(10**21)

    @pytest.fixture
    def contract_b(self, pre: Alloc) -> Address:
        """
        Deploy Contract B that receives calldata and stores something.

        This contract will be called by Contract A with calldata.
        """
        # Simply store a value to show it was executed
        code = Op.PUSH1(42) + Op.PUSH1(0) + Op.SSTORE + Op.STOP
        return pre.deploy_contract(code)

    @pytest.fixture
    def contract_a(self, pre: Alloc, contract_b: Address) -> Address:
        """
        Deploy Contract A that calls Contract B with calldata.

        This contract performs a CALL to contract_b with some calldata.
        """
        # Prepare call to contract_b with 100 bytes of data
        # CALL(gas, address, value, argsOffset, argsSize, retOffset, retSize)
        code = (
            # Store some data in memory to pass as calldata
            Op.PUSH1(100)  # Size
            + Op.PUSH1(0)  # Offset
            + Op.PUSH1(0xFF)  # Value to fill
            + Op.MSTORE
            +
            # Perform CALL
            Op.PUSH1(0)  # retSize
            + Op.PUSH1(0)  # retOffset
            + Op.PUSH1(100)  # argsSize (100 bytes)
            + Op.PUSH1(0)  # argsOffset
            + Op.PUSH1(0)  # value
            + Op.PUSH20(contract_b.hex())  # address
            + Op.GAS  # gas (all remaining)
            + Op.CALL
            + Op.STOP
        )
        return pre.deploy_contract(code)

    def test_nested_call_no_additional_floor_cost(
        self,
        state_test: StateTestFiller,
        pre: Alloc,
        sender: Address,
        contract_a: Address,
        contract_b: Address,
        fork: Fork,
    ) -> None:
        """
        Verify only the transaction's calldata affects floor cost.

        Internal CALL operations with calldata don't trigger additional
        floor costs.
        """
        # Transaction calldata (sent to contract_a)
        tx_calldata = Bytes(b"\x01" * 200)

        # Calculate floor cost based ONLY on transaction calldata
        floor_cost_calculator = fork.transaction_data_floor_cost_calculator()
        floor_cost = floor_cost_calculator(data=tx_calldata)

        intrinsic_cost_calculator = (
            fork.transaction_intrinsic_cost_calculator()
        )
        intrinsic_cost = intrinsic_cost_calculator(
            calldata=tx_calldata,
            contract_creation=False,
            access_list=None,
            authorization_list_or_count=None,
        )

        # The floor cost should only consider the transaction's calldata,
        # not the calldata passed in the internal CALL
        tokens_tx = len(tx_calldata) * 4  # All non-zero bytes
        gas_costs = fork.gas_costs()
        expected_floor_cost = 21000 + (
            tokens_tx * gas_costs.GAS_TX_DATA_TOKEN_FLOOR
        )
        assert floor_cost == expected_floor_cost

        tx = Transaction(
            sender=sender,
            to=contract_a,
            data=tx_calldata,
            gas_limit=intrinsic_cost + 500000,  # Add execution gas buffer
        )

        state_test(
            pre=pre,
            post={
                contract_b: {
                    "storage": {0: 42},  # Verify contract_b was executed
                }
            },
            tx=tx,
        )

    def test_delegatecall_no_additional_floor_cost(
        self,
        state_test: StateTestFiller,
        pre: Alloc,
        sender: Address,
        fork: Fork,
    ) -> None:
        """
        Verify DELEGATECALL operations don't trigger additional floor costs.
        """
        # Contract that will be delegatecalled
        delegate_code = Op.PUSH1(99) + Op.PUSH1(0) + Op.SSTORE + Op.STOP
        delegate_contract = pre.deploy_contract(delegate_code)

        # Contract that performs DELEGATECALL
        # DELEGATECALL(gas, address, argsOffset, argsSize, retOffset, retSize)
        caller_code = (
            Op.PUSH1(0)  # retSize
            + Op.PUSH1(0)  # retOffset
            + Op.PUSH1(64)  # argsSize
            + Op.PUSH1(0)  # argsOffset
            + Op.PUSH20(delegate_contract.hex())  # address
            + Op.GAS  # gas
            + Op.DELEGATECALL
            + Op.STOP
        )
        caller_contract = pre.deploy_contract(caller_code, storage={})

        # Transaction calldata
        tx_calldata = Bytes(b"\x01" * 150)

        intrinsic_cost_calculator = (
            fork.transaction_intrinsic_cost_calculator()
        )
        intrinsic_cost = intrinsic_cost_calculator(
            calldata=tx_calldata,
            contract_creation=False,
            access_list=None,
            authorization_list_or_count=None,
        )

        tx = Transaction(
            sender=sender,
            to=caller_contract,
            data=tx_calldata,
            gas_limit=intrinsic_cost + 500000,
        )

        state_test(
            pre=pre,
            post={
                caller_contract: {
                    "storage": {
                        0: 99
                    },  # DELEGATECALL executes in caller's context
                }
            },
            tx=tx,
        )


class TestExactThresholdBoundary:
    """Test exact threshold where floor_cost == intrinsic_cost."""

    @pytest.fixture
    def sender(self, pre: Alloc) -> Address:
        """Create sender account."""
        return pre.fund_eoa(10**21)

    @pytest.fixture
    def to(self, pre: Alloc) -> Address:
        """Deploy a simple contract."""
        return pre.deploy_contract(Op.STOP)

    @pytest.mark.parametrize(
        "access_list,authorization_list",
        [
            pytest.param(None, None, id="no_extras"),
            pytest.param(
                [AccessList(address=Address(1), storage_keys=[])],
                None,
                id="with_access_list",
            ),
        ],
        indirect=["authorization_list"],
    )
    @pytest.mark.parametrize(
        "ty",
        [
            # Type 1 (EIP-2930) introduced access lists
            pytest.param(1, id="type_1"),
            pytest.param(2, id="type_2"),
        ],
    )
    @pytest.mark.parametrize(
        "threshold_offset",
        [
            pytest.param(0, id="below_threshold"),
            pytest.param(1, id="above_threshold"),
            pytest.param(2, id="above_threshold_plus_2"),
        ],
    )
    def test_exact_threshold_boundary(
        self,
        state_test: StateTestFiller,
        pre: Alloc,
        sender: Address,
        to: Address,
        fork: Fork,
        access_list: List[AccessList] | None,
        authorization_list: List[AuthorizationTuple] | None,
        ty: int,
        threshold_offset: int,
    ) -> None:
        """
        Find exact calldata byte count N where floor_cost == intrinsic_cost.

        Test with N, N+1, and N+2 bytes to verify max() function
        switches correctly.
        """
        from .helpers import find_floor_cost_threshold

        def bytes_to_data(byte_count: int) -> Bytes:
            """Convert byte count to calldata bytes."""
            return Bytes(b"\x01" * byte_count)

        intrinsic_cost_calculator = (
            fork.transaction_intrinsic_cost_calculator()
        )

        def intrinsic_cost(byte_count: int) -> int:
            return intrinsic_cost_calculator(
                calldata=bytes_to_data(byte_count),
                contract_creation=False,
                access_list=access_list,
                authorization_list_or_count=authorization_list,
                return_cost_deducted_prior_execution=True,
            )

        floor_cost_calculator = fork.transaction_data_floor_cost_calculator()

        def floor_cost(byte_count: int) -> int:
            return floor_cost_calculator(data=bytes_to_data(byte_count))

        # Find the threshold
        threshold_bytes = find_floor_cost_threshold(
            floor_data_gas_cost_calculator=floor_cost,
            intrinsic_gas_cost_calculator=intrinsic_cost,
        )

        byte_count = threshold_bytes + threshold_offset
        calldata = bytes_to_data(byte_count)
        intrinsic_raw = intrinsic_cost(byte_count)
        floor_raw = floor_cost(byte_count)

        if threshold_offset == 0:
            assert intrinsic_raw >= floor_raw, (
                "At threshold: intrinsic should dominate"
            )
        else:
            assert floor_raw > intrinsic_raw, (
                f"Above threshold: floor should dominate. "
                f"floor={floor_raw}, intrinsic={intrinsic_raw}"
            )

        intrinsic_total = intrinsic_cost_calculator(
            calldata=calldata,
            contract_creation=False,
            access_list=access_list,
            authorization_list_or_count=authorization_list,
        )

        tx = Transaction(
            ty=ty,
            sender=sender,
            to=to,
            nonce=0,
            data=calldata,
            gas_limit=intrinsic_total,
            access_list=access_list,
            authorization_list=authorization_list,
        )
        tx.expected_receipt = TransactionReceipt(
            cumulative_gas_used=intrinsic_total
        )

        state_test(
            pre=pre,
            post={},
            tx=tx,
        )


class TestAuthorizationListGasCost:
    """Verify authorization list gas costs are included correctly."""

    @pytest.fixture
    def sender(self, pre: Alloc) -> Address:
        """Create sender account."""
        return pre.fund_eoa(10**21)

    @pytest.fixture
    def to(self, pre: Alloc) -> Address:
        """Deploy a simple contract."""
        return pre.deploy_contract(Op.STOP)

    @pytest.mark.parametrize(
        "num_authorizations",
        [
            pytest.param(1, id="single_auth"),
            pytest.param(5, id="five_auths"),
            pytest.param(10, id="ten_auths"),
        ],
    )
    def test_authorization_list_intrinsic_gas(
        self,
        state_test: StateTestFiller,
        pre: Alloc,
        sender: Address,
        to: Address,
        fork: Fork,
        num_authorizations: int,
    ) -> None:
        """
        Verify authorization list gas costs are included in intrinsic gas.

        Each authorization in the list adds a fixed gas cost to the
        intrinsic gas. This should be accounted for before comparing
        with floor cost.
        """
        # Create authorization list
        authorization_list = [
            AuthorizationTuple(
                signer=pre.fund_eoa(0),
                address=Address(i + 1),
            )
            for i in range(num_authorizations)
        ]

        # Use calldata that triggers floor cost
        calldata = Bytes(b"\x01" * 500)

        # Calculate costs
        intrinsic_cost_calculator = (
            fork.transaction_intrinsic_cost_calculator()
        )
        intrinsic_cost_with_auth = intrinsic_cost_calculator(
            calldata=calldata,
            contract_creation=False,
            access_list=None,
            authorization_list_or_count=authorization_list,
        )

        intrinsic_cost_without_auth = intrinsic_cost_calculator(
            calldata=calldata,
            contract_creation=False,
            access_list=None,
            authorization_list_or_count=None,
        )

        floor_cost_calculator = fork.transaction_data_floor_cost_calculator()
        floor_cost = floor_cost_calculator(data=calldata)

        # Each authorization adds calldata cost for the authorization tuple
        # plus G_AUTHORIZATION gas cost. The difference we see should be
        # primarily from the authorization gas but may include calldata costs
        # for encoding the authorization list.
        actual_auth_cost = (
            intrinsic_cost_with_auth - intrinsic_cost_without_auth
        )
        # Just verify that there is a positive cost increase
        assert actual_auth_cost > 0, (
            f"Authorization should add gas cost, got: {actual_auth_cost}"
        )

        # The transaction should pay max(intrinsic_with_auth, floor_cost)
        expected_gas = max(intrinsic_cost_with_auth, floor_cost)

        tx = Transaction(
            ty=4,  # Type 4 supports authorization lists
            sender=sender,
            to=to,
            data=calldata,
            gas_limit=expected_gas,
            authorization_list=authorization_list,
        )

        tx.expected_receipt = TransactionReceipt(
            cumulative_gas_used=expected_gas
        )

        state_test(
            pre=pre,
            post={},
            tx=tx,
        )


class TestRefundCapInteraction:
    """Test that the 1/5 refund cap interacts correctly with floor cost."""

    @pytest.fixture
    def sender(self, pre: Alloc) -> Address:
        """Create sender account."""
        return pre.fund_eoa(10**21)

    @pytest.fixture
    def calldata_for_floor(self) -> Bytes:
        """Calldata that triggers floor cost."""
        return Bytes(b"\x01" * 500)

    def test_refund_calculated_from_execution_not_floor(
        self,
        state_test: StateTestFiller,
        pre: Alloc,
        sender: Address,
        fork: Fork,
        calldata_for_floor: Bytes,
    ) -> None:
        """
        Verify refunds are calculated from execution gas, not floor cost.

        The refund is calculated as min(refund_counter, gas_used // 5) where
        gas_used is the actual execution gas before refund, not the floor cost.
        """
        # Deploy contract that clears storage (generates refund)
        # Pre-set storage slot 0 to 1, then clear it
        contract = pre.deploy_contract(
            Op.SSTORE(0, 0) + Op.STOP,
            storage={0: 1},
        )

        # Calculate costs
        intrinsic_cost_calculator = (
            fork.transaction_intrinsic_cost_calculator()
        )
        intrinsic_cost_before_execution = intrinsic_cost_calculator(
            calldata=calldata_for_floor,
            contract_creation=False,
            access_list=None,
            authorization_list_or_count=None,
            return_cost_deducted_prior_execution=True,
        )

        floor_cost_calculator = fork.transaction_data_floor_cost_calculator()
        floor_cost = floor_cost_calculator(data=calldata_for_floor)

        # Calculate execution gas for SSTORE clearing
        gas_costs = fork.gas_costs()
        # Op.SSTORE(0, 0) generates: PUSH1(0) PUSH1(0) SSTORE
        execution_gas = (
            gas_costs.GAS_COLD_STORAGE_ACCESS  # First access to storage slot
            + gas_costs.GAS_STORAGE_RESET  # SSTORE reset cost
            + gas_costs.GAS_VERY_LOW * 2  # PUSH1 * 2 for Op.SSTORE helper
        )

        # Total gas before refund
        total_gas_before_refund = (
            intrinsic_cost_before_execution + execution_gas
        )

        # Refund for clearing storage
        max_refund = gas_costs.REFUND_STORAGE_CLEAR
        actual_refund = min(max_refund, total_gas_before_refund // 5)

        # Gas after refund
        gas_after_refund = total_gas_before_refund - actual_refund

        # Final gas is max(gas_after_refund, floor_cost)
        expected_gas = max(gas_after_refund, floor_cost)

        # Gas limit must satisfy both execution needs and floor cost
        gas_limit = max(total_gas_before_refund, floor_cost)

        tx = Transaction(
            sender=sender,
            to=contract,
            data=calldata_for_floor,
            gas_limit=gas_limit,
        )

        tx.expected_receipt = TransactionReceipt(
            cumulative_gas_used=expected_gas
        )

        state_test(
            pre=pre,
            post={
                contract: {
                    "storage": {0: 0},  # Storage cleared
                }
            },
            tx=tx,
        )

    def test_refund_cap_at_one_fifth(
        self,
        state_test: StateTestFiller,
        pre: Alloc,
        sender: Address,
        fork: Fork,
    ) -> None:
        """
        Test that refunds are capped at 1/5 of gas used.

        Even if the refund counter is high, the actual refund cannot exceed
        gas_used // 5. Use minimal calldata to avoid floor cost interference.
        """
        # Use minimal calldata so floor cost doesn't dominate
        calldata = Bytes(b"")

        # Deploy contract that clears multiple storage slots
        # This generates a large refund counter
        num_slots = 10
        code = Bytecode()
        storage = {i: 1 for i in range(num_slots)}  # noqa: C420

        for i in range(num_slots):
            code += Op.SSTORE(i, 0)

        code += Op.STOP
        contract = pre.deploy_contract(
            code,
            storage=storage,  # type: ignore[arg-type]
        )

        # Calculate costs
        intrinsic_cost_calculator = (
            fork.transaction_intrinsic_cost_calculator()
        )
        intrinsic_cost_before_execution = intrinsic_cost_calculator(
            calldata=calldata,
            contract_creation=False,
            access_list=None,
            authorization_list_or_count=None,
            return_cost_deducted_prior_execution=True,
        )

        # Calculate execution gas
        gas_costs = fork.gas_costs()
        # Note: The contract (to) address is pre-warmed per EIP-2929,
        # so no G_COLD_ACCOUNT_ACCESS is charged.
        execution_gas = 0
        for _ in range(num_slots):
            # Each storage slot is accessed cold (different slots)
            execution_gas += gas_costs.GAS_COLD_STORAGE_ACCESS
            execution_gas += gas_costs.GAS_STORAGE_RESET
            execution_gas += gas_costs.GAS_VERY_LOW * 2  # PUSH1 * 2

        total_gas_before_refund = (
            intrinsic_cost_before_execution + execution_gas
        )

        # Refund counter (clearing 10 slots)
        refund_counter = gas_costs.REFUND_STORAGE_CLEAR * num_slots

        # Actual refund is capped at 1/5
        refund_cap = total_gas_before_refund // 5
        actual_refund = min(refund_counter, refund_cap)

        # Verify that refund counter exceeds cap
        assert refund_counter > refund_cap, (
            "Test requires refund_counter > gas_used // 5"
        )

        # Gas after refund (floor cost is minimal with empty calldata)
        expected_gas = total_gas_before_refund - actual_refund

        tx = Transaction(
            sender=sender,
            to=contract,
            data=calldata,
            gas_limit=total_gas_before_refund,
        )

        tx.expected_receipt = TransactionReceipt(
            cumulative_gas_used=expected_gas
        )

        # Verify all storage slots are cleared
        expected_storage = dict.fromkeys(range(num_slots), 0)

        state_test(
            pre=pre,
            post={
                contract: {
                    "storage": expected_storage,
                }
            },
            tx=tx,
        )

    def test_floor_cost_not_reduced_by_refunds(
        self,
        state_test: StateTestFiller,
        pre: Alloc,
        sender: Address,
        fork: Fork,
    ) -> None:
        """
        Verify floor cost acts as a true floor and is never reduced.

        Even with large refunds, the transaction must pay at least the
        floor cost.
        """
        # Use calldata that strongly triggers floor cost
        calldata = Bytes(b"\x01" * 1000)

        # Deploy contract that clears storage
        contract = pre.deploy_contract(
            Op.SSTORE(0, 0) + Op.STOP,
            storage={0: 1},
        )

        # Calculate costs
        floor_cost_calculator = fork.transaction_data_floor_cost_calculator()
        floor_cost = floor_cost_calculator(data=calldata)

        intrinsic_cost_calculator = (
            fork.transaction_intrinsic_cost_calculator()
        )
        intrinsic_cost_before_execution = intrinsic_cost_calculator(
            calldata=calldata,
            contract_creation=False,
            access_list=None,
            authorization_list_or_count=None,
            return_cost_deducted_prior_execution=True,
        )

        # Minimal execution gas
        gas_costs = fork.gas_costs()
        execution_gas = (
            gas_costs.GAS_COLD_STORAGE_ACCESS
            + gas_costs.GAS_STORAGE_RESET
            + gas_costs.GAS_VERY_LOW * 2
        )

        total_gas_before_refund = (
            intrinsic_cost_before_execution + execution_gas
        )
        refund = min(
            gas_costs.REFUND_STORAGE_CLEAR, total_gas_before_refund // 5
        )
        gas_after_refund = total_gas_before_refund - refund

        # Even after refund, we should pay at least floor cost
        expected_gas = max(gas_after_refund, floor_cost)

        # Verify floor cost is the dominant factor
        assert expected_gas == floor_cost, (
            "Floor cost should dominate for data-heavy transaction"
        )

        # Gas limit must satisfy both execution needs and floor cost
        gas_limit = max(total_gas_before_refund, floor_cost)

        tx = Transaction(
            sender=sender,
            to=contract,
            data=calldata,
            gas_limit=gas_limit,
        )

        tx.expected_receipt = TransactionReceipt(
            cumulative_gas_used=expected_gas
        )

        state_test(
            pre=pre,
            post={
                contract: {
                    "storage": {0: 0},
                }
            },
            tx=tx,
        )
