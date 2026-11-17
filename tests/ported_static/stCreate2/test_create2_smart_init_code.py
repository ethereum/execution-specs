"""
Create2SmartInitCode. create2 works different each time you call it.

Ported from:
state_tests/stCreate2/create2SmartInitCodeFiller.json
"""

import pytest
from execution_testing import (
    Account,
    Address,
    Alloc,
    Hash,
    StateTestFiller,
    Transaction,
    compute_create_address,
)
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


@pytest.mark.ported_from(
    ["state_tests/stCreate2/create2SmartInitCodeFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize("case", ["selfdestruct_then_collide", "store"])
def test_create2_smart_init_code(
    state_test: StateTestFiller,
    pre: Alloc,
    case: str,
) -> None:
    """Run CREATE2 twice with init code that branches on its storage."""
    sender = pre.fund_eoa()

    if case == "selfdestruct_then_collide":
        # Init code: if sload(1) == 0 { sstore(1, 1) selfdestruct(1) }
        # else { return(0, 10) }
        initcode = bytes.fromhex(
            "600060015414601157600a6000f3601a565b60016001556001ff5b"
        )
    elif case == "store":
        # Init code: if sload(1) == 0 { sstore(1, 1) return(0, 10) }
        initcode = bytes.fromhex(
            "600060015414601157600a6000f3601c565b6001600155600a6000f35b"
        )
    else:
        raise ValueError(f"Unknown case: {case}")

    create2 = Op.CREATE2(
        value=0x1, offset=32 - len(initcode), size=len(initcode), salt=0x0
    )
    creator = pre.deploy_contract(
        code=Op.MSTORE(offset=0, value=int.from_bytes(initcode, "big"))
        + Op.SSTORE(key=0x1, value=create2)
        + Op.SSTORE(key=0x2, value=create2)
        + Op.STOP,
        balance=100,
    )
    created = compute_create_address(
        address=creator, salt=0, initcode=initcode, opcode=Op.CREATE2
    )

    post: dict = {creator: Account(storage={1: created, 2: 0}, nonce=3)}
    if case == "selfdestruct_then_collide":
        post[created] = Account.NONEXISTENT
        post[Address(1)] = Account(balance_change=1)
    else:
        post[created] = Account(storage={1: 1}, code=bytes(10), nonce=1)

    # Source: lll
    # { (CALL (GAS) (CALLDATALOAD 0) 0 0 0 0 0) }
    entry = pre.deploy_contract(
        code=Op.CALL(gas=Op.GAS, address=Op.CALLDATALOAD(offset=0x0))
        + Op.STOP,
    )

    tx = Transaction(
        sender=sender,
        to=entry,
        data=Hash(creator, left_padding=True),
    )

    state_test(pre=pre, post=post, tx=tx)
