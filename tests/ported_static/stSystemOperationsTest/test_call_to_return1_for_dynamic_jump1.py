"""
Test_call_to_return1_for_dynamic_jump1.

Ported from:
state_tests/stSystemOperationsTest/CallToReturn1ForDynamicJump1Filler.json
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
        "state_tests/stSystemOperationsTest/CallToReturn1ForDynamicJump1Filler.json"  # noqa: E501
    ],
)
@pytest.mark.valid_from("Cancun")
def test_call_to_return1_for_dynamic_jump1(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test_call_to_return1_for_dynamic_jump1."""
    sender = pre.fund_eoa(amount=0xDE0B6B3A7640000)

    # Source: raw
    # 0x6001600155602b601f536001601ff3
    addr = pre.deploy_contract(
        code=Op.SSTORE(key=0x1, value=0x1)
        + Op.MSTORE8(offset=0x1F, value=0x2B)
        + Op.RETURN(offset=0x1F, size=0x1),
        balance=23,
    )
    # Source: raw
    # 0x6001601f60006000601773<contract:0x945304eb96065b2a98b57a48a06ae28d285a71b5>6103e8f160005560005156605b6023602355  # noqa: E501
    target = pre.deploy_contract(
        code=Op.SSTORE(
            key=0x0,
            value=Op.CALL(
                gas=0x3E8,
                address=addr,
                value=0x17,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x1F,
                ret_size=0x1,
            ),
        )
        + Op.JUMP(pc=Op.MLOAD(offset=0x0))
        + Op.PUSH1[0x5B]
        + Op.SSTORE(key=0x23, value=0x23),
        balance=0xDE0B6B3A7640000,
    )

    tx = Transaction(
        sender=sender,
        to=target,
        data=Bytes(""),
        gas_limit=300000,
        value=0x186A0,
    )

    post = {target: Account(storage={}, nonce=1)}

    state_test(pre=pre, post=post, tx=tx)
