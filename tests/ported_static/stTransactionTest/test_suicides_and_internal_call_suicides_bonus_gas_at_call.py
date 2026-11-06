"""
Call a self-destructing callee with zero gas, then self-destruct to it.

With a value-bearing call the callee runs on the 2300 stipend, which
cannot pay for its SELFDESTRUCT; without value it does not run at all.
The callee holds 1 wei so its SELFDESTRUCT would be observable.

Ported from:
state_tests/stTransactionTest/SuicidesAndInternalCallSuicidesBonusGasAtCallFiller.json
state_tests/stTransactionTest/SuicidesAndInternalCallSuicidesBonusGasAtCallFailedFiller.json
"""

import pytest
from execution_testing import (
    Account,
    Address,
    Alloc,
    StateTestFiller,
    Transaction,
)
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"

CALLEE_BENEFICIARY = Address(0x1)


@pytest.mark.ported_from(
    [
        "state_tests/stTransactionTest/SuicidesAndInternalCallSuicidesBonusGasAtCallFiller.json",  # noqa: E501
        "state_tests/stTransactionTest/SuicidesAndInternalCallSuicidesBonusGasAtCallFailedFiller.json",  # noqa: E501
    ],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "call_value",
    [
        pytest.param(1, id="bonus_gas_at_call"),
        pytest.param(0, id="bonus_gas_at_call_failed"),
    ],
)
def test_suicides_and_internal_call_suicides_bonus_gas_at_call(
    state_test: StateTestFiller,
    pre: Alloc,
    call_value: int,
) -> None:
    """The callee's SELFDESTRUCT never runs; it receives the caller's."""
    sender = pre.fund_eoa()
    callee_code = Op.SELFDESTRUCT(address=CALLEE_BENEFICIARY) + Op.STOP
    callee = pre.deploy_contract(code=callee_code, balance=1)
    caller_code = (
        Op.POP(Op.CALL(gas=0, address=callee, value=call_value))
        + Op.SELFDESTRUCT(address=callee)
        + Op.STOP
    )
    caller = pre.deploy_contract(code=caller_code, balance=10)

    tx = Transaction(sender=sender, to=caller, value=10)

    post = {
        CALLEE_BENEFICIARY: Account.NONEXISTENT,
        callee: Account(code=callee_code, balance=1 + 20),
        caller: Account(code=caller_code, balance=0),
    }

    state_test(pre=pre, post=post, tx=tx)
