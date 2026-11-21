"""
Check opcode values in create2 init code.

CREATE2 is reached through CALL, CALLCODE, DELEGATECALL and STATICCALL,
directly or from the init code of another CREATE2.

Ported from:
state_tests/stCreate2/create2checkFieldsInInitcodeFiller.json
@manually-enhanced: Do not overwrite. Rewritten by hand; tx `gas_limit`
removed.
"""

import pytest
from execution_testing import (
    Account,
    Address,
    Alloc,
    Bytecode,
    Hash,
    StateTestFiller,
    Transaction,
    compute_create_address,
)
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


def create2_with_initcode(initcode: Bytecode) -> Bytecode:
    """Return code that CREATE2s the init code appended to it."""
    size = len(initcode)

    def prefix(offset: int) -> Bytecode:
        return (
            Op.CODECOPY(dest_offset=0, offset=offset, size=size)
            + Op.POP(Op.CREATE2(value=0, offset=0, size=size, salt=0))
            + Op.STOP
        )

    return prefix(len(prefix(0))) + initcode


def created_by(creator: Address, initcode: Bytecode) -> Address:
    """Return the CREATE2 address for salt zero."""
    return compute_create_address(
        address=creator, salt=0, initcode=initcode, opcode=Op.CREATE2
    )


@pytest.mark.ported_from(
    ["state_tests/stCreate2/create2checkFieldsInInitcodeFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.execute(pytest.mark.skip(reason="execute sets its own gas price"))
@pytest.mark.parametrize("nested", [False, True], ids=["direct", "nested"])
@pytest.mark.parametrize(
    "call_opcode",
    [Op.CALL, Op.CALLCODE, Op.DELEGATECALL, Op.STATICCALL],
)
def test_create2check_fields_in_initcode(
    state_test: StateTestFiller,
    pre: Alloc,
    call_opcode: Op,
    nested: bool,
) -> None:
    """Check opcode values in create2 init code."""
    sender = pre.fund_eoa()

    store_fields = (
        Op.SSTORE(key=0x0, value=Op.ADDRESS)
        + Op.SSTORE(key=0x1, value=Op.BALANCE(address=Op.ADDRESS))
        + Op.SSTORE(key=0x2, value=Op.ORIGIN)
        + Op.SSTORE(key=0x3, value=Op.CALLER)
        + Op.SSTORE(key=0x4, value=Op.CALLVALUE)
        + Op.SSTORE(key=0x5, value=Op.CALLDATASIZE)
        + Op.SSTORE(key=0x6, value=Op.CODESIZE)
        + Op.SSTORE(key=0x7, value=Op.GASPRICE)
        + Op.STOP * 2
    )
    return_fields = (
        Op.MSTORE(offset=0x0, value=Op.ADDRESS)
        + Op.MSTORE(offset=0x20, value=Op.BALANCE(address=Op.ADDRESS))
        + Op.MSTORE(offset=0x40, value=Op.ORIGIN)
        + Op.MSTORE(offset=0x60, value=Op.CALLER)
        + Op.MSTORE(offset=0x80, value=Op.CALLVALUE)
        + Op.MSTORE(offset=0xA0, value=Op.CALLDATASIZE)
        + Op.MSTORE(offset=0xC0, value=Op.CODESIZE)
        + Op.MSTORE(offset=0xE0, value=Op.GASPRICE)
        + Op.RETURN(offset=0x0, size=0x100)
        + Op.STOP * 2
    )
    if call_opcode == Op.STATICCALL:
        fields_creator = pre.deploy_contract(
            code=create2_with_initcode(return_fields)
        )
        fields_initcode = return_fields
        reach_creator = Op.POP(
            Op.STATICCALL(address=fields_creator, ret_size=0x100)
        ) + Op.SSTORE(key=0xA, value=Op.MLOAD(offset=0x0))
    else:
        fields_creator = pre.deploy_contract(
            code=create2_with_initcode(store_fields)
        )
        fields_initcode = store_fields
        reach_creator = Op.POP(call_opcode(address=fields_creator))
    reach_creator += Op.STOP

    if nested:
        intermediate = pre.deploy_contract(
            code=create2_with_initcode(reach_creator)
        )
        target = intermediate
        context = created_by(intermediate, reach_creator)
    else:
        target = pre.deploy_contract(code=reach_creator)
        context = target

    entry = pre.deploy_contract(
        code=Op.CALL(address=Op.CALLDATALOAD(offset=0x0)) + Op.STOP,
    )

    tx = Transaction(
        sender=sender, to=entry, data=Hash(target, left_padding=True)
    )

    post: dict = {sender: Account(nonce=1)}
    if call_opcode == Op.STATICCALL:
        post[created_by(fields_creator, fields_initcode)] = Account.NONEXISTENT
        post[context] = Account(storage={})
    else:
        if call_opcode == Op.CALL:
            create2_context = fields_creator
        else:
            create2_context = context
        created = created_by(create2_context, fields_initcode)
        post[created] = Account(
            storage={
                0: created,
                1: 0,
                2: sender,
                3: create2_context,
                4: 0,
                5: 0,
                6: len(fields_initcode),
                7: tx.gas_price,
            },
            balance=0,
            nonce=1,
        )

    state_test(pre=pre, post=post, tx=tx)
