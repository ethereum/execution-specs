"""
A non-static frame A STATICCALLs B, which STATICCALLs A back.

Ported from:
state_tests/stStaticCall/static_ABAcalls0Filler.json
state_tests/stStaticCall/static_ABAcalls1Filler.json
state_tests/stStaticCall/static_ABAcalls2Filler.json
state_tests/stStaticCall/static_ABAcalls3Filler.json
state_tests/stStaticCall/static_ABAcallsSuicide0Filler.json

@manually-enhanced: Do not overwrite. Merged; B calls back via CALLER.
"""

import pytest
from execution_testing import (
    Account,
    Address,
    Alloc,
    Bytecode,
    Hash,
    Op,
    StateTestFiller,
    Transaction,
)

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"

TX_VALUE = 100_000
RESULT_SLOT = 1
RESULT_SENTINEL = 0xFF
COUNTER_SLOT = 0


def frame_code(
    body: str,
    writes: str,
    call_gas: Bytecode | int,
    callee: Bytecode | Address,
) -> Bytecode:
    """Return the code of one side of the A <-> B ping-pong."""
    store = Op.SSTORE if writes == "storage" else Op.MSTORE
    load = Op.SLOAD if writes == "storage" else Op.MLOAD
    call = Op.STATICCALL(gas=call_gas, address=callee)
    if body == "result":
        return store(RESULT_SLOT, call)
    if body == "result_plus_one":
        return store(RESULT_SLOT, Op.ADD(1, call))
    if body == "counter":
        return store(COUNTER_SLOT, Op.ADD(load(COUNTER_SLOT), 1)) + call
    raise ValueError(f"Unknown body: {body}")


@pytest.mark.ported_from(
    [
        "state_tests/stStaticCall/static_ABAcalls0Filler.json",
        "state_tests/stStaticCall/static_ABAcalls1Filler.json",
        "state_tests/stStaticCall/static_ABAcalls2Filler.json",
        "state_tests/stStaticCall/static_ABAcalls3Filler.json",
        "state_tests/stStaticCall/static_ABAcallsSuicide0Filler.json",
    ],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize("writes", ["storage", "memory"])
@pytest.mark.parametrize(
    "body, relative_gas, self_destruct",
    [
        pytest.param("result", False, False, id="acalls0"),
        pytest.param("result", True, False, id="acalls1"),
        pytest.param("counter", True, False, id="acalls2"),
        pytest.param("result", False, True, id="acalls_suicide0"),
    ],
)
def test_static_ab_acalls(
    state_test: StateTestFiller,
    pre: Alloc,
    body: str,
    relative_gas: bool,
    self_destruct: bool,
    writes: str,
) -> None:
    """
    Verify only the outermost, non-static A frame keeps its writes.

    Every frame below it is static, so B's writes and A's re-entered
    writes fail. With `self_destruct`, A sends its balance to B after
    the call.
    """
    a_gas: Bytecode | int = (
        Op.SUB(Op.GAS, 100_000) if relative_gas else 100_000
    )
    b_gas: Bytecode | int = Op.SUB(Op.GAS, 100_000) if relative_gas else 50_000
    b_body = "result_plus_one" if body == "result" else body
    b = pre.deploy_contract(
        code=frame_code(b_body, writes, b_gas, Op.CALLER) + Op.STOP
    )
    a_code = frame_code(body, writes, a_gas, b)
    if self_destruct:
        a_code += Op.SELFDESTRUCT(b)
    seeded = body == "result" and writes == "storage"
    a = pre.deploy_contract(
        code=a_code + Op.STOP,
        storage={RESULT_SLOT: RESULT_SENTINEL} if seeded else {},
    )
    entry = pre.deploy_contract(
        code=Op.SSTORE(
            0, Op.CALL(address=Op.CALLDATALOAD(0), value=Op.CALLVALUE)
        )
        + Op.SSTORE(1, 1)
        + Op.STOP
    )

    tx = Transaction(
        sender=pre.fund_eoa(),
        to=entry,
        data=Hash(a, left_padding=True),
        value=TX_VALUE,
    )

    a_storage: dict[int, int] = {}
    if writes == "storage":
        if body == "counter":
            a_storage = {COUNTER_SLOT: 1}
        else:
            a_storage = {RESULT_SLOT: 0}
    post = {
        entry: Account(storage={0: 1, 1: 1}),
        a: Account(
            storage=a_storage, balance=0 if self_destruct else TX_VALUE
        ),
        b: Account(storage={}, balance=TX_VALUE if self_destruct else 0),
    }

    state_test(pre=pre, post=post, tx=tx)
