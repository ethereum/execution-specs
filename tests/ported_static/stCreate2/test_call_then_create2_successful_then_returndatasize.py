"""
RETURNDATASIZE is zero after a successful CREATE2 that follows a CALL.

Ported from:
state_tests/stCreate2/call_then_create2_successful_then_returndatasizeFiller.json
state_tests/stCreate2/call_outsize_then_create2_successful_then_returndatasizeFiller.json
"""

import pytest
from execution_testing import (
    Account,
    Alloc,
    Bytecode,
    StateTestFiller,
    Transaction,
    compute_create_address,
)
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


@pytest.mark.ported_from(
    [
        "state_tests/stCreate2/call_then_create2_successful_then_returndatasizeFiller.json",  # noqa: E501
        "state_tests/stCreate2/call_outsize_then_create2_successful_then_returndatasizeFiller.json",  # noqa: E501
    ],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "call_ret_size",
    [
        pytest.param(0, id="call_then"),
        pytest.param(0x20, id="call_outsize_then"),
    ],
)
def test_call_then_create2_successful_then_returndatasize(
    state_test: StateTestFiller,
    pre: Alloc,
    call_ret_size: int,
) -> None:
    """RETURNDATASIZE is zero after a successful CREATE2 after a CALL."""
    sender = pre.fund_eoa()

    # Source: lll
    # { (seq (MSTORE 0 0x0000111122223333444455556666777788889999aaaabbbbccccddddeeeeffff) (RETURN 0 32) (STOP) ) }  # noqa: E501
    returner = pre.deploy_contract(
        code=Op.MSTORE(
            offset=0x0,
            value=0x111122223333444455556666777788889999AAAABBBBCCCCDDDDEEEEFFFF,  # noqa: E501
        )
        + Op.RETURN(offset=0x0, size=0x20),
    )
    initcode = Op.MSTORE(offset=0, value=0x112233) + Op.RETURN(
        offset=0, size=0x20
    )

    # Source: lll
    # { (seq (CALL 0x0900000000 <returner> 0 0 0 0 0) (CREATE2 0 0 (lll (seq (mstore 0 0x112233) (RETURN 0 32) (STOP) ) 0) 0) (SSTORE 0 (RETURNDATASIZE)) (STOP) )}  # noqa: E501
    def creator_code(initcode_offset: int) -> Bytecode:
        return (
            Op.POP(Op.CALL(address=returner, ret_size=call_ret_size))
            + Op.CODECOPY(
                dest_offset=0, offset=initcode_offset, size=len(initcode)
            )
            + Op.POP(Op.CREATE2(value=0, offset=0, size=len(initcode), salt=0))
            + Op.SSTORE(key=0, value=Op.RETURNDATASIZE)
            + Op.STOP
        )

    initcode_offset = len(creator_code(0))
    assert len(creator_code(initcode_offset)) == initcode_offset
    creator = pre.deploy_contract(
        code=creator_code(initcode_offset) + initcode,
        storage={0: 1},
    )

    tx = Transaction(sender=sender, to=creator)

    post = {
        creator: Account(storage={0: 0}),
        compute_create_address(
            address=creator, salt=0, initcode=initcode, opcode=Op.CREATE2
        ): Account(code=(0x112233).to_bytes(32, "big")),
    }

    state_test(pre=pre, post=post, tx=tx)
