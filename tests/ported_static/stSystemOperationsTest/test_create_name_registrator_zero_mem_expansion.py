"""
test_create_name_registrator_zero_mem_expansion

Ported from:
state_tests/stSystemOperationsTest/createNameRegistratorZeroMemExpansionFiller.json
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
    ["state_tests/stSystemOperationsTest/createNameRegistratorZeroMemExpansionFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_create_name_registrator_zero_mem_expansion(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """test_create_name_registrator_zero_mem_expansion"""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    contract_0 = Address("0x095e7baea6a6c7c4c2dfeb977efac326af552d87")
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
    # { (MSTORE 0 0x601080600c6000396000f3006000355415600957005b60203560003555) [[ 0 ]] (CREATE 23 0 0) }
    contract_0 = pre.deploy_contract(
        code=Op.MSTORE(offset=0x0, value=0x601080600c6000396000f3006000355415600957005b60203560003555)
        + Op.SSTORE(key=0x0, value=Op.CREATE(value=0x17, offset=0x0, size=0x0))
        + Op.STOP,
        balance=0xde0b6b3a7640000,
        nonce=0,
        address=Address("0x095e7baea6a6c7c4c2dfeb977efac326af552d87"),  # noqa: E501
    )
    pre[sender] = Account(balance=0xde0b6b3a7640000)


    tx = Transaction(
        sender=sender,
        to=contract_0,
        data=b'',
        gas_limit=300000,
        value=0x186a0,
        nonce=0,
        gas_price=10,
    )

    post = {
        contract_0: Account(
                storage={0: 0xd2571607e241ecf590ed94b12d87c94babe36db6},
                nonce=1,
            ),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
