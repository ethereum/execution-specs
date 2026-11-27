"""
Test if calldata is empty in initcode context.


Ported from:
state_tests/stCreateTest/CREATE2_CallDataFiller.yml
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


@pytest.mark.ported_from(
    ["state_tests/stCreateTest/CREATE2_CallDataFiller.yml"],
)
@pytest.mark.valid_from("Cancun")
def test_create2_call_data(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test if calldata is empty in initcode context."""
    sender = pre.fund_eoa()

    # Source: yul
    # berlin object "C" {
    #   code {
    #     let s := datasize("initcode")
    #     let o := dataoffset("initcode")
    #     codecopy(0, o, s)
    #     let r := create2(0, 0, s, 0)
    #     sstore(0, r)
    #     stop()
    #   }
    #
    #   object "initcode" {
    #     code {
    #       sstore(0, calldataload(0))
    #       calldatacopy(0, 0, 64)
    #       return(0, msize())
    #     }
    #   }
    # }
    creator_code = (
        Op.PUSH1[0x0]
        + Op.PUSH1[0x10]
        + Op.CODECOPY(dest_offset=Op.DUP4, offset=0x11, size=Op.DUP1)
        + Op.DUP2
        + Op.DUP1
        + Op.SSTORE(key=0x0, value=Op.CREATE2)
        + Op.STOP
        + Op.INVALID
        + Op.SSTORE(key=0x0, value=Op.CALLDATALOAD(offset=0x0))
        + Op.CALLDATACOPY(dest_offset=Op.DUP1, offset=0x0, size=0x40)
        + Op.RETURN(offset=0x0, size=Op.MSIZE)
    )
    creator = pre.deploy_contract(code=creator_code)

    initcode = bytes(creator_code)[0x11:]
    created = compute_create_address(
        address=creator, salt=0, initcode=initcode, opcode=Op.CREATE2
    )

    tx = Transaction(
        sender=sender,
        to=creator,
        data=bytes(range(1, 65)),
    )

    post = {
        creator: Account(storage={0: created}),
        created: Account(storage={}, code=bytes(64)),
    }

    state_test(pre=pre, post=post, tx=tx)
