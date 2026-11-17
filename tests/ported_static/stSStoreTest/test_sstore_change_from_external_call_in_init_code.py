"""
Change a pre-existing slot X -> 0 -> X from a call made in init code.

Ported from:
state_tests/stSStoreTest/sstore_changeFromExternalCallInInitCodeFiller.json
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

CALL_OPS = {
    "call": Op.CALL,
    "callcode": Op.CALLCODE,
    "delegatecall": Op.DELEGATECALL,
    "staticcall": Op.STATICCALL,
}
REFUND_SLOTS = 16
STATICCALL_GAS = 300_000


def store_in_memory(data: bytes) -> Bytecode:
    """Write `data` to memory starting at offset 0."""
    code = Bytecode()
    for offset in range(0, len(data), 32):
        chunk = data[offset : offset + 32].ljust(32, b"\0")
        code += Op.MSTORE(offset, int.from_bytes(chunk, "big"))
    return code


@pytest.mark.ported_from(
    [
        "state_tests/stSStoreTest/sstore_changeFromExternalCallInInitCodeFiller.json"  # noqa: E501
    ],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize("call_op", list(CALL_OPS))
@pytest.mark.parametrize(
    "context", ["direct", "create2", "create2_revert", "create2_refund"]
)
def test_sstore_change_from_external_call_in_init_code(
    state_test: StateTestFiller,
    pre: Alloc,
    call_op: str,
    context: str,
) -> None:
    """
    Run X -> 0 -> X on slot 1 and 0 -> 1 on slot 0 through a call.

    The call runs from the creation transaction or from CREATE2 init code
    (optionally reverted afterwards, or followed by a refunder call).
    """
    sender = pre.fund_eoa()
    creator = compute_create_address(address=sender, nonce=0)
    target = pre.deploy_contract(
        code=Op.SSTORE(1, 0) + Op.SSTORE(1, 1) + Op.SSTORE(0, 1) + Op.STOP,
        storage={1: 1},
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

    if call_op == "staticcall":
        call = Op.POP(Op.STATICCALL(gas=STATICCALL_GAS, address=target))
    else:
        call = Op.POP(CALL_OPS[call_op](address=target))
    changed = {0: 1, 1: 1}
    post: Dict[Address, Account | None] = {}

    if context == "direct":
        initcode = call
        frame = creator
    else:
        create2_initcode = bytes(call + Op.STOP)
        frame = compute_create2_address(creator, 0, create2_initcode)
        initcode = store_in_memory(create2_initcode) + Op.POP(
            Op.CREATE2(value=0, offset=0, size=len(create2_initcode), salt=0)
        )
        if context == "create2_revert":
            initcode += Op.REVERT(0, 0)
        elif context == "create2_refund":
            initcode += Op.POP(Op.CALL(address=refunder))
            post[refunder] = Account(storage={1: 1})

    if context == "create2_revert":
        post[target] = Account(storage={1: 1})
        post[frame] = Account.NONEXISTENT
    elif call_op == "call":
        post[target] = Account(storage=changed)
        post[frame] = Account(storage={}, nonce=1)
    elif call_op == "staticcall":
        post[target] = Account(storage={1: 1})
        post[frame] = Account(storage={}, nonce=1)
    else:
        post[target] = Account(storage={1: 1})
        post[frame] = Account(storage=changed, nonce=1)

    tx = Transaction(sender=sender, to=None, data=initcode)
    state_test(pre=pre, post=post, tx=tx)
