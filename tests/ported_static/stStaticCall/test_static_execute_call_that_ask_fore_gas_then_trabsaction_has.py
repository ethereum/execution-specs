"""
Verify a STATICCALL that asks for more gas than is available is clamped to
63/64 of the remaining gas (EIP-150), across callees that succeed, out-of-gas,
and violate the static context.

Ported from:
state_tests/stStaticCall/static_ExecuteCallThatAskForeGasThenTrabsactionHasFiller.json

@manually-enhanced: Do not overwrite. An outer call caps the caller frame so
the callee budgets are fork-independent; the flag slot is pre-written so the
post-call store is a cheap dirty-warm write affordable from the 1/64
retention even under EIP-8037; distinct flag values discriminate success,
callee failure, and caller OOG (the ported {1: 0} expectation could not).
"""

import pytest
from execution_testing import (
    Account,
    Alloc,
    Fork,
    StateTestFiller,
    Transaction,
)
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"

FLAG_SLOT = 0x1
# Pre-written sentinel: if the caller frame dies after the call, the slot
# keeps this value instead of reverting to an ambiguous zero.
FLAG_PREWRITE = 0xFF
# Stored flag = 0x10 + STATICCALL result: 0x11 success, 0x10 failure.
FLAG_BASE = 0x10

# Far larger than any gas the caller frame can hold, so the EIP-150 clamp
# (not the operand) decides what the callee receives.
OVERSIZED_GAS_ASK = 2**61
# The outer call pins the caller frame's budget: large enough to cover the
# caller's own cold flag store (~111k under EIP-8037) and the successful
# callee, small enough that the looping callee (~6.5M) still runs out.
CALLER_GAS = 1_000_000


@pytest.mark.ported_from(
    [
        "state_tests/stStaticCall/static_ExecuteCallThatAskForeGasThenTrabsactionHasFiller.json"  # noqa: E501
    ],
)
@pytest.mark.valid_from("Byzantium")
@pytest.mark.parametrize(
    "callee_kind, callee_succeeds",
    [
        pytest.param("mstore", True, id="d0"),
        pytest.param("extcodesize_loop", False, id="d1"),
        pytest.param("sstore_static_violation", False, id="d2"),
    ],
)
def test_static_execute_call_that_ask_fore_gas_then_trabsaction_has(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    callee_kind: str,
    callee_succeeds: bool,
) -> None:
    """A STATICCALL asking for more gas than available gets 63/64 of it."""
    if callee_kind == "mstore":
        # Trivial: succeeds well within the forwarded gas.
        callee = pre.deploy_contract(
            code=Op.MSTORE(offset=0x1, value=0x1) + Op.STOP
        )
    elif callee_kind == "extcodesize_loop":
        # 50000 EXTCODESIZE iterations (~6.5M gas): must exhaust the
        # clamped forwarded gas, proving the callee did not receive the
        # oversized ask.
        callee = pre.deploy_contract(
            code=Op.JUMPDEST
            + Op.JUMPI(
                pc=0x1C,
                condition=Op.ISZERO(Op.LT(Op.MLOAD(offset=0x80), 0xC350)),
            )
            + Op.POP(Op.EXTCODESIZE(address=0x1))
            + Op.MSTORE(offset=0x80, value=Op.ADD(Op.MLOAD(offset=0x80), 0x1))
            + Op.JUMP(pc=0x0)
            + Op.JUMPDEST
            + Op.STOP,
        )
    else:
        # SSTORE inside a static context: exceptional halt regardless of
        # gas.
        callee = pre.deploy_contract(
            code=Op.SSTORE(key=0x1, value=0x1) + Op.STOP
        )

    # The flag slot is written twice: the pre-write pays the cold/state
    # cost with the full budget, so the post-call store is a dirty-warm
    # write the 1/64 retention can always afford.
    caller = pre.deploy_contract(
        code=Op.SSTORE(key=FLAG_SLOT, value=FLAG_PREWRITE)
        + Op.SSTORE(
            key=FLAG_SLOT,
            value=Op.ADD(
                FLAG_BASE,
                Op.STATICCALL(gas=OVERSIZED_GAS_ASK, address=callee),
            ),
        )
        + Op.STOP,
    )

    # The outer call pins the caller frame's gas so the callee budgets do
    # not depend on the tx gas limit; the clamp must always bite.
    assert CALLER_GAS < OVERSIZED_GAS_ASK, "the 63/64 clamp must apply"
    entry = pre.deploy_contract(
        code=Op.SSTORE(key=0x0, value=Op.CALL(gas=CALLER_GAS, address=caller))
        + Op.STOP,
    )

    tx = Transaction(
        sender=pre.fund_eoa(),
        to=entry,
        state_gas_reservoir=0,
    )

    post = {
        entry: Account(storage={0: 1}),
        caller: Account(
            storage={FLAG_SLOT: FLAG_BASE + (1 if callee_succeeds else 0)},
        ),
    }

    state_test(pre=pre, post=post, tx=tx)
