"""
Call -> callcode <->  call.

Ported from:
state_tests/stCallCodes/callcallcodecall_ABCB_RECURSIVEFiller.json
"""

import pytest
from execution_testing import (
    Account,
    Alloc,
    Bytes,
    Fork,
    StateTestFiller,
    Transaction,
)
from execution_testing.forks import Amsterdam
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


@pytest.mark.ported_from(
    ["state_tests/stCallCodes/callcallcodecall_ABCB_RECURSIVEFiller.json"],
)
@pytest.mark.valid_from("Cancun")
def test_callcallcodecall_abcb_recursive(
    state_test: StateTestFiller,
    fork: Fork,
    pre: Alloc,
) -> None:
    """Call -> callcode <->  call."""
    sender = pre.fund_eoa(amount=0xDE0B6B3A7640000)

    # Source: lll
    # {  [[ 2 ]] (CALL 500000 <contract:0x1000000000000000000000000000000000000001> 0 0 64 0 64 ) }  # noqa: E501
    addr_2 = pre.deploy_contract(
        code=Op.SSTORE(
            key=0x2,
            value=Op.CALL(
                gas=0x7A120,
                address=Op.ADDRESS,
                value=0x0,
                args_offset=0x0,
                args_size=0x40,
                ret_offset=0x0,
                ret_size=0x40,
            ),
        )
        + Op.STOP,
        balance=0x2540BE400,
    )
    # Source: lll
    # {  [[ 1 ]] (CALLCODE 1000000 <contract:0x1000000000000000000000000000000000000002> 0 0 64 0 64 ) }  # noqa: E501
    addr = pre.deploy_contract(
        code=Op.SSTORE(
            key=0x1,
            value=Op.CALLCODE(
                gas=0xF4240,
                address=addr_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x40,
                ret_offset=0x0,
                ret_size=0x40,
            ),
        )
        + Op.STOP,
        balance=0x2540BE400,
    )
    # Source: lll
    # {  [[ 0 ]] (CALL 25000000 <contract:0x1000000000000000000000000000000000000001> 0 0 64 0 64 ) }  # noqa: E501
    target = pre.deploy_contract(
        code=Op.SSTORE(
            key=0x0,
            value=Op.CALL(
                gas=0x17D7840,
                address=addr,
                value=0x0,
                args_offset=0x0,
                args_size=0x40,
                ret_offset=0x0,
                ret_size=0x40,
            ),
        )
        + Op.STOP,
        balance=0xDE0B6B3A7640000,
    )

    tx = Transaction(
        sender=sender,
        to=target,
        data=Bytes(""),
        gas_limit=2600000 if fork >= Amsterdam else 600000,
    )

    post = {
        target: Account(storage={0: 1, 1: 0}),
        addr: Account(storage={1: 1, 2: 0}),
        addr_2: Account(storage={1: 0, 2: 0}),
    }

    state_test(pre=pre, post=post, tx=tx)
