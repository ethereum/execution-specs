"""
Test the GAS opcode after memory expansion.

The original tests were written by Ori Pomerantz.

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
@pytest.mark.valid_from("Frontier")
@pytest.mark.parametrize(
    "prefix",
    [
        pytest.param(
            # Expand memory by one aligned word, then write at the
            # unaligned offset 0x5A, which ends memory at byte 0x7A and
            # is charged as rounded up to 4 words.
            Op.MSTORE(0, 0xFFFFFFFFFF, new_memory_size=0x20)
            + Op.MSTORE(
                0x5A, 0xEEEE, old_memory_size=0x20, new_memory_size=0x7A
            ),
            id="after_memory_expansion",
        ),
        pytest.param(Bytecode(), id="no_prior_operations"),
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
    tx = Transaction(
        sender=pre.fund_eoa(),
        to=contract,
        gas_limit=gas_limit,
        protected=fork.supports_protected_txs(),
    )
    expected = EXECUTION_GAS - (prefix + Op.GAS).gas_cost(fork)
    post = {contract: Account(storage={0: expected})}
    state_test(pre=pre, post=post, tx=tx)
