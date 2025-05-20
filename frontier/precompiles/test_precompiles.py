"""Tests supported precompiled contracts."""

from typing import Iterator, Tuple

import pytest

from ethereum_test_forks import Fork
from ethereum_test_tools import (
    Account,
    Alloc,
    Environment,
    StateTestFiller,
    Transaction,
)
from ethereum_test_tools.vm.opcode import Opcodes as Op

UPPER_BOUND = 0xFF
NUM_UNSUPPORTED_PRECOMPILES = 1


def precompile_addresses(fork: Fork) -> Iterator[Tuple[str, bool]]:
    """
    Yield the addresses of precompiled contracts and their support status for a given fork.

    Args:
        fork (Fork): The fork instance containing precompiled contract information.

    Yields:
        Iterator[Tuple[str, bool]]: A tuple containing the address in hexadecimal format and a
            boolean indicating whether the address is a supported precompile.

    """
    supported_precompiles = fork.precompiles()

    num_unsupported = NUM_UNSUPPORTED_PRECOMPILES
    for address in range(1, UPPER_BOUND + 1):
        if address in supported_precompiles:
            yield (hex(address), True)
        elif num_unsupported > 0:
            # Check unsupported precompiles up to NUM_UNSUPPORTED_PRECOMPILES
            yield (hex(address), False)
            num_unsupported -= 1


@pytest.mark.ported_from(
    [
        "https://github.com/ethereum/tests/blob/v13.3/src/GeneralStateTestsFiller/stPreCompiledContracts/idPrecompsFiller.yml"
    ],
    pr=["https://github.com/ethereum/execution-spec-tests/pull/1120"],
)
@pytest.mark.valid_from("Berlin")
@pytest.mark.parametrize_by_fork("address,precompile_exists", precompile_addresses)
def test_precompiles(
    state_test: StateTestFiller, address: str, precompile_exists: bool, pre: Alloc
):
    """
    Tests the behavior of precompiled contracts in the Ethereum state test.

    Args:
        state_test (StateTestFiller): The state test filler object used to run the test.
        address (str): The address of the precompiled contract to test.
        precompile_exists (bool): A flag indicating whether the precompiled contract exists at the
            given address.
        pre (Alloc): The allocation object used to deploy the contract and set up the initial
            state.

    This test deploys a contract that performs two CALL operations to the specified address and a
    fixed address (0x10000), measuring the gas used for each call. It then stores the difference
    in gas usage in storage slot 0. The test verifies the expected storage value based on
    whether the precompiled contract exists at the given address.

    """
    env = Environment()

    account = pre.deploy_contract(
        Op.MSTORE(0, 0)  # Pre-expand the memory so the gas costs are exactly the same
        + Op.GAS
        + Op.CALL(
            address=address,
            value=0,
            args_offset=0,
            args_size=32,
            output_offset=32,
            output_size=32,
        )
        + Op.POP
        + Op.SUB(Op.SWAP1, Op.GAS)
        + Op.GAS
        + Op.CALL(
            address=pre.fund_eoa(amount=0),
            value=0,
            args_offset=0,
            args_size=32,
            output_offset=32,
            output_size=32,
        )
        + Op.POP
        + Op.SUB(Op.SWAP1, Op.GAS)
        + Op.SWAP1
        + Op.SUB
        + Op.SSTORE(0, Op.ISZERO)
        + Op.STOP,
        storage={0: 0xDEADBEEF},
    )

    tx = Transaction(
        to=account,
        sender=pre.fund_eoa(),
        gas_limit=1_000_000,
        protected=True,
    )

    # A high gas cost will result from calling a precompile
    # Expect 0x00 when a precompile exists at the address, 0x01 otherwise
    post = {account: Account(storage={0: "0x00" if precompile_exists else "0x01"})}

    state_test(env=env, pre=pre, post=post, tx=tx)
