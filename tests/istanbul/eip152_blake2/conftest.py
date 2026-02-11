"""pytest fixtures for testing the BLAKE2b precompile."""

import pytest
from execution_testing import Bytecode, Op
from execution_testing.forks.helpers import Fork

from .spec import Spec


@pytest.fixture
def blake2b_contract_bytecode(call_opcode: Op, fork: Fork) -> Bytecode:
    """
    Contract code that performs the provided opcode (CALL or CALLCODE) to the
    BLAKE2b precompile and stores the result.
    """
    gas_costs = fork.gas_costs()
    sstore_cost = 3 * (gas_costs.G_STORAGE_SET + gas_costs.G_COLD_SLOAD)
    return (
        Op.CALLDATACOPY(0, 0, Op.CALLDATASIZE())
        + Op.SSTORE(
            0,
            call_opcode(
                # failed calls would consume gas required for test teardown
                gas=Op.SUB(Op.GAS, sstore_cost + 10_000),
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
