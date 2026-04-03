"""
Call(oog during init) ->  code.

Ported from:
state_tests/stCallCodes/call_OOG_additionalGasCosts1Filler.json
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
    ["state_tests/stCallCodes/call_OOG_additionalGasCosts1Filler.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_call_oog_additional_gas_costs1(
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
    # { (CALL 6000 <contract:0x1000000000000000000000000000000000000001> 0 0 64 0 64 ) }  # noqa: E501
    target = pre.deploy_contract(  # noqa: F841
        code=Op.CALL(
            gas=0x1770,
            address=0xD0735F094C16E509E8D76999D9EE2E4FD5166C2E,
            value=0x0,
            args_offset=0x0,
            args_size=0x40,
            ret_offset=0x0,
            ret_size=0x40,
        )
        + Op.STOP,
        balance=0xDE0B6B3A7640000,
        nonce=0,
        address=Address(0xEF8DD89DEA93DC2BFF0CE3A1196188496E6C28DC),  # noqa: E501
    )
    # Source: raw
    # 0x6000
    addr = pre.deploy_contract(  # noqa: F841
        code=Op.PUSH1[0x0],
        balance=0xDE0B6B3A7640000,
        nonce=0,
        address=Address(0xD0735F094C16E509E8D76999D9EE2E4FD5166C2E),  # noqa: E501
    )
    pre[sender] = Account(balance=0xDE0B6B3A7640000)

    tx = Transaction(
        sender=sender,
        to=target,
        data=Bytes(""),
        gas_limit=30000,
    )

    post = {sender: Account(nonce=1)}

    state_test(env=env, pre=pre, post=post, tx=tx)
