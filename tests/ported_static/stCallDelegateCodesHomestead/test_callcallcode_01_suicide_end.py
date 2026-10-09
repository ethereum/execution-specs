"""
Test_callcallcode_01_suicide_end.

Ported from:
state_tests/stCallDelegateCodesHomestead/callcallcode_01_SuicideEndFiller.json

@manually-enhanced: Do not overwrite. Explicit gas values removed.
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
        "state_tests/stCallDelegateCodesHomestead/callcallcode_01_SuicideEndFiller.json"  # noqa: E501
    ],
)
@pytest.mark.valid_from("Cancun")
def test_callcallcode_01_suicide_end(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test_callcallcode_01_suicide_end."""
    sender = pre.fund_eoa(amount=0xDE0B6B3A7640000)

    # Source: lll
    # {  (SSTORE 2 1) }
    addr_2 = pre.deploy_contract(
        code=Op.SSTORE(key=0x2, value=0x1) + Op.STOP,
        balance=0x2540BE400,
    )
    # Source: lll
    # {  [[ 1 ]] (DELEGATECALL 50000 <contract:0x1000000000000000000000000000000000000002> 0 64 0 64 ) (SELFDESTRUCT <contract:target:0x1000000000000000000000000000000000000000>) }  # noqa: E501
    addr = pre.deploy_contract(
        code=Op.SSTORE(
            key=0x1,
            value=Op.DELEGATECALL(
                address=addr_2,
                args_offset=0x0,
                args_size=0x40,
                ret_offset=0x0,
                ret_size=0x40,
            ),
        )
        + Op.SELFDESTRUCT(address=Op.CALLER)
        + Op.STOP,
        balance=0x2540BE400,
    )
    # Source: lll
    # {  [[ 0 ]] (CALL 150000 <contract:0x1000000000000000000000000000000000000001> 0 0 64 0 64 ) }  # noqa: E501
    target = pre.deploy_contract(
        code=Op.SSTORE(
            key=0x0,
            value=Op.CALL(
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

    tx = Transaction(sender=sender, to=target, data=Bytes(""))

    post = {
        target: Account(storage={0: 1, 2: 0}),
        addr: Account(storage={1: 1, 2: 1}, balance=0, nonce=1),
        addr_2: Account(storage={2: 0, 3: 0}),
        sender: Account(storage={1: 0, 2: 0, 3: 0}),
    }

    state_test(pre=pre, post=post, tx=tx)
