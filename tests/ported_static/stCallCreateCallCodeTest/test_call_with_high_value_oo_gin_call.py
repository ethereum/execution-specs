"""
Call with value and oog happens inside.

Ported from:
state_tests/stCallCreateCallCodeTest/callWithHighValueOOGinCallFiller.json
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
    [
        "state_tests/stCallCreateCallCodeTest/callWithHighValueOOGinCallFiller.json"  # noqa: E501
    ],
)
@pytest.mark.valid_from("Cancun")
def test_call_with_high_value_oo_gin_call(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Call with value and oog happens inside."""
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
    # {  [[ 0 ]] (ADD (CALL 10000 <contract:0x945304eb96065b2a98b57a48a06ae28d285a71b5> 1000000000000000000 0 0 0 0 ) 1) }  # noqa: E501
    target = pre.deploy_contract(
        code=Op.SSTORE(
            key=0x0,
            value=Op.ADD(
                Op.CALL(
                    gas=0x2710,
                    address=addr,
                    value=0xDE0B6B3A7640000,
                    args_offset=0x0,
                    args_size=0x0,
                    ret_offset=0x0,
                    ret_size=0x0,
                ),
                0x1,
            ),
        )
        + Op.STOP,
        balance=0xDE0B6B3A7640001,
    )

    tx = Transaction(
        sender=sender,
        to=target,
        data=Bytes(""),
        gas_limit=3000000,
    )

    post = {
        target: Account(storage={0: 1}, balance=0xDE0B6B3A7640001),
        addr: Account(balance=23),
    }

    state_test(pre=pre, post=post, tx=tx)
