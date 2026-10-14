"""
Test_static_call_value_inherit.

Ported from:
state_tests/stStaticCall/static_call_value_inheritFiller.json
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
    ["state_tests/stStaticCall/static_call_value_inheritFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.slow
def test_static_call_value_inherit(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test_static_call_value_inherit."""
    sender = pre.fund_eoa(amount=0xE8D4A51000)

    # Source: lll
    # { (MSTORE 0 (CALLVALUE)) (RETURN 0 32) }
    addr = pre.deploy_contract(
        code=Op.MSTORE(offset=0x0, value=Op.CALLVALUE)
        + Op.RETURN(offset=0x0, size=0x20)
        + Op.STOP,
        balance=1,
    )
    # Source: lll
    # { [[0]] (STATICCALL 50000 <contract:0xc94f5374fce5edbc8e2a8697c15331677e6ebf0b> 0 0 0 32) [[1]] (MLOAD 0) }  # noqa: E501
    target = pre.deploy_contract(
        code=Op.SSTORE(
            key=0x0,
            value=Op.STATICCALL(
                gas=0xC350,
                address=addr,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x20,
            ),
        )
        + Op.SSTORE(key=0x1, value=Op.MLOAD(offset=0x0))
        + Op.STOP,
        storage={1: 1},
        balance=1,
    )

    tx = Transaction(
        sender=sender,
        to=target,
        data=Bytes(""),
        gas_limit=460000,
        value=10,
    )

    post = {target: Account(storage={0: 1, 1: 0})}

    state_test(pre=pre, post=post, tx=tx)
