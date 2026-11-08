"""
Test_callto_return2.

Ported from:
state_tests/stSystemOperationsTest/CalltoReturn2Filler.json
"""

import pytest
from execution_testing import (
    Account,
    Alloc,
    Bytes,
    StateTestFiller,
    Transaction,
)
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


@pytest.mark.ported_from(
    ["state_tests/stSystemOperationsTest/CalltoReturn2Filler.json"],
)
@pytest.mark.valid_from("Cancun")
def test_callto_return2(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test_callto_return2."""
    sender = pre.fund_eoa(amount=0xDE0B6B3A7640000)

    # Source: raw
    # 0x6001600155603760005360026000f2
    addr = pre.deploy_contract(
        code=Op.SSTORE(key=0x1, value=0x1)
        + Op.MSTORE8(offset=0x0, value=0x37)
        + Op.PUSH1[0x2]
        + Op.PUSH1[0x0]
        + Op.CALLCODE,
        balance=23,
    )
    # Source: lll
    # { (MSTORE 0 0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff) (MSTORE 32 0xaaffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffaa ) [[ 0 ]] (CALL 5000 <contract:0x945304eb96065b2a98b57a48a06ae28d285a71b5> 23 0 64 0 2 ) }  # noqa: E501
    target = pre.deploy_contract(
        code=Op.MSTORE(
            offset=0x0,
            value=0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF,  # noqa: E501
        )
        + Op.MSTORE(
            offset=0x20,
            value=0xAAFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFAA,  # noqa: E501
        )
        + Op.SSTORE(
            key=0x0,
            value=Op.CALL(
                gas=0x1388,
                address=addr,
                value=0x17,
                args_offset=0x0,
                args_size=0x40,
                ret_offset=0x0,
                ret_size=0x2,
            ),
        )
        + Op.STOP,
        balance=0xDE0B6B3A7640000,
    )

    tx = Transaction(
        sender=sender,
        to=target,
        data=Bytes(""),
        gas_limit=300000,
        value=0x186A0,
    )

    post = {target: Account(storage={0: 0}, nonce=1)}

    state_test(pre=pre, post=post, tx=tx)
