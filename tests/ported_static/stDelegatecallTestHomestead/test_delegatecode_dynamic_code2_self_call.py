"""
Test_delegatecode_dynamic_code2_self_call.

Ported from:
state_tests/stDelegatecallTestHomestead/delegatecodeDynamicCode2SelfCallFiller.json
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
    compute_create_address,
)
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


@pytest.mark.ported_from(
    [
        "state_tests/stDelegatecallTestHomestead/delegatecodeDynamicCode2SelfCallFiller.json"  # noqa: E501
    ],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_delegatecode_dynamic_code2_self_call(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test_delegatecode_dynamic_code2_self_call."""
    coinbase = Address(0x2ADC25665018AA1FE0E6BC666DAC8FC2697FF9BA)
    contract_0 = Address(0x1000000000000000000000000000000000000000)
    sender = EOA(
        key=0x45A915E4D060149EB4365960E6A7A45F334393093061116B197E3240065FF2D8
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=1000000,
    )

    # Source: lll
    # {(MSTORE 0 0x60406000604060007313136008b64ff592819b2fa6d43f2835c452020e620186) (MSTORE 32 0xa0f4600b5533600c550000000000000000000000000000000000000000000000) (CREATE 1 0 64) }  # noqa: E501
    contract_0 = pre.deploy_contract(  # noqa: F841
        code=Op.MSTORE(
            offset=0x0,
            value=0x60406000604060007313136008B64FF592819B2FA6D43F2835C452020E620186,  # noqa: E501
        )
        + Op.MSTORE(
            offset=0x20,
            value=0xA0F4600B5533600C550000000000000000000000000000000000000000000000,  # noqa: E501
        )
        + Op.CREATE(value=0x1, offset=0x0, size=0x40)
        + Op.STOP,
        balance=0x10C8E0,
        nonce=0,
        address=Address(0x1000000000000000000000000000000000000000),  # noqa: E501
    )
    pre[sender] = Account(balance=0x2386F26FC10000)

    tx = Transaction(
        sender=sender,
        to=contract_0,
        data=Bytes(""),
        gas_limit=453081,
    )

    post = {
        compute_create_address(address=contract_0, nonce=0): Account(
            storage={
                11: 1,
                12: 0x1000000000000000000000000000000000000000,
            },
            balance=1,
        ),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
