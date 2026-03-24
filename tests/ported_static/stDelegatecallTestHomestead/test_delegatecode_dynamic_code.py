"""
Test ported from static filler.

Ported from:
tests/static/state_tests/stDelegatecallTestHomestead
delegatecodeDynamicCodeFiller.json
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
    [
        "tests/static/state_tests/stDelegatecallTestHomestead/delegatecodeDynamicCodeFiller.json",  # noqa: E501
    ],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_delegatecode_dynamic_code(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test ported from static filler."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
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

    # Source: LLL
    # { (MSTORE 0 0x716860016000553360145560005260096017f36000526012600e6001f0600a55) (MSTORE 32 0x604060006040600073ffe4ebd2a68c02d9dcb0a17283d13346beb2d8b6620186) (MSTORE 64 0xa0f4600b55000000000000000000000000000000000000000000000000000000) (CREATE 1 0 96) }  # noqa: E501
    contract = pre.deploy_contract(
        code=(
            Op.MSTORE(
                offset=0x0,
                value=0x716860016000553360145560005260096017F36000526012600E6001F0600A55,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0x20,
                value=0x604060006040600073FFE4EBD2A68C02D9DCB0A17283D13346BEB2D8B6620186,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0x40,
                value=0xA0F4600B55000000000000000000000000000000000000000000000000000000,  # noqa: E501
            )
            + Op.CREATE(value=0x1, offset=0x0, size=0x60)
            + Op.STOP
        ),
        balance=0x2710,
        nonce=0,
        address=Address("0x1000000000000000000000000000000000000000"),  # noqa: E501
    )
    pre[sender] = Account(balance=0x2386F26FC10000)

    tx = Transaction(
        sender=sender,
        to=contract,
        gas_limit=453081,
    )

    post = {
        Address("0x13136008b64ff592819b2fa6d43f2835c452020e"): Account(
            storage={
                10: 0x568A95F77B047BECE6AA68843D2019332C46A585,
                11: 1,
            },
        ),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
