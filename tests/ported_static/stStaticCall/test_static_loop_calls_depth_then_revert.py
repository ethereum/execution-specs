"""
Ping-pong STATICCALLs between two contracts until the innermost one fails.

Ported from:
state_tests/stStaticCall/static_LoopCallsDepthThenRevertFiller.json

@manually-enhanced: Do not overwrite. Target calls A, not itself.
"""

import pytest
from execution_testing import (
    Account,
    Alloc,
    Op,
    StateTestFiller,
    Transaction,
)

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"

RESERVED_GAS = 100_000


@pytest.mark.ported_from(
    ["state_tests/stStaticCall/static_LoopCallsDepthThenRevertFiller.json"],
)
@pytest.mark.valid_from("Cancun")
def test_static_loop_calls_depth_then_revert(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """
    Verify the caller survives a STATICCALL loop that runs until it fails.

    Each frame returns the number of frames below it that returned, plus
    one, so the caller sees that the loop went A -> B -> A at least.
    """
    count_and_return = Op.MSTORE(0, Op.ADD(Op.MLOAD(0), 1)) + Op.RETURN(0, 32)
    b = pre.deploy_contract(
        code=Op.POP(Op.STATICCALL(address=Op.CALLER, ret_size=32))
        + count_and_return
    )
    a = pre.deploy_contract(
        code=Op.POP(Op.STATICCALL(address=b, ret_size=32)) + count_and_return
    )
    target = pre.deploy_contract(
        code=Op.SSTORE(
            0,
            Op.CALL(gas=Op.SUB(Op.GAS, RESERVED_GAS), address=a, ret_size=32),
        )
        + Op.SSTORE(2, Op.GT(Op.MLOAD(0), 2))
        + Op.SSTORE(1, 1)
        + Op.STOP
    )

    tx = Transaction(sender=pre.fund_eoa(), to=target)

    post = {target: Account(storage={0: 1, 1: 1, 2: 1})}

    state_test(pre=pre, post=post, tx=tx)
