"""Define programs that can not be run in static context."""

from functools import cached_property

from ethereum_test_forks import Fork
from ethereum_test_tools import Alloc, Bytecode
from ethereum_test_tools.vm.opcode import Opcodes as Op

from ..common import ProgramResult, ScenarioTestProgram, make_invalid_opcode_contract


class ProgramInvalidOpcode(ScenarioTestProgram):
    """Test each invalid opcode."""

    def make_test_code(self, pre: Alloc, fork: Fork) -> Bytecode:
        """Test code."""
        contract = make_invalid_opcode_contract(pre, fork)
        return Op.MSTORE(
            0,
            Op.CALL(Op.SUB(Op.GAS, 200000), contract, 0, 64, 32, 100, 32),
        ) + Op.RETURN(100, 32)

    @cached_property
    def id(self) -> str:
        """Id."""
        return "program_INVALID"

    def result(self) -> ProgramResult:
        """Test result."""
        return ProgramResult(result=1)
