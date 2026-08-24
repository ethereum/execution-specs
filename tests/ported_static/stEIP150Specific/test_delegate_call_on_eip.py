"""
Measure a DELEGATECALL that asks for more gas than its frame holds: the
EIP-150 clamp decides the grant, the delegate writes into the caller's
storage, and the measured cost is the call plus the delegate's work.

Ported from:
state_tests/stEIP150Specific/DelegateCallOnEIPFiller.json

@manually-enhanced: Do not overwrite. An outer call pins the frame budget
so the oversized ask always clamps; the DELEGATECALL is measured with
CodeGasMeasure (success flag inside the window) and the expectation is the
composite plus the delegate's fork-priced store.
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

DELEGATE_VALUE = 0x12
FLAG_SLOT = 0x9
GAS_SLOT = 0x8

# The ported ask (600000): above the pinned frame budget, so the EIP-150
# clamp decides the grant on every fork.
ASK_GAS = 0x927C0
CALLER_GAS = 400_000


@pytest.mark.ported_from(
    ["state_tests/stEIP150Specific/DelegateCallOnEIPFiller.json"],
)
@pytest.mark.valid_from("Berlin")
@pytest.mark.valid_before("EIP8368")
def test_delegate_call_on_eip(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """Measure a clamped DELEGATECALL running a store in the caller."""
    # Runs in the caller's storage context: one cold fresh store.
    delegate_store = Op.SSTORE(
        key=0x0,
        value=DELEGATE_VALUE,
        key_warm=False,
        original_value=0,
        new_value=DELEGATE_VALUE,
    )
    delegate = pre.deploy_contract(code=delegate_store + Op.STOP)

    delegatecall_code = Op.DELEGATECALL(
        gas=ASK_GAS,
        address=delegate,
        address_warm=False,
    )
    flag_store = Op.SSTORE(
        key=FLAG_SLOT,
        value=delegatecall_code,
        key_warm=False,
        original_value=0,
        new_value=1,
    )
    target = pre.deploy_contract(
        code=CodeGasMeasure(
            code=flag_store,
            extra_stack_items=0,
            sstore_key=GAS_SLOT,
        ),
    )

    assert CALLER_GAS < ASK_GAS, "the 63/64 clamp must apply"
    entry = pre.deploy_contract(
        code=Op.SSTORE(key=0x0, value=Op.CALL(gas=CALLER_GAS, address=target))
        + Op.STOP,
    )

    tx = Transaction(
        sender=pre.fund_eoa(),
        to=entry,
        state_gas_reservoir=0,
    )

    measured = flag_store.gas_cost(fork) + delegate_store.gas_cost(fork)

    post = {
        entry: Account(storage={0: 1}),
        target: Account(
            storage={
                0: DELEGATE_VALUE,
                GAS_SLOT: measured,
                FLAG_SLOT: 1,
            },
        ),
    }

    state_test(pre=pre, post=post, tx=tx)
