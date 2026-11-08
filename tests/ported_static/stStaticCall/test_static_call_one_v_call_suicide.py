"""
Test_static_call_one_v_call_suicide.

Ported from:
state_tests/stStaticCall/static_CALL_OneVCallSuicideFiller.json
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
    ["state_tests/stStaticCall/static_CALL_OneVCallSuicideFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.slow
def test_static_call_one_v_call_suicide(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test_static_call_one_v_call_suicide."""
    sender = pre.fund_eoa(amount=0xE8D4A51000)

    # Source: lll
    # { (SELFDESTRUCT <contract:target:0xb94f5374fce5edbc8e2a8697c15331677e6ebf0b>) }  # noqa: E501
    addr = pre.deploy_contract(
        code=Op.SELFDESTRUCT(address=Op.CALLER) + Op.STOP,
        balance=1,
    )
    # Source: lll
    # {  [[1]](STATICCALL 60000 <contract:0xc94f5374fce5edbc8e2a8697c15331677e6ebf0b> 0 0 0 0) [[100]] 1 }  # noqa: E501
    target = pre.deploy_contract(
        code=Op.SSTORE(
            key=0x1,
            value=Op.STATICCALL(
                gas=0xEA60,
                address=addr,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            ),
        )
        + Op.SSTORE(key=0x64, value=0x1)
        + Op.STOP,
        balance=100,
    )

    tx = Transaction(
        sender=sender,
        to=target,
        data=Bytes(""),
        gas_limit=600000,
    )

    post = {
        addr: Account(balance=1),
        target: Account(storage={1: 0, 100: 1}),
    }

    state_test(pre=pre, post=post, tx=tx)
