"""
Test the GAS opcode after memory expansion.

Ported from:
state_tests/VMTests/vmIOandFlowOperations/gasFiller.yml
"""

import pytest
from execution_testing import (
    Account,
    Alloc,
    Bytecode,
    Fork,
    StateTestFiller,
    Transaction,
)
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"

SENTINEL = 0x0BAD
EXECUTION_GAS = 100_000


@pytest.mark.ported_from(
    ["state_tests/VMTests/vmIOandFlowOperations/gasFiller.yml"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "prefix",
    [
        pytest.param(
            Op.MSTORE(0, 0xFFFFFFFFFF, new_memory_size=0x20)
            + Op.MSTORE(
                0x5A, 0xEEEE, old_memory_size=0x20, new_memory_size=0x7A
            ),
            id="gas1",
        ),
        pytest.param(Bytecode(), id="gas2"),
    ],
)
def test_gas(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    prefix: Bytecode,
) -> None:
    """Store the gas left after running `prefix`."""
    contract = pre.deploy_contract(
        code=prefix + Op.SSTORE(0, Op.GAS) + Op.STOP,
        storage={0: SENTINEL},
    )
    intrinsic_gas = fork.transaction_intrinsic_cost_calculator()()
    gas_limit = intrinsic_gas + EXECUTION_GAS
    tx = Transaction(sender=pre.fund_eoa(), to=contract, gas_limit=gas_limit)
    expected = EXECUTION_GAS - (prefix + Op.GAS).gas_cost(fork)
    post = {contract: Account(storage={0: expected})}
    state_test(pre=pre, post=post, tx=tx)
