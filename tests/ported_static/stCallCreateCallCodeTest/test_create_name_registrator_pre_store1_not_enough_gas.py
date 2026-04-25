"""
Legacy Test from Christoph. J.

Ported from:
state_tests/stCallCreateCallCodeTest/createNameRegistratorPreStore1NotEnoughGasFiller.json
"""

import pytest
from execution_testing import (
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
        "state_tests/stCallCreateCallCodeTest/createNameRegistratorPreStore1NotEnoughGasFiller.json"  # noqa: E501
    ],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_create_name_registrator_pre_store1_not_enough_gas(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Legacy Test from Christoph."""
    coinbase = Address(0x2ADC25665018AA1FE0E6BC666DAC8FC2697FF9BA)
    contract_0 = Address(0x095E7BAEA6A6C7C4C2DFEB977EFAC326AF552D87)
    sender = pre.fund_eoa(amount=0xDE0B6B3A7640000)

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=100000000,
    )

    # Source: lll
    # {(MSTORE 0 0x6001600155601080600c6000396000f3006000355415600957005b6020356000 )  (MSTORE8 32 0x35) (MSTORE8 33 0x55) (CREATE 23 0 34) }  # noqa: E501
    contract_0 = pre.deploy_contract(  # noqa: F841
        code=Op.MSTORE(
            offset=0x0,
            value=0x6001600155601080600C6000396000F3006000355415600957005B6020356000,  # noqa: E501
        )
        + Op.MSTORE8(offset=0x20, value=0x35)
        + Op.MSTORE8(offset=0x21, value=0x55)
        + Op.CREATE(value=0x17, offset=0x0, size=0x22)
        + Op.STOP,
        balance=0xDE0B6B3A7640000,
        nonce=0,
    )

    tx = Transaction(
        sender=sender,
        to=contract_0,
        data=Bytes(""),
        gas_limit=73071,
        value=0x186A0,
    )

    post = {
        contract_0: Account(nonce=1),
        compute_create_address(
            address=contract_0, nonce=0
        ): Account.NONEXISTENT,
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
