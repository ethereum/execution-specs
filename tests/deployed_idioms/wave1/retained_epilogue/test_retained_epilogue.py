"""
Archetype 4: retained-gas epilogue survival (the 63/64 rule).

`call(gas(), ...)` forwards all-but-1/64:
`gas = min(requested, max_message_call_gas(gas_left - memory_cost - extra_gas))`
with `max_message_call_gas(g) = g - g // 64` (amsterdam/vm/gas.py:861).

A caller that forwards everything still depends on the retained `avail // 64`
covering its own post-call work -- releasing a reentrancy lock, emitting,
recording a result. **No gas literal appears anywhere in this shape**, which
is exactly why a frozen-budget test cannot catch it: the budget is implicit
in the retention fraction.

Witnessed by L4's `retention-6364` probe at 245,595 mainnet addresses from
183 source files, FP 0/18 hand-validated; and by L5 at 239 transactions that
commit *only* because of the rule.

Sensitive to two independent rules at once: the retention divisor, and the
cost of the epilogue itself.
"""

import pytest
from execution_testing import (
    Account,
    Alloc,
    Fork,
    GasConsumer,
    Op,
    StateTestFiller,
    Storage,
    Transaction,
)

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


@pytest.mark.valid_from("Berlin")
def test_retained_gas_covers_post_call_store(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    Test the gas retained by the 63/64 rule still funds the caller's
    epilogue after a child consumes everything it was given.

    The child is bytecode that runs out of gas, so it consumes the entire
    forwarded allowance and returns 0. The caller must still complete a
    fresh storage write from the `avail // 64` it kept back. The
    transaction pins `state_gas_reservoir=0`, so the epilogue's state
    charge has to come out of that retained execution gas rather than a
    reservoir.
    """
    burner = pre.deploy_contract(GasConsumer(gas=None, fork=fork))

    caller_storage = Storage()
    caller = pre.deploy_contract(
        Op.POP(Op.CALL(gas=Op.GAS, address=burner))
        + Op.SSTORE(caller_storage.store_next(1, "epilogue_ran"), 1)
        + Op.STOP
    )

    tx = Transaction(to=caller, state_gas_reservoir=0, sender=pre.fund_eoa())
    state_test(pre=pre, post={caller: Account(storage=caller_storage)}, tx=tx)
