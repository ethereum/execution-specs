"""Define programs that will run all context opcodes for test scenarios."""

from functools import cached_property

from ethereum_test_forks import Byzantium, Cancun, Constantinople, Fork, Istanbul, London, Shanghai
from ethereum_test_tools import Alloc, Bytecode
from ethereum_test_tools.vm.opcode import Opcodes as Op

from ..common import (
    ProgramResult,
    ScenarioExpectOpcode,
    ScenarioTestProgram,
    make_gas_hash_contract,
)


class ProgramAddress(ScenarioTestProgram):
    """Check that ADDRESS is really the code execution address in all scenarios."""

    def make_test_code(self, pre: Alloc, fork: Fork) -> Bytecode:
        """Test code."""
        return Op.MSTORE(0, Op.ADDRESS) + Op.RETURN(0, 32)

    @cached_property
    def id(self) -> str:
        """Id."""
        return "program_ADDRESS"

    def result(self) -> ProgramResult:
        """Test result."""
        return ProgramResult(result=ScenarioExpectOpcode.CODE_ADDRESS)


class ProgramBalance(ScenarioTestProgram):
    """Check the BALANCE in all execution contexts."""

    external_balance: int = 123

    def make_test_code(self, pre: Alloc, fork: Fork) -> Bytecode:
        """Test code."""
        external_address = pre.deploy_contract(code=Op.ADD(1, 1), balance=self.external_balance)
        return Op.MSTORE(0, Op.BALANCE(external_address)) + Op.RETURN(0, 32)

    @cached_property
    def id(self) -> str:
        """Id."""
        return "program_BALANCE"

    def result(self) -> ProgramResult:
        """Test result."""
        return ProgramResult(result=self.external_balance)


class ProgramOrigin(ScenarioTestProgram):
    """Check that ORIGIN stays the same in all contexts."""

    def make_test_code(self, pre: Alloc, fork: Fork) -> Bytecode:
        """Test code."""
        return Op.MSTORE(0, Op.ORIGIN) + Op.RETURN(0, 32)

    @cached_property
    def id(self) -> str:
        """Id."""
        return "program_ORIGIN"

    def result(self) -> ProgramResult:
        """Test result."""
        return ProgramResult(result=ScenarioExpectOpcode.TX_ORIGIN)


class ProgramCaller(ScenarioTestProgram):
    """Check the CALLER in all execution contexts."""

    def make_test_code(self, pre: Alloc, fork: Fork) -> Bytecode:
        """Test code."""
        return Op.MSTORE(0, Op.CALLER) + Op.RETURN(0, 32)

    @cached_property
    def id(self) -> str:
        """Id."""
        return "program_CALLER"

    def result(self) -> ProgramResult:
        """Test result."""
        return ProgramResult(result=ScenarioExpectOpcode.CODE_CALLER)


class ProgramCallValue(ScenarioTestProgram):
    """Check the CALLVALUE in all execution contexts."""

    def make_test_code(self, pre: Alloc, fork: Fork) -> Bytecode:
        """Test code."""
        return Op.MSTORE(0, Op.CALLVALUE) + Op.RETURN(0, 32)

    @cached_property
    def id(self) -> str:
        """Id."""
        return "program_CALLVALUE"

    def result(self) -> ProgramResult:
        """Test result."""
        return ProgramResult(result=ScenarioExpectOpcode.CALL_VALUE)


class ProgramCallDataLoad(ScenarioTestProgram):
    """Check the CALLDATALOAD in all execution contexts."""

    def make_test_code(self, pre: Alloc, fork: Fork) -> Bytecode:
        """Test code."""
        return Op.MSTORE(0, Op.CALLDATALOAD(0)) + Op.RETURN(0, 32)

    @cached_property
    def id(self) -> str:
        """Id."""
        return "program_CALLDATALOAD"

    def result(self) -> ProgramResult:
        """Test result."""
        return ProgramResult(result=ScenarioExpectOpcode.CALL_DATALOAD_0)


class ProgramCallDataSize(ScenarioTestProgram):
    """Check the CALLDATASIZE in all execution contexts."""

    def make_test_code(self, pre: Alloc, fork: Fork) -> Bytecode:
        """Test code."""
        return Op.MSTORE(0, Op.CALLDATASIZE) + Op.RETURN(0, 32)

    @cached_property
    def id(self) -> str:
        """Id."""
        return "program_CALLDATASIZE"

    def result(self) -> ProgramResult:
        """Test result."""
        return ProgramResult(result=ScenarioExpectOpcode.CALL_DATASIZE)


class ProgramCallDataCopy(ScenarioTestProgram):
    """Check the CALLDATACOPY in all execution contexts."""

    def make_test_code(self, pre: Alloc, fork: Fork) -> Bytecode:
        """Test code."""
        return Op.CALLDATACOPY(0, 0, Op.CALLDATASIZE) + Op.RETURN(0, 32)

    @cached_property
    def id(self) -> str:
        """Id."""
        return "program_CALLDATACOPY"

    def result(self) -> ProgramResult:
        """Test result."""
        return ProgramResult(result=ScenarioExpectOpcode.CALL_DATALOAD_0)


class ProgramCodeCopyCodeSize(ScenarioTestProgram):
    """Check that codecopy and codesize stays the same in all contexts."""

    def make_test_code(self, pre: Alloc, fork: Fork) -> Bytecode:
        """Test code."""
        return Op.MSTORE(0, Op.CODESIZE) + Op.CODECOPY(0, 0, 30) + Op.RETURN(0, 32)

    @cached_property
    def id(self) -> str:
        """Id."""
        return "program_CODECOPY_CODESIZE"

    def result(self) -> ProgramResult:
        """Test result."""
        return ProgramResult(
            result=0x38600052601E600060003960206000F300000000000000000000000000000010
        )


class ProgramGasPrice(ScenarioTestProgram):
    """Check that gasprice stays the same in all contexts."""

    def make_test_code(self, pre: Alloc, fork: Fork) -> Bytecode:
        """Test code."""
        return Op.MSTORE(0, Op.GASPRICE) + Op.RETURN(0, 32)

    @cached_property
    def id(self) -> str:
        """Id."""
        return "program_GASPRICE"

    def result(self) -> ProgramResult:
        """Test result."""
        return ProgramResult(result=ScenarioExpectOpcode.GASPRICE)


class ProgramExtCodeCopyExtCodeSize(ScenarioTestProgram):
    """Check that gasprice stays the same in all contexts."""

    external_balance: int = 123

    def make_test_code(self, pre: Alloc, fork: Fork) -> Bytecode:
        """Test code."""
        external_address = pre.deploy_contract(code=Op.ADD(1, 1), balance=self.external_balance)
        return (
            Op.MSTORE(0, Op.EXTCODESIZE(external_address))
            + Op.EXTCODECOPY(external_address, 0, 0, 30)
            + Op.RETURN(0, 32)
        )

    @cached_property
    def id(self) -> str:
        """Id."""
        return "program_EXTCODECOPY_EXTCODESIZE"

    def result(self) -> ProgramResult:
        """Test result."""
        return ProgramResult(
            result=0x6001600101000000000000000000000000000000000000000000000000000005
        )


class ProgramReturnDataSize(ScenarioTestProgram):
    """Check that returndatasize stays the same in all contexts."""

    def make_test_code(self, pre: Alloc, fork: Fork) -> Bytecode:
        """Test code."""
        return (
            Op.MSTORE(0, Op.RETURNDATASIZE)
            + Op.CALL(100000, 2, 0, 0, 10, 32, 20)
            + Op.MSTORE(0, Op.ADD(Op.MLOAD(0), Op.RETURNDATASIZE))
            + Op.RETURN(0, 32)
        )

    @cached_property
    def id(self) -> str:
        """Id."""
        return "program_RETURNDATASIZE"

    def result(self) -> ProgramResult:
        """Test result."""
        return ProgramResult(result=32, from_fork=Byzantium)


class ProgramReturnDataCopy(ScenarioTestProgram):
    """Check that returndatacopy stays the same in all contexts."""

    def make_test_code(self, pre: Alloc, fork: Fork) -> Bytecode:
        """Test code."""
        return (
            Op.CALL(100000, 2, 0, 0, 10, 32, 20) + Op.RETURNDATACOPY(0, 0, 32) + Op.RETURN(0, 32)
        )

    @cached_property
    def id(self) -> str:
        """Id."""
        return "program_RETURNDATACOPY"

    def result(self) -> ProgramResult:
        """Test result."""
        return ProgramResult(
            result=0x1D448AFD928065458CF670B60F5A594D735AF0172C8D67F22A81680132681CA,
            from_fork=Byzantium,
        )


class ProgramExtCodehash(ScenarioTestProgram):
    """Check that extcodehash stays the same in all contexts."""

    def make_test_code(self, pre: Alloc, fork: Fork) -> Bytecode:
        """Test code."""
        external_address = pre.deploy_contract(code=Op.ADD(1, 1), balance=123)
        return Op.MSTORE(0, Op.EXTCODEHASH(external_address)) + Op.RETURN(0, 32)

    @cached_property
    def id(self) -> str:
        """Id."""
        return "program_EXTCODEHASH"

    def result(self) -> ProgramResult:
        """Test result."""
        return ProgramResult(
            result=0x8C634A8B28DD46F5DCB9A9F5DA1FAED26D0FB5ED98F3873A29AD27AAAFFDE0E4,
            from_fork=Constantinople,
        )


class ProgramBlockhash(ScenarioTestProgram):
    """Check that blockhash stays the same in all contexts."""

    # Need a way to pre calculate at least hash of block 0

    def make_test_code(self, pre: Alloc, fork: Fork) -> Bytecode:
        """Test code."""
        # Calculate gas hash of Op.BLOCKHASH(0) value
        gas_hash = make_gas_hash_contract(pre)

        return (
            Op.MSTORE(64, Op.BLOCKHASH(0))
            + Op.CALL(Op.SUB(Op.GAS, 200000), gas_hash, 0, 64, 32, 0, 0)
            + Op.MSTORE(0, 1)
            + Op.RETURN(0, 32)
        )

    @cached_property
    def id(self) -> str:
        """Id."""
        return "program_BLOCKHASH"

    def result(self) -> ProgramResult:
        """Test result."""
        return ProgramResult(result=1)


class ProgramCoinbase(ScenarioTestProgram):
    """Check that coinbase stays the same in all contexts."""

    def make_test_code(self, pre: Alloc, fork: Fork) -> Bytecode:
        """Test code."""
        return Op.MSTORE(0, Op.COINBASE) + Op.RETURN(0, 32)

    @cached_property
    def id(self) -> str:
        """Id."""
        return "program_COINBASE"

    def result(self) -> ProgramResult:
        """Test result."""
        return ProgramResult(result=ScenarioExpectOpcode.COINBASE)


class ProgramTimestamp(ScenarioTestProgram):
    """Check that timestamp stays the same in all contexts."""

    def make_test_code(self, pre: Alloc, fork: Fork) -> Bytecode:
        """Test code."""
        gas_hash = make_gas_hash_contract(pre)
        return (
            Op.MSTORE(64, Op.TIMESTAMP)
            + Op.CALL(Op.SUB(Op.GAS, 200000), gas_hash, 0, 64, 32, 0, 0)
            + Op.MSTORE(0, 1)
            + Op.RETURN(0, 32)
        )

    @cached_property
    def id(self) -> str:
        """Id."""
        return "program_TIMESTAMP"

    def result(self) -> ProgramResult:
        """Test result."""
        return ProgramResult(result=1)


class ProgramNumber(ScenarioTestProgram):
    """Check that block number stays the same in all contexts."""

    def make_test_code(self, pre: Alloc, fork: Fork) -> Bytecode:
        """Test code."""
        return Op.MSTORE(0, Op.NUMBER) + Op.RETURN(0, 32)

    @cached_property
    def id(self) -> str:
        """Id."""
        return "program_NUMBER"

    def result(self) -> ProgramResult:
        """Test result."""
        return ProgramResult(result=ScenarioExpectOpcode.NUMBER)


class ProgramDifficultyRandao(ScenarioTestProgram):
    """Check that difficulty/randao stays the same in all contexts."""

    def make_test_code(self, pre: Alloc, fork: Fork) -> Bytecode:
        """Test code."""
        # Calculate gas hash of DIFFICULTY value
        gas_hash = make_gas_hash_contract(pre)
        return (
            Op.MSTORE(0, Op.PREVRANDAO)
            + Op.MSTORE(64, Op.PREVRANDAO)
            + Op.CALL(Op.SUB(Op.GAS, 200000), gas_hash, 0, 64, 32, 0, 0)
            + Op.MSTORE(0, 1)
            + Op.RETURN(0, 32)
        )

    @cached_property
    def id(self) -> str:
        """Id."""
        return "program_DIFFICULTY"

    def result(self) -> ProgramResult:
        """Test result."""
        return ProgramResult(result=1)


class ProgramGasLimit(ScenarioTestProgram):
    """Check that gaslimit stays the same in all contexts."""

    def make_test_code(self, pre: Alloc, fork: Fork) -> Bytecode:
        """Test code."""
        return Op.MSTORE(0, Op.GASLIMIT) + Op.RETURN(0, 32)

    @cached_property
    def id(self) -> str:
        """Id."""
        return "program_GASLIMIT"

    def result(self) -> ProgramResult:
        """Test result."""
        return ProgramResult(result=ScenarioExpectOpcode.GASLIMIT)


class ProgramChainid(ScenarioTestProgram):
    """Check that chainid stays the same in all contexts."""

    def make_test_code(self, pre: Alloc, fork: Fork) -> Bytecode:
        """Test code."""
        return Op.MSTORE(0, Op.CHAINID) + Op.RETURN(0, 32)

    @cached_property
    def id(self) -> str:
        """Id."""
        return "program_CHAINID"

    def result(self) -> ProgramResult:
        """Test result."""
        return ProgramResult(result=1, from_fork=Istanbul)


class ProgramSelfbalance(ScenarioTestProgram):
    """Check the SELFBALANCE in all execution contexts."""

    def make_test_code(self, pre: Alloc, fork: Fork) -> Bytecode:
        """Test code."""
        return Op.MSTORE(0, Op.SELFBALANCE) + Op.RETURN(0, 32)

    @cached_property
    def id(self) -> str:
        """Id."""
        return "program_SELFBALANCE"

    def result(self) -> ProgramResult:
        """Test result."""
        return ProgramResult(result=ScenarioExpectOpcode.SELFBALANCE, from_fork=Istanbul)


class ProgramBasefee(ScenarioTestProgram):
    """Check the BASEFEE in all execution contexts."""

    def make_test_code(self, pre: Alloc, fork: Fork) -> Bytecode:
        """Test code."""
        gas_hash = make_gas_hash_contract(pre)
        return (
            Op.MSTORE(64, Op.BASEFEE)
            + Op.CALL(Op.SUB(Op.GAS, 200000), gas_hash, 0, 64, 32, 0, 0)
            + Op.MSTORE(0, 1)
            + Op.RETURN(0, 32)
        )

    @cached_property
    def id(self) -> str:
        """Id."""
        return "program_BASEFEE"

    def result(self) -> ProgramResult:
        """Test result."""
        return ProgramResult(result=1, from_fork=London)


class ProgramBlobhash(ScenarioTestProgram):
    """Check the blobhash in all execution contexts."""

    def make_test_code(self, pre: Alloc, fork: Fork) -> Bytecode:
        """Test code."""
        return Op.MSTORE(0, Op.BLOBHASH(0)) + Op.RETURN(0, 32)

    @cached_property
    def id(self) -> str:
        """Id."""
        return "program_BLOBHASH"

    def result(self) -> ProgramResult:
        """Test result."""
        return ProgramResult(result=0, from_fork=Cancun)


class ProgramBlobBaseFee(ScenarioTestProgram):
    """Check the blob basefee in all execution contexts."""

    def make_test_code(self, pre: Alloc, fork: Fork) -> Bytecode:
        """Test code."""
        gas_hash = make_gas_hash_contract(pre)
        return (
            Op.MSTORE(64, Op.BLOBBASEFEE)
            + Op.CALL(Op.SUB(Op.GAS, 200000), gas_hash, 0, 64, 32, 0, 0)
            + Op.MSTORE(0, 1)
            + Op.RETURN(0, 32)
        )

    @cached_property
    def id(self) -> str:
        """Id."""
        return "program_BLOBBASEFEE"

    def result(self) -> ProgramResult:
        """Test result."""
        return ProgramResult(result=1, from_fork=Cancun)


class ProgramTload(ScenarioTestProgram):
    """Check the tload in all execution contexts."""

    def make_test_code(self, pre: Alloc, fork: Fork) -> Bytecode:
        """Test code."""
        return Op.MSTORE(0, Op.TLOAD(0)) + Op.RETURN(0, 32)

    @cached_property
    def id(self) -> str:
        """Id."""
        return "program_TLOAD"

    def result(self) -> ProgramResult:
        """Test result."""
        return ProgramResult(result=0, from_fork=Cancun)


class ProgramMcopy(ScenarioTestProgram):
    """Check the mcopy in all execution contexts."""

    def make_test_code(self, pre: Alloc, fork: Fork) -> Bytecode:
        """Test code."""
        return (
            Op.MSTORE(0, 0)
            + Op.MSTORE(32, 0x000102030405060708090A0B0C0D0E0F101112131415161718191A1B1C1D1E1F)
            + Op.MCOPY(0, 32, 32)
            + Op.RETURN(0, 32)
        )

    @cached_property
    def id(self) -> str:
        """Id."""
        return "program_MCOPY"

    def result(self) -> ProgramResult:
        """Test result."""
        return ProgramResult(
            result=0x000102030405060708090A0B0C0D0E0F101112131415161718191A1B1C1D1E1F,
            from_fork=Cancun,
        )


class ProgramPush0(ScenarioTestProgram):
    """Check the push0 in all execution contexts."""

    def make_test_code(self, pre: Alloc, fork: Fork) -> Bytecode:
        """Test code."""
        return Op.PUSH1(10) + Op.PUSH0 + Op.MSTORE + Op.RETURN(0, 32)

    @cached_property
    def id(self) -> str:
        """Id."""
        return "program_PUSH0"

    def result(self) -> ProgramResult:
        """Test result."""
        return ProgramResult(result=10, from_fork=Shanghai)
