"""
Verify a mutual DELEGATECALL recursion that terminates by gas
exhaustion: both contracts' code increments the entry contract's counter
(the storage context never changes) until the EIP-150 63/64 attenuation
starves the deepest frame, which halts before its own store while every
ancestor's increment persists.

Ported from:
state_tests/stRevertTest/LoopDelegateCallsDepthThenRevertFiller.json

@manually-enhanced: Do not overwrite. The reached depth is bounded by the
fixed gas budget (not the 1024 depth limit), so the frame count is
pinned per gas-schedule era: EIP-8037/EIP-2780 shift the attenuation on
Amsterdam. One address literal remains to break the reference cycle.
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
# forwarding rule. Changing it changes the pinned frame count.
GAS_BUDGET = 10_000_000
# Fixed address for the second contract: it must be known before the
# first contract's code (which delegate-calls it) can be built.
PONG_ADDRESS = Address(0xF798CB78490DA31DFACDCD1F2B3FB1948BB2B228)


def loop_code(partner: Address) -> Bytecode:
    """Increment the context counter, then recurse into the partner."""
    return (
        Op.SSTORE(key=0x0, value=Op.ADD(Op.SLOAD(key=0x0), 0x1))
        + Op.DELEGATECALL(address=partner)
        + Op.STOP
    )


@pytest.mark.ported_from(
    ["state_tests/stRevertTest/LoopDelegateCallsDepthThenRevertFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_loop_delegate_calls_depth_then_revert(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """Only the gas-starved deepest frame of a delegate loop fails."""
    ping = pre.deploy_contract(code=loop_code(PONG_ADDRESS))
    pong = pre.deploy_contract(code=loop_code(ping), address=PONG_ADDRESS)

    sender = pre.fund_eoa()
    tx = Transaction(
        sender=sender,
        to=ping,
        gas_limit=GAS_BUDGET,
    )

    # Completed frames under GAS_BUDGET, pinned per gas-schedule era:
    # every frame increments the entry contract's counter because
    # DELEGATECALL keeps the storage context. The partner's own storage
    # is never touched. EIP-8037's state gas for the first store shifts
    # the depth the 63/64 attenuation allows.
    frames = 385 if fork.is_eip_enabled(8037) else 386

    post = {
        ping: Account(storage={0: frames}),
        pong: Account(storage={}),
    }

    state_test(pre=pre, post=post, tx=tx)
