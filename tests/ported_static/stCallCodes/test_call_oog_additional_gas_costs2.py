"""
Call(oog during init) ->  code.

Ported from:
state_tests/stCallCodes/call_OOG_additionalGasCosts2Filler.json
"""

import pytest
from execution_testing import (
    EOA,
    Account,
    Address,
    Alloc,
    Bytes,
    Environment,
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
@pytest.mark.pre_alloc_mutable
def test_call_oog_additional_gas_costs2(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Call(oog during init) ->  code ."""
    coinbase = Address(0xEB201D2887816E041F6E807E804F64F3A7A226FE)
    sender = EOA(
        key=0xE04D1AC7DDDA0C98397D56A0B501E960D4CD325A39286919AC23C1A07009A869
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=3000000000,
    )

    pre[coinbase] = Account(balance=0, nonce=1)
    # Source: lll
    # { [[0]] (CALL 6000 <contract:0x1000000000000000000000000000000000000001> 1 0 64 0 64 ) }  # noqa: E501
    target = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(
            key=0x0,
            value=Op.CALL(
                gas=0x1770,
                address=0x89CD1CB7AD11C6949BEC0C8C7533DC073960C54F,
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
        nonce=0,
        address=Address(0xC1F36F15E971B13F8178B8C0C5C4F5E6B1B2B2C3),  # noqa: E501
    )
    # Source: raw
    # 0x6000
    addr = pre.deploy_contract(  # noqa: F841
        code=Op.PUSH1[0x0],
        nonce=0,
        address=Address(0x89CD1CB7AD11C6949BEC0C8C7533DC073960C54F),  # noqa: E501
    )
    pre[sender] = Account(balance=0xDE0B6B3A7640000)

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

    state_test(env=env, pre=pre, post=post, tx=tx)
