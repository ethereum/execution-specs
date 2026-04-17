"""
Test_test_random_test.

Ported from:
state_tests/stSystemOperationsTest/testRandomTestFiller.json
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
    ["state_tests/stSystemOperationsTest/testRandomTestFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_test_random_test(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test_test_random_test."""
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
        gas_limit=1000000,
    )

    pre[sender] = Account(balance=0xDE0B6B3A7640000)
    # Source: raw
    # 0x424443444243434383f0155af055
    contract_0 = pre.deploy_contract(  # noqa: F841
        code=Op.TIMESTAMP
        + Op.PREVRANDAO
        + Op.NUMBER
        + Op.PREVRANDAO
        + Op.SSTORE(
            key=Op.CREATE(
                value=Op.GAS,
                offset=Op.ISZERO(
                    Op.CREATE(value=Op.DUP4, offset=Op.NUMBER, size=Op.NUMBER)
                ),
                size=Op.NUMBER,
            ),
            value=Op.TIMESTAMP,
        ),
        balance=0xDE0B6B3A7640000,
        nonce=0,
        address=Address(0x0F572E5295C57F15886F9B263E2F6D2D6C7B5EC6),  # noqa: E501
    )

    tx = Transaction(
        sender=sender,
        to=contract_0,
        data=Bytes(""),
        gas_limit=300000,
        value=0x186A0,
    )

    post = {
        contract_0: Account(
            storage={0xEBCCE5F60530275EE9318CE1EFF9E4BFEE810172: 1000},
            nonce=2,
        ),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
