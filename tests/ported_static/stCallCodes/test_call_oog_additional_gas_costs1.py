"""
call(oog during init) ->  code 

Ported from:
state_tests/stCallCodes/call_OOG_additionalGasCosts1Filler.json
"""

import pytest
from execution_testing import (
    EOA,
    Account,
    Address,
    Alloc,
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
    """call(oog during init) ->  code """
    coinbase = Address("0xeb201d2887816e041f6e807e804f64f3a7a226fe")
    sender = EOA(
        key=0xe04d1ac7ddda0c98397d56a0b501e960d4cd325a39286919ac23c1a07009a869
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        difficulty=0x20000,
        base_fee_per_gas=10,
        gas_limit=3000000000,
    )

    pre[coinbase] = Account(balance=0, nonce=1)
    # Source: lll
    # { (CALL 6000 <contract:0x1000000000000000000000000000000000000001> 0 0 64 0 64 ) }
    target = pre.deploy_contract(
        code=Op.CALL(gas=0x1770, address=0xd0735f094c16e509e8d76999d9ee2e4fd5166c2e, value=0x0, args_offset=0x0, args_size=0x40, ret_offset=0x0, ret_size=0x40)
        + Op.STOP,
        balance=0xde0b6b3a7640000,
        nonce=0,
        address=Address("0xef8dd89dea93dc2bff0ce3a1196188496e6c28dc"),  # noqa: E501
    )
    # Source: raw
    # 0x6000
    addr_0x1000000000000000000000000000000000000001 = pre.deploy_contract(
        code=Op.PUSH1[0x0],
        balance=0xde0b6b3a7640000,
        nonce=0,
        address=Address("0xd0735f094c16e509e8d76999d9ee2e4fd5166c2e"),  # noqa: E501
    )
    pre[sender] = Account(balance=0xde0b6b3a7640000)


    tx = Transaction(
        sender=sender,
        to=target,
        data=b'',
        gas_limit=30000,
        nonce=0,
        gas_price=10,
    )

    post = {sender: Account(nonce=1)}

    state_test(env=env, pre=pre, post=post, tx=tx)
