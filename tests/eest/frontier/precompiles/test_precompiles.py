"""Tests supported precompiled contracts."""

from typing import Iterator, Tuple

import pytest

from ethereum_test_forks import Fork
from ethereum_test_tools import (
    Account,
    Address,
    Alloc,
    Environment,
    StateTestFiller,
    Transaction,
)
from ethereum_test_tools.vm.opcode import Opcodes as Op


def precompile_addresses(fork: Fork) -> Iterator[Tuple[Address, bool]]:
    """
    Yield the addresses of precompiled contracts and their support status for a given fork.

    Args:
        fork (Fork): The fork instance containing precompiled contract information.

    Yields:
        Iterator[Tuple[str, bool]]: A tuple containing the address in hexadecimal format and a
            boolean indicating whether the address is a supported precompile.

    """
    supported_precompiles = fork.precompiles()

    for address in supported_precompiles:
        address_int = int.from_bytes(address, byteorder="big")
        yield (address, True)
        if address_int > 0 and (address_int - 1) not in supported_precompiles:
            yield (Address(address_int - 1), False)
        if (address_int + 1) not in supported_precompiles:
            yield (Address(address_int + 1), False)


@pytest.mark.ported_from(
    [
        "https://github.com/ethereum/tests/blob/v13.3/src/GeneralStateTestsFiller/stPreCompiledContracts/idPrecompsFiller.yml"
    ],
    pr=["https://github.com/ethereum/execution-spec-tests/pull/1120"],
    coverage_missed_reason=(
        "Original test saves variables to memory, loads from storage, uses calldataload to get "
        "the precompile address to call, uses lt and gt to compare the gas differences, "
        "sends non-zero data and value with the transaction, uses conditional jumps to save "
        "different values to storage."
    ),
)
@pytest.mark.valid_from("Berlin")
@pytest.mark.parametrize_by_fork("address,precompile_exists", precompile_addresses)
def test_precompiles(
    state_test: StateTestFiller, address: Address, precompile_exists: bool, pre: Alloc
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

    # Empty account to serve as reference
    empty_account = pre.fund_eoa(amount=0)

    # Memory
    args_offset = 0
    ret_offset = 32
    length = 32

    account = pre.deploy_contract(
        Op.MSTORE(args_offset, 0xFF)  # Pre-expand the memory and setup inputs for pre-compiles
        + Op.MSTORE(ret_offset, 0xFF)
        + Op.MSTORE8(args_offset, 0xFF)
        + Op.MSTORE8(ret_offset, 0xFF)
        + Op.POP(Op.BALANCE(empty_account))  # Warm the accounts
        + Op.POP(Op.BALANCE(address))
        + Op.GAS
        + Op.CALL(
            gas=50_000,
            address=address,
            args_offset=args_offset,
            args_size=length,
            ret_offset=ret_offset,
            ret_size=length,
        )
        + Op.POP
        + Op.SUB(Op.SWAP1, Op.GAS)
        + Op.GAS
        + Op.CALL(
            gas=50_000,
            address=empty_account,
            args_offset=args_offset,
            args_size=length,
            ret_offset=ret_offset,
            ret_size=length,
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
    post = {account: Account(storage={0: 0 if precompile_exists else 1})}

    state_test(env=env, pre=pre, post=post, tx=tx)
