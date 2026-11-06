"""
Read RETURNDATASIZE and RETURNDATACOPY after a successful CREATE/CREATE2.

A successful creation leaves empty return data, so copying 32 bytes of it
overruns the buffer and halts the frame, reverting the creation.

Ported from:
state_tests/stCreateTest/CreateOOGafterInitCodeReturndataFiller.json
state_tests/stCreateTest/CreateOOGafterInitCodeReturndata2Filler.json
state_tests/stCreate2/Create2OOGafterInitCodeReturndataFiller.json
state_tests/stCreate2/Create2OOGafterInitCodeReturndata2Filler.json
"""

import pytest
from execution_testing import (
    Account,
    Alloc,
    StateTestFiller,
    Transaction,
    compute_create_address,
)
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"

INITCODE_WORD = 0x6460016001556000526005601BF3
INITCODE = INITCODE_WORD.to_bytes(32, "big")[0x12:]
DEPLOYED_CODE = bytes.fromhex("6001600155")
UNTOUCHED = 0xFF


@pytest.mark.ported_from(
    [
        "state_tests/stCreateTest/CreateOOGafterInitCodeReturndataFiller.json",  # noqa: E501
        "state_tests/stCreateTest/CreateOOGafterInitCodeReturndata2Filler.json",  # noqa: E501
        "state_tests/stCreate2/Create2OOGafterInitCodeReturndataFiller.json",
        "state_tests/stCreate2/Create2OOGafterInitCodeReturndata2Filler.json",
    ],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize("opcode", [Op.CREATE, Op.CREATE2])
@pytest.mark.parametrize(
    "copy_size",
    [pytest.param(0, id="in_bounds"), pytest.param(32, id="overrun")],
)
def test_create_oo_gafter_init_code_returndata(
    state_test: StateTestFiller,
    pre: Alloc,
    opcode: Op,
    copy_size: int,
) -> None:
    """Read return data after a successful CREATE/CREATE2."""
    sender = pre.fund_eoa()

    # Source: lll
    # { (MSTORE 0 0x6460016001556000526005601bf3) (CREATE2 0 18 14 0) [[ 1 ]] (RETURNDATASIZE) (RETURNDATACOPY 0 0 32) [[ 2 ]] (MLOAD 0) }  # noqa: E501
    if opcode == Op.CREATE2:
        create = Op.CREATE2(value=0, offset=0x12, size=len(INITCODE), salt=0)
    else:
        create = Op.CREATE(value=0, offset=0x12, size=len(INITCODE))
    contract = pre.deploy_contract(
        code=Op.MSTORE(offset=0, value=INITCODE_WORD)
        + Op.POP(create)
        + Op.SSTORE(key=1, value=Op.RETURNDATASIZE)
        + Op.RETURNDATACOPY(dest_offset=0, offset=0, size=copy_size)
        + Op.SSTORE(key=2, value=Op.MLOAD(offset=0))
        + Op.SSTORE(key=3, value=1)
        + Op.STOP,
        storage={1: UNTOUCHED, 2: UNTOUCHED},
    )
    created = compute_create_address(
        address=contract, nonce=1, salt=0, initcode=INITCODE, opcode=opcode
    )

    tx = Transaction(sender=sender, to=contract)

    post: dict
    if copy_size == 0:
        post = {
            contract: Account(storage={1: 0, 2: INITCODE_WORD, 3: 1}, nonce=2),
            created: Account(code=DEPLOYED_CODE, nonce=1),
        }
    else:
        post = {
            contract: Account(storage={1: UNTOUCHED, 2: UNTOUCHED}, nonce=1),
            created: Account.NONEXISTENT,
        }

    state_test(pre=pre, post=post, tx=tx)
