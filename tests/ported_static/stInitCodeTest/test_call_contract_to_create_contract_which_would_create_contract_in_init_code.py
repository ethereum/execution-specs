"""
Test ported from static filler.

Ported from:
tests/static/state_tests/stInitCodeTest
CallContractToCreateContractWhichWouldCreateContractInInitCodeFiller.json
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
        "tests/static/state_tests/stInitCodeTest/CallContractToCreateContractWhichWouldCreateContractInInitCodeFiller.json",  # noqa: E501
    ],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_call_contract_to_create_contract_which_would_create_contract_in_init_code(  # noqa: E501
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
        gas_limit=1000000000,
    )

    # Source: LLL
    # {(MSTORE 0 0x600c600055602060406000f0)(CREATE 0 20 12)}
    contract = pre.deploy_contract(
        code=(
            Op.MSTORE(offset=0x0, value=0x600C600055602060406000F0)
            + Op.CREATE(value=0x0, offset=0x14, size=0xC)
            + Op.STOP
        ),
        balance=1,
        nonce=0,
        address=Address("0x095e7baea6a6c7c4c2dfeb977efac326af552d87"),  # noqa: E501
    )
    pre[sender] = Account(balance=0x3B9ACA00)

    tx = Transaction(
        sender=sender,
        to=contract,
        data=bytes.fromhex("00"),
        gas_limit=200000,
    )

    post = {
        Address("0xd2571607e241ecf590ed94b12d87c94babe36db6"): Account(
            storage={0: 12},
        ),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
