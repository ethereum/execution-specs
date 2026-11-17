"""
Measure the gas of a value-1 CALL / CALLCODE to an EOA with a non-zero
balance, from a caller that can and one that cannot afford the value.

Ported from:
state_tests/stNonZeroCallsTest/NonZeroValue_CALL_ToNonNonZeroBalanceFiller.json
state_tests/stNonZeroCallsTest/NonZeroValue_CALLCODE_ToNonNonZeroBalanceFiller.json

@manually-enhanced: Do not overwrite. Two fillers parametrized by opcode.
The fillers' caller had no balance, so the value-1 call always failed;
that case is kept as `caller_balance=0` and a funded caller is added. The
call's gas is measured with CodeGasMeasure, and the call success flag is
stored inside the measured window (a call that fails for lack of balance
costs the same gas as one that succeeds into an EOA).
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

CALL_VALUE = 1
FORWARDED_GAS = 0xEA60
GAS_SLOT = 0x64
SUCCESS_SLOT = 0x1


@pytest.mark.ported_from(
    [
        "state_tests/stNonZeroCallsTest/NonZeroValue_CALL_ToNonNonZeroBalanceFiller.json",  # noqa: E501
        "state_tests/stNonZeroCallsTest/NonZeroValue_CALLCODE_ToNonNonZeroBalanceFiller.json",  # noqa: E501
    ],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "caller_balance",
    [
        pytest.param(1000, id="funded_caller"),
        pytest.param(0, id="caller_without_balance"),
    ],
)
@pytest.mark.parametrize(
    "opcode",
    [
        pytest.param(Op.CALL, id="call"),
        pytest.param(Op.CALLCODE, id="callcode"),
    ],
)
def test_non_zero_value_call(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    opcode: Op,
    caller_balance: int,
) -> None:
    """Measure a value-1 `opcode` call to an EOA with a non-zero balance."""
    succeeds = caller_balance >= CALL_VALUE
    callee = pre.fund_eoa()

    store_code = Op.SSTORE(
        SUCCESS_SLOT,
        opcode(
            gas=FORWARDED_GAS,
            address=callee,
            value=CALL_VALUE,
            value_transfer=True,
        ),
        key_warm=False,
        original_value=0,
        new_value=1 if succeeds else 0,
    )
    caller = pre.deploy_contract(
        code=CodeGasMeasure(code=store_code, sstore_key=GAS_SLOT),
        balance=caller_balance,
    )

    tx = Transaction(
        sender=pre.fund_eoa(),
        to=caller,
        state_gas_reservoir=0,
    )

    # Succeeding or not, the callee runs no code and the stipend returns.
    measured = store_code.gas_cost(fork) - fork.gas_costs().CALL_STIPEND
    # Only a successful CALL moves the value; CALLCODE sends it to itself.
    moved = CALL_VALUE if succeeds and opcode == Op.CALL else 0

    post = {
        caller: Account(
            storage={GAS_SLOT: measured, SUCCESS_SLOT: int(succeeds)},
            balance=caller_balance - moved,
        ),
        callee: Account(balance_change=moved),
    }

    state_test(pre=pre, post=post, tx=tx)
