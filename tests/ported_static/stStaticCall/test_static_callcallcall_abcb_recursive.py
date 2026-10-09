"""
Test_static_callcallcall_abcb_recursive.

Ported from:
state_tests/stStaticCall/static_callcallcall_ABCB_RECURSIVEFiller.json
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
    ["state_tests/stStaticCall/static_callcallcall_ABCB_RECURSIVEFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.slow
def test_static_callcallcall_abcb_recursive(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test_static_callcallcall_abcb_recursive."""
    sender = pre.fund_eoa(amount=0xDE0B6B3A7640000)

    # Source: lll
    # { (MSTORE 5 1) (STATICCALL 500000 <contract:0x1000000000000000000000000000000000000001> 0 64 0 64 ) (MSTORE 6 1) }  # noqa: E501
    addr_2 = pre.deploy_contract(
        code=Op.MSTORE(offset=0x5, value=0x1)
        + Op.POP(
            Op.STATICCALL(
                gas=0x7A120,
                address=Op.CALLER,
                args_offset=0x0,
                args_size=0x40,
                ret_offset=0x0,
                ret_size=0x40,
            )
        )
        + Op.MSTORE(offset=0x6, value=0x1)
        + Op.STOP,
        balance=0x2540BE400,
    )
    # Source: lll
    # {   (MSTORE 3 1) (STATICCALL 1000000 <contract:0x1000000000000000000000000000000000000002> 0 64 0 64 ) (MSTORE 4 1) }  # noqa: E501
    addr = pre.deploy_contract(
        code=Op.MSTORE(offset=0x3, value=0x1)
        + Op.POP(
            Op.STATICCALL(
                gas=0xF4240,
                address=addr_2,
                args_offset=0x0,
                args_size=0x40,
                ret_offset=0x0,
                ret_size=0x40,
            )
        )
        + Op.MSTORE(offset=0x4, value=0x1)
        + Op.STOP,
        balance=0x2540BE400,
    )
    # Source: lll
    # {  (MSTORE 1 1) (STATICCALL 25000000 <contract:0x1000000000000000000000000000000000000001> 0 64 0 64 ) (MSTORE 2 1) }  # noqa: E501
    target = pre.deploy_contract(
        code=Op.MSTORE(offset=0x1, value=0x1)
        + Op.POP(
            Op.STATICCALL(
                gas=0x17D7840,
                address=addr,
                args_offset=0x0,
                args_size=0x40,
                ret_offset=0x0,
                ret_size=0x40,
            )
        )
        + Op.MSTORE(offset=0x2, value=0x1)
        + Op.STOP,
        balance=0xDE0B6B3A7640000,
    )

    tx = Transaction(
        sender=sender,
        to=target,
        data=Bytes(""),
        gas_limit=600000,
    )

    post = {
        target: Account(storage={0: 0, 1: 0}),
        addr: Account(storage={1: 0, 2: 0}),
        addr_2: Account(storage={1: 0, 2: 0}),
    }

    state_test(pre=pre, post=post, tx=tx)
