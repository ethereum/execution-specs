"""Define programs that can not be run in static context."""

from functools import cached_property

from ethereum_test_forks import Cancun, Fork
from ethereum_test_tools import Alloc, Bytecode
from ethereum_test_tools.vm.opcode import Opcodes as Op

from ..common import ProgramResult, ScenarioTestProgram


class ProgramSstoreSload(ScenarioTestProgram):
    """Test sstore, sload working."""

    def make_test_code(self, pre: Alloc, fork: Fork) -> Bytecode:
        """Test code."""
        return (
            Op.SSTORE(0, 11)
            + Op.MSTORE(0, Op.ADD(Op.MLOAD(0), Op.SLOAD(0)))
            + Op.SSTORE(0, 5)
            + Op.MSTORE(0, Op.ADD(Op.MLOAD(0), Op.SLOAD(0)))
            + Op.RETURN(0, 32)
        )

    @cached_property
    def id(self) -> str:
        """Id."""
        return "program_SSTORE_SLOAD"

    def result(self) -> ProgramResult:
        """Test result."""
        return ProgramResult(result=16, static_support=False)


class ProgramTstoreTload(ScenarioTestProgram):
    """Test sstore, sload working."""

    def make_test_code(self, pre: Alloc, fork: Fork) -> Bytecode:
        """Test code."""
        return Op.TSTORE(0, 11) + Op.MSTORE(0, Op.TLOAD(0)) + Op.RETURN(0, 32)

    @cached_property
    def id(self) -> str:
        """Id."""
        return "program_TSTORE_TLOAD"

    def result(self) -> ProgramResult:
        """Test result."""
        return ProgramResult(result=11, static_support=False, from_fork=Cancun)


class ProgramLogs(ScenarioTestProgram):
    """Test Logs."""

    def make_test_code(self, pre: Alloc, fork: Fork) -> Bytecode:
        """Test code."""
        return (
            Op.MSTORE(0, 0x1122334455667788991011121314151617181920212223242526272829303132)
            + Op.LOG0(0, 1)
            + Op.LOG1(1, 1, 0x1000)
            + Op.LOG2(2, 1, 0x2000, 0x2001)
            + Op.LOG3(3, 1, 0x3000, 0x3001, 0x3002)
            + Op.LOG4(4, 1, 0x4000, 0x4001, 0x4002, 0x4003)
            + Op.MSTORE(0, 1)
            + Op.RETURN(0, 32)
        )

    @cached_property
    def id(self) -> str:
        """Id."""
        return "program_LOGS"

    def result(self) -> ProgramResult:
        """Test result."""
        return ProgramResult(result=1, static_support=False)


class ProgramSuicide(ScenarioTestProgram):
    """Test Suicide."""

    def make_test_code(self, pre: Alloc, fork: Fork) -> Bytecode:
        """Test code."""
        return Op.MSTORE(0, 1) + Op.SELFDESTRUCT(0) + Op.RETURN(0, 32)

    @cached_property
    def id(self) -> str:
        """Id."""
        return "program_SUICIDE"

    def result(self) -> ProgramResult:
        """Test result."""
        return ProgramResult(result=0, static_support=False)
