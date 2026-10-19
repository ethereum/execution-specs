"""
Verify EIP-150's clamp on a call's gas operand: a frame may hand down at
most all but one 64th of what it holds, so an ask above that is silently
reduced rather than honoured or rejected.

The callee reports the gas it actually received, which pins the forwarded
amount exactly instead of inferring it from whether the callee survived.

Ported from:
state_tests/stEIP150Specific/ExecuteCallThatAskForeGasThenTrabsactionHasFiller.json
state_tests/stEIP150Specific/CallAskMoreGasOnDepth2ThenTransactionHasFiller.json
state_tests/stMemExpandingEIP150Calls/ExecuteCallThatAskMoreGasThenTransactionHasWithMemExpandingCallsFiller.json
state_tests/stMemExpandingEIP150Calls/CallAskMoreGasOnDepth2ThenTransactionHasWithMemExpandingCallsFiller.json
state_tests/stStaticCall/static_ExecuteCallThatAskForeGasThenTrabsactionHasFiller.json
state_tests/stStaticCall/static_CallAskMoreGasOnDepth2ThenTransactionHasFiller.json

@manually-enhanced: Do not overwrite. The fillers proved the clamp only
indirectly -- a callee looping 50,000 times ran out, so it cannot have
received the oversized ask. Reporting GAS upward asserts the forwarded
amount to the gas, which also catches the `available * 63 // 64` form and
a window whose expansion is charged after the split rather than before.
The containment property those loops relied on -- that a callee burning
its grant leaves its caller's retention intact -- is covered separately by
`test_call_goes_oog_on_second_level`. The two depths get separate
functions because what the ask is measured against differs: at the top
frame it is what the transaction granted, one level down it is what the
frame was handed.
"""

import pytest
from execution_testing import (
    Account,
    Address,
    Alloc,
    Bytecode,
    Fork,
    Opcodes,
    StateTestFiller,
    Transaction,
)
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"

OBSERVED_GAS_SLOT = 0x1

# The ported argument/return window. Its expansion is part of the asking
# call's own cost, so it is charged before the 63/64 split and lands in
# every expectation below.
MEM_WINDOW = 0xFF

# What the top frame is granted, and what the nested frame is handed. Both
# are explicit: at each depth the ask is measured against one of them.
TX_GAS_LIMIT = 1_000_000
NESTED_FRAME_GAS = 500_000

ASK_KINDS = ["honoured", "over_frame", "over_transaction"]


def reporter_code() -> Bytecode:
    """Return code that reports the gas its frame received."""
    return Op.MSTORE(offset=0x0, value=Op.GAS) + Op.RETURN(
        offset=0x0, size=0x20
    )


def asking_call(
    call_opcode: Opcodes, callee: Address, ask: int, window: int
) -> Bytecode:
    """Return the call that asks `ask` gas, with the ported window."""
    return call_opcode(
        gas=ask,
        address=callee,
        args_offset=window,
        args_size=window,
        ret_offset=0x0,
        ret_size=0x20,
        new_memory_size=max(2 * window, 0x20),
    )


def record_reply(call: Bytecode) -> Bytecode:
    """Return code that makes `call` and stores what the callee replied."""
    return Op.POP(call) + Op.SSTORE(OBSERVED_GAS_SLOT, Op.MLOAD(offset=0x0))


def forwarded_from(frame_gas: int, call: Bytecode, fork: Fork) -> int:
    """
    Return the most `call` can hand down out of `frame_gas`.

    Only the call's own cost is spent by the time it executes -- whatever
    the frame does afterwards is paid for out of the retention.
    """
    available = frame_gas - call.gas_cost(fork)
    assert available > 0, "the frame must afford the call itself"
    # The EVM withholds `available // 64`, which is not the same as handing
    # down `available * 63 // 64`.
    return available - available // 64


@pytest.mark.ported_from(
    [
        "state_tests/stEIP150Specific/ExecuteCallThatAskForeGasThenTrabsactionHasFiller.json",  # noqa: E501
        "state_tests/stMemExpandingEIP150Calls/ExecuteCallThatAskMoreGasThenTransactionHasWithMemExpandingCallsFiller.json",  # noqa: E501
        "state_tests/stStaticCall/static_ExecuteCallThatAskForeGasThenTrabsactionHasFiller.json",  # noqa: E501
    ],
)
@pytest.mark.valid_from("Berlin")
@pytest.mark.parametrize(
    "memory_expansion", [False, True], ids=["flat", "mem_expansion"]
)
@pytest.mark.parametrize("ask_kind", ASK_KINDS)
@pytest.mark.with_all_call_opcodes
def test_top_frame_asks_more_gas_than_available(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    call_opcode: Opcodes,
    ask_kind: str,
    memory_expansion: bool,
) -> None:
    """
    Verify the clamp when the transaction's own callee makes the ask.

    Here the ceiling comes from the transaction's grant, so `over_transaction`
    asks for one gas more than the whole transaction was given -- which is
    still just an oversized ask, not an error.
    """
    callee = pre.deploy_contract(code=reporter_code())
    window = MEM_WINDOW if memory_expansion else 0

    # The frame holds the whole grant less the intrinsic.
    frame_gas = TX_GAS_LIMIT - fork.transaction_intrinsic_cost_calculator()()
    # Sizing uses a placeholder ask; every candidate below assembles to the
    # same length, so the cost this measures is the one that applies.
    ceiling = forwarded_from(
        frame_gas, asking_call(call_opcode, callee, TX_GAS_LIMIT, window), fork
    )
    ask = {
        "honoured": ceiling // 2,
        "over_frame": ceiling + 1,
        "over_transaction": TX_GAS_LIMIT + 1,
    }[ask_kind]

    call = asking_call(call_opcode, callee, ask, window)
    assert forwarded_from(frame_gas, call, fork) == ceiling, (
        "the ask must not change the call's own cost"
    )
    caller = pre.deploy_contract(code=record_reply(call) + Op.STOP)

    tx = Transaction(
        sender=pre.fund_eoa(),
        to=caller,
        gas_limit=TX_GAS_LIMIT,
        state_gas_reservoir=0,
    )

    forwarded = min(ask, ceiling)
    post = {
        caller: Account(
            storage={OBSERVED_GAS_SLOT: forwarded - Op.GAS.gas_cost(fork)}
        )
    }

    state_test(pre=pre, post=post, tx=tx)


@pytest.mark.ported_from(
    [
        "state_tests/stEIP150Specific/CallAskMoreGasOnDepth2ThenTransactionHasFiller.json",  # noqa: E501
        "state_tests/stMemExpandingEIP150Calls/CallAskMoreGasOnDepth2ThenTransactionHasWithMemExpandingCallsFiller.json",  # noqa: E501
        "state_tests/stStaticCall/static_CallAskMoreGasOnDepth2ThenTransactionHasFiller.json",  # noqa: E501
    ],
)
@pytest.mark.valid_from("Berlin")
@pytest.mark.parametrize(
    "memory_expansion", [False, True], ids=["flat", "mem_expansion"]
)
@pytest.mark.parametrize("ask_kind", ASK_KINDS)
@pytest.mark.with_all_call_opcodes
def test_nested_frame_asks_more_gas_than_available(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    call_opcode: Opcodes,
    ask_kind: str,
    memory_expansion: bool,
) -> None:
    """
    Verify the clamp when a frame one level down makes the ask.

    The ceiling now comes from what that frame was handed, not from the
    transaction, so `over_transaction` overshoots by far more than
    `over_frame` and yet is clamped to exactly the same amount.
    """
    callee = pre.deploy_contract(code=reporter_code())
    window = MEM_WINDOW if memory_expansion else 0

    ceiling = forwarded_from(
        NESTED_FRAME_GAS,
        asking_call(call_opcode, callee, TX_GAS_LIMIT, window),
        fork,
    )
    ask = {
        "honoured": ceiling // 2,
        "over_frame": ceiling + 1,
        "over_transaction": TX_GAS_LIMIT + 1,
    }[ask_kind]

    call = asking_call(call_opcode, callee, ask, window)
    assert forwarded_from(NESTED_FRAME_GAS, call, fork) == ceiling, (
        "the ask must not change the call's own cost"
    )
    # The asking frame reports upward, so the entry can store what it saw
    # without the asking frame needing storage of its own.
    asking_frame = pre.deploy_contract(
        code=record_reply(call)
        + Op.MSTORE(
            offset=0x0, value=Op.SLOAD(key=OBSERVED_GAS_SLOT, key_warm=True)
        )
        + Op.RETURN(offset=0x0, size=0x20)
    )

    # The entry hands the asking frame a fixed budget, so the ceiling does
    # not depend on the transaction's own grant.
    entry = pre.deploy_contract(
        code=Op.POP(
            Op.CALL(
                gas=NESTED_FRAME_GAS,
                address=asking_frame,
                ret_offset=0x0,
                ret_size=0x20,
            )
        )
        + Op.SSTORE(OBSERVED_GAS_SLOT, Op.MLOAD(offset=0x0))
        + Op.STOP,
    )

    tx = Transaction(
        sender=pre.fund_eoa(),
        to=entry,
        gas_limit=TX_GAS_LIMIT,
        state_gas_reservoir=0,
    )

    forwarded = min(ask, ceiling)
    observed = forwarded - Op.GAS.gas_cost(fork)
    post = {
        entry: Account(storage={OBSERVED_GAS_SLOT: observed}),
        asking_frame: Account(storage={OBSERVED_GAS_SLOT: observed}),
    }

    state_test(pre=pre, post=post, tx=tx)
