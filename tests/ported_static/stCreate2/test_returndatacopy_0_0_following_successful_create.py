"""
Test_returndatacopy_0_0_following_successful_create.

Ported from:
state_tests/stCreate2/returndatacopy_0_0_following_successful_createFiller.json
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
)
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


@pytest.mark.ported_from(
    [
        "state_tests/stCreate2/returndatacopy_0_0_following_successful_createFiller.json"  # noqa: E501
    ],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_returndatacopy_0_0_following_successful_create(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test_returndatacopy_0_0_following_successful_create."""
    coinbase = Address(0x2ADC25665018AA1FE0E6BC666DAC8FC2697FF9BA)
    contract_0 = Address(0x0F572E5295C57F15886F9B263E2F6D2D6C7B5EC6)
    sender = EOA(
        key=0x45A915E4D060149EB4365960E6A7A45F334393093061116B197E3240065FF2D8
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=47244640256,
    )

    pre[sender] = Account(balance=0x6400000000)
    # Source: lll
    # { (create2 0 0 (lll (seq (SSTORE 0 1) (STOP) ) 0) 0) (RETURNDATACOPY 0 0 0) (SSTORE 0 0) (STOP) }  # noqa: E501
    contract_0 = pre.deploy_contract(  # noqa: F841
        code=Op.PUSH1[0x0]
        + Op.PUSH1[0x7]
        + Op.CODECOPY(dest_offset=0x0, offset=0x1F, size=Op.DUP1)
        + Op.PUSH1[0x0] * 2
        + Op.POP(Op.CREATE2)
        + Op.RETURNDATACOPY(dest_offset=0x0, offset=0x0, size=0x0)
        + Op.SSTORE(key=0x0, value=0x0)
        + Op.STOP * 2
        + Op.INVALID
        + Op.SSTORE(key=0x0, value=0x1)
        + Op.STOP * 2,
        storage={0: 1},
        nonce=0,
        address=Address(0x0F572E5295C57F15886F9B263E2F6D2D6C7B5EC6),  # noqa: E501
    )

    tx = Transaction(
        sender=sender,
        to=contract_0,
        data=Bytes(""),
        gas_limit=100000,
    )

    post = {
        contract_0: Account(storage={0: 0}),
        Address(0x75579E0E990D8361C48B86C1B57686589DF3264A): Account(
            storage={0: 1}
        ),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
