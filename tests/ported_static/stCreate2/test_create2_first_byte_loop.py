"""
CREATE2 init code returning each possible first byte of the deployed code.

Ported from:
state_tests/stCreate2/CREATE2_FirstByte_loopFiller.yml
@manually-enhanced: Do not overwrite. Rewritten by hand; tx `gas_limit`
removed.
"""

import pytest
from execution_testing import (
    Account,
    Alloc,
    Bytes,
    Hash,
    StateTestFiller,
    Transaction,
    compute_create_address,
)
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"

INVALID_FIRST_BYTE = 0xEF


@pytest.mark.ported_from(
    ["state_tests/stCreate2/CREATE2_FirstByte_loopFiller.yml"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "start, end",
    [
        pytest.param(0x0, 0xEF, id="firstHalf"),
        pytest.param(0xEF, 0xF0, id="invalidByte"),
        pytest.param(0xF0, 0x100, id="secondHalf"),
    ],
)
def test_create2_first_byte_loop(
    state_test: StateTestFiller,
    pre: Alloc,
    start: int,
    end: int,
) -> None:
    """CREATE2 init code returning each possible first code byte."""
    sender = pre.fund_eoa()

    # Source: yul
    # berlin
    # {
    #   let start := calldataload(4)
    #   let end := calldataload(36)
    #   // initcode: { mstore8(0, 0x00) return(0, 1) }
    #   mstore(0, 0x600060005360016000f300000000000000000000000000000000000000000000)  # noqa: E501
    #   for { let code := start } lt(code, end) { code := add(code, 1) }
    #   {
    #     mstore8(1, code) // change returned byte in initcode
    #     if iszero(create2(0, 0, 10, 0)) { sstore(code, 1) }
    #   }
    #   sstore(256, 1)
    # }
    entry = pre.deploy_contract(
        code=Op.MSTORE(
            offset=0x0,
            value=0x600060005360016000F300000000000000000000000000000000000000000000,  # noqa: E501
        )
        + Op.CALLDATALOAD(offset=0x24)
        + Op.CALLDATALOAD(offset=0x4)
        + Op.JUMPDEST
        + Op.JUMPI(pc=0x38, condition=Op.LT(Op.DUP2, Op.DUP2))
        + Op.SSTORE(key=0x100, value=0x1)
        + Op.STOP
        + Op.JUMPDEST
        + Op.DUP1
        + Op.PUSH1[0x1]
        + Op.SWAP2
        + Op.DUP3
        + Op.MSTORE8
        + Op.JUMPI(
            pc=0x4F,
            condition=Op.ISZERO(
                Op.CREATE2(value=Op.DUP1, offset=Op.DUP2, size=0xA, salt=0x0)
            ),
        )
        + Op.JUMPDEST
        + Op.ADD
        + Op.JUMP(pc=0x2A)
        + Op.JUMPDEST
        + Op.SSTORE(key=Op.DUP2, value=Op.DUP2)
        + Op.JUMP(pc=0x4A),
    )

    storage = {256: 1}
    post: dict = {sender: Account(nonce=1)}
    for first_byte in range(start, end):
        # initcode: { mstore8(0, first_byte) return(0, 1) }
        initcode = bytes([0x60, first_byte]) + bytes.fromhex(
            "60005360016000f3"
        )
        created = compute_create_address(
            address=entry, salt=0, initcode=initcode, opcode=Op.CREATE2
        )
        if first_byte == INVALID_FIRST_BYTE:
            storage[first_byte] = 1
            post[created] = Account.NONEXISTENT
        else:
            post[created] = Account(nonce=1, code=bytes([first_byte]))
    post[entry] = Account(storage=storage, nonce=1 + end - start)

    tx = Transaction(
        sender=sender,
        to=entry,
        data=Bytes("1a8451e6") + Hash(start) + Hash(end),
    )

    state_test(pre=pre, post=post, tx=tx)
