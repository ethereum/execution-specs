"""Code generating classes and functions."""

from dataclasses import dataclass
from typing import Any, List, Self, SupportsBytes, Tuple, Type

from execution_testing.base_types import Bytes
from execution_testing.forks import Fork
from execution_testing.test_types import ceiling_division
from execution_testing.vm import Bytecode, ForkOpcodeInterface, Op

GAS_PER_DEPLOYED_CODE_BYTE = 0xC8


class Initcode(Bytecode):
    """
    Helper class used to generate initcode for the specified deployment code.

    The execution gas cost of the initcode is calculated, and also the
    deployment gas costs for the deployed code.

    The initcode can be padded to a certain length if necessary, which does not
    affect the deployed code.

    Other costs such as the CREATE2 hashing costs or the initcode_word_cost of
    EIP-3860 are *not* taken into account by any of these calculated costs.
    """

    deploy_code: SupportsBytes | Bytes
    """
    Bytecode to be deployed by the initcode.
    """
    execution_gas: int
    """
    Gas cost of executing the initcode, without considering deployment gas
    costs.
    """
    deployment_gas: int
    """
    Gas cost of deploying the cost, subtracted after initcode execution,
    """

    def __new__(
        cls,
        *,
        deploy_code: SupportsBytes | Bytes | None = None,
        initcode_length: int | None = None,
        initcode_prefix: Bytecode | None = None,
        initcode_prefix_execution_gas: int = 0,
        padding_byte: int = 0x00,
        name: str = "",
    ) -> Self:
        """
        Generate legacy initcode that inits a contract with the specified code.
        The initcode can be padded to a specified length for testing purposes.
        """
        if deploy_code is None:
            deploy_code = Bytecode()
        if initcode_prefix is None:
            initcode_prefix = Bytecode()

        initcode = initcode_prefix
        code_length = len(bytes(deploy_code))
        execution_gas = initcode_prefix_execution_gas

        # PUSH2: length=<bytecode length>
        initcode += Op.PUSH2(code_length)
        execution_gas = 3

        # PUSH1: offset=0
        initcode += Op.PUSH1(0)
        execution_gas += 3

        # DUP2
        initcode += Op.DUP2
        execution_gas += 3

        # PUSH1: initcode_length=11 + len(initcode_prefix_bytes) (constant)
        no_prefix_length = 0x0B
        assert no_prefix_length + len(initcode_prefix) <= 0xFF, (
            "initcode prefix too long"
        )
        initcode += Op.PUSH1(no_prefix_length + len(initcode_prefix))
        execution_gas += 3

        # DUP3
        initcode += Op.DUP3
        execution_gas += 3

        # CODECOPY: destinationOffset=0, offset=0, length
        initcode += Op.CODECOPY
        execution_gas += (
            3
            + (3 * ceiling_division(code_length, 32))
            + (3 * code_length)
            + ((code_length * code_length) // 512)
        )

        # RETURN: offset=0, length
        initcode += Op.RETURN
        execution_gas += 0

        initcode_plus_deploy_code = bytes(initcode) + bytes(deploy_code)
        padding_bytes = bytes()

        if initcode_length is not None:
            assert initcode_length >= len(initcode_plus_deploy_code), (
                "specified invalid length for initcode"
            )

            padding_bytes = bytes(
                [padding_byte]
                * (initcode_length - len(initcode_plus_deploy_code))
            )

        initcode_bytes = initcode_plus_deploy_code + padding_bytes
        instance = super().__new__(
            cls,
            initcode_bytes,
            popped_stack_items=initcode.popped_stack_items,
            pushed_stack_items=initcode.pushed_stack_items,
            max_stack_height=initcode.max_stack_height,
            min_stack_height=initcode.min_stack_height,
        )
        instance._name_ = name
        instance.deploy_code = deploy_code
        instance.execution_gas = execution_gas
        instance.deployment_gas = GAS_PER_DEPLOYED_CODE_BYTE * len(
            bytes(instance.deploy_code)
        )

        return instance


class CodeGasMeasure(Bytecode):
    """
    Helper class used to generate bytecode that measures gas usage of a
    bytecode, taking into account and subtracting any extra overhead gas costs
    required to execute. By default, the result gas calculation is saved to
    storage key 0.
    """

    code: Bytecode
    """
    Bytecode to be executed to measure the gas usage.
    """
    overhead_cost: int
    """
    Extra gas cost to be subtracted from extra operations.
    """
    extra_stack_items: int
    """
    Extra stack items that remain at the end of the execution.
    To be considered when subtracting the value of the previous GAS operation,
    and to be popped at the end of the execution.
    """
    sstore_key: int | Bytes
    """
    Storage key to save the gas used.
    """

    def __new__(
        cls,
        *,
        code: Bytecode,
        overhead_cost: int = 0,
        extra_stack_items: int = 0,
        sstore_key: int | Bytes = 0,
        stop: bool = True,
    ) -> Self:
        """Assemble the bytecode that measures gas usage."""
        res = Op.GAS + code + Op.GAS
        # We need to swap and pop for each extra stack item that remained from
        # the execution of the code
        res += (Op.SWAP1 + Op.POP) * extra_stack_items
        res += (
            Op.SWAP1
            + Op.SUB
            + Op.PUSH1(overhead_cost + 2)
            + Op.SWAP1
            + Op.SSTORE(sstore_key, Op.SUB)
        )
        if stop:
            res += Op.STOP

        instance = super().__new__(cls, res)
        instance.code = code
        instance.overhead_cost = overhead_cost
        instance.extra_stack_items = extra_stack_items
        instance.sstore_key = sstore_key
        return instance


class Conditional(Bytecode):
    """Helper class used to generate conditional bytecode."""

    def __new__(
        cls,
        *,
        condition: Bytecode | Op,
        if_true: Bytecode | Op | None = None,
        if_false: Bytecode | Op | None = None,
    ) -> Self:
        """
        Assemble the conditional bytecode by generating the necessary jump and
        jumpdest opcodes surrounding the condition and the two possible
        execution paths.

        In the future, PC usage should be replaced by using RJUMP and RJUMPI
        """
        if if_true is None:
            if_true = Bytecode()
        if if_false is None:
            if_false = Bytecode()

        # First we append a jumpdest to the start of the true branch
        if_true = Op.JUMPDEST + if_true

        # Then we append the unconditional jump to the end of the false
        # branch, used to skip the true branch
        if_false += Op.JUMP(Op.ADD(Op.PC, len(if_true) + 3))

        # Then we need to do the conditional jump by skipping the false
        # branch
        condition = Op.JUMPI(Op.ADD(Op.PC, len(if_false) + 3), condition)

        # Finally we append the condition, false and true branches, plus
        # the jumpdest at the very end
        bytecode = condition + if_false + if_true + Op.JUMPDEST

        return super().__new__(cls, bytecode)


class While(Bytecode):
    """Helper class used to generate while-loop bytecode."""

    def __new__(
        cls,
        *,
        body: Bytecode | Op,
        condition: Bytecode | Op | None = None,
    ) -> Self:
        """
        Assemble the loop bytecode.

        The condition nor the body can leave a stack item on the stack.
        """
        bytecode = Bytecode()
        bytecode += Op.JUMPDEST
        bytecode += body
        if condition is not None:
            bytecode += Op.JUMPI(
                Op.SUB(Op.PC, Op.PUSH4[len(body) + len(condition) + 6]),
                condition,
            )
        else:
            bytecode += Op.JUMP(Op.SUB(Op.PC, Op.PUSH4[len(body) + 6]))
        return super().__new__(cls, bytecode)


@dataclass(kw_only=True, slots=True)
class Case:
    """
    Small helper class to represent a single, generic case in a `Switch` cases
    list.
    """

    condition: Bytecode | Op
    action: Bytecode | Op
    terminating: bool | None = None

    @property
    def is_terminating(self) -> bool:
        """Returns whether the case is terminating."""
        return (
            self.terminating
            if self.terminating is not None
            else self.action.terminating
        )


class CalldataCase(Case):
    """
    Small helper class to represent a single case whose condition depends on
    the value of the contract's calldata in a Switch case statement.

    By default the calldata is read from position zero, but this can be
    overridden using `position`.

    The `condition` is generated automatically based on the `value` (and
    optionally `position`) and may not be set directly.
    """

    def __init__(
        self, value: int | str | Bytecode, position: int = 0, **kwargs: Any
    ) -> None:
        """Generate the condition base on `value` and `position`."""
        condition = Op.EQ(Op.CALLDATALOAD(position), value)
        super().__init__(condition=condition, **kwargs)


class Switch(Bytecode):
    """
    Helper class used to generate switch-case expressions in EVM bytecode.

    Switch-case behavior:
      - If no condition is met in the list of BytecodeCases
        conditions, the `default_action` bytecode is executed.

      - If multiple conditions are met, the action from the first valid
        condition is the only one executed.

      - There is no fall through; it is not possible to execute
        multiple actions.
    """

    default_action: Bytecode | Op | None
    """
    The default bytecode to execute; if no condition is met, this bytecode is
    executed.
    """

    cases: List[Case]
    """
    A list of Cases: The first element with a condition that
    evaluates to a non-zero value is the one that is executed.
    """

    def __new__(
        cls,
        *,
        default_action: Bytecode | Op | None = None,
        cases: List[Case],
    ) -> Self:
        """
        Assemble the bytecode by looping over the list of cases and adding the
        necessary [R]JUMPI and JUMPDEST opcodes in order to replicate
        switch-case behavior.
        """
        # The length required to jump over subsequent actions to the final
        # JUMPDEST at the end of the switch-case block:
        #   - add 6 per case for the length of the JUMPDEST and
        #     JUMP(ADD(PC, action_jump_length)) bytecode
        #
        #   - add 3 to the total to account for this action's JUMP;
        #     the PC within the call requires a "correction" of 3.

        bytecode = Bytecode()

        # All conditions get prepended to this bytecode; if none are met, we
        # reach the default
        action_jump_length = sum(len(case.action) + 6 for case in cases) + 3
        bytecode = default_action + Op.JUMP(Op.ADD(Op.PC, action_jump_length))
        # The length required to jump over the default action and its JUMP
        # bytecode
        condition_jump_length = len(bytecode) + 3

        # Reversed: first case in the list has priority; it will become the
        # outer-most onion layer. We build up layers around the default_action,
        # after 1 iteration of the loop, a simplified representation of the
        # bytecode is:
        #
        # JUMPI(case[n-1].condition)
        # + default_action + JUMP()
        # + JUMPDEST + case[n-1].action + JUMP()
        #
        # and after n=len(cases) iterations:
        #
        # JUMPI(case[0].condition)
        # + JUMPI(case[1].condition)
        # ...
        # + JUMPI(case[n-1].condition) + default_action + JUMP() + JUMPDEST +
        # case[n-1].action + JUMP() + ... + JUMPDEST + case[1].action + JUMP()
        # + JUMPDEST + case[0].action + JUMP()
        for case in reversed(cases):
            action = case.action
            action_jump_length -= len(action) + 6
            action = (
                Op.JUMPDEST
                + action
                + Op.JUMP(Op.ADD(Op.PC, action_jump_length))
            )
            condition = Op.JUMPI(
                Op.ADD(Op.PC, condition_jump_length), case.condition
            )
            # wrap the current case around the onion as its next layer
            bytecode = condition + bytecode + action
            condition_jump_length += len(condition) + len(action)

        bytecode += Op.JUMPDEST

        instance = super().__new__(cls, bytecode)
        instance.default_action = default_action
        instance.cases = cases
        return instance


class Create2PreimageLayout(Bytecode):
    """
    Set up the preimage in memory for CREATE2 address computation.

    Creates the standard memory layout required to compute a CREATE2 address
    using keccak256(0xFF ++ factory_address ++ salt ++ init_code_hash).

    Memory layout after execution:
    - MEM[offset + 0: offset + 32] = zero padding + factory_address (20 bytes)
    - MEM[offset + 11] = 0xFF prefix byte
    - MEM[offset + 32: offset + 64] = salt (32 bytes)
    - MEM[offset + 64: offset + 96] = init_code_hash (32 bytes)

    To compute the CREATE2 address, use: `.address_op` or
    `Op.SHA3(offset + 11, 85)`.
    The resulting hash's lower 20 bytes (bytes 12-31) form the address.
    """

    offset: int = 0

    def __new__(
        cls,
        *,
        factory_address: int | bytes | Bytecode,
        salt: int | bytes | Bytecode,
        init_code_hash: int | bytes | Bytecode,
        offset: int = 0,
        old_memory_size: int = 0,
    ) -> Self:
        """
        Assemble the bytecode that sets up the memory layout for CREATE2
        address computation.
        """
        required_size = offset + 96
        new_memory_size = max(old_memory_size, required_size)
        bytecode = (
            Op.MSTORE(offset=offset, value=factory_address)
            + Op.MSTORE8(offset=offset + 11, value=0xFF)
            + Op.MSTORE(offset=offset + 32, value=salt)
            + Op.MSTORE(
                offset=offset + 64,
                value=init_code_hash,
                # Gas accounting
                old_memory_size=old_memory_size,
                new_memory_size=new_memory_size,
            )
        )
        instance = super().__new__(cls, bytecode)
        instance.offset = offset
        return instance

    @property
    def salt_offset(self) -> int:
        """
        Return the salt memory offset of the preimage.
        """
        return self.offset + 32

    def address_op(self) -> Bytecode:
        """
        Return the bytecode that computes the CREATE2 address.
        """
        return Op.SHA3(
            offset=self.offset + 11,
            size=85,
            # Gas accounting
            data_size=85,
        )

    def increment_salt_op(self, increment: int = 1) -> Bytecode:
        """Return the bytecode that increments the current salt."""
        return Op.MSTORE(
            self.salt_offset,
            Op.ADD(Op.MLOAD(self.salt_offset), increment),
        )


class IteratingBytecode(Bytecode):
    """
    Bytecode composed of distinct execution phases: setup, iteration, and
    cleanup.

    Some phases (warm_iterating and iterating_subcall) are analytical only and
    exist solely to model gas costs; they are not emitted in the final
    bytecode.
    """

    setup: Bytecode
    """Bytecode executed once at the beginning before iterations start."""
    iterating: Bytecode
    """Bytecode executed in the first iteration."""
    warm_iterating: Bytecode
    """
    Analytical bytecode representing subsequent iterations after the first
    (warm state).
    This bytecode is _not_ included in the final bytecode, and it's only
    used for the gas accounting properties of its opcodes and therefore gas
    calculation.
    """
    iterating_subcall: Bytecode | int
    """
    Analytical bytecode representing a subcall performed during each iteration.
    This bytecode is _not_ included in the final bytecode, and it's only
    used for gas calculation.

    The value can also be an integer, in which case it represents the gas cost
    of the subcall (e.g. the subcall is a precompiled contract)
    """
    cleanup: Bytecode
    """Bytecode executed once at the end after all iterations complete."""

    def __new__(
        cls,
        *,
        setup: Bytecode | None = None,
        iterating: Bytecode,
        cleanup: Bytecode | None = None,
        warm_iterating: Bytecode | None = None,
        iterating_subcall: Bytecode | int | None = None,
    ) -> Self:
        """
        Create a new iterating bytecode.

        Args:
            setup: Bytecode executed once at the beginning before
                iterations start.
            iterating: Bytecode executed in the first iteration.
            cleanup: Bytecode executed once at the end after all
                iterations complete.
            warm_iterating: Analytical bytecode representing subsequent
                iterations after the first (warm state).
            iterating_subcall: Analytical bytecode representing a subcall
                performed during each iteration. This bytecode is _not_
                included in the final bytecode, and it's only used for gas
                calculation. The value can also be an integer, in which case it
                represents the gas cost of the subcall (e.g. the subcall is a
                precompiled contract).

        Returns:
            A new IteratingBytecode instance.

        """
        instance = super(IteratingBytecode, cls).__new__(
            cls,
            setup + iterating + cleanup,
        )
        if setup is None:
            setup = Bytecode()
        instance.setup = setup
        instance.iterating = iterating
        if warm_iterating is None:
            instance.warm_iterating = iterating
        else:
            assert bytes(iterating) == bytes(warm_iterating), (
                "iterating and warm_iterating must have the same bytecode"
            )
            instance.warm_iterating = warm_iterating
        if iterating_subcall is None:
            instance.iterating_subcall = Bytecode()
        else:
            instance.iterating_subcall = iterating_subcall
        if cleanup is None:
            cleanup = Bytecode()
        instance.cleanup = cleanup
        return instance

    def iterating_subcall_gas_cost(
        self, *, fork: Type[ForkOpcodeInterface]
    ) -> int:
        """Return the gas cost of the iterating subcall."""
        if isinstance(self.iterating_subcall, int):
            return self.iterating_subcall
        return self.iterating_subcall.gas_cost(fork=fork)

    def iterating_subcall_reserve(
        self, *, fork: Type[ForkOpcodeInterface]
    ) -> int:
        """
        Return the gas reserve needed so that the last iterating subcall does
        not fail due to the 63/64 rule.
        """
        iterating_subcall_gas_cost = self.iterating_subcall_gas_cost(fork=fork)
        return (
            iterating_subcall_gas_cost * 64 // 63
        ) - iterating_subcall_gas_cost

    def gas_cost_by_iteration_count(
        self, *, fork: Type[ForkOpcodeInterface], iteration_count: int
    ) -> int:
        """Return the cost of iterating through the bytecode N times."""
        loop_gas_cost = 0
        if iteration_count > 0:
            # Cold cost is just charged for the first iteration
            loop_gas_cost = self.iterating.gas_cost(fork=fork)
            # Warm cost is charged for all iterations except the first
            loop_gas_cost += self.warm_iterating.gas_cost(fork=fork) * (
                iteration_count - 1
            )
            # Subcall cost is charged for all iterations.
            loop_gas_cost += (
                self.iterating_subcall_gas_cost(fork=fork) * iteration_count
            )
        return (
            self.setup.gas_cost(fork=fork)
            + loop_gas_cost
            + self.cleanup.gas_cost(fork=fork)
        )

    def with_fixed_iteration_count(
        self, *, iteration_count: int
    ) -> "FixedIterationsBytecode":
        """
        Return a new FixedIterationsBytecode with the iteration count fixed.
        """
        return FixedIterationsBytecode(
            setup=self.setup,
            iterating=self.iterating,
            cleanup=self.cleanup,
            warm_iterating=self.warm_iterating,
            iterating_subcall=self.iterating_subcall,
            iteration_count=iteration_count,
        )

    # Methods to calculate transactions that call a contract containing the
    # iterating bytecode.

    def tx_gas_cost_by_iteration_count(
        self,
        *,
        fork: Fork,
        iteration_count: int,
        **intrinsic_cost_kwargs: Any,
    ) -> int:
        """
        Calculate the exact gas cost of a transaction calling the bytecode
        for a given number of iterations.
        """
        intrinsic_gas_cost_calc = fork.transaction_intrinsic_cost_calculator()
        # Required extra gas for the last iteration due to the 63/64 rule.
        return self.gas_cost_by_iteration_count(
            fork=fork, iteration_count=iteration_count
        ) + intrinsic_gas_cost_calc(**intrinsic_cost_kwargs)

    def tx_gas_limit_by_iteration_count(
        self,
        *,
        fork: Fork,
        iteration_count: int,
        **intrinsic_cost_kwargs: Any,
    ) -> int:
        """
        Calculate the minimum gas limit of a transaction calling the bytecode
        for a given number of iterations.

        The gas limit is calculated by adding the required extra gas for the
        last iteration due to the 63/64 rule.
        """
        return self.tx_gas_cost_by_iteration_count(
            fork=fork,
            iteration_count=iteration_count,
            **intrinsic_cost_kwargs,
        ) + self.iterating_subcall_reserve(fork=fork)

    def tx_iterations_by_gas_limit_cap(
        self,
        *,
        fork: Fork,
        **intrinsic_cost_kwargs: Any,
    ) -> Tuple[int, int]:
        """
        Calculate the number of iterations needed to reach the fork's
        transaction gas limit cap.
        """
        gas_limit_cap = fork.transaction_gas_limit_cap()
        if gas_limit_cap is None:
            raise ValueError("Fork has no gas limit cap.")

        # Estimate maximum possible iterations
        low = 0
        high = 1
        high_gas_cost = self.tx_gas_limit_by_iteration_count(
            fork=fork,
            iteration_count=high,
            **intrinsic_cost_kwargs,
        )
        while high_gas_cost < gas_limit_cap:
            low = high
            high *= 2
            high_gas_cost = self.tx_gas_limit_by_iteration_count(
                fork=fork,
                iteration_count=high,
                **intrinsic_cost_kwargs,
            )

        # Binary search for the maximum number of iterations that fits
        # within both remaining_gas and gas_limit_cap
        best_iterations = 0
        best_iterations_gas = 0

        while low <= high:
            mid = (low + high) // 2
            if mid == 0:
                break

            tx_gas = self.tx_gas_limit_by_iteration_count(
                fork=fork,
                iteration_count=mid,
                **intrinsic_cost_kwargs,
            )

            if tx_gas <= gas_limit_cap:
                best_iterations = mid
                best_iterations_gas = tx_gas
                low = mid + 1
            else:
                high = mid - 1

        return best_iterations, best_iterations_gas

    def tx_iterations_by_gas_limit(
        self,
        *,
        fork: Fork,
        gas_limit: int,
        **intrinsic_cost_kwargs: Any,
    ) -> List[int]:
        """
        Calculate the number of iterations needed to reach the given a
        gas-to-be-used value.

        If the fork's transaction gas limit cap is not `None`, the returned
        list will contain one item per transaction that represents the
        iteration count for that transaction, and no transaction will exceed
        the gas limit cap.
        """
        gas_limit_cap = fork.transaction_gas_limit_cap()
        result: List[int] = []
        remaining_gas = gas_limit

        if gas_limit_cap is not None and remaining_gas > gas_limit_cap:
            max_iterations_per_tx, gas_used = (
                self.tx_iterations_by_gas_limit_cap(
                    fork=fork,
                    **intrinsic_cost_kwargs,
                )
            )
            if max_iterations_per_tx == 0:
                raise ValueError(
                    "No iterations possible with the given gas limit cap."
                )
            txs_with_max_iterations = remaining_gas // gas_used
            result.extend(
                max_iterations_per_tx for _ in range(txs_with_max_iterations)
            )
            remaining_gas -= gas_used * txs_with_max_iterations
        single_iteration_gas = self.tx_gas_limit_by_iteration_count(
            fork=fork,
            iteration_count=1,
            **intrinsic_cost_kwargs,
        )
        while remaining_gas >= single_iteration_gas:
            # Estimate maximum possible iterations
            low = 1
            high = 2
            high_gas_cost = self.tx_gas_limit_by_iteration_count(
                fork=fork,
                iteration_count=high,
                **intrinsic_cost_kwargs,
            )
            while high_gas_cost < remaining_gas:
                low = high
                high *= 2
                high_gas_cost = self.tx_gas_limit_by_iteration_count(
                    fork=fork,
                    iteration_count=high,
                    **intrinsic_cost_kwargs,
                )

            # Binary search for the maximum number of iterations that fits
            # within remaining_gas
            best_iterations = 0
            best_iterations_gas = 0
            while low <= high:
                mid = (low + high) // 2
                if mid == 0:
                    break

                tx_gas = self.tx_gas_limit_by_iteration_count(
                    fork=fork,
                    iteration_count=mid,
                    **intrinsic_cost_kwargs,
                )

                if tx_gas <= remaining_gas:
                    best_iterations = mid
                    best_iterations_gas = tx_gas
                    low = mid + 1
                else:
                    high = mid - 1

            if best_iterations == 0:
                # Can't fit any more iterations
                break

            result.append(best_iterations)
            remaining_gas -= best_iterations_gas

        return result

    def tx_iterations_by_total_iteration_count(
        self,
        *,
        fork: Fork,
        total_iterations: int,
        **intrinsic_cost_kwargs: Any,
    ) -> List[int]:
        """
        Calculate how to split a total number of iterations across multiple
        transactions so that each transaction fits within the gas limit cap.

        Returns a list where each element represents the number of iterations
        for that transaction, and the sum equals total_iterations.
        """
        gas_limit_cap = fork.transaction_gas_limit_cap()
        if gas_limit_cap is None:
            # No limit, all iterations fit in a single transaction.
            return [total_iterations]
        remaining_iterations = total_iterations

        max_iterations_per_tx, _ = self.tx_iterations_by_gas_limit_cap(
            fork=fork,
            **intrinsic_cost_kwargs,
        )

        if max_iterations_per_tx == 0:
            raise ValueError(
                "No iterations possible with the given gas limit cap."
            )

        full_txs = remaining_iterations // max_iterations_per_tx
        result = [max_iterations_per_tx] * full_txs
        remaining_iterations -= max_iterations_per_tx * full_txs
        return result + [remaining_iterations]


class FixedIterationsBytecode(IteratingBytecode):
    """
    Bytecode that contains a setup phase, an iterating phase, and a cleanup
    phase, with a fixed number of iterations.

    This type can be used in place of a normal Bytecode and will return the
    appropriate gas cost for the given number of iterations.
    """

    iteration_count: int
    """The fixed number of times the iterating bytecode will be executed."""

    def __new__(
        cls,
        *,
        setup: Bytecode,
        iterating: Bytecode,
        cleanup: Bytecode,
        iteration_count: int,
        warm_iterating: Bytecode | None = None,
        iterating_subcall: Bytecode | int | None = None,
    ) -> Self:
        """
        Create a new FixedIterationsBytecode instance.

        Args:
            setup: Bytecode executed once at the beginning before
                iterations start.
            iterating: Bytecode executed in the first iteration.
            cleanup: Bytecode executed once at the end after all
                iterations complete.
            iteration_count: The fixed number of times the iterating
                bytecode will be executed.
            warm_iterating: Bytecode executed in subsequent iterations
                after the first. If None, uses the same bytecode as
                iterating.
            iterating_subcall: Analytical bytecode representing a subcall
                performed during each iteration. This bytecode is _not_
                included in the final bytecode, and it's only used for gas
                calculation. The value can also be an integer, in which case it
                represents the gas cost of the subcall (e.g. the subcall is a
                precompiled contract).

        Returns:
            A new FixedIterationsBytecode instance.

        """
        instance = super(FixedIterationsBytecode, cls).__new__(
            cls,
            setup=setup,
            iterating=iterating,
            cleanup=cleanup,
            warm_iterating=warm_iterating,
            iterating_subcall=iterating_subcall,
        )
        instance.iteration_count = iteration_count
        return instance

    def gas_cost(
        self,
        fork: Type[ForkOpcodeInterface],
        *,
        block_number: int = 0,
        timestamp: int = 0,
    ) -> int:
        """Return the cost of iterating through the bytecode N times."""
        del block_number, timestamp
        return self.gas_cost_by_iteration_count(
            fork=fork,
            iteration_count=self.iteration_count,
        )
