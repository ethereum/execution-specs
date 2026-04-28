"""
Test_delegatecall_in_initcode_to_existing_contract.

Ported from:
state_tests/stDelegatecallTestHomestead/delegatecallInInitcodeToExistingContractFiller.json
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
        "state_tests/stDelegatecallTestHomestead/delegatecallInInitcodeToExistingContractFiller.json"  # noqa: E501
    ],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_delegatecall_in_initcode_to_existing_contract(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test_delegatecall_in_initcode_to_existing_contract."""
    coinbase = Address(0x2ADC25665018AA1FE0E6BC666DAC8FC2697FF9BA)
    contract_0 = Address(0x1000000000000000000000000000000000000000)
    contract_1 = Address(0x1000000000000000000000000000000000000001)
    contract_2 = Address(0x945304EB96065B2A98B57A48A06AE28D285A71B5)
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

    pre[sender] = Account(balance=0x2386F26FC10000)
    # Source: lll
    # { (MSTORE 0 0x604060006040600073945304eb96065b2a98b57a48a06ae28d285a71b5620186) (MSTORE 32 0xa0f4600055336001550000000000000000000000000000000000000000000000) (CREATE 1 0 64) }  # noqa: E501
    contract_0 = pre.deploy_contract(  # noqa: F841
        code=Op.MSTORE(
            offset=0x0,
            value=0x604060006040600073945304EB96065B2A98B57A48A06AE28D285A71B5620186,  # noqa: E501
        )
        + Op.MSTORE(
            offset=0x20,
            value=0xA0F4600055336001550000000000000000000000000000000000000000000000,  # noqa: E501
        )
        + Op.CREATE(value=0x1, offset=0x0, size=0x40)
        + Op.STOP,
        balance=10000,
        nonce=0,
        address=Address(0x1000000000000000000000000000000000000000),  # noqa: E501
    )
    # Source: lll
    # { (MSTORE 0 0x6001600055) (CREATE 1 27 5) }
    contract_1 = pre.deploy_contract(  # noqa: F841
        code=Op.MSTORE(offset=0x0, value=0x6001600055)
        + Op.CREATE(value=0x1, offset=0x1B, size=0x5)
        + Op.STOP,
        balance=1000,
        nonce=0,
        address=Address(0x1000000000000000000000000000000000000001),  # noqa: E501
    )
    # Source: lll
    # { (SSTORE 2 1) [[ 11 ]] (CALLER) }
    contract_2 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x2, value=0x1)
        + Op.SSTORE(key=0xB, value=Op.CALLER)
        + Op.STOP,
        nonce=0,
        address=Address(0x945304EB96065B2A98B57A48A06AE28D285A71B5),  # noqa: E501
    )

    tx = Transaction(
        sender=sender,
        to=contract_0,
        data=Bytes(""),
        gas_limit=453081,
    )

    post = {
        compute_create_address(address=contract_0, nonce=0): Account(
            storage={0: 1, 1: contract_0, 2: 1, 11: contract_0},
            balance=1,
        ),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
