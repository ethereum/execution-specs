"""
Test_static_zero_value_suicide_oog_revert.

Ported from:
state_tests/stStaticCall/static_ZeroValue_SUICIDE_OOGRevertFiller.json
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
    ["state_tests/stStaticCall/static_ZeroValue_SUICIDE_OOGRevertFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.slow
def test_static_zero_value_suicide_oog_revert(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test_static_zero_value_suicide_oog_revert."""
    sender = pre.fund_eoa(amount=0xE8D4A51000)

    # Source: lll
    # { (SELFDESTRUCT <contract:0xc94f5374fce5edbc8e2a8697c15331677e6ebf0b>)  }
    addr = pre.deploy_contract(
        code=Op.SELFDESTRUCT(address=Op.ADDRESS) + Op.STOP,
    )
    # Source: lll
    # { (STATICCALL 100000 <contract:0xc94f5374fce5edbc8e2a8697c15331677e6ebf0b> 0 0 0 0) (KECCAK256 0x00 0x2fffff) }  # noqa: E501
    target = pre.deploy_contract(
        code=Op.POP(
            Op.STATICCALL(
                gas=0x186A0,
                address=addr,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.SHA3(offset=0x0, size=0x2FFFFF)
        + Op.STOP,
    )

    tx = Transaction(
        sender=sender,
        to=target,
        data=Bytes(""),
        gas_limit=1000000,
    )

    post = {
        sender: Account(nonce=1),
        target: Account(storage={}),
        addr: Account(storage={}),
    }

    state_test(pre=pre, post=post, tx=tx)
