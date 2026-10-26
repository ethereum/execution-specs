"""
Test_callcode_ripemd160_4.

Ported from:
state_tests/stPreCompiledContracts2/CALLCODERipemd160_4Filler.json
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
    ["state_tests/stPreCompiledContracts2/CALLCODERipemd160_4Filler.json"],
)
@pytest.mark.valid_from("Cancun")
def test_callcode_ripemd160_4(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test_callcode_ripemd160_4."""
    sender = pre.fund_eoa(amount=0xDE0B6B3A7640000)

    # Source: lll
    # { (MSTORE 0 0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff) [[ 2 ]] (CALLCODE 720 3 0 0 32 0 32) [[ 0 ]] (MLOAD 0)}  # noqa: E501
    target = pre.deploy_contract(
        code=Op.MSTORE(
            offset=0x0,
            value=0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF,  # noqa: E501
        )
        + Op.SSTORE(
            key=0x2,
            value=Op.CALLCODE(
                gas=0x2D0,
                address=0x3,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x20,
            ),
        )
        + Op.SSTORE(key=0x0, value=Op.MLOAD(offset=0x0))
        + Op.STOP,
        balance=0x1312D00,
    )

    tx = Transaction(
        sender=sender,
        to=target,
        data=Bytes(""),
        gas_limit=365224,
        value=0x186A0,
    )

    post = {
        target: Account(
            storage={
                0: 0x1CF4E77F5966E13E109703CD8A0DF7CEDA7F3DC3,
                2: 1,
            },
        ),
    }

    state_test(pre=pre, post=post, tx=tx)
