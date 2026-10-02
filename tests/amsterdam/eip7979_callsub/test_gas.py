"""
Gas costs of CALLSUB (mid, 8), CALLDEST (jumpdest, 1) and RETURNSUB (low, 5).

Each measurement wraps a call sequence in GAS reads and stores the
difference; the subroutine bodies live after the measured code.
"""

from typing import Callable

import pytest
from execution_testing import (
    Account,
    Alloc,
    Bytecode,
    CodeGasMeasure,
    Op,
    StateTestFiller,
    Transaction,
)

from .helpers import TX_GAS_LIMIT
from .spec import Spec, ref_spec_7979

REFERENCE_SPEC_GIT_PATH = ref_spec_7979.git_path
REFERENCE_SPEC_VERSION = ref_spec_7979.version

pytestmark = pytest.mark.valid_from("EIP7979")

PUSH1_GAS = 3


def measured_program(
    measured_for: Callable[[int], Bytecode],
    subroutines_for: Callable[[int], Bytecode],
) -> Bytecode:
    """
    Build ``CodeGasMeasure(measured_for(offset)) + STOP +
    subroutines_for(offset)``, where `offset` is the code offset at which
    the subroutines start.
    """
    probe = CodeGasMeasure(code=measured_for(0), sstore_key=0)
    offset = len(probe) + 1  # + STOP
    assert offset < 256
    measure = CodeGasMeasure(code=measured_for(offset), sstore_key=0)
    assert len(measure) == len(probe)
    return measure + Op.STOP + subroutines_for(offset)


@pytest.mark.parametrize(
    "case,expected_gas",
    [
        pytest.param(
            "call_and_return",
            PUSH1_GAS
            + Spec.CALLSUB_GAS
            + Spec.CALLDEST_GAS
            + Spec.RETURNSUB_GAS,
            id="call_and_return_17",
        ),
        pytest.param(
            "two_levels",
            2
            * (
                PUSH1_GAS
                + Spec.CALLSUB_GAS
                + Spec.CALLDEST_GAS
                + Spec.RETURNSUB_GAS
            ),
            id="two_levels_34",
        ),
        pytest.param("calldest_alone", Spec.CALLDEST_GAS, id="calldest_1"),
        pytest.param(
            "two_calldests_in_subroutine",
            PUSH1_GAS
            + Spec.CALLSUB_GAS
            + 2 * Spec.CALLDEST_GAS
            + Spec.RETURNSUB_GAS,
            id="extra_calldest_18",
        ),
    ],
)
def test_gas_costs(
    state_test: StateTestFiller,
    pre: Alloc,
    case: str,
    expected_gas: int,
) -> None:
    """
    Measure the gas of call sequences.

    The totals match the EIP's worked examples.
    """
    if case == "call_and_return":
        code = measured_program(
            lambda offset: Op.CALLSUB(offset),
            lambda _: Op.CALLDEST + Op.RETURNSUB,
        )
    elif case == "two_levels":
        # sub1 (5 bytes: CALLDEST, PUSH1, CALLSUB, RETURNSUB) at `offset`
        # calls sub2 at `offset + 5`.
        code = measured_program(
            lambda offset: Op.CALLSUB(offset),
            lambda offset: Op.CALLDEST
            + Op.CALLSUB(offset + 5)
            + Op.RETURNSUB
            + Op.CALLDEST
            + Op.RETURNSUB,
        )
    elif case == "calldest_alone":
        code = measured_program(lambda _: Op.CALLDEST, lambda _: Op.STOP)
    else:
        code = measured_program(
            lambda offset: Op.CALLSUB(offset),
            lambda _: Op.CALLDEST + Op.CALLDEST + Op.RETURNSUB,
        )

    contract = pre.deploy_contract(code)
    tx = Transaction(
        sender=pre.fund_eoa(), to=contract, gas_limit=TX_GAS_LIMIT
    )
    post = {contract: Account(storage={0: expected_gas})}
    state_test(pre=pre, post=post, tx=tx)
