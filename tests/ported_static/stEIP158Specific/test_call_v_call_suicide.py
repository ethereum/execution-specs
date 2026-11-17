"""
Measure a CALL to a contract that SELFDESTRUCTs to an alive account.

Ported from:
state_tests/stEIP158Specific/CALL_OneVCallSuicideFiller.json
state_tests/stEIP158Specific/CALL_OneVCallSuicide2Filler.json
state_tests/stEIP158Specific/CALL_ZeroVCallSuicideFiller.json

@manually-enhanced: Do not overwrite. The measured slot captures the
regular gas of a CALL to a cold contract that SELFDESTRUCTs to either
its caller (warm) or a cold, alive beneficiary: a contract, or an account
alive only through its nonce (EIP-161). EIP-8038 reprices the
cold account accesses and the CALL value transfer; the beneficiary is
alive so there is no new-account write. Each delta is the fork's
constant less Cancun's, exactly 0 before EIP-8038.
"""

import pytest
from execution_testing import (
    Account,
    Address,
    Alloc,
    StateTestFiller,
    Transaction,
)
from execution_testing.forks import Cancun, Fork
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"

INITIAL_BALANCE = 100


@pytest.mark.ported_from(
    [
        "state_tests/stEIP158Specific/CALL_OneVCallSuicideFiller.json",
        "state_tests/stEIP158Specific/CALL_OneVCallSuicide2Filler.json",
        "state_tests/stEIP158Specific/CALL_ZeroVCallSuicideFiller.json",
    ],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "call_value, beneficiary_kind, cancun_gas",
    [
        pytest.param(1, "caller", 14336, id="one_v_call_suicide"),
        pytest.param(
            1,
            "nonce_only",
            16937,
            id="one_v_call_suicide2",
            marks=pytest.mark.pre_alloc_mutable,
        ),
        pytest.param(1, "contract", 16937, id="one_v_call_suicide2_contract"),
        pytest.param(0, "caller", 7636, id="zero_v_call_suicide"),
    ],
)
def test_call_v_call_suicide(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    call_value: int,
    beneficiary_kind: str,
    cancun_gas: int,
) -> None:
    """Store the gas spent around the CALL in slot 100."""
    gas_costs = fork.gas_costs()
    cold_account_delta = (
        gas_costs.COLD_ACCOUNT_ACCESS - Cancun.gas_costs().COLD_ACCOUNT_ACCESS
    )
    call_value_delta = gas_costs.CALL_VALUE - Cancun.gas_costs().CALL_VALUE
    sender = pre.fund_eoa()

    post: dict[Address, Account] = {}
    if beneficiary_kind == "caller":
        destructor = pre.deploy_contract(code=Op.SELFDESTRUCT(Op.CALLER))
        cold_accounts = 1
        caller_balance = INITIAL_BALANCE
    else:
        beneficiary: Address
        if beneficiary_kind == "nonce_only":
            beneficiary = pre.fund_eoa(amount=0, nonce=1)
        else:
            beneficiary = pre.deploy_contract(code=Op.STOP)
        destructor = pre.deploy_contract(code=Op.SELFDESTRUCT(beneficiary))
        cold_accounts = 2
        caller_balance = INITIAL_BALANCE - call_value
        post[beneficiary] = Account(balance=call_value)

    caller = pre.deploy_contract(
        code=Op.MSTORE(0, Op.GAS)
        + Op.POP(Op.CALL(gas=60_000, address=destructor, value=call_value))
        + Op.SSTORE(100, Op.SUB(Op.MLOAD(0), Op.GAS)),
        balance=INITIAL_BALANCE,
    )

    measured = cancun_gas + cold_accounts * cold_account_delta
    if call_value:
        measured += call_value_delta
    post[destructor] = Account(storage={}, balance=0)
    post[caller] = Account(storage={100: measured}, balance=caller_balance)

    tx = Transaction(sender=sender, to=caller)
    state_test(pre=pre, post=post, tx=tx)
