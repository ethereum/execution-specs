"""
Archetype 7: stipend-funded fallback survival.

`transfer()`/`send()` deliver exactly the 2,300-gas stipend, and only on a
value-bearing call (`call_stipend = ZERO if value == 0 else call_stipend`,
amsterdam/vm/gas.py:838). A recipient's fallback must complete inside it.

This is the class with the strongest historical precedent: EIP-1884 raised
SLOAD 200 -> 800 and broke deployed fallbacks on mainnet. L4 established
that EIP-1884 has **zero** tests from any angle -- no `istanbul/eip1884*`
directory exists, and `generators.py:524` refuses pre-Berlin gas tests.

The stipend is not a budget we chose; it is the protocol's own constant, so
this test needs no deployed-contract citation to be realistic. Margin is
tiny by construction: one cold SLOAD is 2,100 (COLD_STORAGE_ACCESS,
unchanged since Berlin) plus the key push and a POP, leaving under 200 gas.
"""

import pytest
from execution_testing import Account, Alloc, Op, StateTestFiller, Storage, Transaction

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


@pytest.mark.valid_from("Berlin")
def test_stipend_covers_cold_sload_fallback(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """
    Test a value-bearing call with no forwarded gas still lets the
    recipient read one cold storage slot.

    The recipient receives exactly the stipend. Success is observed from
    the caller's side -- the recipient cannot SSTORE a marker, because the
    EIP-2200 sentry (`check_gas(max(access_cost, CALL_STIPEND + 1))`,
    amsterdam/.../storage.py:104) makes an SSTORE on a stipend-funded frame
    impossible by construction. So the caller records CALL's return value.
    """
    recipient_code = Op.POP(Op.SLOAD(0)) + Op.STOP
    recipient = pre.deploy_contract(recipient_code)

    caller_storage = Storage()
    caller = pre.deploy_contract(
        Op.SSTORE(
            caller_storage.store_next(1, "stipend_sufficed"),
            Op.CALL(gas=0, address=recipient, value=1),
        )
        + Op.STOP,
        balance=10,
    )

    tx = Transaction(to=caller, state_gas_reservoir=0, sender=pre.fund_eoa())
    state_test(pre=pre, post={caller: Account(storage=caller_storage)}, tx=tx)
