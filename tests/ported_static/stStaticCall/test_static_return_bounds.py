"""
STATICCALL contracts that RETURN with huge offsets and sizes.

Ported from:
state_tests/stStaticCall/static_RETURN_BoundsFiller.json
state_tests/stStaticCall/static_RETURN_BoundsOOGFiller.json

@manually-enhanced: Do not overwrite. Merged; every bound is now called.
"""

import pytest
from execution_testing import (
    Account,
    Alloc,
    Bytecode,
    Op,
    StateTestFiller,
    Transaction,
)

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"

HUGE_VALUES = [
    0xFFFFFFF,
    0xFFFFFFFF,
    0xFFFFFFFFFFFFFFFF,
    0xFFFFFFFFFFFFFFFFFFFFFFFFFFF,
    2**256 - 1,
]
RETURN_BOUNDS = (
    [(0, 0)]
    + [(value, 0) for value in HUGE_VALUES]
    + [(0, value) for value in HUGE_VALUES]
    + [(value, value) for value in HUGE_VALUES]
)
CALL_GAS = 100_000
TX_GAS = 15_000_000
SENTINEL = 0xFF
OUT_OF_GAS_MEMORY = Op.SHA3(offset=0, size=0x2FFFFF)


@pytest.mark.ported_from(
    [
        "state_tests/stStaticCall/static_RETURN_BoundsFiller.json",
        "state_tests/stStaticCall/static_RETURN_BoundsOOGFiller.json",
    ],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize("then_out_of_gas", [False, True])
def test_static_return_bounds(
    state_test: StateTestFiller,
    pre: Alloc,
    then_out_of_gas: bool,
) -> None:
    """
    Verify a RETURN of zero bytes succeeds at any offset, and one of a huge
    size fails, and that a later out-of-gas reverts every result.

    Slot `n` holds the result of calling the `n`-th bound and is seeded
    with a sentinel, so a stored 0 is observable.
    """
    code = Bytecode()
    for slot, (offset, size) in enumerate(RETURN_BOUNDS, start=1):
        callee = pre.deploy_contract(code=Op.RETURN(offset, size))
        code += Op.SSTORE(slot, Op.STATICCALL(gas=CALL_GAS, address=callee))
    if then_out_of_gas:
        code += OUT_OF_GAS_MEMORY
    seeded: dict = dict.fromkeys(range(1, len(RETURN_BOUNDS) + 1), SENTINEL)
    target = pre.deploy_contract(code=code + Op.STOP, storage=seeded)

    tx = Transaction(sender=pre.fund_eoa(), to=target, gas_limit=TX_GAS)

    if then_out_of_gas:
        storage = seeded
    else:
        storage = {
            slot: int(size == 0)
            for slot, (_, size) in enumerate(RETURN_BOUNDS, start=1)
        }
    post = {target: Account(storage=storage)}

    state_test(pre=pre, post=post, tx=tx)
