"""
Ori Pomerantz qbzzt1@gmail.com.

Ported from:
state_tests/stReturnDataTest/revertRetDataSizeFiller.yml

@manually-enhanced: Do not overwrite. Per-case code replaces the calldata
dispatcher; the jump and CREATE2 init codes fail as the filler intended.
"""

import pytest
from execution_testing import (
    Account,
    Alloc,
    Bytecode,
    StateTestFiller,
    Transaction,
)
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"

CALL_OPCODES = {
    "call": Op.CALL,
    "callcode": Op.CALLCODE,
    "delegatecall": Op.DELEGATECALL,
    "staticcall": Op.STATICCALL,
}
FAILING_CODE = {
    "out_of_gas": Op.SHA3(offset=0x0, size=Op.SUB(0x0, 0x1)) + Op.STOP,
    "stack_underflow": Op.POP + Op.STOP,
    "bad_jump": Op.JUMP(pc=0x0),
    "bad_jumpi": Op.JUMPI(pc=0x1, condition=0x1),
    "invalid_opcode": Op.INVALID + Op.STOP,
}
CREATE2_SALT = 0x5A17
CANARY = 0x60A7


@pytest.mark.ported_from(
    ["state_tests/stReturnDataTest/revertRetDataSizeFiller.yml"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "failure",
    [
        "out_of_gas",
        "stack_underflow",
        "bad_jump",
        "bad_jumpi",
        "invalid_opcode",
        "nonexistent_account",
    ],
)
@pytest.mark.parametrize(
    "opcode",
    ["call", "callcode", "delegatecall", "staticcall", "create", "create2"],
)
def test_revert_ret_data_size(
    state_test: StateTestFiller,
    pre: Alloc,
    opcode: str,
    failure: str,
) -> None:
    """Verify a failed call or create clears the previous return data."""
    sender = pre.fund_eoa()

    # Source: lll
    # {
    #    [0x00] (/ (- 0 1) 2)
    #    [0x20] (+ @0x00 1)
    #
    #    (return 0 0x40)
    # }
    returner = pre.deploy_contract(
        code=Op.MSTORE(offset=0x0, value=Op.DIV(Op.SUB(0x0, 0x1), 0x2))
        + Op.MSTORE(offset=0x20, value=Op.ADD(Op.MLOAD(offset=0x0), 0x1))
        + Op.RETURN(offset=0x0, size=0x40),
    )

    failing_call: Bytecode
    if opcode in CALL_OPCODES:
        call_opcode = CALL_OPCODES[opcode]
        succeeding_call = call_opcode(address=returner, ret_size=0x40)
        if failure == "out_of_gas":
            failing_call = call_opcode(gas=0, address=returner, ret_size=0x40)
        elif failure == "nonexistent_account":
            failing_call = call_opcode(
                address=pre.nonexistent_account(), ret_size=0x40
            )
        else:
            failing_call = call_opcode(
                address=pre.deploy_contract(code=FAILING_CODE[failure]),
                ret_size=0x40,
            )
    else:
        succeeding_call = Op.STATICCALL(address=returner, ret_size=0x40)
        initcode = bytes(FAILING_CODE.get(failure, Op.STOP))
        store_initcode = Op.MSTORE(
            offset=0x0,
            value=Op.PUSH32[int.from_bytes(initcode.ljust(32, b"\0"), "big")],
        )
        if opcode == "create":
            create = Op.CREATE(value=0, offset=0x0, size=len(initcode))
        elif opcode == "create2":
            create = Op.CREATE2(
                value=0, offset=0x0, size=len(initcode), salt=CREATE2_SALT
            )
        else:
            raise ValueError(f"unknown opcode {opcode}")
        failing_call = store_initcode + create

    contract = pre.deploy_contract(
        code=Op.POP(succeeding_call)
        + Op.SSTORE(key=0x0, value=Op.RETURNDATASIZE)
        + Op.POP(failing_call)
        + Op.SSTORE(key=0x1, value=Op.RETURNDATASIZE)
        + Op.SSTORE(key=0x2, value=CANARY)
        + Op.STOP,
        storage={0: CANARY, 1: CANARY},
    )

    tx = Transaction(sender=sender, to=contract, gas_limit=16777216)

    post = {contract: Account(storage={0: 0x40, 1: 0, 2: CANARY})}

    state_test(pre=pre, post=post, tx=tx)
