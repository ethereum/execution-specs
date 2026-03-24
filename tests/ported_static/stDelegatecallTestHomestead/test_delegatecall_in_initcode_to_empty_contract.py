"""
Test ported from static filler.

Ported from:
tests/static/state_tests/stDelegatecallTestHomestead
delegatecallInInitcodeToEmptyContractFiller.json
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
        "tests/static/state_tests/stDelegatecallTestHomestead/delegatecallInInitcodeToEmptyContractFiller.json",  # noqa: E501
    ],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_delegatecall_in_initcode_to_empty_contract(
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
    # { (MSTORE 0 0x604060006040600073945304eb96065b2a98b57a48a06ae28d285a71b5620186) (MSTORE 32 0xa0f4600055000000000000000000000000000000000000000000000000000000) (CREATE 1 0 64) }  # noqa: E501
    contract = pre.deploy_contract(
        code=(
            Op.MSTORE(
                offset=0x0,
                value=0x604060006040600073945304EB96065B2A98B57A48A06AE28D285A71B5620186,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0x20,
                value=0xA0F4600055000000000000000000000000000000000000000000000000000000,  # noqa: E501
            )
            + Op.CREATE(value=0x1, offset=0x0, size=0x40)
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
            storage={0: 1},
        ),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
