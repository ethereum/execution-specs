"""
Test_static_call_oog_additional_gas_costs1.

Ported from:
state_tests/stStaticCall/static_call_OOG_additionalGasCosts1Filler.json
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
        "state_tests/stStaticCall/static_call_OOG_additionalGasCosts1Filler.json"  # noqa: E501
    ],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.slow
def test_static_call_oog_additional_gas_costs1(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test_static_call_oog_additional_gas_costs1."""
    sender = pre.fund_eoa(amount=0xDE0B6B3A7640000)

    # Source: lll
    # {  [[ 0 ]] (STATICCALL 6000 0x1000000000000000000000000000000000000001 0 64 0 64 ) [[ 1 ]] (GAS) }  # noqa: E501
    target = pre.deploy_contract(
        code=Op.SSTORE(
            key=0x0,
            value=Op.STATICCALL(
                gas=0x1770,
                address=0x1000000000000000000000000000000000000001,
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
        gas_limit=30000,
    )

    post = {sender: Account(nonce=1)}

    state_test(pre=pre, post=post, tx=tx)
