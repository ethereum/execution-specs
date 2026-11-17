"""
Test that a reverted TSTORE does not affect code run afterwards.

The original tests were written by Ori Pomerantz (qbzzt1@gmail.com).

Ported from:
state_tests/Cancun/stEIP1153_transientStorage/transStorageResetFiller.yml

@manually-enhanced: Do not overwrite. Named call/exit types, direct addresses.
"""

from enum import IntEnum

import pytest
from execution_testing import (
    Account,
    Alloc,
    Bytes,
    Case,
    Conditional,
    StateTestFiller,
    Switch,
    Transaction,
)
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


class CallType(IntEnum):
    """Opcode a contract uses to call the next one, or none at all."""

    NONE = 0x00
    CALL = Op.CALL.int()
    CALLCODE = Op.CALLCODE.int()
    DELEGATECALL = Op.DELEGATECALL.int()


class ExitType(IntEnum):
    """Opcode that ends the `dead` contract's frame."""

    STOP = Op.STOP.int()
    REVERT = Op.REVERT.int()
    INVALID = Op.INVALID.int()
    SELFDESTRUCT = Op.SELFDESTRUCT.int()


CALL_TYPE_IDS = {
    CallType.NONE: "nop",
    CallType.CALL: "call",
    CallType.CALLCODE: "code",
    CallType.DELEGATECALL: "delegate",
}
EXIT_TYPE_IDS = {
    ExitType.STOP: "stop",
    ExitType.REVERT: "revert",
    ExitType.INVALID: "invalid",
}

# (reverter -> dead, dead -> reverter) call types exercised by the filler.
CALL_TYPE_PAIRS = [
    (CallType.CALL, CallType.CALL),
    (CallType.DELEGATECALL, CallType.CALL),
    (CallType.CALLCODE, CallType.CALL),
    (CallType.DELEGATECALL, CallType.DELEGATECALL),
    (CallType.DELEGATECALL, CallType.CALLCODE),
    (CallType.CALLCODE, CallType.DELEGATECALL),
    (CallType.CALLCODE, CallType.CALLCODE),
    (CallType.CALL, CallType.NONE),
    (CallType.DELEGATECALL, CallType.NONE),
    (CallType.CALLCODE, CallType.NONE),
]


@pytest.mark.ported_from(
    [
        "state_tests/Cancun/stEIP1153_transientStorage/transStorageResetFiller.yml"  # noqa: E501
    ],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "reverter_call_type, dead_call_type, dead_exit_type",
    [
        pytest.param(
            reverter_call_type,
            dead_call_type,
            dead_exit_type,
            id=f"reverter-{CALL_TYPE_IDS[reverter_call_type]}"
            f"-{CALL_TYPE_IDS[dead_call_type]}"
            f"-{EXIT_TYPE_IDS[dead_exit_type]}",
        )
        for reverter_call_type, dead_call_type in CALL_TYPE_PAIRS
        for dead_exit_type in EXIT_TYPE_IDS
    ],
)
def test_trans_storage_reset(
    state_test: StateTestFiller,
    pre: Alloc,
    reverter_call_type: CallType,
    dead_call_type: CallType,
    dead_exit_type: ExitType,
) -> None:
    """
    Test that transient writes made in a reverted frame are rolled back.

    `reverter` stores a marker in its transient storage and calls `dead`
    with `reverter_call_type`. `dead` then tries to overwrite the marker,
    either by calling back into `reverter` with `dead_call_type` or, for
    `NONE`, with a direct TSTORE (which only reaches `reverter`'s transient
    storage when `dead` runs in its context via CALLCODE or DELEGATECALL),
    and ends its frame with `dead_exit_type`. After a revert or invalid
    opcode the marker is always intact.
    """
    sender = pre.fund_eoa()

    # The tx calldata holds one selector byte per parameter; `reverter`
    # forwards that word to `dead`, followed by its own address.
    reverter_call_selector = Op.BYTE(0, Op.CALLDATALOAD(0))
    dead_call_selector = Op.BYTE(1, Op.CALLDATALOAD(0))
    dead_exit_selector = Op.BYTE(2, Op.CALLDATALOAD(0))
    reverter_address = Op.CALLDATALOAD(0x20)

    # `dead` calls back into `reverter`, then ends its frame.
    dead = pre.deploy_contract(
        code=Switch(
            cases=[
                Case(
                    condition=Op.EQ(dead_call_selector, CallType.CALL),
                    action=Op.SSTORE(
                        key=0x10,
                        value=Op.CALL(gas=Op.GAS, address=reverter_address),
                    ),
                ),
                Case(
                    condition=Op.EQ(dead_call_selector, CallType.CALLCODE),
                    action=Op.SSTORE(
                        key=0x10,
                        value=Op.CALLCODE(
                            gas=Op.GAS, address=reverter_address
                        ),
                    ),
                ),
                Case(
                    condition=Op.EQ(dead_call_selector, CallType.DELEGATECALL),
                    action=Op.SSTORE(
                        key=0x10,
                        value=Op.DELEGATECALL(
                            gas=Op.GAS, address=reverter_address
                        ),
                    ),
                ),
                Case(
                    condition=Op.EQ(dead_call_selector, CallType.NONE),
                    action=Op.TSTORE(key=0, value=0xBAD0BEEF)
                    + Op.SSTORE(key=0x10, value=0x7E57),
                ),
            ],
            default_action=Op.SSTORE(key=0x10, value=0x7E57),
        )
        + Switch(
            cases=[
                Case(
                    condition=Op.EQ(dead_exit_selector, ExitType.REVERT),
                    action=Op.REVERT(offset=0, size=0),
                ),
                Case(
                    condition=Op.EQ(dead_exit_selector, ExitType.INVALID),
                    action=Op.INVALID,
                ),
                Case(
                    condition=Op.EQ(dead_exit_selector, ExitType.SELFDESTRUCT),
                    action=Op.SELFDESTRUCT(address=0),
                ),
            ],
            default_action=Op.STOP,
        ),
        storage={0x10: 0x60A7},
    )
    # On first entry `reverter` marks Trans[0] and calls `dead`; on the
    # callback from `dead` it overwrites the mark with 0xBEEF.
    reverter = pre.deploy_contract(
        code=Conditional(
            condition=Op.ISZERO(Op.TLOAD(key=0)),
            if_true=Op.TSTORE(key=0, value=0x60A7)
            + Op.MSTORE(offset=0, value=Op.CALLDATALOAD(0))
            + Op.MSTORE(offset=0x20, value=Op.ADDRESS)
            + Switch(
                cases=[
                    Case(
                        condition=Op.EQ(reverter_call_selector, CallType.CALL),
                        action=Op.SSTORE(
                            key=1,
                            value=Op.CALL(
                                gas=Op.DIV(Op.GAS, 2),
                                address=dead,
                                args_size=0x40,
                            ),
                        ),
                    ),
                    Case(
                        condition=Op.EQ(
                            reverter_call_selector, CallType.CALLCODE
                        ),
                        action=Op.SSTORE(
                            key=1,
                            value=Op.CALLCODE(
                                gas=Op.DIV(Op.GAS, 2),
                                address=dead,
                                args_size=0x40,
                            ),
                        ),
                    ),
                    Case(
                        condition=Op.EQ(
                            reverter_call_selector, CallType.DELEGATECALL
                        ),
                        action=Op.SSTORE(
                            key=1,
                            value=Op.DELEGATECALL(
                                gas=Op.DIV(Op.GAS, 2),
                                address=dead,
                                args_size=0x40,
                            ),
                        ),
                    ),
                ],
                default_action=Op.SSTORE(key=1, value=0),
            )
            + Op.SSTORE(key=0, value=Op.TLOAD(key=0))
            + Op.STOP,
            if_false=Conditional(
                condition=Op.EQ(Op.TLOAD(key=0), 0x60A7),
                if_true=Op.TSTORE(key=0, value=0xBEEF),
            ),
        ),
        storage={1: 0x60A7},
    )
    target = pre.deploy_contract(
        code=Op.SSTORE(key=0, value=reverter)
        + Op.MSTORE(offset=0, value=Op.CALLDATALOAD(0))
        + Op.SSTORE(
            key=1,
            value=Op.CALL(gas=Op.GAS, address=reverter, args_size=0x20),
        )
        + Op.STOP,
    )

    post = {target: Account(storage={0: reverter, 1: 1})}
    if dead_exit_type != ExitType.STOP:
        # `dead` fails, discarding the 0xBEEF written by the callback.
        post[reverter] = Account(storage={0: 0x60A7, 1: 0})
        post[dead] = Account(storage={0x10: 0x60A7})
    elif dead_call_type == CallType.NONE:
        # `dead` sets its own Trans[0], which is `reverter`'s too unless
        # `reverter` used CALL.
        if reverter_call_type == CallType.CALL:
            post[reverter] = Account(storage={0: 0x60A7, 1: 1})
            post[dead] = Account(storage={0x10: 0x7E57})
        else:
            post[reverter] = Account(
                storage={0: 0xBAD0BEEF, 1: 1, 0x10: 0x7E57}
            )
    elif reverter_call_type == CallType.CALL:
        post[reverter] = Account(storage={0: 0xBEEF, 1: 1})
        post[dead] = Account(storage={0x10: 1})
    else:
        # `dead` runs in `reverter`'s context, so its SSTORE lands there.
        post[reverter] = Account(storage={0: 0xBEEF, 1: 1, 0x10: 1})

    tx = Transaction(
        sender=sender,
        to=target,
        data=Bytes([reverter_call_type, dead_call_type, dead_exit_type]),
        gas_limit=16777216,
    )

    state_test(pre=pre, post=post, tx=tx)
