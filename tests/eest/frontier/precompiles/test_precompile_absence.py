"""abstract: Test Calling Precompile Range (close to zero)."""

import pytest

from ethereum_test_forks import Fork
from ethereum_test_tools import (
    Account,
    Address,
    Alloc,
    Bytecode,
    StateTestFiller,
    Storage,
    Transaction,
)
from ethereum_test_tools import Opcodes as Op

UPPER_BOUND = 0x101
RETURNDATASIZE_OFFSET = 0x10000000000000000  # Must be greater than UPPER_BOUND


@pytest.mark.parametrize(
    "calldata_size",
    [
        pytest.param(0, id="empty_calldata"),
        pytest.param(31, id="31_bytes"),
        pytest.param(32, id="32_bytes"),
    ],
)
@pytest.mark.valid_from("Byzantium")
def test_precompile_absence(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    calldata_size: int,
):
    """Test that addresses close to zero are not precompiles unless active in the fork."""
    active_precompiles = fork.precompiles()
    storage = Storage()
    call_code = Bytecode()
    for address in range(1, UPPER_BOUND + 1):
        if Address(address) in active_precompiles:
            continue
        call_code += Op.SSTORE(
            address,
            Op.CALL(gas=0, address=address, args_size=calldata_size),
        )
        storage[address] = 1
        if Op.RETURNDATASIZE in fork.valid_opcodes():
            call_code += Op.SSTORE(
                address + RETURNDATASIZE_OFFSET,
                Op.RETURNDATASIZE,
            )
            storage[address + RETURNDATASIZE_OFFSET] = 0

    call_code += Op.STOP

    entry_point_address = pre.deploy_contract(call_code, storage=storage.canary())

    tx = Transaction(
        to=entry_point_address,
        gas_limit=10_000_000,
        sender=pre.fund_eoa(),
        protected=True,
    )

    state_test(
        pre=pre,
        tx=tx,
        post={
            entry_point_address: Account(
                storage=storage,
            )
        },
    )
