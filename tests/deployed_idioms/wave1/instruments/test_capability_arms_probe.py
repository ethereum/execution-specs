"""
Measurement instrument, not a corpus test: for a gas-capped capability
probe at a deployed literal, which side of the literal does each kind of
target land on?

Its FAILURES ARE THE MEASUREMENT. The PASSING param of `test_probe_answer`
names the boolean the probe really derives on that fork. Do not add this
directory to a corpus gate.

Reproduce (from engine/eels):
  ./.venv/bin/fill ../../wave1/instruments --from <Fork> --until <Fork> \
      -k "probe_answer and state_test" --output /tmp/pa -q --tb=no \
      -p no:cacheprovider
"""

import pytest
from execution_testing import Account, Alloc, Op, StateTestFiller, Transaction

SLOT_ANSWER = 0x21

# Capable: one cold storage read, then a non-zero 32-byte answer.
CAPABLE = Op.MSTORE(0, Op.ISZERO(Op.SLOAD(0))) + Op.RETURN(0, 32)
# Legacy halt: solc <=0.4.12 `throw` compiles to INVALID, which burns the
# whole frame and is reported by tracers as "Out of gas".
HALTING = Op.INVALID


def _overrun(n: int) -> object:
    """n cold storage reads, then a non-zero answer. Bounded, not a loop."""
    body = Op.MSTORE(0, 1)
    for k in range(n):
        body += Op.POP(Op.SLOAD(k + 1))
    return body + Op.RETURN(0, 32)


TARGETS = {
    "capable": CAPABLE,
    "halting": HALTING,
    "overrun_1": _overrun(1),
    "overrun_2": _overrun(2),
    "overrun_3": _overrun(3),
    "overrun_4": _overrun(4),
    "overrun_14": _overrun(14),
    "overrun_15": _overrun(15),
}


@pytest.mark.parametrize("answer", [0, 1])
@pytest.mark.parametrize("literal", [5000, 30000])
@pytest.mark.parametrize("target", list(TARGETS))
@pytest.mark.valid_from("Berlin")
def test_probe_answer(
    state_test: StateTestFiller,
    pre: Alloc,
    target: str,
    literal: int,
    answer: int,
) -> None:
    """Probe: the boolean `success && returned_word != 0` yields."""
    callee = pre.deploy_contract(TARGETS[target])
    prober = pre.deploy_contract(
        Op.MSTORE(
            0x20,
            Op.STATICCALL(
                gas=literal, address=callee, ret_offset=0, ret_size=32
            ),
        )
        + Op.SSTORE(
            SLOT_ANSWER,
            Op.AND(Op.MLOAD(0x20), Op.ISZERO(Op.ISZERO(Op.MLOAD(0)))),
        )
        + Op.STOP
    )
    tx = Transaction(to=prober, state_gas_reservoir=0, sender=pre.fund_eoa())
    state_test(
        pre=pre,
        post={prober: Account(storage={SLOT_ANSWER: answer})},
        tx=tx,
    )
