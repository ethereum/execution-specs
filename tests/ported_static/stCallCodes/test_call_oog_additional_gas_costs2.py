"""
Call(oog during init) ->  code.

Ported from:
state_tests/stCallCodes/call_OOG_additionalGasCosts2Filler.json
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
    ["state_tests/stCallCodes/call_OOG_additionalGasCosts2Filler.json"],
)
@pytest.mark.valid_from("Cancun")
def test_call_oog_additional_gas_costs2(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Call(oog during init) ->  code ."""
    sender = pre.fund_eoa(amount=0xDE0B6B3A7640000)

    # Source: raw
    # 0x6000
    addr = pre.deploy_contract(
        code=Op.PUSH1[0x0],
    )
    # Source: lll
    # { [[0]] (CALL 6000 <contract:0x1000000000000000000000000000000000000001> 1 0 64 0 64 ) }  # noqa: E501
    target = pre.deploy_contract(
        code=Op.SSTORE(
            key=0x0,
            value=Op.CALL(
                gas=0x1770,
                address=addr,
                value=0x1,
                args_offset=0x0,
                args_size=0x40,
                ret_offset=0x0,
                ret_size=0x40,
            ),
        )
        + Op.STOP,
        storage={0: 2},
        balance=0xDE0B6B3A7640000,
    )

    tx = Transaction(
        sender=sender,
        to=target,
        data=Bytes(""),
        gas_limit=30000,
    )

    post = {
        addr: Account(balance=0),
        target: Account(storage={0: 2}),
    }

    state_test(pre=pre, post=post, tx=tx)
