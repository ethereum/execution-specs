"""Test the CALL opcode after EIP-2929."""

from typing import List, Tuple

import pytest
from execution_testing import (
    Account,
    Address,
    Alloc,
    CodeGasMeasure,
    Environment,
    Fork,
    Op,
    StateTestFiller,
    Transaction,
)

REFERENCE_SPEC_GIT_PATH = "EIPS/eip-2929.md"
REFERENCE_SPEC_VERSION = "0e11417265a623adb680c527b15d0cb6701b870b"


@pytest.mark.valid_from("Berlin")
@pytest.mark.eels_base_coverage
def test_call_insufficient_balance(
    state_test: StateTestFiller, pre: Alloc, env: Environment, fork: Fork
) -> None:
    """
    Test a regular CALL to see if it warms the destination with insufficient
    balance.
    """
    destination = pre.fund_eoa(1)
    warm_code = Op.BALANCE(destination, address_warm=True)
    contract_address = pre.deploy_contract(
        # Perform the aborted external calls
        Op.SSTORE(
            0,
            Op.CALL(
                gas=Op.GAS,
                address=destination,
                value=1,
                args_offset=0,
                args_size=0,
                ret_offset=0,
                ret_size=0,
            ),
        )
        # Measure the gas cost for BALANCE operation
        + CodeGasMeasure(
            code=warm_code,
            extra_stack_items=1,  # BALANCE puts balance on stack
            sstore_key=1,
        ),
        balance=0,
    )

    tx = Transaction(
        to=contract_address,
        sender=pre.fund_eoa(),
    )

    post = {
        destination: Account(
            balance=1,
        ),
        contract_address: Account(
            storage={
                0: 0,  # The CALL is aborted
                1: warm_code.gas_cost(fork),
            },
        ),
    }
    state_test(env=env, pre=pre, post=post, tx=tx)


def precompile_range_boundaries(fork: Fork) -> List[Tuple[Address, bool]]:
    """
    Return the precompiles at the ends of each range, which are warm, and
    the addresses right outside them, which are cold.
    """
    precompiles = {int.from_bytes(a, "big") for a in fork.precompiles()}
    range_ends = {
        p
        for p in precompiles
        if p - 1 not in precompiles or p + 1 not in precompiles
    }
    outside = {n for p in range_ends for n in (p - 1, p + 1)} - precompiles
    # Same low bytes as a precompile, for clients that compare only those.
    high_byte_set = {p | 1 << 152 for p in range_ends}
    return [(Address(a), True) for a in sorted(range_ends)] + [
        (Address(a), False) for a in sorted(outside | high_byte_set)
    ]


@pytest.mark.valid_from("Berlin")
@pytest.mark.with_all_call_opcodes()
@pytest.mark.parametrize_by_fork("address,warm", precompile_range_boundaries)
def test_call_precompile_range_boundaries(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    call_opcode: Op,
    address: Address,
    warm: bool,
) -> None:
    """
    Verify precompiles are warm and the addresses around them are cold, and
    that only the precompiles run as one.

    Clients encode the precompile set as a list, a numeric range or a
    predicate, so each range edge is checked from both sides.
    """
    call = call_opcode(gas=0, address=address, address_warm=warm)
    contract = pre.deploy_contract(
        CodeGasMeasure(code=call, extra_stack_items=1)
        # A precompile given no gas fails; an empty account succeeds.
        + Op.SSTORE(1, call_opcode(gas=0, address=address)),
    )
    tx = Transaction(to=contract, sender=pre.fund_eoa())
    post = {
        contract: Account(
            storage={0: call.gas_cost(fork), 1: 0 if warm else 1}
        )
    }
    state_test(pre=pre, post=post, tx=tx)
