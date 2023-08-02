"""
Code generating classes and functions.
"""

from dataclasses import dataclass
from typing import Optional, SupportsBytes

from ..common.conversions import to_bytes
from ..common.helpers import ceiling_division
from ..vm.opcode import Opcodes as Op
from .code import Code

GAS_PER_DEPLOYED_CODE_BYTE = 0xC8


class Initcode(Code):
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

    deploy_code: str | bytes | SupportsBytes
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

    def __init__(
        self,
        *,
        deploy_code: str | bytes | SupportsBytes,
        initcode_length: Optional[int] = None,
        padding_byte: int = 0x00,
        name: Optional[str] = None,
    ):
        """
        Generate legacy initcode that inits a contract with the specified code.
        The initcode can be padded to a specified length for testing purposes.
        """
        self.execution_gas = 0
        self.deploy_code = deploy_code
        deploy_code_bytes = to_bytes(self.deploy_code)
        code_length = len(deploy_code_bytes)

        initcode = bytearray()

        # PUSH2: length=<bytecode length>
        initcode.append(0x61)
        initcode += code_length.to_bytes(length=2, byteorder="big")
        self.execution_gas += 3

        # PUSH1: offset=0
        initcode.append(0x60)
        initcode.append(0x00)
        self.execution_gas += 3

        # DUP2
        initcode.append(0x81)
        self.execution_gas += 3

        # PUSH1: initcode_length=11 (constant)
        initcode.append(0x60)
        initcode.append(0x0B)
        self.execution_gas += 3

        # DUP3
        initcode.append(0x82)
        self.execution_gas += 3

        # CODECOPY: destinationOffset=0, offset=0, length
        initcode.append(0x39)
        self.execution_gas += (
            3
            + (3 * ceiling_division(code_length, 32))
            + (3 * code_length)
            + ((code_length * code_length) // 512)
        )

        # RETURN: offset=0, length
        initcode.append(0xF3)
        self.execution_gas += 0

        pre_padding_bytes = bytes(initcode) + deploy_code_bytes

        if initcode_length is not None:
            if len(pre_padding_bytes) > initcode_length:
                raise Exception("Invalid specified length for initcode")

            padding_bytes = bytes([padding_byte] * (initcode_length - len(pre_padding_bytes)))
        else:
            padding_bytes = bytes()

        self.deployment_gas = GAS_PER_DEPLOYED_CODE_BYTE * len(deploy_code_bytes)

        super().__init__(pre_padding_bytes + padding_bytes, name=name)


@dataclass(kw_only=True)
class CodeGasMeasure(Code):
    """
    Helper class used to generate bytecode that measures gas usage of a
    bytecode, taking into account and subtracting any extra overhead gas costs
    required to execute.
    By default, the result gas calculation is saved to storage key 0.
    """

    code: str | bytes | SupportsBytes
    """
    Bytecode to be executed to measure the gas usage.
    """
    overhead_cost: int = 0
    """
    Extra gas cost to be subtracted from extra operations.
    """
    extra_stack_items: int = 0
    """
    Extra stack items that remain at the end of the execution.
    To be considered when subtracting the value of the previous GAS operation,
    and to be popped at the end of the execution.
    """
    sstore_key: int = 0
    """
    Storage key to save the gas used.
    """

    def __post_init__(self):
        """
        Assemble the bytecode that measures gas usage.
        """
        res = bytes()
        res += bytes(
            [
                0x5A,  # GAS
            ]
        )
        res += to_bytes(self.code)  # Execute code to measure its gas cost
        res += bytes(
            [
                0x5A,  # GAS
            ]
        )
        # We need to swap and pop for each extra stack item that remained from
        # the execution of the code
        res += (
            bytes(
                [
                    0x90,  # SWAP1
                    0x50,  # POP
                ]
            )
            * self.extra_stack_items
        )
        res += bytes(
            [
                0x90,  # SWAP1
                0x03,  # SUB
                0x60,  # PUSH1
                self.overhead_cost + 2,  # Overhead cost + GAS opcode price
                0x90,  # SWAP1
                0x03,  # SUB
                0x60,  # PUSH1
                self.sstore_key,  # -> SSTORE key
                0x55,  # SSTORE
                0x00,  # STOP
            ]
        )
        self.bytecode = res


@dataclass(kw_only=True)
class Conditional(Code):
    """
    Helper class used to generate conditional bytecode.
    """

    condition: str | bytes | SupportsBytes
    """
    Condition bytecode which must return the true or false condition of the conditional statement.
    """

    if_true: str | bytes | SupportsBytes
    """
    Bytecode to execute if the condition is true.
    """

    if_false: str | bytes | SupportsBytes
    """
    Bytecode to execute if the condition is false.
    """

    def __post_init__(self):
        """
        Assemble the conditional bytecode by generating the necessary jumps and
        jumpdests surrounding the condition and the two possible execution
        paths.

        In the future, PC usage should be replaced by using RJUMP and RJUMPI
        """
        condition_bytes = to_bytes(self.condition)
        if_true_bytes = to_bytes(self.if_true)
        if_false_bytes = to_bytes(self.if_false)

        # First we append a jumpdest to the start of the true branch
        if_true_bytes = Op.JUMPDEST + if_true_bytes

        # Then we append the unconditional jump to the end of the false branch, used to skip the
        # true branch
        if_false_bytes += Op.JUMP(Op.ADD(Op.PC, len(if_true_bytes) + 3))

        # Then we need to do the conditional jump by skipping the false branch
        condition_bytes = Op.JUMPI(Op.ADD(Op.PC, len(if_false_bytes) + 3), condition_bytes)

        # Finally we append the true and false branches, and the condition, plus the jumpdest at
        # the very end
        self.bytecode = condition_bytes + if_false_bytes + if_true_bytes + Op.JUMPDEST
