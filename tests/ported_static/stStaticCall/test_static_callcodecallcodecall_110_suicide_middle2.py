"""
Test_static_callcodecallcodecall_110_suicide_middle2.

Ported from:
state_tests/stStaticCall/static_callcodecallcodecall_110_SuicideMiddle2Filler.json
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
        "state_tests/stStaticCall/static_callcodecallcodecall_110_SuicideMiddle2Filler.json"  # noqa: E501
    ],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.slow
def test_static_callcodecallcodecall_110_suicide_middle2(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test_static_callcodecallcodecall_110_suicide_middle2."""
    sender = pre.fund_eoa(amount=0xDE0B6B3A7640000)

    # Source: lll
    # {  (MSTORE 3 1) }
    addr_3 = pre.deploy_contract(
        code=Op.MSTORE(offset=0x3, value=0x1) + Op.STOP,
        balance=0x2540BE400,
    )
    # Source: lll
    # {  (SELFDESTRUCT <contract:target:0x1000000000000000000000000000000000000000>) (STATICCALL 50000 <contract:0x1000000000000000000000000000000000000003> 0 64 0 64 ) }  # noqa: E501
    addr_2 = pre.deploy_contract(
        code=Op.SELFDESTRUCT(address=Op.ADDRESS)
        + Op.STATICCALL(
            gas=0xC350,
            address=addr_3,
            args_offset=0x0,
            args_size=0x40,
            ret_offset=0x0,
            ret_size=0x40,
        )
        + Op.STOP,
        balance=0x2540BE400,
    )
    # Source: lll
    # {  (CALLCODE 100000 <contract:0x1000000000000000000000000000000000000002> (CALLVALUE) 0 64 0 64 ) }  # noqa: E501
    addr = pre.deploy_contract(
        code=Op.CALLCODE(
            gas=0x186A0,
            address=addr_2,
            value=Op.CALLVALUE,
            args_offset=0x0,
            args_size=0x40,
            ret_offset=0x0,
            ret_size=0x40,
        )
        + Op.STOP,
        balance=0x2540BE400,
    )
    # Source: lll
    # {  [[ 0 ]] (CALLCODE 150000 <contract:0x1000000000000000000000000000000000000001> (CALLVALUE) 0 64 0 64 ) [[ 1 ]] (GAS) }  # noqa: E501
    target = pre.deploy_contract(
        code=Op.SSTORE(
            key=0x0,
            value=Op.CALLCODE(
                gas=0x249F0,
                address=addr,
                value=Op.CALLVALUE,
                args_offset=0x0,
                args_size=0x40,
                ret_offset=0x0,
                ret_size=0x40,
            ),
        )
        + Op.SSTORE(key=0x1, value=Op.GAS)
        + Op.STOP,
        balance=0xDE0B6B3A7640000,
    )

    tx = Transaction(
        sender=sender,
        to=target,
        data=Bytes(""),
        gas_limit=3000000,
    )

    post = {target: Account(balance=0xDE0B6B3A7640000)}

    state_test(pre=pre, post=post, tx=tx)
