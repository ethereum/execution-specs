"""
Test_return_test.

Ported from:
state_tests/stInitCodeTest/ReturnTestFiller.json
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
    ["state_tests/stInitCodeTest/ReturnTestFiller.json"],
)
@pytest.mark.valid_from("Cancun")
def test_return_test(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test_return_test."""
    sender = pre.fund_eoa(amount=0x989680)

    # Source: lll
    # {(MSTORE 0 0x15) (RETURN 31 1)}
    contract_1 = pre.deploy_contract(
        code=Op.MSTORE(offset=0x0, value=0x15)
        + Op.RETURN(offset=0x1F, size=0x1)
        + Op.STOP,
        balance=0x186A0,
    )
    # Source: lll
    # {(CALL 2000 0xb94f5374fce5edbc8e2a8697c15331677e6ebf0b 0 30 1 31 1) [[0]](MLOAD 0) (RETURN 30 2)}  # noqa: E501
    contract_0 = pre.deploy_contract(
        code=Op.POP(
            Op.CALL(
                gas=0x7D0,
                address=contract_1,
                value=0x0,
                args_offset=0x1E,
                args_size=0x1,
                ret_offset=0x1F,
                ret_size=0x1,
            )
        )
        + Op.SSTORE(key=0x0, value=Op.MLOAD(offset=0x0))
        + Op.RETURN(offset=0x1E, size=0x2)
        + Op.STOP,
    )

    tx = Transaction(
        sender=sender,
        to=contract_0,
        data=Bytes(""),
        gas_limit=300000,
    )

    post = {contract_0: Account(storage={0: 21})}

    state_test(pre=pre, post=post, tx=tx)
