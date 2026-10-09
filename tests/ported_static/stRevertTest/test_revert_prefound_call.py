"""
Test_revert_prefound_call.

Ported from:
state_tests/stRevertTest/RevertPrefoundCallFiller.json
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
    ["state_tests/stRevertTest/RevertPrefoundCallFiller.json"],
)
@pytest.mark.valid_from("Cancun")
def test_revert_prefound_call(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test_revert_prefound_call."""
    sender = pre.fund_eoa(amount=0xE8D4A51000)

    addr = pre.fund_eoa(amount=1)
    # Source: lll
    # { [[0]] (CALL 50000 <eoa:0x7db299e0885c85039f56fa504a13dd8ce8a56aa7> 0 0 32 0 32) [[1]]12 }  # noqa: E501
    target = pre.deploy_contract(
        code=Op.SSTORE(
            key=0x0,
            value=Op.CALL(
                gas=0xC350,
                address=addr,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x20,
            ),
        )
        + Op.SSTORE(key=0x1, value=0xC)
        + Op.STOP,
        balance=1,
    )

    tx = Transaction(
        sender=sender,
        to=target,
        data=Bytes(""),
        gas_limit=94000,
    )

    post = {addr: Account(storage={}, code=b"", balance=1, nonce=0)}

    state_test(pre=pre, post=post, tx=tx)
