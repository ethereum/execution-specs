"""
Test_callcodecallcallcode_101_suicide_middle.

Ported from:
state_tests/stCallDelegateCodesCallCodeHomestead/callcodecallcallcode_101_SuicideMiddleFiller.json
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
    [
        "state_tests/stCallDelegateCodesCallCodeHomestead/callcodecallcallcode_101_SuicideMiddleFiller.json"  # noqa: E501
    ],
)
@pytest.mark.valid_from("Cancun")
def test_callcodecallcallcode_101_suicide_middle(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test_callcodecallcallcode_101_suicide_middle."""
    sender = pre.fund_eoa(amount=0xDE0B6B3A7640000)

    # Source: lll
    # {  (SSTORE 3 1) }
    contract_3 = pre.deploy_contract(
        code=Op.SSTORE(key=0x3, value=0x1) + Op.STOP,
        balance=0x2540BE400,
    )
    # Source: lll
    # { (SELFDESTRUCT 0x1000000000000000000000000000000000000000) [[ 2 ]] (DELEGATECALL 50000 0x1000000000000000000000000000000000000003 0 64 0 64 ) }  # noqa: E501
    contract_2 = pre.deploy_contract(
        code=Op.SELFDESTRUCT(address=Op.ADDRESS)
        + Op.SSTORE(
            key=0x2,
            value=Op.DELEGATECALL(
                gas=0xC350,
                address=contract_3,
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
    # {  [[ 1 ]] (CALLCODE 100000 0x1000000000000000000000000000000000000002 0 0 64 0 64 ) }  # noqa: E501
    contract_1 = pre.deploy_contract(
        code=Op.SSTORE(
            key=0x1,
            value=Op.CALLCODE(
                gas=0x186A0,
                address=contract_2,
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
    # {  [[ 0 ]] (DELEGATECALL 150000 0x1000000000000000000000000000000000000001 0 64 0 64 ) }  # noqa: E501
    contract_0 = pre.deploy_contract(
        code=Op.SSTORE(
            key=0x0,
            value=Op.DELEGATECALL(
                gas=0x249F0,
                address=contract_1,
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
        to=contract_0,
        data=Bytes(""),
        gas_limit=3000000,
    )

    post = {
        contract_0: Account(storage={0: 1, 1: 1}),
        contract_1: Account(storage={1: 0}, balance=0x2540BE400),
        contract_2: Account(storage={2: 0}, balance=0x2540BE400),
        contract_3: Account(storage={3: 0}, balance=0x2540BE400),
        sender: Account(storage={1: 0}),
    }

    state_test(pre=pre, post=post, tx=tx)
