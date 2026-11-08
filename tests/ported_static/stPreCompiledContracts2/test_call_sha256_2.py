"""
Test_call_sha256_2.

Ported from:
state_tests/stPreCompiledContracts2/CallSha256_2Filler.json
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
    ["state_tests/stPreCompiledContracts2/CallSha256_2Filler.json"],
)
@pytest.mark.valid_from("Cancun")
def test_call_sha256_2(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test_call_sha256_2."""
    sender = pre.fund_eoa(amount=0xDE0B6B3A7640000)

    # Source: lll
    # { (MSTORE 5 0xf34578907f) [[ 2 ]] (CALL 500 2 0 0 37 0 32) [[ 0 ]] (MLOAD 0)}  # noqa: E501
    target = pre.deploy_contract(
        code=Op.MSTORE(offset=0x5, value=0xF34578907F)
        + Op.SSTORE(
            key=0x2,
            value=Op.CALL(
                gas=0x1F4,
                address=0x2,
                value=0x0,
                args_offset=0x0,
                args_size=0x25,
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
                0: 0xCB39B3BDE22925B2F931111130C774761D8895E0E08437C9B396C1E97D10F34D,  # noqa: E501
                2: 1,
            },
        ),
    }

    state_test(pre=pre, post=post, tx=tx)
