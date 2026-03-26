"""
test_delegatecode_dynamic_code

Ported from:
state_tests/stDelegatecallTestHomestead/delegatecodeDynamicCodeFiller.json
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
    ["state_tests/stDelegatecallTestHomestead/delegatecodeDynamicCodeFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_delegatecode_dynamic_code(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """test_delegatecode_dynamic_code"""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    contract_0 = Address("0x1000000000000000000000000000000000000000")
    sender = EOA(
        key=0x45a915e4d060149eb4365960e6a7a45f334393093061116b197e3240065ff2d8
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        difficulty=0x20000,
        base_fee_per_gas=10,
        gas_limit=1000000,
    )

    # Source: lll
    # { (MSTORE 0 0x716860016000553360145560005260096017f36000526012600e6001f0600a55) (MSTORE 32 0x604060006040600073ffe4ebd2a68c02d9dcb0a17283d13346beb2d8b6620186) (MSTORE 64 0xa0f4600b55000000000000000000000000000000000000000000000000000000) (CREATE 1 0 96) }
    contract_0 = pre.deploy_contract(
        code=Op.MSTORE(offset=0x0, value=0x716860016000553360145560005260096017f36000526012600e6001f0600a55)
        + Op.MSTORE(offset=0x20, value=0x604060006040600073ffe4ebd2a68c02d9dcb0a17283d13346beb2d8b6620186)
        + Op.MSTORE(offset=0x40, value=0xa0f4600b55000000000000000000000000000000000000000000000000000000)
        + Op.CREATE(value=0x1, offset=0x0, size=0x60) + Op.STOP,
        balance=10000,
        nonce=0,
        address=Address("0x1000000000000000000000000000000000000000"),  # noqa: E501
    )
    pre[sender] = Account(balance=0x2386f26fc10000)


    tx = Transaction(
        sender=sender,
        to=contract_0,
        data=b'',
        gas_limit=453081,
        nonce=0,
        gas_price=10,
    )

    post = {
        Address("0xffe4ebd2a68c02d9dcb0a17283d13346beb2d8b6"): Account.NONEXISTENT,  # noqa: E501
        Address("0x13136008b64ff592819b2fa6d43f2835c452020e"): Account(
                storage={
            0: 0,
            10: 0x568a95f77b047bece6aa68843d2019332c46a585,
            11: 1,
            20: 0,
        },
                balance=0,
            ),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
