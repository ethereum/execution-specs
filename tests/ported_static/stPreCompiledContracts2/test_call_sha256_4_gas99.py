"""
Test_call_sha256_4_gas99.

Ported from:
state_tests/stPreCompiledContracts2/CallSha256_4_gas99Filler.json
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
    ["state_tests/stPreCompiledContracts2/CallSha256_4_gas99Filler.json"],
)
@pytest.mark.valid_from("Cancun")
def test_call_sha256_4_gas99(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test_call_sha256_4_gas99."""
    sender = pre.fund_eoa(amount=0xDE0B6B3A7640000)

    # Source: lll
    # { (MSTORE 0 0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff) [[ 2 ]] (CALL 99 2 0 0 32 0 32) [[ 0 ]] (MLOAD 0)}  # noqa: E501
    target = pre.deploy_contract(
        code=Op.MSTORE(
            offset=0x0,
            value=0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF,  # noqa: E501
        )
        + Op.SSTORE(
            key=0x2,
            value=Op.CALL(
                gas=0x63,
                address=0x2,
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
                0: 0xAF9613760F72635FBDB44A5A0A63C39F12AF30F950A6EE5C971BE188E89C4051,  # noqa: E501
                2: 1,
            },
        ),
    }

    state_test(pre=pre, post=post, tx=tx)
