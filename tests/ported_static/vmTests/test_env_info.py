"""
Test execution environment opcodes in a called frame.

The original tests were written by Ori Pomerantz.

Ported from:
state_tests/VMTests/vmTests/envInfoFiller.yml

@manually-enhanced: Do not overwrite. Built from readable parameters.

A `caller`, sent `TX_VALUE` by the transaction, calls a `callee` with every
call opcode the fork has, passing `CALLDATA_SIZE` bytes of arguments and
`CALL_VALUE` where the opcode takes a value. The callee returns one word,
and the caller stores it with the call's success flag, so the result
lands in the caller's storage whatever the call opcode, including
STATICCALL. `test_env_opcode` returns the value an environment opcode
pushes, which depends on the call opcode for ADDRESS, CALLER and
CALLVALUE. `test_codecopy_own_code` returns the first word of a CODECOPY
of the callee's own code.
"""

from typing import Any

import pytest
from execution_testing import (
    EOA,
    Account,
    Address,
    Alloc,
    Bytecode,
    Hash,
    Op,
    StateTestFiller,
    Transaction,
)
from execution_testing.forks import Fork
from execution_testing.vm import Opcode

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"

SENTINEL = 0x0BAD
MAX_UINT = 2**256 - 1
TX_VALUE = 0x20
CALL_VALUE = 0x10
GAS_PRICE = 4660
CALLDATA_SIZE = 0x24
# Explicit, so the call does not ask for more gas than is left before
# EIP-150 lets it forward all but 1/64th.
CALLEE_GAS = 0x10000

RESULT_SLOT = 0
SUCCESS_SLOT = 1

pytestmark = [
    pytest.mark.ported_from(
        ["state_tests/VMTests/vmTests/envInfoFiller.yml"],
    ),
    pytest.mark.valid_from("Frontier"),
    pytest.mark.with_all_call_opcodes(),
    pytest.mark.execute(
        pytest.mark.skip(
            reason="Pins a gas price below live-network base fees"
        )
    ),
]


@pytest.fixture
def caller(pre: Alloc, call_opcode: Opcode) -> Address:
    """Deploy the caller of the callee address read from calldata."""
    # Only CALL and CALLCODE take a value.
    value: dict[str, Any] = {}
    if call_opcode in (Op.CALL, Op.CALLCODE):
        value = {"value": CALL_VALUE}
    return pre.deploy_contract(
        code=Op.SSTORE(
            SUCCESS_SLOT,
            call_opcode(
                gas=CALLEE_GAS,
                address=Op.CALLDATALOAD(0),
                args_offset=0,
                args_size=CALLDATA_SIZE,
                ret_offset=0,
                ret_size=0x20,
                **value,
            ),
        )
        + Op.SSTORE(RESULT_SLOT, Op.MLOAD(0))
        + Op.STOP,
        storage={RESULT_SLOT: SENTINEL, SUCCESS_SLOT: SENTINEL},
    )


@pytest.mark.parametrize(
    "opcode, code_padding",
    [
        pytest.param(Op.ADDRESS, 0, id="address"),
        pytest.param(Op.CALLER, 0, id="caller"),
        pytest.param(Op.CALLVALUE, 0, id="callvalue"),
        pytest.param(Op.CODESIZE, 0, id="codesize"),
        # The code size no longer fits in one byte.
        pytest.param(Op.CODESIZE, 0x100, id="codesize_multi_byte"),
        pytest.param(Op.GASPRICE, 0, id="gasprice"),
        pytest.param(Op.ORIGIN, 0, id="origin"),
        pytest.param(Op.CALLDATASIZE, 0, id="calldatasize"),
    ],
)
def test_env_opcode(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    caller: Address,
    call_opcode: Opcode,
    opcode: Opcode,
    code_padding: int,
) -> None:
    """Return the value `opcode` pushes in the called frame."""
    sender: EOA = pre.fund_eoa()
    # Unreachable padding after the RETURN only grows the code.
    code = Op.MSTORE(0, opcode) + Op.RETURN(0, 0x20) + Op.STOP * code_padding
    callee = pre.deploy_contract(code=code)
    tx = Transaction(
        sender=sender,
        to=caller,
        data=Hash(callee, left_padding=True),
        value=TX_VALUE,
        gas_price=GAS_PRICE,
        protected=fork.supports_protected_txs(),
    )

    # CALLCODE and DELEGATECALL run the callee's code as the caller, and
    # DELEGATECALL keeps the caller's own caller and value.
    expected: int | Address
    match opcode:
        case Op.ADDRESS:
            expected = callee
            if call_opcode in (Op.CALLCODE, Op.DELEGATECALL):
                expected = caller
        case Op.CALLER:
            expected = caller
            if call_opcode == Op.DELEGATECALL:
                expected = sender
        case Op.CALLVALUE:
            expected = 0
            if call_opcode in (Op.CALL, Op.CALLCODE):
                expected = CALL_VALUE
            elif call_opcode == Op.DELEGATECALL:
                expected = TX_VALUE
        case Op.CODESIZE:
            expected = len(code)
        case Op.GASPRICE:
            expected = GAS_PRICE
        case Op.ORIGIN:
            expected = sender
        case Op.CALLDATASIZE:
            expected = CALLDATA_SIZE
        case _:
            raise ValueError(f"Unknown opcode: {opcode}")
    post = {caller: Account(storage={RESULT_SLOT: expected, SUCCESS_SLOT: 1})}
    state_test(pre=pre, post=post, tx=tx)


@pytest.mark.parametrize(
    "offset, size",
    [
        pytest.param(0, 7, id="first_bytes"),
        pytest.param(0, 0, id="empty"),
        # So far past the code that offset + size wraps around 2**256;
        # the copy must still read zeros rather than the code's start.
        pytest.param(MAX_UINT - 5, 8, id="offset_wraps_around"),
    ],
)
def test_codecopy_own_code(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    caller: Address,
    offset: int,
    size: int,
) -> None:
    """Return the first word of a CODECOPY of the callee's code."""
    code: Bytecode = Op.CODECOPY(
        dest_offset=0, offset=offset, size=size
    ) + Op.RETURN(0, 0x20)
    callee = pre.deploy_contract(code=code)
    tx = Transaction(
        sender=pre.fund_eoa(),
        to=caller,
        data=Hash(callee, left_padding=True),
        value=TX_VALUE,
        gas_price=GAS_PRICE,
        protected=fork.supports_protected_txs(),
    )

    # Bytes past the end of the code copy as zeros.
    copied = bytes(code)[offset : offset + size].ljust(size, b"\0")
    expected = int.from_bytes(copied[:0x20].ljust(0x20, b"\0"))
    post = {caller: Account(storage={RESULT_SLOT: expected, SUCCESS_SLOT: 1})}
    state_test(pre=pre, post=post, tx=tx)
