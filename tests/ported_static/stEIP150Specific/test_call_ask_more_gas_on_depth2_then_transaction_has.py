"""
Verify the EIP-150 63/64 clamp at call depth 2: a first-level call receives
its exact (affordable) ask, and its own oversized ask is clamped to 63/64
of what remains in that frame.

Ported from:
state_tests/stEIP150Specific/CallAskMoreGasOnDepth2ThenTransactionHasFiller.json

@manually-enhanced: Do not overwrite. The lower frames return their
observed GAS up the stack instead of SSTORE-ing it (the ported lower-frame
gas snapshots are EIP-8037 state-gas traps), and both expectations are
derived from the fork: the depth-1 frame sees exactly its asked budget,
the depth-2 frame sees `base - base // 64` of the depth-1 remainder.
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

FLAG_SLOT = 0x0
DEPTH2_GAS_SLOT = 0x1
DEPTH1_GAS_SLOT = 0x2

# The ported depth-1 budget: affordable, so it is forwarded exactly.
CALLER_GAS = 0x30D40
# The ported depth-2 ask: above anything the depth-1 frame can hold, so
# the 63/64 clamp decides what the depth-2 frame receives.
ASK_GAS = 0x927C0


@pytest.mark.ported_from(
    [
        "state_tests/stEIP150Specific/CallAskMoreGasOnDepth2ThenTransactionHasFiller.json"  # noqa: E501
    ],
)
@pytest.mark.valid_from("Berlin")
def test_call_ask_more_gas_on_depth2_then_transaction_has(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """A depth-2 call asking above the frame budget gets 63/64 of it."""
    # Depth 2: returns the gas it observed on entry.
    gas_return_contract = pre.deploy_contract(
        code=Op.MSTORE(0, Op.GAS, new_memory_size=0x20) + Op.RETURN(0, 0x20),
    )

    # Depth 1: records its own entry gas, then asks depth 2 for more gas
    # than this frame holds; both observations return to the top frame.
    entry_snapshot = Op.MSTORE(0x20, Op.GAS, new_memory_size=0x40)
    depth2_call = Op.CALL(
        gas=ASK_GAS,
        address=gas_return_contract,
        ret_size=0x20,
        address_warm=False,
        account_new=False,
        new_memory_size=0x40,
        old_memory_size=0x40,
    )
    caller = pre.deploy_contract(
        code=entry_snapshot + depth2_call + Op.RETURN(0, 0x40),
    )

    # Top frame: forwards the exact (affordable) depth-1 budget and stores
    # the success flag plus both returned observations.
    entry = pre.deploy_contract(
        code=Op.SSTORE(
            key=FLAG_SLOT,
            value=Op.CALL(gas=CALLER_GAS, address=caller, ret_size=0x40),
        )
        + Op.SSTORE(key=DEPTH2_GAS_SLOT, value=Op.MLOAD(0))
        + Op.SSTORE(key=DEPTH1_GAS_SLOT, value=Op.MLOAD(0x20)),
    )

    tx = Transaction(
        sender=pre.fund_eoa(),
        to=entry,
        state_gas_reservoir=0,
    )

    # Depth 1 received exactly CALLER_GAS; its snapshot reads it minus the
    # GAS opcode itself. The depth-2 base is what remains after the
    # snapshot and the call's own costs, clamped by EIP-150.
    depth1_observed = CALLER_GAS - Op.GAS.gas_cost(fork)
    base = (
        CALLER_GAS - entry_snapshot.gas_cost(fork) - depth2_call.gas_cost(fork)
    )
    assert 0 < base < ASK_GAS, "the 63/64 clamp must apply at depth 2"
    forwarded = base - base // 64
    depth2_observed = forwarded - Op.GAS.gas_cost(fork)

    post = {
        entry: Account(
            storage={
                FLAG_SLOT: 1,
                DEPTH2_GAS_SLOT: depth2_observed,
                DEPTH1_GAS_SLOT: depth1_observed,
            },
        ),
    }

    state_test(pre=pre, post=post, tx=tx)
