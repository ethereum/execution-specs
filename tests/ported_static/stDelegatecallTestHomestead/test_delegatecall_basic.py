"""
Test_delegatecall_basic.

Ported from:
state_tests/stDelegatecallTestHomestead/delegatecallBasicFiller.json
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
    ["state_tests/stDelegatecallTestHomestead/delegatecallBasicFiller.json"],
)
@pytest.mark.valid_from("Cancun")
def test_delegatecall_basic(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test_delegatecall_basic."""
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
    # {  [[ 0 ]] (DELEGATECALL 500000 <contract:0x945304eb96065b2a98b57a48a06ae28d285a71b5> 0 64 0 2 ) }  # noqa: E501
    target = pre.deploy_contract(
        code=Op.SSTORE(
            key=0x0,
            value=Op.DELEGATECALL(
                gas=0x7A120,
                address=addr,
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
        gas_limit=3000000,
    )

    post = {target: Account(storage={0: 1, 1: 1})}

    state_test(pre=pre, post=post, tx=tx)
