"""
Test ported from static filler.

Ported from:
tests/static/state_tests/stSystemOperationsTest
createNameRegistratorOOG_MemExpansionOOVFiller.json
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
        "tests/static/state_tests/stSystemOperationsTest/createNameRegistratorOOG_MemExpansionOOVFiller.json",  # noqa: E501
    ],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_create_name_registrator_oog_mem_expansion_oov(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test ported from static filler."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = EOA(
        key=0xE04D1AC7DDDA0C98397D56A0B501E960D4CD325A39286919AC23C1A07009A869
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
    # { (MSTORE 0 0x601080600c6000396000f3006000355415600957005b60203560003555) [[ 0 ]] (CREATE 11000 3 0xffffffffffffffffffffff) }  # noqa: E501
    contract = pre.deploy_contract(
        code=(
            Op.MSTORE(
                offset=0x0,
                value=0x601080600C6000396000F3006000355415600957005B60203560003555,  # noqa: E501
            )
            + Op.SSTORE(
                key=0x0,
                value=Op.CREATE(
                    value=0x2AF8,
                    offset=0x3,
                    size=0xFFFFFFFFFFFFFFFFFFFFFF,
                ),
            )
            + Op.STOP
        ),
        balance=0x2710,
        nonce=0,
        address=Address("0xb8d613d3333f8ce34bc851256b3096ffa7932f6e"),  # noqa: E501
    )
    pre[sender] = Account(balance=0xDE0B6B3A7640000)

    tx = Transaction(
        sender=sender,
        to=contract,
        gas_limit=300000,
        value=100000,
    )

    post: dict = {}

    state_test(env=env, pre=pre, post=post, tx=tx)
