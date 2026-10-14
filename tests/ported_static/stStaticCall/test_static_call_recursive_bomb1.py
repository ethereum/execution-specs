"""
Test_static_call_recursive_bomb1.

Ported from:
state_tests/stStaticCall/static_CallRecursiveBomb1Filler.json
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
    ["state_tests/stStaticCall/static_CallRecursiveBomb1Filler.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.valid_until("Prague")
@pytest.mark.slow
def test_static_call_recursive_bomb1(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test_static_call_recursive_bomb1."""
    sender = pre.fund_eoa(amount=0xDE0B6B3A7640000)

    # Source: lll
    # {  (MSTORE 0 (+ (MLOAD 0) 1))  (STATICCALL (- (GAS) 15000) (ADDRESS) 0 0 0 0)  }  # noqa: E501
    addr = pre.deploy_contract(
        code=Op.MSTORE(offset=0x0, value=Op.ADD(Op.MLOAD(offset=0x0), 0x1))
        + Op.STATICCALL(
            gas=Op.SUB(Op.GAS, 0x3A98),
            address=Op.ADDRESS,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        balance=0x1312D00,
    )
    # Source: lll
    # {  (CALLCODE (GAS) <contract:0x095e7baea6a6c7c4c2dfeb977efac326af552d87> 0 0 0 0 0) [[ 1 ]] 1  }  # noqa: E501
    target = pre.deploy_contract(
        code=Op.POP(
            Op.CALLCODE(
                gas=Op.GAS,
                address=addr,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.SSTORE(key=0x1, value=0x1)
        + Op.STOP,
        balance=0x1312D00,
    )

    tx = Transaction(
        sender=sender,
        to=target,
        data=Bytes(""),
        gas_limit=20622100,
        value=0x186A0,
    )

    post = {target: Account(storage={0: 0, 1: 1})}

    state_test(pre=pre, post=post, tx=tx)
