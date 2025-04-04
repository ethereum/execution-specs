"""pytest fixtures for testing the BLAKE2b precompile."""

import pytest

from ethereum_test_tools.vm.opcode import Opcodes as Op
from ethereum_test_vm.bytecode import Bytecode

from .spec import Spec


@pytest.fixture
def blake2b_contract_bytecode(call_opcode: Op) -> Bytecode:
    """
    Contract code that performs the provided opcode (CALL or CALLCODE) to the BLAKE2b precompile
    and stores the result.
    """
    return (
        Op.CALLDATACOPY(0, 0, Op.CALLDATASIZE())
        + Op.SSTORE(
            0,
            call_opcode(
                address=Spec.BLAKE2_PRECOMPILE_ADDRESS,
                args_offset=0,
                args_size=Op.CALLDATASIZE(),
                ret_offset=0x200,
                ret_size=0x40,
            ),
        )
        + Op.SSTORE(1, Op.MLOAD(0x200))
        + Op.SSTORE(2, Op.MLOAD(0x220))
        + Op.STOP()
    )
