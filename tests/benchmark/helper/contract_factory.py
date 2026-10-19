"""Custom-sized contract initcode and CREATE2 deployment factory."""

from typing import Dict, Generator, List, Self

from execution_testing import (
    EOA,
    Address,
    Alloc,
    Bytecode,
    FixedIterationsBytecode,
    Fork,
    Hash,
    Initcode,
    IteratingBytecode,
    Op,
    TransactionWithCost,
    While,
    compute_create2_address,
    compute_deterministic_create2_address,
)
from pydantic import Field

XOR_TABLE_SIZE = 256
XOR_TABLE = [Hash(i).sha256() for i in range(XOR_TABLE_SIZE)]


class CustomSizedContractInitcode(FixedIterationsBytecode):
    """
    Initcode that deploys a random contract with a custom size.

    If no contract size is provided, the maximum contract size for the given
    fork is used.
    """

    _cached_address: Address
    """Cached address to avoid expensive recomputation."""
    contract_size: int
    """The size of the contract to deploy."""

    def __new__(
        cls, *, pre: Alloc, fork: Fork, contract_size: int | None = None
    ) -> Self:
        """
        Create a new CustomSizedContractInitcode instance.

        Args:
            pre: The pre-allocation state where the contract will be
                deployed.
            fork: The fork to use for determining maximum contract size
                limits.
            contract_size: The size of the contract to deploy. If None,
                the maximum contract size for the fork is used.

        Returns:
            A new CustomSizedContractInitcode instance.

        """
        if contract_size is None:
            contract_size = fork.max_code_size()
        xor_table_byte_size = XOR_TABLE_SIZE * 32
        setup = Op.MSTORE(
            0,
            Op.ADDRESS,
            # Gas accounting
            old_memory_size=0,
            new_memory_size=32,
        )
        iterating: While | Bytecode
        if contract_size > 32:
            iteration_count = ((contract_size - 32) // xor_table_byte_size) + 1
            iterating = While(
                body=(
                    Op.SHA3(Op.SUB(Op.MSIZE, 32), 32, data_size=32)
                    # Use a xor table to avoid having to call the "expensive"
                    # sha3 opcode as much
                    + sum(
                        (
                            Op.PUSH32[xor_value]
                            + Op.XOR
                            + Op.DUP1
                            + Op.MSIZE
                            + Op.MSTORE
                        )
                        for xor_value in XOR_TABLE
                    )
                    + Op.POP
                ),
                condition=Op.LT(Op.MSIZE, contract_size),
            )
            final_memory_size = (xor_table_byte_size * iteration_count) + 32
        else:
            iteration_count = 0
            iterating = Bytecode()
            final_memory_size = 32
        cleanup = (
            # Despite the whole contract has random bytecode, we need the first
            # opcode be a STOP so CALL-like attacks return as soon as possible.
            # However, since the memory starts with address, the first 12 bytes
            # are always zero, so no need to do anything but return.
            Op.RETURN(
                0,
                contract_size,
                # Gas accounting
                code_deposit_size=contract_size,
                # Memory is not expanded here, but it is expanded in the loop.
                old_memory_size=32,
                new_memory_size=final_memory_size,
            )
        )
        instance = super(CustomSizedContractInitcode, cls).__new__(
            cls,
            setup=setup,
            iterating=iterating,
            cleanup=cleanup,
            iteration_count=iteration_count,
        )
        # Cache the address to avoid expensive recomputation
        instance._cached_address = compute_deterministic_create2_address(
            salt=0,
            initcode=Initcode(deploy_code=instance),
            fork=fork,
        )
        instance.contract_size = contract_size
        deployed_address = pre.deterministic_deploy_contract(
            deploy_code=instance
        )
        assert deployed_address == instance._cached_address
        return instance

    def address(self) -> Address:
        """Get the deterministic address of the initcode."""
        return self._cached_address


class ContractDeploymentTransaction(TransactionWithCost):
    """Transaction object that can include the expected gas to be consumed."""

    deployed_contracts: List[Address] = Field(..., exclude=True)


class CustomSizedContractFactory(IteratingBytecode):
    """
    Factory contract that creates contracts with a custom size.

    The contract takes two 32-byte arguments in the calldata:
    - start_index: the starting index of the contract to deploy
    - end_index: the ending index of the contract to deploy

    The contract will deploy a contract for each index in the range, inclusive.

    If no contract size is provided, the maximum contract size for the given
    fork is used.
    """

    initcode: CustomSizedContractInitcode
    """The initcode used to deploy contracts via CREATE2."""

    _cached_address: Address
    """Cached address to avoid expensive recomputation."""
    _cached_created_contracts: Dict[int, Address]
    """Cached created contract addresses to avoid expensive recomputation."""
    contract_size: int
    """The size of the contracts to deploy."""

    def __new__(
        cls, *, pre: Alloc, fork: Fork, contract_size: int | None = None
    ) -> Self:
        """
        Create a new CustomSizedContractFactory instance.

        Args:
            pre: The pre-allocation state where the factory will be
                deployed.
            fork: The fork to use for gas calculations and contract
                size limits.
            contract_size: The size of the contracts to deploy. If None,
                the maximum contract size for the fork is used.

        Returns:
            A new CustomSizedContractFactory instance.

        """
        initcode = CustomSizedContractInitcode(
            pre=pre, fork=fork, contract_size=contract_size
        )
        initcode_address = initcode.address()
        setup = (
            Op.EXTCODECOPY(
                address=initcode_address,
                dest_offset=0,
                offset=0,
                size=len(initcode),
                # Gas accounting
                address_warm=False,
                data_size=len(initcode),
                new_memory_size=len(initcode),
            )
            # CALLDATA[0:32] = start_index
            # CALLDATA[32:64] = end_index
            + Op.ADD(1, Op.CALLDATALOAD(32))
            + Op.CALLDATALOAD(0)
        )
        iterating = While(
            body=Op.POP(
                Op.CREATE2(
                    value=0,
                    offset=0,
                    size=len(initcode),
                    salt=Op.DUP1,
                    # Gas accounting
                    init_code_size=len(initcode),
                )
            ),
            condition=Op.PUSH1(1) + Op.ADD + Op.DUP1 + Op.DUP3 + Op.GT,
        )
        cleanup = Op.STOP
        instance = super(CustomSizedContractFactory, cls).__new__(
            cls,
            setup=setup,
            iterating=iterating,
            iterating_subcall=initcode,
            cleanup=cleanup,
        )
        instance.initcode = initcode
        # Cache the address to avoid expensive recomputation
        instance._cached_address = compute_deterministic_create2_address(
            salt=0,
            initcode=Initcode(deploy_code=instance),
            fork=fork,
        )
        instance._cached_created_contracts = {}
        instance.contract_size = initcode.contract_size
        deployed_address = pre.deterministic_deploy_contract(
            deploy_code=instance
        )
        assert deployed_address == instance._cached_address
        return instance

    def transactions_by_total_contract_count(
        self,
        *,
        fork: Fork,
        sender: EOA,
        contract_count: int,
        contract_start_index: int = 0,
    ) -> Generator[ContractDeploymentTransaction, None, None]:
        """
        Create a list of transactions calling the factory to create the
        given number of contracts, each transaction capped by the fork's
        execution-gas limit cap (EIP-7825). Under EIP-8037 the per-byte code
        deposit is state gas drawn from a separate reservoir, so the split
        bounds execution gas only and lets the combined gas exceed the cap.
        """
        to = self.address()

        # Use a sensible hardcoded maximum for the calldata, to avoid
        # binary searching.
        max_number = (2 ** (contract_count.bit_length() + 1)) - 1
        calldata_max = Hash(max_number) + Hash(max_number)

        def calldata(iteration_count: int, start_iteration: int) -> bytes:
            index_end = iteration_count + start_iteration - 1
            return Hash(start_iteration) + Hash(index_end)

        start_iteration: int = contract_start_index

        tx_gas_limit: int | None = None
        tx_execution_cost: int | None = None
        tx_state_cost: int | None = None
        last_iteration_count: int = 0

        for iteration_count in self.tx_iterations_by_total_iteration_count(
            fork=fork,
            total_iterations=contract_count,
            start_iteration=start_iteration,
            calldata=calldata_max,
        ):
            if (
                tx_gas_limit is None
                or tx_execution_cost is None
                or tx_state_cost is None
                or iteration_count != last_iteration_count
            ):
                tx_gas_limit = self.tx_gas_limit_by_iteration_count(
                    fork=fork,
                    iteration_count=iteration_count,
                    start_iteration=start_iteration,
                    include_state_gas_reservoir=True,
                    calldata=calldata_max,
                )
                tx_execution_cost = (
                    self.tx_execution_gas_cost_by_iteration_count(
                        fork=fork,
                        iteration_count=iteration_count,
                        start_iteration=start_iteration,
                        calldata=calldata_max,
                    )
                )
                tx_state_cost = self.state_gas_cost_by_iteration_count(
                    fork=fork,
                    iteration_count=iteration_count,
                )
            deployed_contracts = [
                self.created_contract_address(
                    salt=i,
                )
                for i in range(
                    start_iteration, start_iteration + iteration_count
                )
            ]
            yield ContractDeploymentTransaction(
                to=to,
                gas_limit=tx_gas_limit,
                sender=sender,
                execution_cost=tx_execution_cost,
                state_cost=tx_state_cost,
                data=calldata(iteration_count, start_iteration),
                deployed_contracts=deployed_contracts,
            )
            start_iteration += iteration_count
            last_iteration_count = iteration_count

    def address(self) -> Address:
        """Get the deterministic address of the factory contract."""
        return self._cached_address

    def created_contract_address(self, *, salt: int) -> Address:
        """Get the deterministic address of the created contract."""
        if salt not in self._cached_created_contracts:
            self._cached_created_contracts[salt] = compute_create2_address(
                address=self.address(),
                salt=salt,
                initcode=self.initcode,
            )
        return self._cached_created_contracts[salt]
