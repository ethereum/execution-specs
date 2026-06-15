"""pytest fixtures for testing the BLAKE2b precompile."""

import pytest
from execution_testing import Bytecode, Fork, Op

from .common import Blake2bInput
from .spec import Spec


@pytest.fixture
def precompile_gas(fork: Fork, data: Blake2bInput | bytes) -> int | None:
    """
    Amount of gas to redirect to the precompile address.

    `None` means redirect all gas.
    """
    assert isinstance(data, Blake2bInput), (
        "Tests that don't use `Blake2bInput` as input must specify "
        "`precompile_gas`"
    )
    return data.estimate_gas(fork)


@pytest.fixture
def precompile_gas_modifier() -> int:
    """
    Amount of gas to redirect add or subtract from the call forwarded gas.
    """
    return 0


@pytest.fixture
def blake2b_contract_bytecode(
    call_opcode: Op,
    precompile_gas: int,
    precompile_gas_modifier: int,
) -> Bytecode:
    """
    Contract code that performs the provided opcode (CALL or CALLCODE) to the
    BLAKE2b precompile and stores the result.
    """
    if precompile_gas_modifier:
        precompile_gas += precompile_gas_modifier
    return (
        Op.CALLDATACOPY(0, 0, Op.CALLDATASIZE())
        + Op.SSTORE(
            0,
            call_opcode(
                gas=precompile_gas,
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
