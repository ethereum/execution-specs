"""
Verify the EIP-150 63/64 clamp at call depth 2 when the calls also expand
memory: a first-level call receives its exact (affordable) ask, and its own
oversized ask is clamped to 63/64 of what remains after the memory
expansion.

Ported from:
state_tests/stMemExpandingEIP150Calls/CallAskMoreGasOnDepth2ThenTransactionHasWithMemExpandingCallsFiller.json

@manually-enhanced: Do not overwrite. The lower frames return their
observed GAS up the stack instead of SSTORE-ing it (the ported lower-frame
gas snapshots are EIP-8037 state-gas traps); every expectation is derived
from the fork, including the top frame's entry snapshot, which pins the
transaction intrinsic cost.
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
ENTRY_GAS_SLOT = 0x3

# The ported depth-1 budget: affordable, so it is forwarded exactly.
CALLER_GAS = 0x30D40
# The ported depth-2 ask: above anything the depth-1 frame can hold, so
# the 63/64 clamp decides what the depth-2 frame receives.
ASK_GAS = 0x927C0
# The ported calls' argument window, driving the memory expansion.
MEM_OFFSET = 0xFF
MEM_SIZE = 0xFF


@pytest.mark.ported_from(
    [
        "state_tests/stMemExpandingEIP150Calls/CallAskMoreGasOnDepth2ThenTransactionHasWithMemExpandingCallsFiller.json"  # noqa: E501
    ],
)
@pytest.mark.valid_from("Berlin")
def test_call_ask_more_gas_on_depth2_then_transaction_has_with_mem_expanding_calls(  # noqa: E501
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """A depth-2 memory-expanding call is clamped to 63/64 of its frame."""
    # Depth 2: returns the gas it observed on entry.
    gas_return_contract = pre.deploy_contract(
        code=Op.MSTORE(0, Op.GAS, new_memory_size=0x20) + Op.RETURN(0, 0x20),
    )

    # Depth 1: records its own entry gas, then asks depth 2 for more gas
    # than this frame holds, expanding memory through the args window;
    # both observations return to the top frame.
    entry_snapshot = Op.MSTORE(0x20, Op.GAS, new_memory_size=0x40)
    depth2_call = Op.CALL(
        gas=ASK_GAS,
        address=gas_return_contract,
        args_offset=MEM_OFFSET,
        args_size=MEM_SIZE,
        ret_size=0x20,
        address_warm=False,
        account_new=False,
        new_memory_size=MEM_OFFSET + MEM_SIZE,
        old_memory_size=0x40,
    )
    caller = pre.deploy_contract(
        code=entry_snapshot + depth2_call + Op.RETURN(0, 0x40),
    )

    # Top frame: snapshots its entry gas (pinning the tx intrinsic), then
    # forwards the exact depth-1 budget and stores the success flag plus
    # both returned observations.
    entry_code = (
        Op.SSTORE(key=ENTRY_GAS_SLOT, value=Op.GAS)
        + Op.SSTORE(
            key=FLAG_SLOT,
            value=Op.CALL(
                gas=CALLER_GAS,
                address=caller,
                ret_size=0x40,
                address_warm=False,
                account_new=False,
                new_memory_size=0x40,
            ),
        )
        + Op.SSTORE(key=DEPTH2_GAS_SLOT, value=Op.MLOAD(0))
        + Op.SSTORE(key=DEPTH1_GAS_SLOT, value=Op.MLOAD(0x20))
    )
    entry = pre.deploy_contract(code=entry_code + Op.STOP)

    # Conservative fork-derived budget: the entry's own costs (incl. the
    # trailing state-priced stores) plus the full depth-1 grant.
    intrinsic = fork.transaction_intrinsic_cost_calculator()()
    gas_limit = intrinsic + entry_code.gas_cost(fork) + CALLER_GAS

    tx = Transaction(
        sender=pre.fund_eoa(),
        to=entry,
        gas_limit=gas_limit,
    )

    # The entry snapshot observes everything after the intrinsic; depth 1
    # received exactly CALLER_GAS; the depth-2 base is what remains after
    # the snapshot and the call's own costs (incl. memory expansion),
    # clamped by EIP-150.
    entry_observed = gas_limit - intrinsic - Op.GAS.gas_cost(fork)
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
                ENTRY_GAS_SLOT: entry_observed,
                FLAG_SLOT: 1,
                DEPTH2_GAS_SLOT: depth2_observed,
                DEPTH1_GAS_SLOT: depth1_observed,
            },
        ),
    }

    state_test(pre=pre, post=post, tx=tx)
