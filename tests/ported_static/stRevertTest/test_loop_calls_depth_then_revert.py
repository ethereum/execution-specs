"""
Verify a mutual CALL or DELEGATECALL recursion that terminates by gas
exhaustion: two contracts increment a counter and call each other until
the EIP-150 63/64 attenuation starves the deepest frame, which halts
before its own store while every ancestor's increment persists.

Ported from:
state_tests/stRevertTest/LoopCallsDepthThenRevertFiller.json
state_tests/stRevertTest/LoopDelegateCallsDepthThenRevertFiller.json

@manually-enhanced: Do not overwrite. The reached depth is bounded by the
fixed gas budget (not the 1024 depth limit), so the frame counts are
pinned per gas-schedule era: EIP-8037/EIP-2780 shift the attenuation on
Amsterdam.
"""

import pytest
from execution_testing import (
    Account,
    Address,
    Alloc,
    Fork,
    StateTestFiller,
    Transaction,
)
from execution_testing.vm import Bytecode, Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"

# The recursion depth is a function of this budget via EIP-150's 63/64
# forwarding rule. Changing it changes the pinned frame counts.
GAS_BUDGET = 10_000_000


def loop_code(opcode: Op, partner: Address | Bytecode) -> Bytecode:
    """Increment the context counter, then recurse into the partner."""
    return (
        Op.SSTORE(key=0x0, value=Op.ADD(Op.SLOAD(key=0x0), 0x1))
        + opcode(address=partner)
        + Op.STOP
    )


@pytest.mark.ported_from(
    [
        "state_tests/stRevertTest/LoopCallsDepthThenRevertFiller.json",
        "state_tests/stRevertTest/LoopDelegateCallsDepthThenRevertFiller.json",
    ],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "opcode",
    [
        pytest.param(Op.CALL, id="loop_calls_depth_then_revert"),
        pytest.param(
            Op.DELEGATECALL, id="loop_delegate_calls_depth_then_revert"
        ),
    ],
)
def test_loop_calls_depth_then_revert(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    opcode: Op,
) -> None:
    """
    Only the gas-starved deepest frame of a call loop fails.

    The partner calls back to CALLER, or for DELEGATECALL to ADDRESS,
    which is the entry contract in every frame.
    """
    back_edge = Op.CALLER if opcode == Op.CALL else Op.ADDRESS
    pong = pre.deploy_contract(code=loop_code(opcode, back_edge))
    ping = pre.deploy_contract(code=loop_code(opcode, pong))

    sender = pre.fund_eoa()
    tx = Transaction(
        sender=sender,
        to=ping,
        gas_limit=GAS_BUDGET,
    )

    # Completed frames under GAS_BUDGET, pinned per gas-schedule era:
    # EIP-8037's state gas for the first stores trims one frame off the
    # depth the 63/64 attenuation allows. DELEGATECALL keeps the storage
    # context, so every frame increments the entry contract's counter.
    if opcode == Op.CALL:
        if fork.is_eip_enabled(8037):
            ping_frames, pong_frames = 192, 192
        else:
            ping_frames, pong_frames = 193, 192
    else:
        ping_frames = 385 if fork.is_eip_enabled(8037) else 386
        pong_frames = 0

    post = {
        ping: Account(storage={0: ping_frames}),
        pong: Account(storage={0: pong_frames}),
    }

    state_test(pre=pre, post=post, tx=tx)
