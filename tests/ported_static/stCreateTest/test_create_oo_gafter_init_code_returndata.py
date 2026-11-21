"""
Read RETURNDATASIZE and RETURNDATACOPY after a successful CREATE/CREATE2.

A successful creation leaves empty return data, so copying 32 bytes of it
overruns the buffer and halts the frame, reverting the creation.

Ported from:
state_tests/stCreateTest/CreateOOGafterInitCodeReturndataFiller.json
state_tests/stCreateTest/CreateOOGafterInitCodeReturndata2Filler.json
state_tests/stCreate2/Create2OOGafterInitCodeReturndataFiller.json
state_tests/stCreate2/Create2OOGafterInitCodeReturndata2Filler.json
@manually-enhanced: Do not overwrite. Rewritten by hand; tx `gas_limit`
removed.
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

DEPLOYED_CODE = Op.SSTORE(key=1, value=1)
INITCODE = Op.MSTORE(
    offset=0, value=int.from_bytes(bytes(DEPLOYED_CODE), "big")
) + Op.RETURN(offset=32 - len(DEPLOYED_CODE), size=len(DEPLOYED_CODE))
INITCODE_WORD = int.from_bytes(bytes(INITCODE), "big")
INITCODE_OFFSET = 32 - len(INITCODE)
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

    if opcode == Op.CREATE2:
        create = Op.CREATE2(
            value=0, offset=INITCODE_OFFSET, size=len(INITCODE), salt=0
        )
    else:
        create = Op.CREATE(value=0, offset=INITCODE_OFFSET, size=len(INITCODE))
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
