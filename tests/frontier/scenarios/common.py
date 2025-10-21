"""Define Scenario structures and helpers for test_scenarios test."""

from abc import abstractmethod
from dataclasses import dataclass
from enum import Enum

from ethereum_test_forks import Fork, Frontier
from ethereum_test_tools import (
    Address,
    Alloc,
    Bytecode,
    Conditional,
    MemoryVariable,
)
from ethereum_test_vm import Opcodes as Op


class ScenarioExpectOpcode(Enum):
    """Opcodes that are replaced to real values computed by the scenario."""

    TX_ORIGIN = 1
    CODE_ADDRESS = 2
    CODE_CALLER = 3
    SELFBALANCE = 4
    CALL_VALUE = 6
    CALL_DATALOAD_0 = 7
    CALL_DATASIZE = 8
    GASPRICE = 9
    BLOCKHASH_0 = 10
    COINBASE = 11
    TIMESTAMP = 12
    NUMBER = 13
    GASLIMIT = 14


@dataclass
class ScenarioEnvironment:
    """
    Scenario evm environment Each scenario must define an environment on which
    program is executed This is so post state verification could check results
    of evm opcodes.
    """

    code_address: Address  # Op.ADDRESS, address scope for program
    code_caller: Address  # Op.CALLER, caller of the program
    selfbalance: (
        int  # Op.SELFBALANCE, balance of the environment of the program
    )
    call_value: int  # Op.CALLVALUE of call that is done to the program
    call_dataload_0: int  # Op.CALLDATALOAD(0) expected result
    call_datasize: int  # Op.CALLDATASIZE expected result
    has_static: bool = False  # Weather scenario execution context is static


@dataclass
class ExecutionEnvironment:
    """Scenario execution environment which is determined by test."""

    fork: Fork
    gasprice: int
    origin: Address
    coinbase: Address
    timestamp: int
    number: int
    gaslimit: int


@dataclass
class ProgramResult:
    """
    Describe expected result of a program.

    Attributes:
      result (int | ScenarioExpectOpcode): The result of the program
      from_fork (Fork): The result is only valid from this fork
                        (default: Frontier)
      static_support (bool): Can be verified in static context (default: True)

    """

    result: int | ScenarioExpectOpcode

    """The result is only valid from this fork"""
    from_fork: Fork = Frontier
    static_support: bool = True

    def translate_result(
        self, env: ScenarioEnvironment, exec_env: ExecutionEnvironment
    ) -> int | Address:
        """
        Translate expected program result code into concrete value, given the
        scenario evm environment and test execution environment.
        """
        if exec_env.fork < self.from_fork:
            return 0
        if not self.static_support and env.has_static:
            return 0
        if isinstance(self.result, ScenarioExpectOpcode):
            if self.result == ScenarioExpectOpcode.TX_ORIGIN:
                return exec_env.origin
            if self.result == ScenarioExpectOpcode.CODE_ADDRESS:
                return env.code_address
            if self.result == ScenarioExpectOpcode.CODE_CALLER:
                return env.code_caller
            if self.result == ScenarioExpectOpcode.CALL_VALUE:
                return int(env.call_value)
            if self.result == ScenarioExpectOpcode.CALL_DATALOAD_0:
                return env.call_dataload_0
            if self.result == ScenarioExpectOpcode.CALL_DATASIZE:
                return env.call_datasize
            if self.result == ScenarioExpectOpcode.GASPRICE:
                return exec_env.gasprice
            if self.result == ScenarioExpectOpcode.COINBASE:
                return exec_env.coinbase
            if self.result == ScenarioExpectOpcode.TIMESTAMP:
                return exec_env.timestamp
            if self.result == ScenarioExpectOpcode.NUMBER:
                return exec_env.number
            if self.result == ScenarioExpectOpcode.GASLIMIT:
                return exec_env.gaslimit
            if self.result == ScenarioExpectOpcode.SELFBALANCE:
                return int(env.selfbalance)
        else:
            return self.result
        return 0


class ScenarioTestProgram:
    """Base class for deploying test code that will be used in scenarios."""

    @abstractmethod
    def make_test_code(self, pre: Alloc, fork: Fork) -> Bytecode:
        """Test code to be deployed."""
        pass

    @property
    @abstractmethod
    def id(self) -> str:
        """Test program pytest id."""
        pass

    @abstractmethod
    def result(self) -> ProgramResult:
        """Test program result."""
        pass

    def __str__(self) -> str:
        """Return the ID (for use as pytest test name)."""
        return self.id


@dataclass
class ScenarioDebug:
    """Debug selector for the development."""

    program_id: str
    scenario_name: str


@dataclass
class ScenarioGeneratorInput:
    """
    Parameters for the scenario generator function.

    Attributes:
      fork (Fork): Fork for which we ask to generate scenarios
      pre(Alloc): Access to the state to be able to deploy contracts into pre
      operation (Bytecode): Evm bytecode program that will be tested
      external_address (Address): Static external address for ext opcodes

    """

    fork: Fork
    pre: Alloc
    operation_code: Bytecode


@dataclass
class Scenario:
    """
    Describe test scenario that will be run in test for each program.

    Attributes:
      category (str): Scenario category name
      name (str): Scenario name for the test vector
      code (Address): Address that is an entry point for scenario code
      env (ScenarioEnvironment): Evm values for ScenarioExpectAddress map
      reverting (bool): If scenario reverts program execution,
                        making result 0 (default: False)

    """

    category: str
    name: str
    code: Address
    env: ScenarioEnvironment
    halts: bool = False


def make_gas_hash_contract(pre: Alloc) -> Address:
    """
    Contract that spends unique amount of gas based on input.
    Used for the values we can't predict, can be gas consuming on high values.
    So that if we can't check exact value in expect section, we at least
    could spend unique gas amount.
    """
    # EVM memory variables
    byte_offset = MemoryVariable(0)
    current_byte = MemoryVariable(32)

    # Code for memory initialization
    initialize_code = byte_offset.set(0)
    calldata_copy = Op.JUMPDEST + Op.CALLDATACOPY(
        dest_offset=current_byte.offset + 32 - 1,
        offset=byte_offset,
        size=1,
    )

    # Code offsets
    offset_calldata_copy = len(initialize_code)
    offset_conditional = offset_calldata_copy + len(calldata_copy)

    # Deploy contract
    gas_hash_address = pre.deploy_contract(
        code=initialize_code
        + calldata_copy  # offset_calldata_copy
        + Op.JUMPDEST  # offset_conditional
        + Conditional(
            condition=Op.ISZERO(current_byte),
            if_true=(
                # Increase the calldata byte offset, and if it's greater than
                # the calldata size, return, otherwise jump to the calldata
                # copy code and read the next byte.
                byte_offset.add(1)
                + Conditional(
                    condition=Op.GT(byte_offset, Op.CALLDATASIZE()),
                    if_true=Op.RETURN(offset=0, size=0),
                    if_false=Op.JUMP(offset_calldata_copy),
                )
            ),
            if_false=(current_byte.sub(1) + Op.JUMP(offset_conditional)),
        )
    )
    return gas_hash_address


def make_invalid_opcode_contract(pre: Alloc, fork: Fork) -> Address:
    """
    Deploy a contract that will execute any asked byte as an opcode from
    calldataload Deploy 20 empty stack elements. Jump to opcode instruction. if
    worked, return 0.
    """
    invalid_opcode_caller = pre.deploy_contract(
        code=Op.PUSH1(0) * 20
        + Op.JUMP(Op.ADD(Op.MUL(7, Op.CALLDATALOAD(0)), 20 * 2 + 10))
        + sum(
            [
                Op.JUMPDEST
                + Bytecode(
                    bytes([opcode]), popped_stack_items=0, pushed_stack_items=0
                )
                + Op.RETURN(0, 0)
                for opcode in range(0x00, 0xFF)
            ],
        )
    )

    invalid_opcodes = []
    valid_opcode_values = [opcode.int() for opcode in fork.valid_opcodes()]

    for op in range(0x00, 0xFF):
        if op not in valid_opcode_values:
            invalid_opcodes.append(op)

    results_sum = MemoryVariable(0)
    current_opcode = MemoryVariable(32)

    code = Bytecode(
        sum(
            current_opcode.set(opcode)
            + results_sum.add(
                Op.CALL(
                    gas=50000,
                    address=invalid_opcode_caller,
                    args_offset=current_opcode.offset,
                    args_size=32,
                ),
            )
            for opcode in invalid_opcodes
        )
        # If any of invalid instructions works, mstore[0] will be > 1
        + results_sum.add(1)
        + results_sum.return_value()
    )

    return pre.deploy_contract(code=code)
