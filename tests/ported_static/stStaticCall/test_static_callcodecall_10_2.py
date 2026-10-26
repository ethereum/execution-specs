"""
Test_static_callcodecall_10_2.

Ported from:
state_tests/stStaticCall/static_callcodecall_10_2Filler.json
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
    ["state_tests/stStaticCall/static_callcodecall_10_2Filler.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.slow
def test_static_callcodecall_10_2(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test_static_callcodecall_10_2."""
    sender = pre.fund_eoa(amount=0xDE0B6B3A7640000)

    # Source: lll
    # {  (MSTORE 1 1) }
    addr_2 = pre.deploy_contract(
        code=Op.MSTORE(offset=0x1, value=0x1) + Op.STOP,
    )
    # Source: lll
    # {  (STATICCALL 250000 <contract:0x1000000000000000000000000000000000000002> 0 64 0 64 ) }  # noqa: E501
    addr = pre.deploy_contract(
        code=Op.STATICCALL(
            gas=0x3D090,
            address=addr_2,
            args_offset=0x0,
            args_size=0x40,
            ret_offset=0x0,
            ret_size=0x40,
        )
        + Op.STOP,
        balance=0xDE0B6B3A7640000,
    )
    # Source: lll
    # {  [[ 0 ]] (CALLCODE 350000 <contract:0x1000000000000000000000000000000000000001> 1 0 64 0 64 ) [[ 1 ]] 1  }  # noqa: E501
    target = pre.deploy_contract(
        code=Op.SSTORE(
            key=0x0,
            value=Op.CALLCODE(
                gas=0x55730,
                address=addr,
                value=0x1,
                args_offset=0x0,
                args_size=0x40,
                ret_offset=0x0,
                ret_size=0x40,
            ),
        )
        + Op.SSTORE(key=0x1, value=0x1)
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
