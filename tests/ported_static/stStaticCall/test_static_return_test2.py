"""
Test_static_return_test2.

Ported from:
state_tests/stStaticCall/static_ReturnTest2Filler.json
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
    ["state_tests/stStaticCall/static_ReturnTest2Filler.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.slow
def test_static_return_test2(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test_static_return_test2."""
    sender = pre.fund_eoa(amount=0x5F5E100)

    # Source: lll
    # {(MSTORE 0 (MUL 3 (CALLDATALOAD 0)))(RETURN 0 32)}
    contract_1 = pre.deploy_contract(
        code=Op.MSTORE(
            offset=0x0, value=Op.MUL(0x3, Op.CALLDATALOAD(offset=0x0))
        )
        + Op.RETURN(offset=0x0, size=0x20)
        + Op.STOP,
        balance=0x186A0,
    )
    # Source: lll
    # {(MSTORE 0 0x15)(STATICCALL 7000 0xb94f5374fce5edbc8e2a8697c15331677e6ebf0b 0 32 32 32) [[0]](MLOAD 0) [[1]](MLOAD 32) (RETURN 0 64)}  # noqa: E501
    contract_0 = pre.deploy_contract(
        code=Op.MSTORE(offset=0x0, value=0x15)
        + Op.POP(
            Op.STATICCALL(
                gas=0x1B58,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x20,
                ret_size=0x20,
            )
        )
        + Op.SSTORE(key=0x0, value=Op.MLOAD(offset=0x0))
        + Op.SSTORE(key=0x1, value=Op.MLOAD(offset=0x20))
        + Op.RETURN(offset=0x0, size=0x40)
        + Op.STOP,
    )

    tx = Transaction(
        sender=sender,
        to=contract_0,
        data=Bytes(""),
        gas_limit=250000,
    )

    post = {contract_0: Account(storage={0: 21, 1: 63})}

    state_test(pre=pre, post=post, tx=tx)
