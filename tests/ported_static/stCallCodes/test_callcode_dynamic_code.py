"""
Callcode to a contract that is being created in the same transaction.

Ported from:
state_tests/stCallCodes/callcodeDynamicCodeFiller.json
state_tests/stDelegatecallTestHomestead/delegatecodeDynamicCodeFiller.json

@manually-enhanced: Do not overwrite. CALLCODE and DELEGATECALL merged; the
DELEGATECALL case delegates into the created child.
"""

import pytest
from execution_testing import (
    Account,
    Alloc,
    Initcode,
    StateTestFiller,
    Transaction,
    compute_create2_address,
    compute_create_address,
)
from execution_testing import Macros as Om
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"

SALT = 0

CHILD_CODE = (
    Op.SSTORE(0x0, 1)
    + Op.SSTORE(0x14, Op.ADDRESS)
    + Op.SSTORE(0x15, Op.ORIGIN)
    + Op.SSTORE(0x16, Op.CALLER)
    + Op.STOP
)
CHILD_INITCODE = Initcode(deploy_code=CHILD_CODE)


@pytest.mark.ported_from(
    [
        "state_tests/stCallCodes/callcodeDynamicCodeFiller.json",
        "state_tests/stDelegatecallTestHomestead/delegatecodeDynamicCodeFiller.json",  # noqa: E501
    ],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "opcode", [Op.CALLCODE, Op.DELEGATECALL], ids=["callcode", "delegatecall"]
)
@pytest.mark.parametrize(
    "create_opcode", [Op.CREATE, Op.CREATE2], ids=["create", "create2"]
)
@pytest.mark.parametrize(
    "in_initcode", [False, True], ids=["code", "initcode"]
)
def test_callcode_dynamic_code(
    state_test: StateTestFiller,
    pre: Alloc,
    opcode: Op,
    create_opcode: Op,
    in_initcode: bool,
) -> None:
    """
    Create a child contract, then CALLCODE or DELEGATECALL into it.

    The creator runs as deployed code, or as the init code of a contract
    created by the transaction target.
    """
    sender = pre.fund_eoa()

    if create_opcode == Op.CREATE:
        create = Op.CREATE(0, 0, len(CHILD_INITCODE))
    else:
        create = Op.CREATE2(0, 0, len(CHILD_INITCODE), SALT)
    creator_code = (
        Om.MSTORE(CHILD_INITCODE, 0)
        + Op.SSTORE(0xA, create)
        + Op.SSTORE(
            0xB, opcode(address=Op.SLOAD(0xA), args_size=0x40, ret_size=0x40)
        )
        + Op.STOP
    )

    if in_initcode:
        target = pre.deploy_contract(
            code=Om.MSTORE(creator_code, 0)
            + Op.CREATE(0, 0, len(creator_code))
            + Op.STOP,
        )
        context = compute_create_address(address=target, nonce=1)
        context_caller = target
    else:
        target = pre.deploy_contract(code=creator_code)
        context = target
        context_caller = sender

    if create_opcode == Op.CREATE:
        child = compute_create_address(address=context, nonce=1)
    else:
        child = compute_create2_address(context, SALT, CHILD_INITCODE)

    tx = Transaction(sender=sender, to=target)

    storage = {
        0x0: 1,
        0xA: child,
        0xB: 1,
        0x14: context,
        0x15: sender,
        0x16: context if opcode == Op.CALLCODE else context_caller,
    }
    post = {
        context: Account(storage=storage),
        child: Account(code=CHILD_CODE, storage={}),
    }
    if in_initcode:
        post[context] = Account(storage=storage, code=b"", nonce=2)

    state_test(pre=pre, post=post, tx=tx)
