"""
Test_raw_call_gas.

Ported from:
state_tests/stEIP150singleCodeGasPrices/RawCallGasFiller.json

@manually-enhanced: Do not overwrite. Nested CALL gas via gas_cost(fork).
"""

import pytest
from execution_testing import (
    Account,
    Alloc,
    CodeGasMeasure,
    Fork,
    StateTestFiller,
    Transaction,
)
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


@pytest.mark.ported_from(
    ["state_tests/stEIP150singleCodeGasPrices/RawCallGasFiller.json"],
)
@pytest.mark.valid_from("Berlin")
def test_raw_call_gas(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """Measure the gas of a CALL to a contract that records its own gas."""
    # Forwarded gas must exceed the callee's SSTORE cost on every fork
    # (EIP-8037 state gas pushes a cold zero->non-zero SSTORE well above the
    # legacy ~22k).
    forward_gas = 200000

    # The callee sees `forward_gas` minus the GAS opcode it just executed, and
    # records it (cold zero->non-zero) to prove the forwarded amount.
    callee_gas_seen = forward_gas - Op.GAS.gas_cost(fork)
    callee_store = Op.SSTORE(
        key=0x2,
        value=Op.GAS,
        key_warm=False,
        original_value=0,
        new_value=callee_gas_seen,
    )
    callee = pre.deploy_contract(code=callee_store + Op.STOP)

    call_code = Op.CALL(
        gas=forward_gas,
        address=callee,
        value=0x0,
        address_warm=False,
        value_transfer=False,
        account_new=False,
    )
    caller = pre.deploy_contract(
        code=CodeGasMeasure(
            code=call_code,
            extra_stack_items=1,
            sstore_key=0x1,
        ),
    )

    tx = Transaction(
        sender=pre.fund_eoa(),
        to=caller,
        state_gas_reservoir=0,
    )

    # Measured CALL cost = the CALL's own cost plus the gas the callee used.
    call_gas = call_code.gas_cost(fork) + callee_store.gas_cost(fork)

    post = {
        callee: Account(storage={0x2: callee_gas_seen}),
        caller: Account(storage={0x1: call_gas}),
    }

    state_test(pre=pre, post=post, tx=tx)
