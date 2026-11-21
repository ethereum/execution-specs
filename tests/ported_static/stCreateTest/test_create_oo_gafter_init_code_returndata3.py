"""
CALLCODE a contract that runs CREATE/CREATE2, then copy its return data.

The callee either creates and stops, or runs out of gas at the creation;
neither returns data, so copying 32 bytes overruns the buffer and halts
the caller, reverting any creation made in its context.

Ported from:
state_tests/stCreateTest/CreateOOGafterInitCodeReturndata3Filler.json
state_tests/stCreate2/Create2OOGafterInitCodeReturndata3Filler.json
"""

import pytest
from execution_testing import (
    Account,
    Alloc,
    StateTestFiller,
    Transaction,
    compute_create_address,
)
from execution_testing.forks import Fork
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
        "state_tests/stCreateTest/CreateOOGafterInitCodeReturndata3Filler.json",  # noqa: E501
        "state_tests/stCreate2/Create2OOGafterInitCodeReturndata3Filler.json",
    ],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize("opcode", [Op.CREATE, Op.CREATE2])
@pytest.mark.parametrize(
    "copy_size",
    [pytest.param(0, id="in_bounds"), pytest.param(32, id="overrun")],
)
@pytest.mark.parametrize("callee_outcome", ["creates", "out_of_gas"])
def test_create_oo_gafter_init_code_returndata3(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    opcode: Op,
    copy_size: int,
    callee_outcome: str,
) -> None:
    """CALLCODE a creating contract, then copy its return data."""
    sender = pre.fund_eoa()

    store_initcode = Op.MSTORE(
        offset=0, value=INITCODE_WORD, new_memory_size=32
    )
    if opcode == Op.CREATE2:
        create = Op.CREATE2(
            value=0,
            offset=INITCODE_OFFSET,
            size=len(INITCODE),
            salt=0,
            init_code_size=len(INITCODE),
        )
    else:
        create = Op.CREATE(
            value=0,
            offset=INITCODE_OFFSET,
            size=len(INITCODE),
            init_code_size=len(INITCODE),
        )
    creator = pre.deploy_contract(code=store_initcode + create + Op.STOP)

    if callee_outcome == "creates":
        callcode = Op.CALLCODE(address=creator, ret_size=0x20)
    elif callee_outcome == "out_of_gas":
        callcode = Op.CALLCODE(
            gas=(store_initcode + create).execution_cost(fork) - 1,
            address=creator,
            ret_size=0x20,
        )
    else:
        raise ValueError(f"Unknown callee outcome: {callee_outcome}")
    caller = pre.deploy_contract(
        code=Op.POP(callcode)
        + Op.RETURNDATACOPY(dest_offset=0, offset=0, size=copy_size)
        + Op.SSTORE(key=1, value=Op.MLOAD(offset=0))
        + Op.SSTORE(key=2, value=1)
        + Op.STOP,
        storage={1: UNTOUCHED},
    )
    created = compute_create_address(
        address=caller, nonce=1, salt=0, initcode=INITCODE, opcode=opcode
    )

    tx = Transaction(sender=sender, to=caller)

    post: dict = {creator: Account(nonce=1)}
    if copy_size == 32:
        post[caller] = Account(storage={1: UNTOUCHED}, nonce=1)
        post[created] = Account.NONEXISTENT
    elif callee_outcome == "creates":
        post[caller] = Account(storage={1: 0, 2: 1}, nonce=2)
        post[created] = Account(code=DEPLOYED_CODE, nonce=1)
    else:
        post[caller] = Account(storage={1: 0, 2: 1}, nonce=1)
        post[created] = Account.NONEXISTENT

    state_test(pre=pre, post=post, tx=tx)
