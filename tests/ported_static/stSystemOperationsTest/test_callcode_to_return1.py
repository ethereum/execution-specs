"""
Test_callcode_to_return1.

Ported from:
state_tests/stSystemOperationsTest/callcodeToReturn1Filler.json

@manually-enhanced: Do not overwrite. Explicit gas values removed.
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
    ["state_tests/stSystemOperationsTest/callcodeToReturn1Filler.json"],
)
@pytest.mark.valid_from("Cancun")
def test_callcode_to_return1(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test_callcode_to_return1."""
    sender = pre.fund_eoa(amount=0xDE0B6B3A7640000)

    # Source: raw
    # 0x6001600155603760005360026000f3
    addr = pre.deploy_contract(
        code=Op.SSTORE(key=0x1, value=0x1)
        + Op.MSTORE8(offset=0x0, value=0x37)
        + Op.RETURN(offset=0x0, size=0x2),
        balance=23,
    )
    # Source: lll
    # { (MSTORE 0 0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff) (MSTORE 32 0xaaffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffaa ) [[ 0 ]] (CALLCODE 50000 <contract:0x945304eb96065b2a98b57a48a06ae28d285a71b5> 23 0 64 0 2 ) }  # noqa: E501
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
            value=Op.CALLCODE(
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

    tx = Transaction(sender=sender, to=target, data=Bytes(""), value=0x186A0)

    post = {target: Account(storage={0: 1, 1: 1}, nonce=1)}

    state_test(pre=pre, post=post, tx=tx)
