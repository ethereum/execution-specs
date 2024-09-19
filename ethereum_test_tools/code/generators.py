"""
Code generating classes and functions.
"""

from dataclasses import dataclass
from typing import List, SupportsBytes

from ethereum_test_types import ceiling_division
from ethereum_test_vm import Bytecode, EVMCodeType
from ethereum_test_vm import Opcodes as Op

GAS_PER_DEPLOYED_CODE_BYTE = 0xC8


class Initcode(Bytecode):
    """
    Helper class used to generate initcode for the specified deployment code.

    The execution gas cost of the initcode is calculated, and also the
    deployment gas costs for the deployed code.

    The initcode can be padded to a certain length if necessary, which
    does not affect the deployed code.

    Other costs such as the CREATE2 hashing costs or the initcode_word_cost
    of EIP-3860 are *not* taken into account by any of these calculated
    costs.
    """

    deploy_code: SupportsBytes
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
        deploy_code: SupportsBytes = Bytecode(),
        initcode_length: int | None = None,
        initcode_prefix: Bytecode = Bytecode(),
        initcode_prefix_execution_gas: int = 0,
        padding_byte: int = 0x00,
        name: str = "",
    ):
        """
        Generate legacy initcode that inits a contract with the specified code.
        The initcode can be padded to a specified length for testing purposes.
        """
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
        assert no_prefix_length + len(initcode_prefix) <= 0xFF, "initcode prefix too long"
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
            assert initcode_length >= len(
                initcode_plus_deploy_code
            ), "specified invalid length for initcode"

            padding_bytes = bytes(
                [padding_byte] * (initcode_length - len(initcode_plus_deploy_code))
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
        instance.deployment_gas = GAS_PER_DEPLOYED_CODE_BYTE * len(bytes(instance.deploy_code))

        return instance


class CodeGasMeasure(Bytecode):
    """
    Helper class used to generate bytecode that measures gas usage of a
    bytecode, taking into account and subtracting any extra overhead gas costs
    required to execute.
    By default, the result gas calculation is saved to storage key 0.
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
    sstore_key: int
    """
    Storage key to save the gas used.
    """

    def __new__(
        cls,
        *,
        code: Bytecode,
        overhead_cost: int = 0,
        extra_stack_items: int = 0,
        sstore_key: int = 0,
        stop: bool = True,
    ):
        """
        Assemble the bytecode that measures gas usage.
        """
        res = Op.GAS + code + Op.GAS
        # We need to swap and pop for each extra stack item that remained from
        # the execution of the code
        res += (Op.SWAP1 + Op.POP) * extra_stack_items
        res += (
            Op.SWAP1
            + Op.SUB
            + Op.PUSH1(overhead_cost + 2)
            + Op.SWAP1
            + Op.SUB
            + Op.PUSH1(sstore_key)
            + Op.SSTORE
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
    """
    Helper class used to generate conditional bytecode.
    """

    def __new__(
        cls,
        *,
        condition: Bytecode | Op,
        if_true: Bytecode | Op = Bytecode(),
        if_false: Bytecode | Op = Bytecode(),
        evm_code_type: EVMCodeType = EVMCodeType.LEGACY,
    ):
        """
        Assemble the conditional bytecode by generating the necessary jump and
        jumpdest opcodes surrounding the condition and the two possible execution
        paths.

        In the future, PC usage should be replaced by using RJUMP and RJUMPI
        """
        if evm_code_type == EVMCodeType.LEGACY:
            # First we append a jumpdest to the start of the true branch
            if_true = Op.JUMPDEST + if_true

            # Then we append the unconditional jump to the end of the false branch, used to skip
            # the true branch
            if_false += Op.JUMP(Op.ADD(Op.PC, len(if_true) + 3))

            # Then we need to do the conditional jump by skipping the false branch
            condition = Op.JUMPI(Op.ADD(Op.PC, len(if_false) + 3), condition)

            # Finally we append the condition, false and true branches, plus the jumpdest at the
            # very end
            bytecode = condition + if_false + if_true + Op.JUMPDEST

        elif evm_code_type == EVMCodeType.EOF_V1:
            if not if_false.terminating:
                if_false += Op.RJUMP[len(if_true)]
            condition = Op.RJUMPI[len(if_false)](condition)

            # Finally we append the condition, false and true branches
            bytecode = condition + if_false + if_true

        return super().__new__(cls, bytecode)


@dataclass(kw_only=True)
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
        """
        Returns whether the case is terminating.
        """
        return self.terminating if self.terminating is not None else self.action.terminating


class CalldataCase(Case):
    """
    Small helper class to represent a single case whose condition depends
    on the value of the contract's calldata in a Switch case statement.

    By default the calldata is read from position zero, but this can be
    overridden using `position`.

    The `condition` is generated automatically based on the `value` (and
    optionally `position`) and may not be set directly.
    """

    def __init__(self, value: int | str | Bytecode, position: int = 0, **kwargs):
        """
        Generate the condition base on `value` and `position`.
        """
        condition = Op.EQ(Op.CALLDATALOAD(position), value)
        super().__init__(condition=condition, **kwargs)


class Switch(Bytecode):
    """
    Helper class used to generate switch-case expressions in EVM bytecode.

    Switch-case behavior:
        - If no condition is met in the list of BytecodeCases conditions,
            the `default_action` bytecode is executed.
        - If multiple conditions are met, the action from the first valid
            condition is the only one executed.
        - There is no fall through; it is not possible to execute multiple
            actions.
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

    evm_code_type: EVMCodeType
    """
    The EVM code type to use for the switch-case bytecode.
    """

    def __new__(
        cls,
        *,
        default_action: Bytecode | Op | None = None,
        cases: List[Case],
        evm_code_type: EVMCodeType = EVMCodeType.LEGACY,
    ):
        """
        Assemble the bytecode by looping over the list of cases and adding
        the necessary [R]JUMPI and JUMPDEST opcodes in order to replicate
        switch-case behavior.
        """
        # The length required to jump over subsequent actions to the final JUMPDEST at the end
        # of the switch-case block:
        # - add 6 per case for the length of the JUMPDEST and JUMP(ADD(PC, action_jump_length))
        #   bytecode
        # - add 3 to the total to account for this action's JUMP; the PC within the call
        #   requires a "correction" of 3.

        bytecode = Bytecode()

        # All conditions get pre-pended to this bytecode; if none are met, we reach the default
        if evm_code_type == EVMCodeType.LEGACY:
            action_jump_length = sum(len(case.action) + 6 for case in cases) + 3
            bytecode = default_action + Op.JUMP(Op.ADD(Op.PC, action_jump_length))
            # The length required to jump over the default action and its JUMP bytecode
            condition_jump_length = len(bytecode) + 3
        elif evm_code_type == EVMCodeType.EOF_V1:
            action_jump_length = sum(
                len(case.action) + (len(Op.RJUMP[0]) if not case.is_terminating else 0)
                for case in cases
                # On not terminating cases, we need to add 3 bytes for the RJUMP
            )
            bytecode = default_action + Op.RJUMP[action_jump_length]
            # The length required to jump over the default action and its JUMP bytecode
            condition_jump_length = len(bytecode)

        # Reversed: first case in the list has priority; it will become the outer-most onion layer.
        # We build up layers around the default_action, after 1 iteration of the loop, a simplified
        # representation of the bytecode is:
        #
        #  JUMPI(case[n-1].condition)
        #  + default_action + JUMP()
        #  + JUMPDEST + case[n-1].action + JUMP()
        #
        # and after n=len(cases) iterations:
        #
        #  JUMPI(case[0].condition)
        #  + JUMPI(case[1].condition)
        #    ...
        #  + JUMPI(case[n-1].condition)
        #  + default_action + JUMP()
        #  + JUMPDEST + case[n-1].action + JUMP()
        #  + ...
        #  + JUMPDEST + case[1].action + JUMP()
        #  + JUMPDEST + case[0].action + JUMP()
        #
        for case in reversed(cases):
            action = case.action
            if evm_code_type == EVMCodeType.LEGACY:
                action_jump_length -= len(action) + 6
                action = Op.JUMPDEST + action + Op.JUMP(Op.ADD(Op.PC, action_jump_length))
                condition = Op.JUMPI(Op.ADD(Op.PC, condition_jump_length), case.condition)
            elif evm_code_type == EVMCodeType.EOF_V1:
                action_jump_length -= len(action) + (
                    len(Op.RJUMP[0]) if not case.is_terminating else 0
                )
                if not case.is_terminating:
                    action += Op.RJUMP[action_jump_length]
                condition = Op.RJUMPI[condition_jump_length](case.condition)
            # wrap the current case around the onion as its next layer
            bytecode = condition + bytecode + action
            condition_jump_length += len(condition) + len(action)

        bytecode += Op.JUMPDEST

        instance = super().__new__(cls, bytecode)
        instance.default_action = default_action
        instance.cases = cases
        return instance
