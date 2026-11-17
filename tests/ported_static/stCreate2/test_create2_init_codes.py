"""
Testing different byte opcodes inside create2 init code.

Ported from:
state_tests/stCreate2/create2InitCodesFiller.json
"""

import pytest
from execution_testing import (
    Account,
    Alloc,
    Bytecode,
    StateTestFiller,
    Transaction,
    compute_create_address,
)
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


@pytest.mark.ported_from(
    ["state_tests/stCreate2/create2InitCodesFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "case",
    [
        "stop",
        "jump_underflow",
        "add_underflow",
        "delegatecall_underflow",
        "sstore_sload",
        "selfdestruct",
        "selfdestruct_with_value",
        "zero_memory",
        "push_with_value",
    ],
)
def test_create2_init_codes(
    state_test: StateTestFiller,
    pre: Alloc,
    case: str,
) -> None:
    """Testing different byte opcodes inside create2 init code."""
    sender = pre.fund_eoa()
    beneficiary = pre.nonexistent_account()
    creator = compute_create_address(address=sender, nonce=0)
    tx_value = 1

    create_value = 0
    initcode: Bytecode | bytes
    if case == "stop":
        initcode = Op.STOP
    elif case == "jump_underflow":
        initcode = Op.JUMP
    elif case == "add_underflow":
        initcode = Op.ADD
    elif case == "delegatecall_underflow":
        initcode = Op.DELEGATECALL
    elif case == "sstore_sload":
        initcode = Op.SSTORE(key=1, value=1) + Op.SSTORE(
            key=2, value=Op.SLOAD(key=1)
        )
    elif case == "selfdestruct":
        initcode = Op.SELFDESTRUCT(address=beneficiary)
    elif case == "selfdestruct_with_value":
        initcode = Op.SELFDESTRUCT(address=beneficiary)
        create_value = 1
    elif case == "zero_memory":
        initcode = bytes(3)
    elif case == "push_with_value":
        initcode = Op.PUSH1[0xA9]
        create_value = 1
    else:
        raise ValueError(f"Unknown case: {case}")

    initcode = bytes(initcode)
    created = compute_create_address(
        address=creator, salt=0, initcode=initcode, opcode=Op.CREATE2
    )
    tx_data = Bytecode()
    if case != "zero_memory":
        tx_data += Op.MSTORE(offset=0, value=int.from_bytes(initcode, "big"))
    tx_data += Op.SSTORE(
        key=0,
        value=Op.CREATE2(
            value=create_value,
            offset=32 - len(initcode),
            size=len(initcode),
            salt=0,
        ),
    )

    post: dict = {sender: Account(nonce=1)}
    if case in ("jump_underflow", "add_underflow", "delegatecall_underflow"):
        post[creator] = Account(storage={}, balance=tx_value, nonce=2)
        post[created] = Account.NONEXISTENT
    elif case == "sstore_sload":
        post[creator] = Account(storage={0: created}, nonce=2)
        post[created] = Account(storage={1: 1, 2: 1}, nonce=1)
    elif case in ("selfdestruct", "selfdestruct_with_value"):
        post[creator] = Account(
            storage={0: created}, balance=tx_value - create_value, nonce=2
        )
        post[created] = Account.NONEXISTENT
        post[beneficiary] = (
            Account(balance=create_value)
            if create_value
            else Account.NONEXISTENT
        )
    else:
        post[creator] = Account(
            storage={0: created}, balance=tx_value - create_value, nonce=2
        )
        post[created] = Account(balance=create_value, nonce=1, code=b"")

    tx = Transaction(sender=sender, to=None, data=tx_data, value=tx_value)

    state_test(pre=pre, post=post, tx=tx)
