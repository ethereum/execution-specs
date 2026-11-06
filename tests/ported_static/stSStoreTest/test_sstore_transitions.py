"""
Change a storage slot through a sequence of SSTOREs from every context.

Ported from:
state_tests/stSStoreTest/sstore_0to0Filler.json
state_tests/stSStoreTest/sstore_0to0to0Filler.json
state_tests/stSStoreTest/sstore_0to0toXFiller.json
state_tests/stSStoreTest/sstore_0toXFiller.json
state_tests/stSStoreTest/sstore_0toXto0Filler.json
state_tests/stSStoreTest/sstore_0toXto0toXFiller.json
state_tests/stSStoreTest/sstore_0toXtoXFiller.json
state_tests/stSStoreTest/sstore_0toXtoYFiller.json
state_tests/stSStoreTest/sstore_Xto0Filler.json
state_tests/stSStoreTest/sstore_Xto0to0Filler.json
state_tests/stSStoreTest/sstore_Xto0toXFiller.json
state_tests/stSStoreTest/sstore_Xto0toXto0Filler.json
state_tests/stSStoreTest/sstore_Xto0toYFiller.json
state_tests/stSStoreTest/sstore_XtoXFiller.json
state_tests/stSStoreTest/sstore_XtoXto0Filler.json
state_tests/stSStoreTest/sstore_XtoXtoXFiller.json
state_tests/stSStoreTest/sstore_XtoXtoYFiller.json
state_tests/stSStoreTest/sstore_XtoYFiller.json
state_tests/stSStoreTest/sstore_XtoYto0Filler.json
state_tests/stSStoreTest/sstore_XtoYtoXFiller.json
state_tests/stSStoreTest/sstore_XtoYtoYFiller.json
state_tests/stSStoreTest/sstore_XtoYtoZFiller.json
"""

from typing import Dict

import pytest
from execution_testing import (
    Account,
    Address,
    Alloc,
    Bytecode,
    StateTestFiller,
    Transaction,
    compute_create2_address,
    compute_create_address,
)
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"

PATTERNS = {
    "0to0": (0, [0]),
    "0to0to0": (0, [0, 0]),
    "0to0to_x": (0, [0, 1]),
    "0to_x": (0, [1]),
    "0to_xto0": (0, [1, 0]),
    "0to_xto0to_x": (0, [1, 0, 1]),
    "0to_xto_x": (0, [1, 1]),
    "0to_xto_y": (0, [2, 1]),
    "xto0": (1, [0]),
    "xto0to0": (1, [0, 0]),
    "xto0to_x": (1, [0, 1]),
    "xto0to_xto0": (1, [0, 1, 0]),
    "xto0to_y": (2, [0, 1]),
    "xto_x": (1, [1]),
    "xto_xto0": (1, [1, 0]),
    "xto_xto_x": (1, [1, 1]),
    "xto_xto_y": (2, [2, 1]),
    "xto_y": (1, [2]),
    "xto_yto0": (1, [2, 0]),
    "xto_yto_x": (1, [2, 1]),
    "xto_yto_y": (2, [1, 1]),
    "xto_yto_z": (1, [2, 3]),
}
"""Original value and the values stored in sequence, per pattern."""

CALL_OPS = {
    "call": Op.CALL,
    "callcode": Op.CALLCODE,
    "delegatecall": Op.DELEGATECALL,
    "staticcall": Op.STATICCALL,
}
SLOT = 1
CREATE2_SLOT = 0
CREATE2_MARKER_SLOT = 1
REFUND_SLOTS = 16
STATICCALL_GAS = 300_000
LOW_GAS_LIMIT = 400_000


def stores(slot: int, values: list[int]) -> Bytecode:
    """Store `values` into `slot` one after another."""
    return sum((Op.SSTORE(slot, value) for value in values), Bytecode())


@pytest.mark.ported_from(
    [
        "state_tests/stSStoreTest/sstore_0to0Filler.json",
        "state_tests/stSStoreTest/sstore_0to0to0Filler.json",
        "state_tests/stSStoreTest/sstore_0to0toXFiller.json",
        "state_tests/stSStoreTest/sstore_0toXFiller.json",
        "state_tests/stSStoreTest/sstore_0toXto0Filler.json",
        "state_tests/stSStoreTest/sstore_0toXto0toXFiller.json",
        "state_tests/stSStoreTest/sstore_0toXtoXFiller.json",
        "state_tests/stSStoreTest/sstore_0toXtoYFiller.json",
        "state_tests/stSStoreTest/sstore_Xto0Filler.json",
        "state_tests/stSStoreTest/sstore_Xto0to0Filler.json",
        "state_tests/stSStoreTest/sstore_Xto0toXFiller.json",
        "state_tests/stSStoreTest/sstore_Xto0toXto0Filler.json",
        "state_tests/stSStoreTest/sstore_Xto0toYFiller.json",
        "state_tests/stSStoreTest/sstore_XtoXFiller.json",
        "state_tests/stSStoreTest/sstore_XtoXto0Filler.json",
        "state_tests/stSStoreTest/sstore_XtoXtoXFiller.json",
        "state_tests/stSStoreTest/sstore_XtoXtoYFiller.json",
        "state_tests/stSStoreTest/sstore_XtoYFiller.json",
        "state_tests/stSStoreTest/sstore_XtoYto0Filler.json",
        "state_tests/stSStoreTest/sstore_XtoYtoXFiller.json",
        "state_tests/stSStoreTest/sstore_XtoYtoYFiller.json",
        "state_tests/stSStoreTest/sstore_XtoYtoZFiller.json",
    ],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize("pattern", list(PATTERNS))
@pytest.mark.parametrize("context", [*CALL_OPS, "create2"])
@pytest.mark.parametrize("revert", [False, True], ids=["", "revert"])
@pytest.mark.parametrize("low_gas", [False, True], ids=["", "low_gas"])
def test_sstore_transitions(
    state_test: StateTestFiller,
    pre: Alloc,
    pattern: str,
    context: str,
    revert: bool,
    low_gas: bool,
) -> None:
    """
    Run an SSTORE sequence from a creation transaction, then a refunder.

    The sequence runs in a called contract, in the creating frame through
    CALLCODE or DELEGATECALL, under STATICCALL (where it fails) or in
    CREATE2 init code. A refunder then sets and clears 16 slots and marks
    slot 1; the marker shows it ran without running out of gas.
    """
    original, sequence = PATTERNS[pattern]
    sender = pre.fund_eoa()
    creator = compute_create_address(address=sender, nonce=0)
    initial: dict = {SLOT: original} if original else {}
    target = pre.deploy_contract(
        code=stores(SLOT, sequence) + Op.STOP, storage=initial
    )
    refunder = pre.deploy_contract(
        code=sum(
            (
                Op.SSTORE(slot, 1) + Op.SSTORE(slot, 0)
                for slot in range(1, REFUND_SLOTS + 1)
            ),
            Bytecode(),
        )
        + Op.SSTORE(1, 1)
        + Op.STOP
    )

    post: Dict[Address, Account | None] = {}
    final = sequence[-1]
    if context == "create2":
        prefix = [original] if original else []
        create2_initcode = bytes(
            stores(CREATE2_SLOT, prefix + sequence)
            + Op.SSTORE(CREATE2_MARKER_SLOT, 1)
            + Op.STOP
        )
        assert len(create2_initcode) <= 32
        action = Op.MSTORE(
            0, int.from_bytes(create2_initcode.ljust(32, b"\0"), "big")
        ) + Op.POP(
            Op.CREATE2(value=0, offset=0, size=len(create2_initcode), salt=0)
        )
        created = compute_create2_address(creator, 0, create2_initcode)
        if not revert:
            post[created] = Account(
                storage={CREATE2_SLOT: final, CREATE2_MARKER_SLOT: 1}
            )
    elif context == "staticcall":
        action = Op.POP(Op.STATICCALL(gas=STATICCALL_GAS, address=target))
        post[target] = Account(storage=initial)
    else:
        action = Op.POP(CALL_OPS[context](address=target))
        if revert:
            post[target] = Account(storage=initial)
        elif context == "call":
            post[target] = Account(storage={SLOT: final})
            post[creator] = Account(storage={}, nonce=1)
        else:
            post[target] = Account(storage=initial)
            post[creator] = Account(storage={SLOT: final}, nonce=1)

    if low_gas:
        post = {}
    post[refunder] = Account(storage={} if revert or low_gas else {1: 1})

    initcode = action + Op.POP(Op.CALL(address=refunder))
    if revert:
        initcode += Op.REVERT(offset=0, size=0x20)
    tx = Transaction(
        sender=sender,
        to=None,
        data=initcode,
        gas_limit=LOW_GAS_LIMIT if low_gas else None,
    )
    state_test(pre=pre, post=post, tx=tx)
